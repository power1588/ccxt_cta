"""
Base strategy module for volume price breakout strategy.

This module contains the core strategy implementation for detecting
volume and price breakouts in cryptocurrency markets.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

import ccxt
import pandas as pd
import numpy as np


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class StrategyMode(Enum):
    """Strategy mode enumeration."""
    BACKTEST = "backtest"
    LIVE = "live"
    PAPER = "paper"


@dataclass
class StrategyParameters:
    """Strategy parameters configuration."""
    volume_period: int = 30
    volume_multiplier: float = 2.0
    price_change_threshold: float = 1.5
    capital_usage_percent: float = 10.0
    add_position_threshold: float = 2.0
    stop_loss_threshold: float = 3.0
    max_positions: int = 3
    min_order_size: float = 0.001
    max_order_size: float = 1.0


@dataclass
class Position:
    """Position information dataclass."""
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    entry_time: datetime
    highest_price: float
    stop_loss_price: float
    total_invested: float
    current_pnl: float = 0.0


@dataclass
class Order:
    """Order information dataclass."""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    status: OrderStatus
    timestamp: datetime
    order_type: str = "market"


@dataclass
class Signal:
    """Trading signal dataclass."""
    signal_type: str
    price: float
    volume: float
    volume_ratio: float
    price_change: float
    timestamp: datetime
    symbol: str


class ExchangeManager:
    """Exchange connection manager."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize exchange manager.

        Args:
            config: Exchange configuration dictionary.
        """
        self.config = config
        self.exchange: Optional[ccxt.Exchange] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize exchange connection."""
        try:
            # Try ccxt.pro first for WebSocket support
            try:
                import ccxt.pro
                self.exchange = ccxt.pro.binance({
                    'apiKey': self.config.get('api_key', ''),
                    'secret': self.config.get('secret', ''),
                    'sandbox': self.config.get('sandbox', False),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                })
                self.logger.info("✅ Using ccxt.pro for WebSocket support")
            except ImportError:
                # Fallback to regular ccxt
                self.exchange = ccxt.binance({
                    'apiKey': self.config.get('api_key', ''),
                    'secret': self.config.get('secret', ''),
                    'sandbox': self.config.get('sandbox', False),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                })
                self.logger.info("✅ Using ccxt for REST API")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize exchange: {e}")
            raise

    async def close(self) -> None:
        """Close exchange connection."""
        if self.exchange and hasattr(self.exchange, 'close'):
            await self.exchange.close()


