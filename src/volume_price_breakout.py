"""
Volume Price Breakout Strategy.

A comprehensive cryptocurrency trading strategy that detects
volume and price breakouts for automated trading.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import ccxt
import pandas as pd
import numpy as np

from src.strategy import (
    StrategyParameters,
    PositionManager,
    SignalDetector,
    ExchangeManager,
    TechnicalIndicators,
    Signal,
)


class VolumePriceBreakoutStrategy:
    """Volume Price Breakout Strategy implementation."""

    def __init__(self, config_path: str = "strategy_config.json") -> None:
        """Initialize the strategy.

        Args:
            config_path: Path to configuration file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

        # Initialize strategy components
        self.parameters = self._parse_strategy_parameters()
        self.exchange_manager = ExchangeManager(self.config["trading"])
        self.signal_detector = SignalDetector(self.parameters)
        self.position_manager = PositionManager(self.parameters)
        self.technical_indicators = TechnicalIndicators()

        # Strategy state
        self.symbol: str = self.config["trading"]["symbol"]
        self.timeframe: str = self.config["trading"]["timeframe"]
        self.running: bool = False
        self.current_price: float = 0.0
        self.klines_data: pd.DataFrame = pd.DataFrame()

        self.logger.info("✅ Volume Price Breakout Strategy initialized")
        self.logger.info(f"📊 Symbol: {self.symbol}, Timeframe: {self.timeframe}")
        self.logger.info(
            f"⚙️ Parameters: R={self.parameters.volume_period}, "
            f"N={self.parameters.volume_multiplier}x, M={self.parameters.price_change_threshold}%"
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.
        """
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"⚠️ Config file {config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"❌ Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration.

        Returns:
            Default configuration dictionary.
        """
        return {
            "strategy": {
                "name": "Volume Price Breakout Strategy",
                "version": "1.0"
            },
            "trading": {
                "symbol": "BTC/USDT",
                "timeframe": "1m",
                "exchange": "binance",
                "sandbox": True,
                "api_key": "",
                "secret": ""
            },
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
            },
            "risk_management": {
                "max_drawdown": 20,
                "position_timeout": 3600
            },
            "execution": {
                "slippage": 0.1,
                "retry_attempts": 3,
                "retry_delay": 1,
                "order_timeout": 30
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_file": "strategy.log",
                "print_trades": True
            }
        }

    def _parse_strategy_parameters(self) -> StrategyParameters:
        """Parse strategy parameters from config.

        Returns:
            StrategyParameters object.
        """
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

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))

        # Configure basic logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.logger = logging.getLogger("VolumePriceBreakoutStrategy")

        # Add file handler if enabled
        if log_config.get("log_to_file", True):
            log_file = log_config.get("log_file", "strategy.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
            self.logger.addHandler(file_handler)

    async def initialize_data(self) -> None:
        """Initialize historical data."""
        try:
            self.logger.info(f"📊 Fetching historical data for {self.symbol}...")

            # Fetch initial OHLCV data
            ohlcv = await self.exchange_manager.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                limit=100
            )

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Calculate technical indicators
            df = self._calculate_indicators(df)

            self.klines_data = df
            self.current_price = float(df['close'].iloc[-1])

            self.logger.info(f"✅ Historical data loaded: {len(df)} candles")
            self.logger.info(f"💰 Current price: ${self.current_price:,.2f}")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize data: {e}")
            raise

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators.

        Args:
            df: OHLCV DataFrame.

        Returns:
            DataFrame with indicators.
        """
        # Calculate volume moving average
        df['volume_ma'] = self.technical_indicators.calculate_volume_ma(
            df, self.parameters.volume_period
        )

        # Calculate volume ratio
        df['volume_ratio'] = self.technical_indicators.calculate_volume_ratio(
            df, df['volume_ma']
        )

        # Calculate price change percentage
        df['price_change_pct'] = self.technical_indicators.calculate_price_change_pct(df)

        return df

    def check_entry_signal(self, kline_data: Dict) -> Optional[Signal]:
        """Check for entry signal.

        Args:
            kline_data: Latest kline data.

        Returns:
            Signal if detected, None otherwise.
        """
        return self.signal_detector.detect_entry_signal(kline_data)

    async def execute_entry(self, signal: Signal) -> None:
        """Execute entry order.

        Args:
            signal: Entry signal.
        """
        try:
            # Get account balance (simulation)
            account_balance = 10000.0  # Placeholder for real implementation

            # Add position
            success = self.position_manager.add_position(signal, account_balance)
            if success:
                # Log trade
                self.logger.info(
                    f"🚨 Entry executed: {signal.symbol} @ ${signal.price:.2f}, "
                    f"vol_ratio: {signal.volume_ratio:.2f}x, "
                    f"price_change: {signal.price_change:+.2f}%"
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to execute entry: {e}")

    async def watch_realtime_data(self) -> None:
        """Watch real-time market data."""
        self.logger.info("📡 Starting real-time data monitoring...")

        try:
            while self.running:
                try:
                    # Get current ticker data
                    ticker = await self.exchange_manager.exchange.fetch_ticker(self.symbol)
                    self.current_price = float(ticker['last'])

                    # Update klines data periodically
                    if len(self.klines_data) > 0:
                        # Get latest candle
                        latest_ohlcv = await self.exchange_manager.exchange.fetch_ohlcv(
                            self.symbol, self.timeframe, limit=1
                        )

                        if latest_ohlcv:
                            latest_data = latest_ohlcv[0]
                            latest_timestamp = pd.to_datetime(latest_data[0], unit='ms')

                            # Update if new candle
                            if latest_timestamp > self.klines_data.index[-1]:
                                new_candle = pd.DataFrame(
                                    [[latest_data[0], latest_data[1], latest_data[2],
                                      latest_data[3], latest_data[4], latest_data[5]]],
                                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                                )
                                new_candle['timestamp'] = pd.to_datetime(new_candle['timestamp'], unit='ms')
                                new_candle.set_index('timestamp', inplace=True)

                                # Recalculate indicators for new candle
                                self.klines_data = pd.concat([self.klines_data, new_candle])
                                self.klines_data = self._calculate_indicators(self.klines_data)

                                # Keep only last 200 candles
                                if len(self.klines_data) > 200:
                                    self.klines_data = self.klines_data.tail(200)

                                # Check entry signal
                                latest_candle = self.klines_data.iloc[-1].to_dict()
                                latest_candle['symbol'] = self.symbol
                                latest_candle['timestamp'] = latest_timestamp

                                signal = self.check_entry_signal(latest_candle)
                                if signal:
                                    await self.execute_entry(signal)

                    # Update positions
                    if self.position_manager.positions:
                        account_balance = 10000.0  # Placeholder
                        self.position_manager.update_positions(
                            self.current_price,
                            self.signal_detector,
                            account_balance
                        )

                    await asyncio.sleep(1)  # Prevent excessive API calls

                except Exception as e:
                    self.logger.error(f"❌ Error in real-time monitoring: {e}")
                    await asyncio.sleep(5)  # Wait before retry

        except Exception as e:
            self.logger.error(f"❌ Real-time monitoring failed: {e}")
            raise

    async def run(self) -> None:
        """Run the strategy."""
        try:
            self.logger.info("🚀 Starting Volume Price Breakout Strategy...")

            # Initialize exchange connection
            await self.exchange_manager.initialize()

            # Initialize historical data
            await self.initialize_data()

            # Start real-time monitoring
            self.running = True
            await self.watch_realtime_data()

        except KeyboardInterrupt:
            self.logger.info("⚠️ Strategy stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Strategy run failed: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.running = False
        await self.exchange_manager.close()
        self.logger.info("✅ Strategy stopped and cleaned up")

    def get_strategy_status(self) -> Dict[str, Any]:
        """Get current strategy status.

        Returns:
            Status dictionary.
        """
        status = self.position_manager.get_status_summary(self.current_price)
        status.update({
            'current_price': self.current_price,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'running': self.running,
            'parameters': {
                'volume_period': self.parameters.volume_period,
                'volume_multiplier': self.parameters.volume_multiplier,
                'price_change_threshold': self.parameters.price_change_threshold,
                'capital_usage_percent': self.parameters.capital_usage_percent,
                'add_position_threshold': self.parameters.add_position_threshold,
                'stop_loss_threshold': self.parameters.stop_loss_threshold,
                'max_positions': self.parameters.max_positions
            }
        })
        return status


async def main() -> None:
    """Main function for running the strategy."""
    strategy = VolumePriceBreakoutStrategy("strategy_config.json")
    await strategy.run()


if __name__ == "__main__":
    asyncio.run(main())