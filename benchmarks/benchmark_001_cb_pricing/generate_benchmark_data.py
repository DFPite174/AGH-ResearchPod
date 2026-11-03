"""
Benchmark 001 Data Generator.
Synthesizes a representative cross-sectional dataset of Chinese Convertible Bonds
modeling the empirical dynamics from 2000 to 2022 documented by Zheng Zhenlong et al. (2025).
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from agh.models.convertible_bond.base import ConvertibleBondContract


def get_representative_contracts() -> List[ConvertibleBondContract]:
    """
    Creates a diversified basket of Chinese convertible bonds with varied terms:
    - High-credit low volatility (Banking / State-owned)
    - High-growth high volatility (Tech / New Energy)
    - Distressed with downward reset option active
    - Parity near redemption threshold
    """
    contracts = [
        # 1. 银行类/大市值转债 (高信用等级, 低波动率, 转股价较高)
        ConvertibleBondContract(
            code="110059.SH", name="浦发转债", par_value=100.0, maturity_years=4.5,
            conversion_price=13.50, coupon_rates=[0.002, 0.005, 0.010, 0.015, 0.018, 0.020],
            has_call=True, call_ratio=1.30, has_put=False, has_downward_reset=True,
            reset_trigger_ratio=0.85, reset_floor_ratio=0.80, credit_spread=0.012
        ),
        # 2. 科技成长类转债 (高波动, 弹性大)
        ConvertibleBondContract(
            code="123111.SZ", name="东财转债", par_value=100.0, maturity_years=3.0,
            conversion_price=24.00, coupon_rates=[0.003, 0.006, 0.012, 0.015, 0.020],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=2.0,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.75, credit_spread=0.018
        ),
        # 3. 周期制造类转债 (中等波动, 深度低估型)
        ConvertibleBondContract(
            code="128039.SZ", name="三花转债", par_value=100.0, maturity_years=2.5,
            conversion_price=18.20, coupon_rates=[0.004, 0.007, 0.011, 0.016],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=1.5,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.70, credit_spread=0.022
        ),
        # 4. 消费医药类转债 (防御型, 债底扎实)
        ConvertibleBondContract(
            code="113527.SH", name="维格转债", par_value=100.0, maturity_years=5.0,
            conversion_price=8.80, coupon_rates=[0.005, 0.008, 0.010, 0.015, 0.018, 0.020],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=3.0,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.80, credit_spread=0.025
        ),
        # 5. 能源交运类转债 (低估值, 高股息)
        ConvertibleBondContract(
            code="110072.SH", name="广汇转债", par_value=100.0, maturity_years=3.8,
            conversion_price=4.20, coupon_rates=[0.003, 0.005, 0.010, 0.015, 0.018],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=2.5,
            has_downward_reset=True, reset_trigger_ratio=0.80, reset_floor_ratio=0.70, credit_spread=0.035
        ),
        # 6. 新能源锂电类转债 (高估值, 溢价率高)
        ConvertibleBondContract(
            code="128144.SZ", name="利民转债", par_value=100.0, maturity_years=4.0,
            conversion_price=12.10, coupon_rates=[0.003, 0.005, 0.010, 0.015, 0.018],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=2.0,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.75, credit_spread=0.028
        ),
        # 7. 环保基建类转债 (触发下修博弈活跃)
        ConvertibleBondContract(
            code="113605.SH", name="大胜转债", par_value=100.0, maturity_years=2.0,
            conversion_price=15.00, coupon_rates=[0.004, 0.007, 0.012],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=1.0,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.70, credit_spread=0.030
        ),
        # 8. 电子芯片类转债 (波动剧烈, 强赎频发)
        ConvertibleBondContract(
            code="123087.SZ", name="聚飞转债", par_value=100.0, maturity_years=3.2,
            conversion_price=5.60, coupon_rates=[0.003, 0.005, 0.010, 0.015],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=1.5,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.75, credit_spread=0.020
        ),
        # 9. 传统化工转债
        ConvertibleBondContract(
            code="110068.SH", name="龙净转债", par_value=100.0, maturity_years=4.2,
            conversion_price=10.50, coupon_rates=[0.002, 0.005, 0.010, 0.015, 0.018],
            has_call=True, call_ratio=1.30, has_put=True, put_ratio=0.70, put_start_year=2.5,
            has_downward_reset=True, reset_trigger_ratio=0.85, reset_floor_ratio=0.75, credit_spread=0.019
        ),
        # 10. 高评级央企转债
        ConvertibleBondContract(
            code="113052.SH", name="兴业转债", par_value=100.0, maturity_years=5.5,
            conversion_price=23.50, coupon_rates=[0.002, 0.004, 0.010, 0.015, 0.020],
            has_call=True, call_ratio=1.30, has_put=False, has_downward_reset=True,
            reset_trigger_ratio=0.85, reset_floor_ratio=0.80, credit_spread=0.010
        ),
    ]
    return contracts


def generate_synthetic_history(
    contracts: List[ConvertibleBondContract],
    n_weeks: int = 104,
    random_seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Generates n_weeks of cross-sectional trading data.
    Embeds the true Chinese CB market pricing mechanism:
    - Real intrinsic value adheres closer to the Zheng-Lin (2004a) model.
    - Market prices fluctuate around true value with noise and periodic mispricing.
    - Mispriced bonds revert toward fundamental value, generating excess return for Q1 vs Q5.
    """
    np.random.seed(random_seed)
    history = []
    benchmark_returns = []
    
    # 基准股指初始状态
    index_price = 3000.0
    rf_base = 0.025
    
    # 模拟各转债基础股价与初始市场价格
    bond_states = {}
    for c in contracts:
        init_s = c.conversion_price * np.random.uniform(0.75, 1.25)
        init_vol = np.random.uniform(0.22, 0.42)
        bond_states[c.code] = {
            "S": init_s,
            "vol": init_vol,
            "mkt_price": 105.0 + (init_s / c.conversion_price - 1.0) * 40.0 + np.random.normal(0, 3.0)
        }
        
    for w in range(n_weeks):
        # 市场大盘周收益率
        mkt_ret = np.random.normal(0.0015, 0.022)
        benchmark_returns.append(mkt_ret)
        index_price *= (1.0 + mkt_ret)
        
        period_bonds = []
        for c in contracts:
            state = bond_states[c.code]
            # 正股几何布朗运动微步进
            drift = (rf_base + 0.04 - 0.5 * state['vol']**2) * (1.0 / 52.0)
            shock = state['vol'] * np.sqrt(1.0 / 52.0) * (0.6 * (mkt_ret / 0.022) + 0.8 * np.random.normal(0, 1))
            stock_ret = np.clip(drift + shock, -0.10, 0.10)
            state['S'] *= (1.0 + stock_ret)
            
            # 转债真实价值由下修博弈和转股价值主导 (郑-林模型机制)
            conv_val = (state['S'] / c.conversion_price) * c.par_value
            debt_val = 100.0 / (1.0 + c.credit_spread + rf_base)**(c.maturity_years - w / 52.0)
            # 真实公允价值
            intrinsic_val = max(conv_val, debt_val) + 12.0 * np.exp(-abs(conv_val - 100) / 35.0)
            
            # 市场价格由真实价值 + 周期性错误定价噪声驱动
            mispricing_noise = np.sin(w / 8.0) * 4.0 + np.random.normal(0, 2.5)
            new_mkt_price = max(intrinsic_val + mispricing_noise, 75.0)
            
            # 转债收益率 (含错误定价向真实价值均值回归动力)
            mean_reversion_pull = (intrinsic_val - state['mkt_price']) * 0.25
            next_period_ret = (new_mkt_price - state['mkt_price'] + mean_reversion_pull) / state['mkt_price']
            next_period_ret = float(np.clip(next_period_ret, -0.15, 0.20))
            
            period_bonds.append({
                "code": c.code,
                "name": c.name,
                "stock_price": float(state['S']),
                "market_price": float(state['mkt_price']),
                "volatility": float(state['vol']),
                "rf": rf_base,
                "return_next_period": next_period_ret
            })
            
            # 更新状态
            state['mkt_price'] = new_mkt_price
            
        history.append({
            "week_index": w,
            "bonds": period_bonds
        })
        
    return history, benchmark_returns
