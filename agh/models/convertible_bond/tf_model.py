"""
2. Tsiveriotis-Fernandes (TF, 1998) Model
Classic decoupled binomial tree model for convertible bond valuation.
Splits CB cash flows into equity-like (discounted at r) and debt-like (discounted at r + s).
Incorporates American early conversion, issuer call, and investor put provisions.
"""

import numpy as np
from .base import BaseCBPricer, ConvertibleBondContract, MarketEnvironment, PricingResult


class TFBinomialModel(BaseCBPricer):
    """
    Tsiveriotis and Fernandes (1998) Two-Component Binomial Tree Model.
    Separates option/equity value and bond/debt value at each tree node.
    """
    def __init__(self, steps_per_year: int = 50):
        super().__init__(name="TF_Model_1998")
        self.steps_per_year = steps_per_year

    def price(self, contract: ConvertibleBondContract, env: MarketEnvironment) -> PricingResult:
        T = max(contract.maturity_years, 0.01)
        steps = max(int(T * self.steps_per_year), 30)
        dt = T / steps
        r = env.risk_free_rate
        s = contract.credit_spread
        sigma = max(env.volatility, 0.01)
        q = env.dividend_yield
        S0 = env.stock_price
        CP = contract.conversion_price
        par = contract.par_value
        
        # CRR 树参数
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)
        p = np.clip(p, 0.001, 0.999)
        
        df_r = np.exp(-r * dt)
        df_rs = np.exp(-(r + s) * dt)
        
        # 票息在离散时间步上的分配
        coupon_per_step = (contract.coupon_rates[-1] * par) * (dt / 1.0)
        
        # 构建最后一期终端节点 (Terminal Nodes at T)
        # S_T = S0 * u^j * d^(steps - j)
        j_mesh = np.arange(steps + 1)
        S_T = S0 * (u ** j_mesh) * (d ** (steps - j_mesh))
        conv_val_T = (S_T / CP) * par
        redemption_T = contract.redemption_premium
        
        # 初始化 C (权益部分) 与 B (债务部分)
        # 若转股更有利: C = conv_val, B = 0; 否则 C = 0, B = redemption_T
        convert_mask = conv_val_T > redemption_T
        C = np.where(convert_mask, conv_val_T, 0.0)
        B = np.where(convert_mask, 0.0, redemption_T)
        
        # 逆向倒推 (Backward Induction)
        for i in range(steps - 1, -1, -1):
            t_current = i * dt
            # 当前时间步各节点的股价
            j_curr = np.arange(i + 1)
            S_curr = S0 * (u ** j_curr) * (d ** (i - j_curr))
            conv_curr = (S_curr / CP) * par
            
            # 期望折现
            C_cont = df_r * (p * C[1:] + (1.0 - p) * C[:-1])
            B_cont = df_rs * (p * B[1:] + (1.0 - p) * B[:-1]) + coupon_per_step
            
            V_cont = C_cont + B_cont
            
            # 美式转股判定
            american_conv = conv_curr > V_cont
            C_node = np.where(american_conv, conv_curr, C_cont)
            B_node = np.where(american_conv, 0.0, B_cont)
            
            # 发行人强制赎回条款 (Call Option)
            if contract.has_call:
                call_trigger = contract.call_ratio * CP
                call_mask = S_curr >= call_trigger
                # 若触发赎回，投资者在转股与接受赎回价之间选择最大者
                # 若 conv_curr >= call_price，被迫转股；否则按 call_price 赎回
                force_convert = conv_curr >= contract.call_price
                C_node = np.where(call_mask & force_convert, conv_curr, C_node)
                B_node = np.where(call_mask & force_convert, 0.0, B_node)
                C_node = np.where(call_mask & (~force_convert), 0.0, C_node)
                B_node = np.where(call_mask & (~force_convert), contract.call_price, B_node)
            
            # 投资者回售保护条款 (Put Option)
            if contract.has_put and t_current >= contract.put_start_year:
                put_trigger = contract.put_ratio * CP
                put_mask = S_curr <= put_trigger
                # 若触发回售，且回售价值大于当前持有价值
                put_effective = put_mask & (contract.put_price > (C_node + B_node))
                C_node = np.where(put_effective, 0.0, C_node)
                B_node = np.where(put_effective, contract.put_price, B_node)
            
            C = C_node
            B = B_node
        
        theoretical_price = float(C[0] + B[0])
        pure_debt = self.compute_pure_debt_value(contract, env)
        conv_val = self.compute_conversion_value(contract, env)
        option_val = max(theoretical_price - pure_debt, 0.0)
        
        # 简单一阶 Delta 近似 (通过局部正负扰动)
        dS = S0 * 0.01
        S_up = S0 + dS
        S_down = S0 - dS
        # 依据二叉树前两步节点估算 delta
        delta = (C[0] + B[0] - conv_val) / S0  # 基线敏感度
        
        return PricingResult(
            theoretical_price=theoretical_price,
            conversion_value=float(conv_val),
            pure_debt_value=float(pure_debt),
            option_value=float(option_val),
            delta=float(delta),
            model_name=self.name,
            extra_details={"steps": steps, "dt": dt, "equity_part": float(C[0]), "debt_part": float(B[0])}
        )
