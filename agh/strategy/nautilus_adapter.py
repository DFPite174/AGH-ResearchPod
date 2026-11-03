"""
Adapter for ashare-nautilus-backtest-engine (NautilusTrader 1.231.0 backend).
Connects AGH Research Pod with institutional-grade A-share execution and golden ledger reconciliation.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

NAUTILUS_PROJECT_PATH = Path(r"C:\Users\SKT80\.gemini\antigravity\scratch\ashare-nautilus-backtest-engine")


class NautilusEngineAdapter:
    """
    Bridges AGH valuation outputs with ashare-nautilus-backtest-engine.
    """
    def __init__(self, engine_dir: Path = NAUTILUS_PROJECT_PATH):
        self.engine_dir = engine_dir
        self.is_available = self._check_availability()
        if self.is_available:
            if str(self.engine_dir) not in sys.path:
                sys.path.insert(0, str(self.engine_dir))

    def _check_availability(self) -> bool:
        return self.engine_dir.exists() and (self.engine_dir / "engine").exists()

    def get_suitability_assessment(self) -> Dict[str, Any]:
        """
        Technical suitability review of ashare-nautilus-backtest-engine for AGH Research Pod.
        """
        return {
            "engine_name": "ashare-nautilus-backtest-engine",
            "kernel_version": "NautilusTrader 1.231.0 (Rust/Cython)",
            "overall_suitability": "Highly Suitable for Equity-Long Execution; Requires Adaptation for Derivatives/CB",
            "strengths": [
                "原生订单级撮合 (Native Order Matching)，彻底杜绝传统回测的无滑点、偷价漏洞",
                "严格复刻中国 A 股制度：T+1、涨跌停 (BOUNDED) 强制拦截、价格笼子",
                "双账本逐日核对机制 (Golden Ledger)，资金与持仓不一致时 Fail-fast，达到机构级审计标准",
                "包含成交量参与率预算 (participation_rate)，防止大资金虚假流动性成交"
            ],
            "limitations_for_cb_research": [
                "标的原生限定于沪深普通股票 (Cash-only Equity)，未原生支持可转债 1手=10张(面值1000元) 及免印花税机制",
                "方向仅支持单边多头 (Long-only Cash Account)，未开放融券卖空 (Short-Selling) 与衍生品对冲",
                "输入数据要求强严格的每日每股 rules.csv (涨跌停价、停牌状态)，数据对齐门槛高"
            ],
            "recommended_deployment_architecture": (
                "双轨制协同: "
                "1. 上游学术与因子研究层: 采用 Tushare 全量真实可转债数据进行五大模型理论定价与五分位偏离度多空检验; "
                "2. 下游生产执行回测层: 将 Q1 深度低估转债对应的 A 股正股，输入 ashare-nautilus-backtest-engine 作为高保真多头现货组合回测。"
            )
        }
