"""
Convertible Bond Data Structures & Abstract Base Pricer Interface.
Implements standardized contract representations and pricing protocol.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class ConvertibleBondContract:
    """
    Representation of Chinese A-share Convertible Bond Terms and Clauses.
    """
    code: str                                  # 转债代码 (如 110059.SH)
    name: str                                  # 转债简称 (如 浦发转债)
    par_value: float = 100.0                   # 债券面值 (标准 100 元)
    maturity_years: float = 6.0                # 债券剩余到期期限 (年)
    conversion_price: float = 10.0             # 初始/当前转股价
    coupon_rates: List[float] = field(default_factory=lambda: [0.002, 0.005, 0.010, 0.015, 0.018, 0.020]) # 各年票面利率
    redemption_premium: float = 106.0          # 到期赎回价 (面值 + 补偿利息)
    
    # 强制赎回条款 (Call Provision): 正股价格 >= conversion_price * call_ratio (如 130%)
    has_call: bool = True
    call_ratio: float = 1.30
    call_price: float = 103.0                  # 发行人赎回价格 (面值 + 应计利息)
    
    # 条件回售条款 (Put Provision): 正股价格 <= conversion_price * put_ratio (如 70%)
    has_put: bool = True
    put_ratio: float = 0.70
    put_price: float = 100.0                   # 回售面值加利息
    put_start_year: float = 4.0                # 允许回售的起始年份 (通常为最后两计息年度)
    
    # 向下修正转股价条款 (Downward Conversion Price Reset - 中国特色核心条款)
    has_downward_reset: bool = True
    reset_trigger_ratio: float = 0.85          # 下修触发比例 (如 85%)
    reset_floor_ratio: float = 0.75            # 下修底价约束 (净资产/20日均价约束)
    credit_spread: float = 0.02                # 发行人评级对应的信用违约利差 (Credit Spread)


@dataclass
class MarketEnvironment:
    """
    Market parameters and macroeconomic environment.
    """
    stock_price: float                         # 正股最新股价 S
    volatility: float                          # 正股年化历史/隐含波动率 sigma
    risk_free_rate: float                      # 无风险折现率 r (如 3M SHIBOR 或国债到期收益率)
    dividend_yield: float = 0.0                # 正股年化分红率 q
    credit_spread: float = 0.02                # 违约信用利差 s (纯债部分折现率为 r + s)


@dataclass
class PricingResult:
    """
    Standard output of convertible bond pricing models.
    """
    theoretical_price: float                   # 理论价值 V
    conversion_value: float                    # 纯转股价值 (S / CP * 100)
    pure_debt_value: float                     # 纯债价值 (DCF)
    option_value: float                        # 内含期权总价值 (V - pure_debt_value)
    delta: float = 0.0                         # 对正股价格敏感度 dV / dS
    gamma: float = 0.0                         # 二阶敏感度 d^2V / dS^2
    vega: float = 0.0                          # 对波动率敏感度 dV / dsigma
    model_name: str = ""                       # 估值模型名称
    extra_details: Dict[str, Any] = field(default_factory=dict)


class BaseCBPricer(ABC):
    """
    Abstract Base Class for Convertible Bond Pricing Models.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def price(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> PricingResult:
        """
        Calculate theoretical fair value and risk metrics of the convertible bond.
        """
        pass

    def compute_pure_debt_value(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> float:
        """
        Calculate pure bond investment value using DCF discounted at (r + s).
        """
        discount_rate = env.risk_free_rate + contract.credit_spread
        years = int(np.ceil(contract.maturity_years))
        pv = 0.0
        for i in range(1, years + 1):
            t = min(float(i), contract.maturity_years)
            c = contract.coupon_rates[min(i - 1, len(contract.coupon_rates) - 1)] * contract.par_value
            if i == years:
                # 最后一期支付票息与到期赎回面值补偿
                c += contract.redemption_premium
            pv += c * np.exp(-discount_rate * t)
        return pv

    def compute_conversion_value(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> float:
        """
        Calculate parity conversion value = (S / CP) * 100
        """
        return (env.stock_price / contract.conversion_price) * contract.par_value
