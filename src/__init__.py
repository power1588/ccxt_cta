"""
CCXT CTA Strategy Package.

A comprehensive cryptocurrency trading strategy package implementing
volume price breakout strategies with advanced risk management.

Author: Power Air
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Power Air"
__email__ = "powerair@example.com"
__license__ = "MIT"

from .volume_price_breakout import VolumePriceBreakoutStrategy
from .strategy import (
    # Enums
    OrderSide,
    OrderStatus,
    StrategyMode,

    # Dataclasses
    StrategyParameters,
    Position,
    Order,
    Signal,

    # Managers
    ExchangeManager,
    SignalDetector,
    PositionManager,
    TechnicalIndicators,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",

    # Main strategy
    "VolumePriceBreakoutStrategy",

    # Enums
    "OrderSide",
    "OrderStatus",
    "StrategyMode",

    # Dataclasses
    "StrategyParameters",
    "Position",
    "Order",
    "Signal",

    # Managers
    "ExchangeManager",
    "SignalDetector",
    "PositionManager",
    "TechnicalIndicators",
]