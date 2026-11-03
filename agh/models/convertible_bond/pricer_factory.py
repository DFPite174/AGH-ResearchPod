"""
Convertible Bond Pricer Factory & Evaluation Registry.
Provides unified dispatching and batch pricing across all 5 benchmark models.
"""

from typing import Dict, List, Type
from .base import BaseCBPricer, ConvertibleBondContract, MarketEnvironment, PricingResult
from .bs_model import BSDecompositionModel
from .tf_model import TFBinomialModel
from .zheng_lin_2004_model import ZhengLin2004Model
from .lai_2005_model import Lai2005Model
from .liu_wei_2006_model import LiuWei2006Model


class CBPricerFactory:
    """
    Factory to instantiate and manage convertible bond pricing engines.
    """
    _REGISTRY: Dict[str, Type[BaseCBPricer]] = {
        "BS_1973": BSDecompositionModel,
        "TF_1998": TFBinomialModel,
        "ZhengLin_2004": ZhengLin2004Model,
        "Lai_2005": Lai2005Model,
        "LiuWei_2006": LiuWei2006Model,
    }

    @classmethod
    def list_available_models(cls) -> List[str]:
        return list(cls._REGISTRY.keys())

    @classmethod
    def get_pricer(cls, model_name: str, **kwargs) -> BaseCBPricer:
        if model_name not in cls._REGISTRY:
            raise ValueError(f"Unknown CB pricer model: '{model_name}'. Available: {list(cls._REGISTRY.keys())}")
        return cls._REGISTRY[model_name](**kwargs)

    @classmethod
    def price_all_models(cls, contract: ConvertibleBondContract, env: MarketEnvironment) -> Dict[str, PricingResult]:
        """
        Price the convertible bond with all 5 models simultaneously.
        """
        results = {}
        for name, pricer_cls in cls._REGISTRY.items():
            pricer = pricer_cls()
            results[name] = pricer.price(contract, env)
        return results
