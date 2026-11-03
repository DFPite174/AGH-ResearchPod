"""
DuckDB Data Lake Pipeline for China Convertible Bonds & A-Share Equities (2017-2024).
Pulls 100% authentic market data from Tushare Pro with checkpoint-based resume capability.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import duckdb
import pandas as pd
import tushare as ts

DEFAULT_TOKEN_FILE = Path(r"C:\Users\SKT80\Downloads\Tushare api.txt")
DEFAULT_LAKE_PATH = Path(r"C:\Users\SKT80\Downloads\data_lake\quant_lake.duckdb")


class DuckDBLakeBuilder:
    """
    Orchestrates the ingestion of 8 years (2017-2024) of Chinese CBs and A-share daily bars.
    """
    def __init__(
        self,
        token_path: Path = DEFAULT_TOKEN_FILE,
        db_path: Path = DEFAULT_LAKE_PATH,
        start_date: str = "20170101",
        end_date: str = "20241231"
    ):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.start_date = start_date
        self.end_date = end_date
        
        # Load token
        with open(token_path, "r", encoding="utf-8") as f:
            self.token = f.read().strip()
        ts.set_token(self.token)
        self.pro = ts.pro_api(self.token)
        
        # Connect to DuckDB
        self.con = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self):
        """Initialize relational schema and resume checkpoints in DuckDB."""
        self.con.execute("""
            -- 1. 交易日历表
            CREATE TABLE IF NOT EXISTS tb_trade_cal (
                cal_date VARCHAR PRIMARY KEY,
                is_open INT,
                pretrade_date VARCHAR
            );

            -- 2. 全市场可转债逐日行情 (2017-2024)
            CREATE TABLE IF NOT EXISTS tb_cb_daily (
                ts_code VARCHAR,
                trade_date VARCHAR,
                pre_close DOUBLE,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                change DOUBLE,
                pct_chg DOUBLE,
                vol DOUBLE,
                amount DOUBLE,
                PRIMARY KEY (ts_code, trade_date)
            );

            -- 3. 全市场 A 股所有股票逐日行情 (2017-2024)
            CREATE TABLE IF NOT EXISTS tb_stock_daily (
                ts_code VARCHAR,
                trade_date VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                pre_close DOUBLE,
                change DOUBLE,
                pct_chg DOUBLE,
                vol DOUBLE,
                amount DOUBLE,
                PRIMARY KEY (ts_code, trade_date)
            );

            -- 4. 断点续传检查点表 (确保中断后秒级恢复，不重跑已完成日期)
            CREATE TABLE IF NOT EXISTS tb_sync_checkpoint (
                trade_date VARCHAR PRIMARY KEY,
                cb_synced BOOLEAN DEFAULT FALSE,
                stock_synced BOOLEAN DEFAULT FALSE,
                cb_rows INT DEFAULT 0,
                stock_rows INT DEFAULT 0,
                updated_at TIMESTAMP
            );
        """)

    def sync_metadata(self):
        """Syncs trade calendar, CB basic info, and Stock basic info."""
        print("[Step 1/3] Syncing metadata (Calendar, CB master, Stock master)...")
        
        # 1. 交易日历
        df_cal = self.pro.trade_cal(exchange="SSE", start_date=self.start_date, end_date=self.end_date)
        if df_cal is not None and not df_cal.empty:
            self.con.register("df_cal_view", df_cal[["cal_date", "is_open", "pretrade_date"]])
            self.con.execute("INSERT OR REPLACE INTO tb_trade_cal SELECT * FROM df_cal_view")
            print(f" -> Trade calendar synced: {len(df_cal)} records.")

        # 2. 可转债基础信息
        df_cb = self.pro.cb_basic(fields="ts_code,bond_short_name,stk_code,stk_short_name,list_date,delist_date,issue_size,conv_price")
        if df_cb is not None and not df_cb.empty:
            self.con.register("df_cb_view", df_cb)
            self.con.execute("CREATE OR REPLACE TABLE tb_cb_basic AS SELECT * FROM df_cb_view")
            print(f" -> CB metadata synced: {len(df_cb)} convertible bonds.")

        # 3. 股票基础信息
        df_stk = self.pro.stock_basic(fields="ts_code,symbol,name,area,industry,market,list_date,delist_date")
        if df_stk is not None and not df_stk.empty:
            self.con.register("df_stk_view", df_stk)
            self.con.execute("CREATE OR REPLACE TABLE tb_stock_basic AS SELECT * FROM df_stk_view")
            print(f" -> Stock metadata synced: {len(df_stk)} A-share stocks.")

    def get_open_trading_days(self) -> list:
        """Fetch all open trading days in the target interval."""
        res = self.con.execute("""
            SELECT cal_date FROM tb_trade_cal 
            WHERE is_open = 1 AND cal_date >= ? AND cal_date <= ?
            ORDER BY cal_date ASC
        """, [self.start_date, self.end_date]).fetchall()
        return [r[0] for r in res]

    def sync_daily_data(self, sync_stocks: bool = True, limit_days: Optional[int] = None):
        """
        Syncs daily bars by trading day with checkpoint resume.
        Takes advantage of Tushare's single-call-per-day cross-sectional endpoint.
        """
        trading_days = self.get_open_trading_days()
        if limit_days:
            trading_days = trading_days[:limit_days]
            
        print(f"[Step 2/3] Starting daily bars ingestion for {len(trading_days)} trading days...")
        
        for idx, t_date in enumerate(trading_days, 1):
            # 检查断点
            cp = self.con.execute("SELECT cb_synced, stock_synced FROM tb_sync_checkpoint WHERE trade_date = ?", [t_date]).fetchone()
            cb_synced = cp[0] if cp else False
            stock_synced = cp[1] if cp else False
            
            cb_count = 0
            stk_count = 0
            
            # 1. 拉取可转债全市场单日日线
            if not cb_synced:
                for retry in range(3):
                    try:
                        df_cb_day = self.pro.cb_daily(trade_date=t_date)
                        if df_cb_day is not None and not df_cb_day.empty:
                            cb_cols = ["ts_code", "trade_date", "pre_close", "open", "high", "low", "close", "change", "pct_chg", "vol", "amount"]
                            df_cb_filtered = df_cb_day[cb_cols]
                            self.con.register("df_cb_batch", df_cb_filtered)
                            self.con.execute("INSERT OR REPLACE INTO tb_cb_daily SELECT * FROM df_cb_batch")
                            cb_count = len(df_cb_filtered)
                        cb_synced = True
                        break
                    except Exception as e:
                        time.sleep(2.0 * (retry + 1))
                time.sleep(0.15)  # 限流保护
                
            # 2. 拉取全市场 5300 只 A 股所有股票单日日线
            if sync_stocks and not stock_synced:
                for retry in range(3):
                    try:
                        df_stk_day = self.pro.daily(trade_date=t_date)
                        if df_stk_day is not None and not df_stk_day.empty:
                            stk_cols = ["ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]
                            df_stk_filtered = df_stk_day[stk_cols]
                            self.con.register("df_stk_batch", df_stk_filtered)
                            self.con.execute("INSERT OR REPLACE INTO tb_stock_daily SELECT * FROM df_stk_batch")
                            stk_count = len(df_stk_filtered)
                        stock_synced = True
                        break
                    except Exception as e:
                        time.sleep(2.0 * (retry + 1))
                time.sleep(0.15)  # 限流保护

            # 更新检查点
            now_ts = datetime.now()
            self.con.execute("""
                INSERT OR REPLACE INTO tb_sync_checkpoint (trade_date, cb_synced, stock_synced, cb_rows, stock_rows, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [t_date, cb_synced, stock_synced, cb_count, stk_count, now_ts])
            
            if idx % 10 == 0 or idx == len(trading_days):
                print(f" -> Progress: [{idx}/{len(trading_days)}] ({t_date}) | CB rows: {cb_count} | Stock rows: {stk_count}")

    def inspect_lake(self):
        """Displays total row counts and storage profile of the DuckDB lake."""
        print("\n" + "=" * 70)
        print(" [DuckDB Quant Lake Status Report]")
        print("=" * 70)
        tables = ["tb_trade_cal", "tb_cb_basic", "tb_stock_basic", "tb_cb_daily", "tb_stock_daily", "tb_sync_checkpoint"]
        for t in tables:
            cnt = self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f" Table: {t:<22} | Row Count: {cnt:>10,}")
            
        file_size_mb = self.db_path.stat().st_size / (1024 * 1024)
        print(f"\n Database File Location: {self.db_path}")
        print(f" Database Disk Footprint: {file_size_mb:.2f} MB")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="DuckDB Data Lake Builder for China CBs & Equities")
    parser.add_argument("--days", type=int, default=None, help="Limit number of days to sync")
    parser.add_argument("--status", action="store_true", help="Display lake row counts and storage")
    parser.add_argument("--meta-only", action="store_true", help="Sync only metadata tables")
    args = parser.parse_args()

    builder = DuckDBLakeBuilder(start_date="20170101", end_date="20241231")
    
    if args.status:
        builder.inspect_lake()
        return

    builder.sync_metadata()
    if not args.meta_only:
        builder.sync_daily_data(sync_stocks=True, limit_days=args.days)
    builder.inspect_lake()


if __name__ == "__main__":
    main()
