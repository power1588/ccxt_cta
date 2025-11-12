"""
Test cases for strategy components.

This module contains unit tests for the core strategy components
including signal detection, position management, and technical indicators.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.strategy import (
    StrategyParameters,
    Position,
    Signal,
    SignalDetector,
    PositionManager,
    TechnicalIndicators,
    OrderSide,
)


class TestStrategyParameters:
    """Test StrategyParameters dataclass."""

    def test_default_parameters(self) -> None:
        """Test default parameter values."""
        params = StrategyParameters()
        assert params.volume_period == 30
        assert params.volume_multiplier == 2.0
        assert params.price_change_threshold == 1.5
        assert params.capital_usage_percent == 10
        assert params.add_position_threshold == 2.0
        assert params.stop_loss_threshold == 3.0
        assert params.max_positions == 3
        assert params.min_order_size == 0.001
        assert params.max_order_size == 1.0

    def test_custom_parameters(self) -> None:
        """Test custom parameter values."""
        params = StrategyParameters(
            volume_period=20,
            volume_multiplier=1.5,
            price_change_threshold=1.0,
            capital_usage_percent=5,
            add_position_threshold=1.5,
            stop_loss_threshold=2.0,
            max_positions=5,
            min_order_size=0.0005,
            max_order_size=2.0
        )
        assert params.volume_period == 20
        assert params.volume_multiplier == 1.5
        assert params.price_change_threshold == 1.0
        assert params.capital_usage_percent == 5
        assert params.add_position_threshold == 1.5
        assert params.stop_loss_threshold == 2.0
        assert params.max_positions == 5
        assert params.min_order_size == 0.0005
        assert params.max_order_size == 2.0


class TestTechnicalIndicators:
    """Test TechnicalIndicators class."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=10),
            end=datetime.now(),
            freq='1h'
        )

        np.random.seed(42)
        data = []
        close_price = 50000

        for date in dates:
            open_price = close_price
            price_change = np.random.normal(0, 0.02)
            close_price = open_price * (1 + price_change)

            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.uniform(1000, 10000)

            data.append([open_price, high_price, low_price, close_price, volume])

        return pd.DataFrame(
            data,
            columns=['open', 'high', 'low', 'close', 'volume'],
            index=dates
        )

    def test_calculate_volume_ma(self, sample_data: pd.DataFrame) -> None:
        """Test volume moving average calculation."""
        period = 5
        ma = TechnicalIndicators.calculate_volume_ma(sample_data, period)

        assert len(ma) == len(sample_data)
        assert ma.isna().sum() == period - 1  # First period-1 values should be NaN

        # Verify calculation for non-NaN values
        for i in range(period, len(sample_data)):
            expected = sample_data['volume'].iloc[i-period:i].mean()
            assert abs(ma.iloc[i] - expected) < 1e-10

    def test_calculate_volume_ratio(self, sample_data: pd.DataFrame) -> None:
        """Test volume ratio calculation."""
        volume_ma = TechnicalIndicators.calculate_volume_ma(sample_data, 5)
        ratio = TechnicalIndicators.calculate_volume_ratio(sample_data, volume_ma)

        assert len(ratio) == len(sample_data)

        # Verify calculation for valid values
        for i in range(5, len(sample_data)):
            expected = sample_data['volume'].iloc[i] / volume_ma.iloc[i]
            assert abs(ratio.iloc[i] - expected) < 1e-10

    def test_calculate_price_change_pct(self, sample_data: pd.DataFrame) -> None:
        """Test price change percentage calculation."""
        change_pct = TechnicalIndicators.calculate_price_change_pct(sample_data)

        assert len(change_pct) == len(sample_data)

        # Verify calculation
        for i in range(len(sample_data)):
            open_price = sample_data['open'].iloc[i]
            close_price = sample_data['close'].iloc[i]
            expected = ((close_price - open_price) / open_price) * 100
            assert abs(change_pct.iloc[i] - expected) < 1e-10


