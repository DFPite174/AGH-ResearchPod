"""
5. Liu-Wei (2006) Model - 刘娥平与韦科帆 (2006) 模型
Model with Liquidity-Credit Spread Adjustments and Execution Delay Boundaries.
Reference: Liu Eping, Wei Kefan (2006), 'Empirical Comparison of Pricing Models for Chinese Convertible Bonds'.
"""

import numpy as np
from .base import BaseCBPricer, ConvertibleBondContract, MarketEnvironment, PricingResult


class LiuWei2006Model(BaseCBPricer):
    """
    Liu & Wei (2006) Binomial Model.
    Considers liquidity discounts, credit risk spreads, and delayed execution friction
    in China's call and conversion provisions.
    """
    def __init__(self, steps_per_year: int = 50, liquidity_discount: float = 0.015):
        super().__init__(name="Liu_Wei_2006")
        self.steps_per_year = steps_per_year
        self.liquidity_discount = liquidity_discount  # 流动性摩擦折价

    def price(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> PricingResult:
        T = max(contract.maturity_years, 0.01)
        steps = max(int(T * self.steps_per_year), 30)
        dt = T / steps
        r = env.risk_free_rate
        s = contract.credit_spread
        # 综合考虑违约风险与流动性溢价的折现率
        discount_rate = r + s + self.liquidity_discount
        
        sigma = max(env.volatility, 0.01)
        q = env.dividend_yield
        S0 = env.stock_price
        CP_base = contract.conversion_price
        par = contract.par_value
        
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)
        p = np.clip(p, 0.001, 0.999)
        df = np.exp(-discount_rate * dt)
        coupon_step = (contract.coupon_rates[-1] * par) * (dt / 1.0)
        
        # 终端节点 (T)
        j_mesh = np.arange(steps + 1)
        S_T = S0 * (u ** j_mesh) * (d ** (steps - j_mesh))
        
        # 终端价值计算
        conv_T = (S_T / CP_base) * par
        V = np.maximum(conv_T, contract.redemption_premium)
        
        # 逆向倒推
        for i in range(steps - 1, -1, -1):
            t_curr = i * dt
            j_curr = np.arange(i + 1)
            S_curr = S0 * (u ** j_curr) * (d ** (i - j_curr))
            
            # 刘-韦模型假定下修具有一定的滞后平滑效应
            if contract.has_downward_reset:
                reset_cond = S_curr <= (CP_base * contract.reset_trigger_ratio)
                # 平滑下修转股价
                effective_cp = np.where(reset_cond, np.maximum(0.9 * S_curr + 0.1 * CP_base, CP_base * contract.reset_floor_ratio), CP_base)
            else:
                effective_cp = CP_base
                
            conv_curr = (S_curr / effective_cp) * par
            hold_val = df * (p * V[1:] + (1.0 - p) * V[:-1]) + coupon_step
            
            # 美式转股
            node_val = np.maximum(hold_val, conv_curr)
            
            # 提前赎回条款 (带有 5% 的公告缓冲摩擦)
            if contract.has_call:
                call_mask = S_curr >= (contract.call_ratio * CP_base * 1.02)
                node_val = np.where(call_mask, np.maximum(conv_curr, contract.call_price), node_val)
            
            # 回售条款
            if contract.has_put and t_curr >= contract.put_start_year:
                put_mask = S_curr <= (contract.put_ratio * CP_base)
                node_val = np.where(put_mask, np.maximum(node_val, contract.put_price), node_val)
                
            V = node_val
            
        theoretical_price = float(V[0])
        pure_debt = self.compute_pure_debt_value(contract, env)
        conv_val = self.compute_conversion_value(contract, env)
        option_val = max(theoretical_price - pure_debt, 0.0)
        delta = (theoretical_price - conv_val) / (S0 * 0.1)
        
        return PricingResult(
            theoretical_price=theoretical_price,
            conversion_value=float(conv_val),
            pure_debt_value=float(pure_debt),
            option_value=float(option_val),
            delta=float(delta),
            model_name=self.name,
            extra_details={"steps": steps, "liquidity_discount": self.liquidity_discount}
        )
