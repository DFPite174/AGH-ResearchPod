"""
Convertible Bond Mispricing Cross-Sectional Hedging Strategy.
Direct replication of the methodology in Zheng Zhenlong, Zhu Tiancheng, Chen Rong (2025).

Constructs quintile long-short hedging portfolios based on model pricing deviations:
  Mispricing = (Market_Price - Theoretical_Price) / Theoretical_Price
Evaluates model accuracy via portfolio excess returns, Sharpe ratios, and Alphas.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from ..models.convertible_bond.base import ConvertibleBondContract, MarketEnvironment
from ..models.convertible_bond.pricer_factory import CBPricerFactory


@dataclass
class BacktestMetrics:
    model_name: str
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    alpha_capm: float
    t_stat_alpha: float
    q1_mean_return: float
    q5_mean_return: float


class CBMispricingHedgingEngine:
    """
    Backtesting engine for the 5-quintile cross-sectional L/S hedging strategy.
    """
    def __init__(self, n_quintiles: int = 5, annual_periods: int = 52):
        self.n_quintiles = n_quintiles
        self.annual_periods = annual_periods  # 周频重仓，每年约52期

    def run_simulation(
        self,
        contracts: List[ConvertibleBondContract],
        cross_section_history: List[Dict[str, Any]],
        market_benchmark_returns: List[float]
    ) -> Dict[str, BacktestMetrics]:
        """
        Run cross-sectional quintile backtest across all 5 models.
        
        cross_section_history: List of time-slices.
        Each time slice has:
          - 'date': str
          - 'bonds': list of dicts with keys: 'code', 'market_price', 'stock_price', 'volatility', 'rf', 'return_next_period'
        """
        model_names = CBPricerFactory.list_available_models()
        model_portfolio_returns = {m: [] for m in model_names}
        q1_returns = {m: [] for m in model_names}
        q5_returns = {m: [] for m in model_names}
        
        contract_map = {c.code: c for c in contracts}
        
        for period in cross_section_history:
            bonds_data = period['bonds']
            if len(bonds_data) < self.n_quintiles:
                continue
                
            period_df = pd.DataFrame(bonds_data)
            
            # 对每个模型分别计算该期的理论价值与定价偏差
            for m_name in model_names:
                pricer = CBPricerFactory.get_pricer(m_name)
                mispricing_list = []
                
                for idx, row in period_df.iterrows():
                    c_obj = contract_map[row['code']]
                    env = MarketEnvironment(
                        stock_price=row['stock_price'],
                        volatility=row['volatility'],
                        risk_free_rate=row['rf'],
                        credit_spread=c_obj.credit_spread
                    )
                    res = pricer.price(c_obj, env)
                    theo_price = res.theoretical_price
                    mkt_price = row['market_price']
                    
                    # 偏离度: (P_market - V_model) / V_model
                    # 若 < 0 表示市场低估 (应做多), 若 > 0 表示市场高估 (应做空)
                    mp = (mkt_price - theo_price) / theo_price
                    mispricing_list.append(mp)
                
                period_df[f'mp_{m_name}'] = mispricing_list
                # 按偏离度升序排序: 最前面的组最被低估 (Q1), 最后面的组最被高估 (Q5)
                period_df_sorted = period_df.sort_values(by=f'mp_{m_name}')
                
                group_size = len(period_df_sorted) // self.n_quintiles
                q1 = period_df_sorted.iloc[:group_size]
                q5 = period_df_sorted.iloc[-group_size:]
                
                r_q1 = q1['return_next_period'].mean()
                r_q5 = q5['return_next_period'].mean()
                # 多空对冲收益: 买入被严重低估的 Q1，做空被严重高估的 Q5
                r_ls = r_q1 - r_q5
                
                model_portfolio_returns[m_name].append(r_ls)
                q1_returns[m_name].append(r_q1)
                q5_returns[m_name].append(r_q5)
        
        # 统计绩效指标
        metrics_dict = {}
        for m_name in model_names:
            rets = np.array(model_portfolio_returns[m_name])
            bench = np.array(market_benchmark_returns[:len(rets)])
            
            if len(rets) < 2:
                continue
                
            mean_ret = np.mean(rets) * self.annual_periods
            vol = np.std(rets, ddof=1) * np.sqrt(self.annual_periods)
            sharpe = (mean_ret - 0.02) / (vol + 1e-8)
            
            # 最大回撤
            cum_rets = np.cumprod(1.0 + rets)
            peaks = np.maximum.accumulate(cum_rets)
            drawdowns = (peaks - cum_rets) / peaks
            max_dd = float(np.max(drawdowns))
            
            win_rate = float(np.mean(rets > 0))
            
            # CAPM 回归: R_LS = alpha + beta * R_m + epsilon
            cov_mb = np.cov(rets, bench)
            var_b = np.var(bench, ddof=1)
            beta = cov_mb[0, 1] / (var_b + 1e-8)
            alpha_period = np.mean(rets) - beta * np.mean(bench)
            alpha_ann = alpha_period * self.annual_periods
            
            # t-statistic for alpha
            resid = rets - (alpha_period + beta * bench)
            se_alpha = np.std(resid, ddof=2) / np.sqrt(len(rets))
            t_stat = alpha_period / (se_alpha + 1e-8)
            
            metrics_dict[m_name] = BacktestMetrics(
                model_name=m_name,
                annualized_return=float(mean_ret),
                annualized_volatility=float(vol),
                sharpe_ratio=float(sharpe),
                max_drawdown=float(max_dd),
                win_rate=float(win_rate),
                alpha_capm=float(alpha_ann),
                t_stat_alpha=float(t_stat),
                q1_mean_return=float(np.mean(q1_returns[m_name]) * self.annual_periods),
                q5_mean_return=float(np.mean(q5_returns[m_name]) * self.annual_periods),
            )
            
        return metrics_dict
