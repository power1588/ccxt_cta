"""
Signal demonstration module.

This module provides a focused demonstration of strategy signals
with clear visualization of entry, add position, and exit signals.
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from src.strategy import (
    StrategyParameters,
    PositionManager,
    SignalDetector,
    Signal,
    OrderSide,
)


class SignalDataGenerator:
    """Generate market data specifically designed to trigger signals."""

    def __init__(self, symbol: str = "BTC/USDT") -> None:
        """Initialize signal data generator.

        Args:
            symbol: Trading symbol.
        """
        self.symbol = symbol

    def generate_signal_rich_klines(self, count: int = 40) -> pd.DataFrame:
        """Generate klines with high probability of signals.

        Args:
            count: Number of candles to generate.

        Returns:
            DataFrame with OHLCV data.
        """
        print(f"🔧 Generating {count} signal-rich candles...")

        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=count),
            end=datetime.now(),
            freq='1min'
        )

        data = []
        current_price = 100000.0

        # Set seed for reproducibility
        np.random.seed(42)

        for i, timestamp in enumerate(timestamps):
            open_price = current_price

            # Create deliberate signals every 10 minutes
            if i % 10 == 5:  # Signal every 10th minute
                # Strong price movement
                price_increase = random.uniform(0.008, 0.015)  # 0.8%-1.5%
                close_price = open_price * (1 + price_increase)

                # High volume
                volume = 5000 * random.uniform(3, 6)  # 3-6x base volume
            else:
                # Normal price movement
                price_change = np.random.normal(0, 0.002)  # 0.2% volatility
                close_price = open_price * (1 + price_change)
                volume = 1000 * random.uniform(0.5, 1.5)  # Normal volume

            # Generate high/low prices
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

            data.append([timestamp, open_price, high_price, low_price, close_price, volume])
            current_price = close_price

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.set_index('timestamp', inplace=True)

        # Calculate indicators
        df = self._calculate_indicators(df)

        print(f"✅ Generated {len(df)} candles")
        return df

    def _calculate_indicators(self, df: pd.DataFrame, volume_period: int = 20) -> pd.DataFrame:
        """Calculate technical indicators."""
        df['volume_ma'] = df['volume'].rolling(window=volume_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100)
        return df


class SignalDemoStrategy:
    """Simplified strategy for signal demonstration."""

    def __init__(self, parameters: StrategyParameters) -> None:
        """Initialize demo strategy.

        Args:
            parameters: Strategy parameters.
        """
        self.parameters = parameters
        self.symbol = "BTC/USDT"
        self.positions = []
        self.current_price = 100000.0

        self._print_parameters()

    def _print_parameters(self) -> None:
        """Print current parameters."""
        print(f"🎯 Demo Strategy Parameters:")
        print(f"   Volume Period (R): {self.parameters.volume_period}")
        print(f"   Volume Multiplier (N): {self.parameters.volume_multiplier}")
        print(f"   Price Change Threshold (M): {self.parameters.price_change_threshold}%")
        print(f"   Add Position Threshold (U): {self.parameters.add_position_threshold}%")
        print(f"   Stop Loss Threshold (S): {self.parameters.stop_loss_threshold}%")

    def check_entry_signal(self, kline_data: Dict, timestamp: datetime) -> Optional[Signal]:
        """Check for entry signal."""
        volume_breakout = kline_data['volume_ratio'] >= self.parameters.volume_multiplier
        price_breakout = kline_data['price_change_pct'] >= self.parameters.price_change_threshold

        if volume_breakout and price_breakout:
            return Signal(
                signal_type="ENTRY",
                price=kline_data['close'],
                volume=kline_data['volume'],
                volume_ratio=kline_data['volume_ratio'],
                price_change=kline_data['price_change_pct'],
                timestamp=timestamp,
                symbol=self.symbol
            )
        return None

    def execute_entry(self, signal: Signal) -> None:
        """Execute entry with visual feedback."""
        position_size = 0.01  # Fixed size for demo

        position = {
            'symbol': self.symbol,
            'entry_price': signal.price,
            'quantity': position_size,
            'entry_time': signal.timestamp,
            'highest_price': signal.price,
            'stop_loss_price': signal.price * (1 - self.parameters.stop_loss_threshold / 100),
            'total_invested': signal.price * position_size
        }

        self.positions.append(position)
        self._print_entry_execution(signal, position)

    def _print_entry_execution(self, signal: Signal, position: Dict) -> None:
        """Print entry execution with clear formatting."""
        print("\n" + "🚨" * 60)
        print("🚨【ENTRY SIGNAL EXECUTED!】")
        print(f"💰 Entry Price: ${signal.price:,.2f}")
        print(f"📊 Position Size: {position['quantity']:.6f} BTC")
        print(f"📈 Volume Ratio: {signal.volume_ratio:.2f}x (Threshold: {self.parameters.volume_multiplier}x)")
        print(f"📊 Price Change: {signal.price_change:+.2f}% (Threshold: {self.parameters.price_change_threshold}%)")
        print(f"📍 Stop Loss: ${position['stop_loss_price']:,.2f}")
        print("🚨" * 60)

    def check_add_position_signal(self, position: Dict, current_price: float) -> bool:
        """Check for add position signal."""
        price_increase_pct = ((current_price - position['entry_price']) / position['entry_price'] * 100)
        return price_increase_pct >= self.parameters.add_position_threshold

    def execute_add_position(self, position: Dict) -> None:
        """Execute add position."""
        additional_size = 0.005  # Fixed additional size
        additional_cost = self.current_price * additional_size

        # Update position
        total_quantity = position['quantity'] + additional_size
        total_cost = position['total_invested'] + additional_cost

        position['quantity'] = total_quantity
        position['entry_price'] = total_cost / total_quantity
        position['total_invested'] = total_cost

        self._print_add_position_execution(position)

    def _print_add_position_execution(self, position: Dict) -> None:
        """Print add position execution."""
        print("\n" + "📈" * 50)
        print("📈【ADD POSITION SIGNAL EXECUTED!】")
        print(f"💰 Add Price: ${self.current_price:,.2f}")
        print(f"📊 Additional Size: {0.005:.6f} BTC")
        print(f"💼 New Average Price: ${position['entry_price']:,.2f}")
        print(f"📈 Total Quantity: {position['quantity']:.6f} BTC")
        print("📈" * 50)

    def check_exit_signal(self, position: Dict, current_price: float) -> bool:
        """Check for exit signal."""
        # Update highest price first
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
            position['stop_loss_price'] = position['highest_price'] * (
                1 - self.parameters.stop_loss_threshold / 100
            )

        drawdown_pct = ((position['highest_price'] - current_price) / position['highest_price'] * 100)
        return drawdown_pct >= self.parameters.stop_loss_threshold

    def execute_exit(self, position: Dict) -> None:
        """Execute exit."""
        exit_price = self.current_price
        pnl = (exit_price - position['entry_price']) * position['quantity']
        pnl_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)

        self._print_exit_execution(position, pnl, pnl_pct)
        self.positions.remove(position)

    def _print_exit_execution(self, position: Dict, pnl: float, pnl_pct: float) -> None:
        """Print exit execution."""
        print("\n" + "🔴" * 60)
        print("🔴【EXIT SIGNAL EXECUTED!】")
        print(f"💰 Exit Price: ${self.current_price:,.2f}")
        print(f"📊 Entry Price: ${position['entry_price']:,.2f}")
        print(f"💼 Position Size: {position['quantity']:.6f} BTC")
        print(f"⬆️  Highest Price: ${position['highest_price']:,.2f}")
        print(f"🛑 Stop Loss: ${position['stop_loss_price']:,.2f}")
        print(f"💵 PnL Amount: ${pnl:+.2f}")
        print(f"📊 PnL Percentage: {pnl_pct:+.2f}%")
        print("🔴" * 60)

    def print_positions_status(self) -> None:
        """Print current positions status."""
        if not self.positions:
            return

        print(f"\n📊【CURRENT POSITIONS STATUS】")
        for i, pos in enumerate(self.positions, 1):
            current_pnl = (self.current_price - pos['entry_price']) * pos['quantity']
            pnl_pct = ((self.current_price - pos['entry_price']) / pos['entry_price'] * 100)

            print(f"Position {i}:")
            print(f"  Entry Price: ${pos['entry_price']:,.2f}")
            print(f"  Current Price: ${self.current_price:,.2f}")
            print(f"  Quantity: {pos['quantity']:.6f} BTC")
            print(f"  Highest Price: ${pos['highest_price']:,.2f}")
            print(f"  Stop Loss: ${pos['stop_loss_price']:,.2f}")
            print(f"  PnL: ${current_pnl:+.2f} ({pnl_pct:+.2f}%)")


def create_demo_parameters(
    volume_period: int = 20,
    volume_multiplier: float = 1.5,
    price_change_threshold: float = 0.8,
    add_position_threshold: float = 1.5,
    stop_loss_threshold: float = 2.0
) -> StrategyParameters:
    """Create parameters optimized for signal demonstration.

    Args:
        volume_period: Volume moving average period.
        volume_multiplier: Volume breakout multiplier.
        price_change_threshold: Price change threshold.
        add_position_threshold: Add position threshold.
        stop_loss_threshold: Stop loss threshold.

    Returns:
        StrategyParameters object.
    """
    return StrategyParameters(
        volume_period=volume_period,
        volume_multiplier=volume_multiplier,
        price_change_threshold=price_change_threshold,
        capital_usage_percent=10,
        add_position_threshold=add_position_threshold,
        stop_loss_threshold=stop_loss_threshold,
        max_positions=3,
        min_order_size=0.001,
        max_order_size=1.0
    )


def main() -> None:
    """Main function."""
    print("🎯 Volume Price Breakout Signal Demonstration")
    print("=" * 60)
    print("💡 Lower threshold parameters for frequent signal generation")
    print("=" * 60)

    # Create strategy with optimized parameters
    parameters = create_demo_parameters(
        volume_period=20,    # Shorter period
        volume_multiplier=1.5,  # Lower multiplier
        price_change_threshold=0.8,  # Lower threshold
        add_position_threshold=1.5,  # Lower add threshold
        stop_loss_threshold=2.0   # Lower stop loss
    )

    strategy = SignalDemoStrategy(parameters)

    # Generate signal-rich data
    data_generator = SignalDataGenerator()
    klines_data = data_generator.generate_signal_rich_klines(40)

    print(f"\n📈 Starting signal simulation...")
    print("=" * 60)

    signal_count = 0
    for i, (timestamp, kline) in enumerate(klines_data.iterrows()):
        if i < 20:  # Skip first candles for indicator calculation
            continue

        strategy.current_price = float(kline['close'])

        print(f"\n⏰ {timestamp.strftime('%H:%M:%S')}")
        print(f"💰 Price: ${strategy.current_price:,.2f} ({kline['price_change_pct']:+.2f}%)")
        print(f"📊 Volume: {kline['volume']:,.0f} (ratio: {kline['volume_ratio']:.2f}x)")

        # Check entry signal
        signal = strategy.check_entry_signal(kline.to_dict(), timestamp)
        if signal:
            signal_count += 1
            strategy.execute_entry(signal)

        # Update positions
        positions_to_close = []
        for position in strategy.positions:
            # Check add position
            if strategy.check_add_position_signal(position, strategy.current_price):
                strategy.execute_add_position(position)

            # Check exit signal
            if strategy.check_exit_signal(position, strategy.current_price):
                strategy.execute_exit(position)
                positions_to_close.append(position)

        # Remove closed positions
        for pos in positions_to_close:
            if pos in strategy.positions:
                strategy.positions.remove(pos)

        # Print status periodically
        if i % 5 == 0 or signal:
            strategy.print_positions_status()

        time.sleep(0.2)  # Visual delay

    # Final summary
    print(f"\n🏁 Simulation completed!")
    print(f"📊 Total Entry Signals: {signal_count}")
    print(f"📈 Final Positions: {len(strategy.positions)}")

    if strategy.positions:
        strategy.print_positions_status()
    else:
        print("💼 All positions closed")

    print("\n✅ Demo completed!")
    print("\n💡 Signal Demo Summary:")
    print("1. ✅ Volume breakout detection")
    print("2. ✅ Price breakout detection")
    print("3. ✅ Automatic entry execution")
    print("4. ✅ Position addition logic")
    print("5. ✅ Stop loss mechanism")
    print("6. ✅ Complete risk management")

    print("\n🎮 Adjust parameters in create_demo_parameters() to test different scenarios")


if __name__ == "__main__":
    main()