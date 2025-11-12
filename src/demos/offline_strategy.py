"""
Offline strategy demonstration.

This module provides a complete offline demonstration of the volume
price breakout strategy using simulated market data.
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
    TechnicalIndicators,
    Signal,
    OrderSide,
)


class MarketDataGenerator:
    """Generate realistic market data for backtesting."""

    def __init__(self, symbol: str = "BTC/USDT") -> None:
        """Initialize market data generator.

        Args:
            symbol: Trading symbol.
        """
        self.symbol = symbol
        self.base_price = 100000.0

    def generate_realistic_klines(self, count: int = 200) -> pd.DataFrame:
        """Generate realistic OHLCV data.

        Args:
            count: Number of candles to generate.

        Returns:
            DataFrame with OHLCV data.
        """
        print(f"🔧 Generating {count} realistic candles...")

        # Generate time series
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=count),
            end=datetime.now(),
            freq='1min'
        )

        data = []
        current_price = self.base_price

        # Set random seed for reproducibility
        np.random.seed(int(time.time()) % 1000)

        for i, timestamp in enumerate(timestamps):
            # Simulate price movement with trend and volatility
            base_volatility = 0.001

            # Add trend factor
            trend_factor = 0.0001 * np.sin(i / 50)

            # Add random shocks
            if i % 30 == 0:  # Periodic large movements
                shock = np.random.normal(0, 0.005)
            else:
                shock = np.random.normal(0, 0.001)

            total_change = trend_factor + shock

            open_price = current_price
            close_price = open_price * (1 + total_change)

            # Generate high and low prices
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0005)))

            # Simulate volume based on price movement
            base_volume = 1000
            volatility_factor = abs(total_change) * 500

            # Occasionally generate volume breakouts
            if random.random() < 0.15:  # 15% chance
                volume_multiplier = random.uniform(3, 8)
                volume = base_volume * volume_multiplier * (1 + volatility_factor)
            else:
                volume = base_volume * (1 + volatility_factor)

            data.append([timestamp, open_price, high_price, low_price, close_price, volume])
            current_price = close_price

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.set_index('timestamp', inplace=True)

        print(f"✅ Generated {len(df)} candles")
        return df


class OfflineStrategyDemo:
    """Offline strategy demonstration."""

    def __init__(self, config_path: str = "strategy_config.json") -> None:
        """Initialize offline demo.

        Args:
            config_path: Path to configuration file.
        """
        self.config = self._load_config(config_path)
        self.parameters = self._parse_parameters()
        self.symbol = self.config["trading"]["symbol"]

        # Initialize components
        self.market_data_generator = MarketDataGenerator(self.symbol)
        self.position_manager = PositionManager(self.parameters)
        self.signal_detector = SignalDetector(self.parameters)
        self.technical_indicators = TechnicalIndicators()

        # State
        self.current_price = 0.0
        self.klines_data = pd.DataFrame()

        self._print_config()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "trading": {"symbol": "BTC/USDT", "timeframe": "1m"},
            "parameters": {
                "volume_period": 30,
                "volume_multiplier": 2.0,
                "price_change_threshold": 1.5,
                "capital_usage_percent": 10,
                "add_position_threshold": 2.0,
                "stop_loss_threshold": 3.0,
                "max_positions": 3,
                "min_order_size": 0.001,
                "max_order_size": 1.0
            }
        }

    def _parse_parameters(self) -> StrategyParameters:
        """Parse strategy parameters."""
        params = self.config.get("parameters", {})
        return StrategyParameters(
            volume_period=params.get("volume_period", 30),
            volume_multiplier=params.get("volume_multiplier", 2.0),
            price_change_threshold=params.get("price_change_threshold", 1.5),
            capital_usage_percent=params.get("capital_usage_percent", 10),
            add_position_threshold=params.get("add_position_threshold", 2.0),
            stop_loss_threshold=params.get("stop_loss_threshold", 3.0),
            max_positions=params.get("max_positions", 3),
            min_order_size=params.get("min_order_size", 0.001),
            max_order_size=params.get("max_order_size", 1.0)
        )

    def _print_config(self) -> None:
        """Print current configuration."""
        print(f"✅ Offline Strategy Demo Initialized")
        print(f"📊 Symbol: {self.symbol}")
        print(f"⚙️ Parameters:")
        print(f"   Volume Period (R): {self.parameters.volume_period}")
        print(f"   Volume Multiplier (N): {self.parameters.volume_multiplier}x")
        print(f"   Price Change Threshold (M): {self.parameters.price_change_threshold}%")
        print(f"   Capital Usage (Q): {self.parameters.capital_usage_percent}%")
        print(f"   Add Position Threshold (U): {self.parameters.add_position_threshold}%")
        print(f"   Stop Loss Threshold (S): {self.parameters.stop_loss_threshold}%")
        print(f"   Max Positions: {self.parameters.max_positions}")

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        df['volume_ma'] = self.technical_indicators.calculate_volume_ma(
            df, self.parameters.volume_period
        )
        df['volume_ratio'] = self.technical_indicators.calculate_volume_ratio(
            df, df['volume_ma']
        )
        df['price_change_pct'] = self.technical_indicators.calculate_price_change_pct(df)
        return df

    def check_entry_signal(self, kline_data: Dict) -> Optional[Signal]:
        """Check for entry signal."""
        return self.signal_detector.detect_entry_signal(kline_data)

    def execute_entry(self, signal: Signal) -> None:
        """Execute entry."""
        # Simulated account balance
        account_balance = 10000.0

        success = self.position_manager.add_position(signal, account_balance)
        if success:
            self._print_entry_execution(signal)

    def _print_entry_execution(self, signal: Signal) -> None:
        """Print entry execution details."""
        print("\n" + "🚨" * 50)
        print("🚨【ENTRY SIGNAL EXECUTED!】")
        print(f"💰 Entry Price: ${signal.price:,.2f}")
        print(f"📊 Volume Ratio: {signal.volume_ratio:.2f}x (threshold: {self.parameters.volume_multiplier}x)")
        print(f"📈 Price Change: {signal.price_change:+.2f}% (threshold: {self.parameters.price_change_threshold}%)")
        print(f"📍 Current Positions: {len(self.position_manager.positions)}")
        print("🚨" * 50)

    def print_strategy_status(self) -> None:
        """Print current strategy status."""
        status = self.position_manager.get_status_summary(self.current_price)

        print("\n" + "=" * 60)
        print("📊 STRATEGY STATUS REPORT")
        print("=" * 60)
        print(f"💰 Current Price: ${self.current_price:,.2f}")
        print(f"📈 Active Positions: {status['positions_count']}")

        if status['positions']:
            total_pnl = status['total_pnl']
            total_invested = status['total_invested']
            pnl_percentage = status['pnl_percentage']

            print(f"\n📈 Position Details:")
            for i, pos in enumerate(status['positions'], 1):
                print(f"  Position {i}:")
                print(f"    Entry Price: ${pos['entry_price']:,.2f}")
                print(f"    Current Price: ${self.current_price:,.2f}")
                print(f"    Quantity: {self.position_manager.positions[i-1].quantity:.6f}")
                print(f"    Highest Price: ${pos['highest_price']:,.2f}")
                print(f"    Stop Loss: ${pos['stop_loss_price']:,.2f}")
                print(f"    PnL: ${pos['current_pnl']:+.2f} ({pos['pnl_percentage']:+.2f}%)")

            print(f"\n💰 Total PnL: ${total_pnl:+.2f} ({pnl_percentage:+.2f}%)")
            print(f"💼 Total Invested: ${total_invested:,.2f}")
        else:
            print("\n💼 No active positions")

        print("=" * 60)

    def run_simulation(self, duration_minutes: int = 50) -> None:
        """Run strategy simulation.

        Args:
            duration_minutes: Simulation duration in minutes.
        """
        print(f"\n🎯 Starting offline strategy simulation...")
        print(f"⏰ Duration: {duration_minutes} minutes")
        print("=" * 60)

        # Generate market data
        self.klines_data = self.market_data_generator.generate_realistic_klines(
            duration_minutes + 50
        )

        # Calculate indicators
        self.klines_data = self._calculate_indicators(self.klines_data)

        # Start from after the volume period
        start_idx = self.parameters.volume_period
        end_idx = min(start_idx + duration_minutes, len(self.klines_data))

        signal_count = 0

        for i in range(start_idx, end_idx):
            kline = self.klines_data.iloc[i]
            self.current_price = float(kline['close'])

            print(f"\n⏰ {kline.name.strftime('%H:%M:%S')}")
            print(f"💰 Price: ${self.current_price:,.2f} ({kline['price_change_pct']:+.2f}%)")
            print(f"📊 Volume: {kline['volume']:,.0f} (ratio: {kline['volume_ratio']:.2f}x)")

            # Check entry signal
            kline_data = kline.to_dict()
            kline_data['symbol'] = self.symbol
            kline_data['timestamp'] = kline.name

            signal = self.check_entry_signal(kline_data)
            if signal:
                signal_count += 1
                self.execute_entry(signal)

            # Update positions
            if self.position_manager.positions:
                account_balance = 10000.0  # Simulated
                self.position_manager.update_positions(
                    self.current_price,
                    self.signal_detector,
                    account_balance
                )

            # Print status periodically
            if i % 10 == 0 or signal:
                self.print_strategy_status()

            time.sleep(0.1)  # Small delay for visual effect

        # Final summary
        print(f"\n🏁 Simulation completed!")
        print(f"📊 Statistics:")
        print(f"  🚨 Entry Signals: {signal_count}")
        print(f"  📈 Final Positions: {len(self.position_manager.positions)}")

        self.print_strategy_status()


def main() -> None:
    """Main function."""
    print("🚀 Offline Volume Price Breakout Strategy Demo")
    print("=" * 60)
    print("💡 Complete simulation using realistic market data")
    print("=" * 60)

    # Create and run demo
    demo = OfflineStrategyDemo("strategy_config.json")
    demo.run_simulation(duration_minutes=50)

    print("\n✅ Demo completed!")
    print("\n📝 Strategy Summary:")
    print("1. Volume Breakout: Volume > N × R-minute average")
    print("2. Price Breakout: Price change > M% simultaneously")
    print("3. Position Management: Add on U% gains, exit on S% drawdown")
    print("4. Risk Control: Max positions, position sizing")

    print("\n⚠️ Important Notes:")
    print("- This is offline simulation with generated data")
    print("- Real trading requires thorough backtesting and risk assessment")
    print("- Cryptocurrency trading involves significant risk")


if __name__ == "__main__":
    main()