class TestSignalDetector:
    """Test SignalDetector class."""

    @pytest.fixture
    def parameters(self) -> StrategyParameters:
        """Create test parameters."""
        return StrategyParameters(
            volume_multiplier=2.0,
            price_change_threshold=1.5,
            add_position_threshold=2.0,
            stop_loss_threshold=3.0
        )

    @pytest.fixture
    def signal_detector(self, parameters: StrategyParameters) -> SignalDetector:
        """Create signal detector instance."""
        return SignalDetector(parameters)

    def test_detect_entry_signal_success(self, signal_detector: SignalDetector) -> None:
        """Test successful entry signal detection."""
        kline_data = {
            'close': 105000,
            'volume': 5000,
            'volume_ratio': 2.5,  # Above threshold
            'price_change_pct': 2.0,  # Above threshold
            'timestamp': datetime.now(),
            'symbol': 'BTC/USDT'
        }

        signal = signal_detector.detect_entry_signal(kline_data)

        assert signal is not None
        assert signal.signal_type == "ENTRY"
        assert signal.price == 105000
        assert signal.volume_ratio == 2.5
        assert signal.price_change == 2.0

    def test_detect_entry_signal_no_signal(self, signal_detector: SignalDetector) -> None:
        """Test no entry signal detection."""
        kline_data = {
            'close': 105000,
            'volume': 5000,
            'volume_ratio': 1.5,  # Below threshold
            'price_change_pct': 2.0,  # Above threshold
            'timestamp': datetime.now(),
            'symbol': 'BTC/USDT'
        }

        signal = signal_detector.detect_entry_signal(kline_data)
        assert signal is None

    def test_check_add_position_signal_success(self, signal_detector: SignalDetector) -> None:
        """Test successful add position signal."""
        position = Position(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            entry_price=100000,
            quantity=0.01,
            entry_time=datetime.now(),
            highest_price=100000,
            stop_loss_price=97000,
            total_invested=1000
        )

        # Current price is 2.5% higher than entry (above 2.0% threshold)
        current_price = 102500
        result = signal_detector.check_add_position_signal(position, current_price)

        assert result is True

    def test_check_add_position_signal_no_signal(self, signal_detector: SignalDetector) -> None:
        """Test no add position signal."""
        position = Position(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            entry_price=100000,
            quantity=0.01,
            entry_time=datetime.now(),
            highest_price=100000,
            stop_loss_price=97000,
            total_invested=1000
        )

        # Current price is 1.5% higher than entry (below 2.0% threshold)
        current_price = 101500
        result = signal_detector.check_add_position_signal(position, current_price)

        assert result is False

    def test_check_exit_signal_success(self, signal_detector: SignalDetector) -> None:
        """Test successful exit signal."""
        position = Position(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            entry_price=100000,
            quantity=0.01,
            entry_time=datetime.now(),
            highest_price=105000,  # Peak price
            stop_loss_price=101850,  # 3% below peak
            total_invested=1000
        )

        # Current price is 3.5% below highest price (above 3.0% threshold)
        current_price = 101325
        result = signal_detector.check_exit_signal(position, current_price)

        assert result is True

    def test_check_exit_signal_no_signal(self, signal_detector: SignalDetector) -> None:
        """Test no exit signal."""
        position = Position(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            entry_price=100000,
            quantity=0.01,
            entry_time=datetime.now(),
            highest_price=105000,  # Peak price
            stop_loss_price=101850,  # 3% below peak
            total_invested=1000
        )

        # Current price is 2.5% below highest price (below 3.0% threshold)
        current_price = 102375
        result = signal_detector.check_exit_signal(position, current_price)

        assert result is False


