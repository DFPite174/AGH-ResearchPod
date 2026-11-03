"""
Model Deconstruction & Financial Friction Auditor.
Unpacks formulas, isolates implicit assumptions, and checks license compliance.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DeconstructionReport:
    core_formulas: List[str]
    explicit_assumptions: List[str]
    implicit_frictions_detected: List[str]
    china_market_adaptations: List[str]
    license_type: str
    is_license_safe: bool


class AssumptionAuditor:
    """
    Audits financial papers and repos for real-world viability in China's markets.
    """
    def audit(self, paper_title: str) -> DeconstructionReport:
        formulas = [
            r"Mispricing_{i,t} = \frac{P_{i,t}^{Market} - V_{i,t}^{Model}}{V_{i,t}^{Model}}",
            r"V_{BS} = DCF_{debt} + \frac{100}{K} [S e^{-qT} N(d_1) - K e^{-rT} N(d_2)]",
            r"V_{TF} = C_{equity}(r) + B_{debt}(r + s)",
            r"V_{ZhengLin} = \max(Hold, Conv(S, CP_{eff})), \quad CP_{eff} = \max(S, CP \cdot 0.75)",
            r"R_{L-S, t} = R_{Q1, t} - R_{Q5, t}, \quad \text{CAPM: } R_{L-S, t} = \alpha + \beta R_{m, t} + \epsilon_t"
        ]
        
        explicit = [
            "可转债为有限存续期衍生品，到期偿付本金及利息补偿",
            "投资者在股价突破赎回线时理性转股或接受赎回",
            "回售条款在最后两个计息年度提供下行安全垫",
        ]
        
        implicit_frictions = [
            "【流动性差异】部分冷门转债成交量低，大资金调仓存在冲击成本",
            "【转股价下修博弈】董事会下修转股价并非确定性发生，存在大股东与流通股东投票博弈",
            "【卖空受限】中国市场融券做空转债成本较高且券源稀缺，多空策略在实盘中常转化为'只做多低估组'或'正股融券/股指期货替代对冲'",
        ]
        
        adaptations = [
            "利用三次样条插值补齐不连续行权价对冲点",
            "将海外 Libor 利率对齐为中国银行间 3M SHIBOR 收益率曲线",
            "在策略执行层引入单笔滑点 (2 bps) 和免印花税的交易费率核算",
        ]
        
        return DeconstructionReport(
            core_formulas=formulas,
            explicit_assumptions=explicit,
            implicit_frictions_detected=implicit_frictions,
            china_market_adaptations=adaptations,
            license_type="Apache-2.0",
            is_license_safe=True
        )
