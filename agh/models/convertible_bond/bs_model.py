"""
1. BS Decomposition Model (Black & Scholes, 1973; Ingersoll, 1977)
Decomposes convertible bond into: Pure Bond (DCF) + European Call Option.
Serves as the classical benchmark model with the most restrictive assumptions.
"""

import numpy as np
from scipy.stats import norm
from .base import BaseCBPricer, ConvertibleBondContract, MarketEnvironment, PricingResult


class BSDecompositionModel(BaseCBPricer):
    """
    Classical Black-Scholes Decomposition Model.
    V = Pure Debt + Conversion Call Option.
    Neglects American early conversion, call, put, and reset features.
    """
    def __init__(self):
        super().__init__(name="BS_Model_1973")

    def price(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> PricingResult:
        pure_debt = self.compute_pure_debt_value(contract, env)
        conv_value = self.compute_conversion_value(contract, env)
        
        S = env.stock_price
        K = contract.conversion_price
        T = max(contract.maturity_years, 0.001)
        sigma = max(env.volatility, 0.001)
        r = env.risk_free_rate
        q = env.dividend_yield
        
        # Black-Scholes 欧式看涨期权公式
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        option_per_share = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        # 每张可转债对应的股票转换手数: 100 / K
        conversion_ratio = contract.par_value / K
        total_option_val = conversion_ratio * max(option_per_share, 0.0)
        
        theoretical_price = pure_debt + total_option_val
        
        # Greeks
        delta = conversion_ratio * np.exp(-q * T) * norm.cdf(d1)
        gamma = conversion_ratio * (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))
        vega = conversion_ratio * S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100.0
        
        return PricingResult(
            theoretical_price=float(theoretical_price),
            conversion_value=float(conv_value),
            pure_debt_value=float(pure_debt),
            option_value=float(total_option_val),
            delta=float(delta),
            gamma=float(gamma),
            vega=float(vega),
            model_name=self.name,
            extra_details={"d1": float(d1), "d2": float(d2)}
        )
