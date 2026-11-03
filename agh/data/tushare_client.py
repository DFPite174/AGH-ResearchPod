"""
Tushare Pro Real Financial Data Client for China Convertible Bonds and Equities.
Token is securely loaded from user configuration.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import tushare as ts

DEFAULT_TOKEN_PATH = Path(r"C:\Users\SKT80\Downloads\Tushare api.txt")


class TushareDataClient:
    """
    Dedicated client for pulling authenticated real market data from Tushare Pro.
    """
    def __init__(self, token_path: Optional[Path] = None, cache_dir: Optional[Path] = None):
        self.token_path = token_path or DEFAULT_TOKEN_PATH
        self.token = self._load_token()
        ts.set_token(self.token)
        self.pro = ts.pro_api(self.token)
        
        self.cache_dir = cache_dir or Path(__file__).resolve().parents[2] / "data_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_token(self) -> str:
        if self.token_path.exists():
            with open(self.token_path, "r", encoding="utf-8") as f:
                token = f.read().strip()
                if token:
                    return token
        # Fallback to environment variable
        token = os.environ.get("TUSHARE_TOKEN", "")
        if not token:
            raise ValueError(f"Tushare token file not found at: {self.token_path} and TUSHARE_TOKEN not set.")
        return token

    def get_cb_basic_info(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch basic information of all Chinese convertible bonds.
        """
        cache_file = self.cache_dir / "cb_basic.parquet"
        if cache_file.exists() and not force_refresh:
            return pd.read_parquet(cache_file)
            
        df = self.pro.cb_basic(
            fields="ts_code,bond_short_name,stk_code,stk_short_name,list_date,delist_date,issue_size,conv_price,rates"
        )
        df.to_parquet(cache_file)
        return df

    def get_cb_daily_bars(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch real daily bars for a convertible bond.
        """
        cache_file = self.cache_dir / f"cb_{ts_code}_{start_date}_{end_date}.parquet"
        if cache_file.exists():
            return pd.read_parquet(cache_file)
            
        df = self.pro.cb_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and not df.empty:
            df = df.sort_values(by="trade_date").reset_index(drop=True)
            df.to_parquet(cache_file)
        return df

    def get_stock_daily_bars(self, stk_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch real daily bars for the underlying stock.
        """
        cache_file = self.cache_dir / f"stk_{stk_code}_{start_date}_{end_date}.parquet"
        if cache_file.exists():
            return pd.read_parquet(cache_file)
            
        df = self.pro.daily(ts_code=stk_code, start_date=start_date, end_date=end_date)
        if df is not None and not df.empty:
            df = df.sort_values(by="trade_date").reset_index(drop=True)
            df.to_parquet(cache_file)
        return df

    def get_trade_calendar(self, start_date: str, end_date: str) -> List[str]:
        """
        Fetch trading calendar dates from SSE.
        """
        df = self.pro.trade_cal(exchange="SSE", start_date=start_date, end_date=end_date, is_open="1")
        if df is not None and not df.empty:
            return df["cal_date"].sort_values().tolist()
        return []