class TechnicalIndicators:
    """Technical indicators calculator."""

    @staticmethod
    def calculate_volume_ma(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate volume moving average.

        Args:
            df: DataFrame with volume data.
            period: Moving average period.

        Returns:
            Volume moving average series.
        """
        return df['volume'].rolling(window=period).mean()

    @staticmethod
    def calculate_volume_ratio(
        df: pd.DataFrame,
        volume_ma: pd.Series
    ) -> pd.Series:
        """Calculate volume ratio to moving average.

        Args:
            df: DataFrame with volume data.
            volume_ma: Volume moving average series.

        Returns:
            Volume ratio series.
        """
        return df['volume'] / volume_ma

    @staticmethod
    def calculate_price_change_pct(df: pd.DataFrame) -> pd.Series:
        """Calculate price change percentage.

        Args:
            df: DataFrame with OHLC data.

        Returns:
            Price change percentage series.
        """
        return ((df['close'] - df['open']) / df['open'] * 100)


class SignalDetector:
    """Signal detection logic."""

    def __init__(self, parameters: StrategyParameters) -> None:
        """Initialize signal detector.

        Args:
            parameters: Strategy parameters.
        """
        self.parameters = parameters
        self.logger = logging.getLogger(__name__)

    def detect_entry_signal(self, kline_data: Dict) -> Optional[Signal]:
        """Detect entry signal based on volume and price breakout.

        Args:
            kline_data: Kline data dictionary.

        Returns:
            Signal object if signal detected, None otherwise.
        """
        volume_breakout = (
            kline_data['volume_ratio'] >= self.parameters.volume_multiplier
        )
        price_breakout = (
            kline_data['price_change_pct'] >= self.parameters.price_change_threshold
        )

        if volume_breakout and price_breakout:
            return Signal(
                signal_type="ENTRY",
                price=kline_data['close'],
                volume=kline_data['volume'],
                volume_ratio=kline_data['volume_ratio'],
                price_change=kline_data['price_change_pct'],
                timestamp=kline_data['timestamp'],
                symbol=kline_data['symbol']
            )

        return None

    def check_add_position_signal(self, position: Position, current_price: float) -> bool:
        """Check if add position signal is triggered.

        Args:
            position: Current position.
            current_price: Current market price.

        Returns:
            True if add position signal triggered, False otherwise.
        """
        price_increase_pct = (
            (current_price - position.entry_price) / position.entry_price * 100
        )
        return price_increase_pct >= self.parameters.add_position_threshold

    def check_exit_signal(self, position: Position, current_price: float) -> bool:
        """Check if exit signal is triggered.

        Args:
            position: Current position.
            current_price: Current market price.

        Returns:
            True if exit signal triggered, False otherwise.
        """
        # Update highest price first
        if current_price > position.highest_price:
            position.highest_price = current_price
            position.stop_loss_price = (
                position.highest_price * (1 - self.parameters.stop_loss_threshold / 100)
            )

        drawdown_pct = (
            (position.highest_price - current_price) / position.highest_price * 100
        )
        return drawdown_pct >= self.parameters.stop_loss_threshold


class PositionManager:
    """Position management."""

    def __init__(self, parameters: StrategyParameters) -> None:
        """Initialize position manager.

        Args:
            parameters: Strategy parameters.
        """
        self.parameters = parameters
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(self, account_balance: float, current_price: float) -> float:
        """Calculate position size based on account balance.

        Args:
            account_balance: Available account balance.
            current_price: Current market price.

        Returns:
            Position size in base currency.
        """
        invest_amount = account_balance * (self.parameters.capital_usage_percent / 100)
        position_size = invest_amount / current_price

        # Apply size limits
        position_size = max(
            self.parameters.min_order_size,
            min(position_size, self.parameters.max_order_size)
        )

        return position_size

    def add_position(self, signal: Signal, account_balance: float) -> bool:
        """Add new position based on signal.

        Args:
            signal: Entry signal.
            account_balance: Available account balance.

        Returns:
            True if position added successfully, False otherwise.
        """
        if len(self.positions) >= self.parameters.max_positions:
            self.logger.warning(f"⚠️ Max positions ({self.parameters.max_positions}) reached")
            return False

        position_size = self.calculate_position_size(account_balance, signal.price)

        position = Position(
            symbol=signal.symbol,
            side=OrderSide.BUY,
            entry_price=signal.price,
            quantity=position_size,
            entry_time=signal.timestamp,
            highest_price=signal.price,
            stop_loss_price=signal.price * (1 - self.parameters.stop_loss_threshold / 100),
            total_invested=signal.price * position_size
        )

        self.positions.append(position)

        self.logger.info(
            f"🚨 Entry executed: {signal.symbol} @ ${signal.price:.2f}, "
            f"size: {position_size:.6f}, vol_ratio: {signal.volume_ratio:.2f}x"
        )

        return True

    def add_to_position(self, position: Position, current_price: float, account_balance: float) -> bool:
        """Add to existing position.

        Args:
            position: Existing position to add to.
            current_price: Current market price.
            account_balance: Available account balance.

        Returns:
            True if position added successfully, False otherwise.
        """
        additional_size = self.calculate_position_size(account_balance, current_price)
        additional_cost = current_price * additional_size

        # Update position
        total_quantity = position.quantity + additional_size
        total_cost = position.total_invested + additional_cost

        position.quantity = total_quantity
        position.entry_price = total_cost / total_quantity
        position.total_invested = total_cost

        self.logger.info(
            f"📈 Position added: {position.symbol} @ ${current_price:.2f}, "
            f"additional: {additional_size:.6f}, new avg: ${position.entry_price:.2f}"
        )

        return True

    def close_position(self, position: Position, current_price: float) -> None:
        """Close position.

        Args:
            position: Position to close.
            current_price: Current market price.
        """
        pnl = (current_price - position.entry_price) * position.quantity
        pnl_pct = ((current_price - position.entry_price) / position.entry_price * 100)

        self.logger.info(
            f"🔴 Position closed: {position.symbol} @ ${current_price:.2f}, "
            f"PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)"
        )

        self.positions.remove(position)

    def update_positions(self, current_price: float, signal_detector: SignalDetector, account_balance: float) -> None:
        """Update all positions.

        Args:
            current_price: Current market price.
            signal_detector: Signal detector instance.
            account_balance: Available account balance.
        """
        positions_to_close = []

        for position in self.positions:
            # Check add position signal
            if signal_detector.check_add_position_signal(position, current_price):
                self.add_to_position(position, current_price, account_balance)

            # Check exit signal
            if signal_detector.check_exit_signal(position, current_price):
                positions_to_close.append(position)

        # Close positions
        for position in positions_to_close:
            self.close_position(position, current_price)

    def get_total_pnl(self, current_price: float) -> float:
        """Calculate total PnL for all positions.

        Args:
            current_price: Current market price.

        Returns:
            Total PnL.
        """
        return sum(
            (current_price - pos.entry_price) * pos.quantity
            for pos in self.positions
        )

    def get_status_summary(self, current_price: float) -> Dict[str, Any]:
        """Get position status summary.

        Args:
            current_price: Current market price.

        Returns:
            Status summary dictionary.
        """
        if not self.positions:
            return {
                'positions_count': 0,
                'total_pnl': 0.0,
                'total_invested': 0.0,
                'pnl_percentage': 0.0,
                'positions': []
            }

        total_pnl = self.get_total_pnl(current_price)
        total_invested = sum(pos.total_invested for pos in self.positions)
        pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        positions_details = []
        for pos in self.positions:
            current_pnl = (current_price - pos.entry_price) * pos.quantity
            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price * 100)

            positions_details.append({
                'symbol': pos.symbol,
                'entry_price': pos.entry_price,
                'quantity': pos.quantity,
                'highest_price': pos.highest_price,
                'stop_loss_price': pos.stop_loss_price,
                'current_pnl': current_pnl,
                'pnl_percentage': pnl_pct
            })

        return {
            'positions_count': len(self.positions),
            'total_pnl': total_pnl,
            'total_invested': total_invested,
            'pnl_percentage': pnl_percentage,
            'positions': positions_details
        }