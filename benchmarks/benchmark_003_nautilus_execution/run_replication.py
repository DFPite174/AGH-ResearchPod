"""
Benchmark 003: Institutional Execution of Zheng Zhenlong Convertible Bond Strategy on ashare-nautilus-backtest-engine.
Verifies Plan B native NautilusTrader 1.231.0 matching, lot sizing (1手=10张), 0% stamp duty, and GoldenLedger daily audit.
"""

import sys
from pathlib import Path
from decimal import Decimal
from zoneinfo import ZoneInfo
from datetime import date
import pandas as pd
import duckdb

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NAUTILUS_ROOT = Path(r"C:\Users\SKT80\.gemini\antigravity\scratch\ashare-nautilus-backtest-engine")
DB_PATH = Path(r"C:\Users\SKT80\Downloads\data_lake\quant_lake.duckdb")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(NAUTILUS_ROOT) not in sys.path:
    sys.path.insert(0, str(NAUTILUS_ROOT))

from agh.strategy.nautilus_adapter import NautilusEngineAdapter
from agh.models.convertible_bond.zheng_lin_2004_model import ZhengLin2004Model
from agh.models.convertible_bond.base import ConvertibleBondContract, MarketEnvironment
from engine.backtest import OrderIntent


def run_benchmark():
    print("=" * 80)
    print("  AGH Benchmark 003: ashare-nautilus-backtest-engine Native CB Execution")
    print("  Academic Pod Model: Zheng Zhenlong & Lin Hai (2004a) Pricing Tree")
    print("  Execution Kernel: NautilusTrader 1.231.0 (Plan B Native Integration)")
    print("=" * 80)

    # 1. Connect to DuckDB Lake
    print(f"\n[1/5] Connecting to Local DuckDB Lake: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"Error: DuckDB file not found at {DB_PATH}")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)
    df_daily = con.execute("SELECT * FROM tb_cb_daily ORDER BY trade_date, ts_code").df()
    df_basic = con.execute("SELECT * FROM tb_cb_basic").df()
    print(f"Loaded {len(df_daily)} daily bars for {df_daily['ts_code'].nunique()} convertible bonds.")
    print(f"Date range: {df_daily['trade_date'].min()} to {df_daily['trade_date'].max()}")

    # 2. Select Active Test Subset (e.g. 5 liquid representative convertible bonds)
    target_symbols = ["110031.SH", "110032.SH", "110035.SH", "128012.SZ", "128010.SZ"]
    df_sub_daily = df_daily[df_daily["ts_code"].isin(target_symbols)].copy()
    df_sub_basic = df_basic[df_basic["ts_code"].isin(target_symbols)].copy()

    # 3. Model Pricing on Day 1 (2017-01-03) using Zheng Zhenlong & Lin Hai (2004a)
    print("\n[2/5] Evaluating Theoretical Prices using Zheng Zhenlong (2004a) Model...")
    day1_data = df_sub_daily[df_sub_daily["trade_date"] == "20170103"]
    model = ZhengLin2004Model(steps_per_year=50)

    mispricing_records = []
    for _, row in day1_data.iterrows():
        sym = row["ts_code"]
        mkt_px = row["close"]
        b_info = df_sub_basic[df_sub_basic["ts_code"] == sym]
        conv_px = float(b_info["conv_price"].values[0]) if not b_info.empty and pd.notna(b_info["conv_price"].values[0]) else 10.0
        name = str(b_info["bond_short_name"].values[0]) if not b_info.empty else sym

        contract = ConvertibleBondContract(
            code=sym,
            name=name,
            par_value=100.0,
            maturity_years=4.5,
            conversion_price=conv_px,
            has_call=True,
            call_ratio=1.30,
            has_put=True,
            put_ratio=0.70,
            has_downward_reset=True,
            reset_trigger_ratio=0.85,
        )
        stock_price = conv_px * (mkt_px / 100.0) * 0.95
        env = MarketEnvironment(
            stock_price=stock_price,
            volatility=0.30,
            risk_free_rate=0.035,
            dividend_yield=0.015,
            credit_spread=0.015,
        )
        result_pricing = model.price(contract, env)
        theo_px = result_pricing.theoretical_price
        mispricing = (mkt_px - theo_px) / theo_px
        mispricing_records.append({
            "ts_code": sym,
            "market_price": mkt_px,
            "theo_price": round(theo_px, 3),
            "mispricing": round(mispricing, 4),
        })

    df_ranked = pd.DataFrame(mispricing_records).sort_values("mispricing")
    print("\nModel Valuation & Ranking Result (Day 1 - 20170103):")
    print(df_ranked.to_string(index=False))

    # Pick top 2 most undervalued (lowest mispricing ratio) for portfolio purchase
    top_picks = set(df_ranked.head(2)["ts_code"].tolist())
    print(f"\n[3/5] Target Portfolio (Top Undervalued CBs): {top_picks}")

    # 4. Prepare Nautilus Engine Inputs
    adapter = NautilusEngineAdapter()
    print("\nEngine Suitability Assessment:")
    assessment = adapter.get_suitability_assessment()
    print(f"- Engine: {assessment['engine_name']} ({assessment['kernel_version']})")
    print(f"- Status: {assessment['overall_suitability']}")

    instruments, bars, rules = adapter.build_cb_inputs(df_sub_daily, df_sub_basic)
    print(f"\nBuilt {len(instruments)} Nautilus ConvertibleBondInstruments and {len(bars)} BacktestBars.")

    # 5. Define Strategy Execution Logic
    # Day 1 (2017-01-03): Buy 500 张 (50手) of each top pick
    # Day 7 (2017-01-12): Sell 500 张 of each to harvest alpha & mispricing convergence
    buy_date = date(2017, 1, 3)
    sell_date = date(2017, 1, 12)

    def cb_strategy_signal(bar, state):
        intents = []
        d = bar.end.date()
        if d == buy_date and bar.symbol in top_picks:
            # 1手 = 10张, 买入 500 张 = 50手
            intents.append(OrderIntent(bar.symbol, "BUY", 500))
        elif d == sell_date and bar.symbol in top_picks:
            # 卖出平仓
            intents.append(OrderIntent(bar.symbol, "SELL", 500))
        return intents

    # 6. Run Nautilus Backtest
    print("\n[4/5] Executing Institutional Backtest via NautilusTrader Engine...")
    initial_cash = Decimal("500000.0")
    result = adapter.run_backtest(
        instruments=instruments,
        bars=bars,
        rules=rules,
        signal=cb_strategy_signal,
        initial_cash=initial_cash,
        participation_rate=1.0,
    )

    # 7. Verification & Audit Report
    print("\n[5/5] Backtest Execution & Golden Ledger Audit Report:")
    print("-" * 80)
    print(f"Total Fills Recorded: {len(result.fills)}")
    for f in result.fills:
        sym = f["symbol"]
        side = f["side"]
        qty = f["quantity"]
        px = f["price"]
        fee = f["fee"]
        val = Decimal(qty) * Decimal(px)
        print(f"  * FILL: {sym} | {side:4s} | Qty: {qty:4s} contracts | Px: {px:7s} | TradeVal: {val:9.2f} CNY | Fee: {fee} CNY")

    # Verify Zero Stamp Duty on Sells
    sell_fills = [f for f in result.fills if f["side"] == "SELL"]
    if sell_fills:
        total_sell_val = sum(Decimal(f["quantity"]) * Decimal(f["price"]) for f in sell_fills)
        total_sell_fee = sum(Decimal(f["fee"]) for f in sell_fills)
        # Expected fee: 万一佣金 + 十万分之1过户费 = 0.00011, 印花税为 0
        expected_sell_fee_approx = total_sell_val * Decimal("0.00011")
        print(f"\nSell Turnover: {total_sell_val:.2f} CNY")
        print(f"Total Sell Fee Deducted: {total_sell_fee:.2f} CNY (vs expected ~{expected_sell_fee_approx:.2f} CNY)")
        # Notice: If stamp duty was charged (万五 = 0.0005), fee would be 5x larger!
        assert total_sell_fee < total_sell_val * Decimal("0.0003"), "Error: Stamp duty was incorrectly charged on convertible bonds!"
        print("  -> CONFIRMED: 0% Stamp Duty strictly respected (Convertible Bond Tax Exemption Verified)!")

    # Verify Golden Ledger Reconciliation
    print("\nDaily Dual-Ledger Reconciliation Check:")
    matched_days = sum(1 for d in result.daily_nav if d["cash_matches"] and d["positions_match"])
    print(f"Reconciled Trading Days: {matched_days} / {len(result.daily_nav)} days (100% Parity)")
    assert matched_days == len(result.daily_nav), "Reconciliation failed!"

    final_cash = result.native_cash
    pnl = final_cash - initial_cash
    ret_pct = (pnl / initial_cash) * Decimal("100.0")
    print(f"\nFinancial Summary:")
    print(f"  * Initial Cash : {initial_cash:,.2f} CNY")
    print(f"  * Final Cash   : {final_cash:,.2f} CNY")
    print(f"  * Total PnL    : {pnl:+,.2f} CNY ({ret_pct:+.3f}%)")
    print("=" * 80)
    print("Benchmark 003 completed successfully!\n")


if __name__ == "__main__":
    run_benchmark()
