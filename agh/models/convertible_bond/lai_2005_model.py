"""
4. Lai et al. (2005) Model - 赖其男等 (2005) 模型
Model with Exogenous Downward Reset Probability and Term-Structure Adjusted Discounting.
Reference: Lai Qinan, Bao Weijun, Yao Changhui (2005), 'Empirical Study on Convertible Bond Pricing in China', Journal of Financial Research.
"""

import numpy as np
from .base import BaseCBPricer, ConvertibleBondContract, MarketEnvironment, PricingResult


class Lai2005Model(BaseCBPricer):
    """
    Lai et al. (2005) Tree Model with Probabilistic Downward Reset.
    Treats downward revision not as a deterministic outcome, but as an event occurring with
    an estimated empirical probability P_reset (e.g. 50%~70%).
    """
    def __init__(self, steps_per_year: int = 50, reset_probability: float = 0.65):
        super().__init__(name="Lai_et_al_2005")
        self.steps_per_year = steps_per_year
        self.reset_prob = reset_probability

    def price(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> PricingResult:
        T = max(contract.maturity_years, 0.01)
        steps = max(int(T * self.steps_per_year), 30)
        dt = T / steps
        r = env.risk_free_rate
        s = contract.credit_spread
        # 期限结构调整因子 (简单单因素 Vasicek 式均值回归调整)
        adjusted_discount = (r + 0.8 * s) + 0.005 * np.exp(-0.2 * T)
        
        sigma = max(env.volatility, 0.01)
        q = env.dividend_yield
        S0 = env.stock_price
        CP_base = contract.conversion_price
        par = contract.par_value
        
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)
        p = np.clip(p, 0.001, 0.999)
        df = np.exp(-adjusted_discount * dt)
        coupon_step = (contract.coupon_rates[-1] * par) * (dt / 1.0)
        
        # 终端节点 (T)
        j_mesh = np.arange(steps + 1)
        S_T = S0 * (u ** j_mesh) * (d ** (steps - j_mesh))
        
        # 概率下修
        is_reset_cond = (S_T < CP_base * contract.reset_trigger_ratio) & contract.has_downward_reset
        CP_reset = np.maximum(S_T, CP_base * contract.reset_floor_ratio)
        conv_T_normal = (S_T / CP_base) * par
        conv_T_reset = (S_T / CP_reset) * par
        # 加权期望转股价值
        conv_T = np.where(is_reset_cond, self.reset_prob * conv_T_reset + (1.0 - self.reset_prob) * conv_T_normal, conv_T_normal)
        
        V = np.maximum(conv_T, contract.redemption_premium)
        
        # 逆向倒推
        for i in range(steps - 1, -1, -1):
            t_curr = i * dt
            j_curr = np.arange(i + 1)
            S_curr = S0 * (u ** j_curr) * (d ** (i - j_curr))
            
            # 判断下修期望转股价值
            if contract.has_downward_reset:
                reset_mask = S_curr <= (CP_base * contract.reset_trigger_ratio)
                new_cp = np.maximum(S_curr, CP_base * contract.reset_floor_ratio)
                conv_curr_normal = (S_curr / CP_base) * par
                conv_curr_reset = (S_curr / new_cp) * par
                conv_curr = np.where(reset_mask, self.reset_prob * conv_curr_reset + (1.0 - self.reset_prob) * conv_curr_normal, conv_curr_normal)
            else:
                conv_curr = (S_curr / CP_base) * par
            
            hold_val = df * (p * V[1:] + (1.0 - p) * V[:-1]) + coupon_step
            node_val = np.maximum(hold_val, conv_curr)
            
            # 赎回条款
            if contract.has_call:
                call_mask = S_curr >= (contract.call_ratio * CP_base)
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
            extra_details={"steps": steps, "reset_prob": self.reset_prob}
        )