class TestPositionManager:
    """Test PositionManager class."""

    @pytest.fixture
    def parameters(self) -> StrategyParameters:
        """Create test parameters."""
        return StrategyParameters(
            capital_usage_percent=10,
            max_positions=3,
            min_order_size=0.001,
            max_order_size=1.0
        )

    @pytest.fixture
    def position_manager(self, parameters: StrategyParameters) -> PositionManager:
        """Create position manager instance."""
        return PositionManager(parameters)

    def test_calculate_position_size(self, position_manager: PositionManager) -> None:
        """Test position size calculation."""
        account_balance = 10000
        current_price = 50000

        # Expected: 10% of balance / price = 1000 / 50000 = 0.02
        size = position_manager.calculate_position_size(account_balance, current_price)

        assert size == 0.02

    def test_calculate_position_size_limits(self, position_manager: PositionManager) -> None:
        """Test position size calculation with limits."""
        # Test minimum size
        account_balance = 10  # Very small balance
        current_price = 50000
        size = position_manager.calculate_position_size(account_balance, current_price)
        assert size >= position_manager.parameters.min_order_size

        # Test maximum size
        account_balance = 10000000  # Very large balance
        current_price = 1
        size = position_manager.calculate_position_size(account_balance, current_price)
        assert size <= position_manager.parameters.max_order_size

    def test_add_position_success(self, position_manager: PositionManager) -> None:
        """Test successful position addition."""
        signal = Signal(
            signal_type="ENTRY",
            price=50000,
            volume=1000,
            volume_ratio=2.0,
            price_change=2.0,
            timestamp=datetime.now(),
            symbol="BTC/USDT"
        )

        account_balance = 10000
        result = position_manager.add_position(signal, account_balance)

        assert result is True
        assert len(position_manager.positions) == 1

        position = position_manager.positions[0]
        assert position.symbol == "BTC/USDT"
        assert position.entry_price == 50000
        assert position.side == OrderSide.BUY

    def test_add_position_max_limit(self, position_manager: PositionManager) -> None:
        """Test position addition with max positions limit."""
        # Add maximum number of positions
        for i in range(position_manager.parameters.max_positions):
            signal = Signal(
                signal_type="ENTRY",
                price=50000 + i * 1000,
                volume=1000,
                volume_ratio=2.0,
                price_change=2.0,
                timestamp=datetime.now(),
                symbol="BTC/USDT"
            )
            account_balance = 10000
            position_manager.add_position(signal, account_balance)

        # Try to add one more position
        signal = Signal(
            signal_type="ENTRY",
            price=60000,
            volume=1000,
            volume_ratio=2.0,
            price_change=2.0,
            timestamp=datetime.now(),
            symbol="BTC/USDT"
        )
        result = position_manager.add_position(signal, 10000)

        assert result is False
        assert len(position_manager.positions) == position_manager.parameters.max_positions

    def test_close_position(self, position_manager: PositionManager) -> None:
        """Test position closing."""
        # Add a position
        signal = Signal(
            signal_type="ENTRY",
            price=50000,
            volume=1000,
            volume_ratio=2.0,
            price_change=2.0,
            timestamp=datetime.now(),
            symbol="BTC/USDT"
        )
        account_balance = 10000
        position_manager.add_position(signal, account_balance)

        # Close position
        position = position_manager.positions[0]
        current_price = 55000
        position_manager.close_position(position, current_price)

        assert len(position_manager.positions) == 0

    def test_get_total_pnl(self, position_manager: PositionManager) -> None:
        """Test total PnL calculation."""
        # Add multiple positions
        for i, price in enumerate([50000, 51000, 52000]):
            signal = Signal(
                signal_type="ENTRY",
                price=price,
                volume=1000,
                volume_ratio=2.0,
                price_change=2.0,
                timestamp=datetime.now(),
                symbol="BTC/USDT"
            )
            position_manager.add_position(signal, 10000)

        # Calculate expected PnL
        current_price = 55000
        expected_pnl = sum(
            (current_price - price) * 0.0002  # position_size = balance * 10% / price
            for price in [50000, 51000, 52000]
        )

        actual_pnl = position_manager.get_total_pnl(current_price)
        assert abs(actual_pnl - expected_pnl) < 1e-10

    def test_get_status_summary_empty(self, position_manager: PositionManager) -> None:
        """Test status summary with no positions."""
        summary = position_manager.get_status_summary(50000)

        assert summary['positions_count'] == 0
        assert summary['total_pnl'] == 0.0
        assert summary['total_invested'] == 0.0
        assert summary['pnl_percentage'] == 0.0
        assert summary['positions'] == []

    def test_get_status_summary_with_positions(self, position_manager: PositionManager) -> None:
        """Test status summary with positions."""
        # Add a position
        signal = Signal(
            signal_type="ENTRY",
            price=50000,
            volume=1000,
            volume_ratio=2.0,
            price_change=2.0,
            timestamp=datetime.now(),
            symbol="BTC/USDT"
        )
        position_manager.add_position(signal, 10000)

        current_price = 55000
        summary = position_manager.get_status_summary(current_price)

        assert summary['positions_count'] == 1
        assert summary['total_pnl'] > 0
        assert summary['total_invested'] > 0
        assert summary['pnl_percentage'] > 0
        assert len(summary['positions']) == 1


if __name__ == "__main__":
    pytest.main([__file__])