"""
Unit test for NautilusEngineAdapter and Plan B native integration.
"""

from decimal import Decimal
import pytest
from agh.strategy.nautilus_adapter import NautilusEngineAdapter


def test_nautilus_adapter_availability():
    adapter = NautilusEngineAdapter()
    assert adapter.is_available is True
    assessment = adapter.get_suitability_assessment()
    assert "ashare-nautilus-backtest-engine" in assessment["engine_name"]
    assert "Plan B" in assessment["overall_suitability"]


def test_nautilus_cb_backtest_execution():
    from benchmarks.benchmark_003_nautilus_execution.run_replication import run_benchmark
    # Execute full benchmark replication
    run_benchmark()
