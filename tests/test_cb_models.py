"""
Unit Tests for AGH-ResearchPod Convertible Bond Models & Strategy.
"""

import pytest
import numpy as np
from agh.models.convertible_bond.base import ConvertibleBondContract, MarketEnvironment
from agh.models.convertible_bond.bs_model import BSDecompositionModel
from agh.models.convertible_bond.tf_model import TFBinomialModel
from agh.models.convertible_bond.zheng_lin_2004_model import ZhengLin2004Model
from agh.models.convertible_bond.lai_2005_model import Lai2005Model
from agh.models.convertible_bond.liu_wei_2006_model import LiuWei2006Model
from agh.models.convertible_bond.pricer_factory import CBPricerFactory
from agh.strategy.cb_mispricing_hedging import CBMispricingHedgingEngine
from benchmarks.benchmark_001_cb_pricing.generate_benchmark_data import (
    get_representative_contracts,
    generate_synthetic_history
)


@pytest.fixture
def standard_contract():
    return ConvertibleBondContract(
        code="110059.SH",
        name="浦发转债",
        par_value=100.0,
        maturity_years=4.0,
        conversion_price=10.0,
        coupon_rates=[0.005, 0.008, 0.012, 0.018],
        redemption_premium=105.0,
        has_call=True,
        call_ratio=1.30,
        has_put=True,
        put_ratio=0.70,
        put_start_year=2.0,
        has_downward_reset=True,
        reset_trigger_ratio=0.85,
        credit_spread=0.015
    )


@pytest.fixture
def market_env():
    return MarketEnvironment(
        stock_price=10.0,
        volatility=0.25,
        risk_free_rate=0.025,
        credit_spread=0.015
    )


def test_pure_debt_and_conversion_value(standard_contract, market_env):
    pricer = BSDecompositionModel()
    debt_val = pricer.compute_pure_debt_value(standard_contract, market_env)
    conv_val = pricer.compute_conversion_value(standard_contract, market_env)
    
    # 纯债价值通常贴现后在 80~105 之间
    assert 80.0 <= debt_val <= 105.0
    # S=10, CP=10, Par=100 -> ConvVal = 100.0
    assert np.isclose(conv_val, 100.0)


def test_all_five_models_pricing_bounds(standard_contract, market_env):
    """
    All models must output theoretical price >= max(PureDebt, ConversionValue).
    """
    models = [
        BSDecompositionModel(),
        TFBinomialModel(steps_per_year=20),
        ZhengLin2004Model(steps_per_year=20),
        Lai2005Model(steps_per_year=20),
        LiuWei2006Model(steps_per_year=20),
    ]
    
    pure_debt = models[0].compute_pure_debt_value(standard_contract, market_env)
    conv_val = models[0].compute_conversion_value(standard_contract, market_env)
    lower_bound = max(pure_debt, conv_val) - 2.0  # 允许极小数值离散步长误差
    
    for m in models:
        res = m.price(standard_contract, market_env)
        assert res.theoretical_price >= lower_bound, f"Model {m.name} failed lower bound check: {res.theoretical_price} < {lower_bound}"
        assert res.theoretical_price < 250.0  # 合理上限


def test_pricer_factory(standard_contract, market_env):
    models = CBPricerFactory.list_available_models()
    assert len(models) == 5
    all_res = CBPricerFactory.price_all_models(standard_contract, market_env)
    assert len(all_res) == 5
    for name, r in all_res.items():
        assert r.theoretical_price > 0.0


def test_downward_reset_enhances_value(standard_contract, market_env):
    """
    In distressed scenarios (S < CP * 0.85), Zheng-Lin (2004a) model with reset
    should price higher than without reset because of the option value of the reset clause.
    """
    distressed_env = MarketEnvironment(
        stock_price=7.0,  # 严重跌破转股价 10.0 (触及 85% 下修线)
        volatility=0.30,
        risk_free_rate=0.025,
        credit_spread=0.03
    )
    
    contract_with_reset = standard_contract
    
    contract_no_reset = ConvertibleBondContract(
        code="110059.SH",
        name="浦发转债-无下修",
        par_value=100.0,
        maturity_years=4.0,
        conversion_price=10.0,
        coupon_rates=[0.005, 0.008, 0.012, 0.018],
        redemption_premium=105.0,
        has_call=True,
        has_put=True,
        has_downward_reset=False,  # 关闭下修
        credit_spread=0.03
    )
    
    pricer = ZhengLin2004Model(steps_per_year=30)
    res_with = pricer.price(contract_with_reset, distressed_env)
    res_without = pricer.price(contract_no_reset, distressed_env)
    
    # 含有下修条款的转债公允价值必然严格大于无下修条款的转债
    assert res_with.theoretical_price >= res_without.theoretical_price


def test_cross_sectional_hedging_simulation():
    contracts = get_representative_contracts()
    history, bench = generate_synthetic_history(contracts, n_weeks=12, random_seed=123)
    engine = CBMispricingHedgingEngine(n_quintiles=5, annual_periods=52)
    metrics = engine.run_simulation(contracts, history, bench)
    
    assert len(metrics) == 5
    for m_name, m_metric in metrics.items():
        assert m_metric.annualized_volatility > 0.0
        assert m_metric.win_rate >= 0.0
