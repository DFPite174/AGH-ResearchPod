"""
Convertible Bond Valuation Package.
Implements the 5 core models analyzed in Zheng Zhenlong et al. (2025).
"""

from .base import ConvertibleBondContract, MarketEnvironment, PricingResult, BaseCBPricer
from .bs_model import BSDecompositionModel
from .tf_model import TFBinomialModel
from .zheng_lin_2004_model import ZhengLin2004Model
from .lai_2005_model import Lai2005Model
from .liu_wei_2006_model import LiuWei2006Model
from .pricer_factory import CBPricerFactory

__all__ = [
    "ConvertibleBondContract",
    "MarketEnvironment",
    "PricingResult",
    "BaseCBPricer",
    "BSDecompositionModel",
    "TFBinomialModel",
    "ZhengLin2004Model",
    "Lai2005Model",
    "LiuWei2006Model",
    "CBPricerFactory",
]
