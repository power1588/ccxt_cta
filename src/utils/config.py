"""
Configuration management utilities.

This module provides utilities for loading, validating, and managing
strategy configurations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from src.strategy import StrategyParameters


class ConfigManager:
    """Configuration management class."""

    DEFAULT_CONFIG_PATHS = [
        "strategy_config.json",
        "config/strategy.default.json",
        "config/strategy.conservative.json",
        "config/strategy.aggressive.json",
    ]

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file.
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file.
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            self.logger.info(f"✅ Configuration loaded from {config_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to load configuration: {e}")
            raise

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration.

        Returns:
            Default configuration dictionary.
        """
        return {
            "strategy": {
                "name": "Volume Price Breakout Strategy",
                "description": "Cryptocurrency trading strategy based on volume and price breakouts",
                "version": "1.0.0",
                "mode": "paper"
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
                "position_timeout": 3600,
                "max_daily_loss": 1000,
                "stop_all_trading": False
            },
            "execution": {
                "slippage": 0.1,
                "retry_attempts": 3,
                "retry_delay": 1,
                "order_timeout": 30,
                "use_market_orders": True,
                "partial_fill_handling": "retry"
            },
            "monitoring": {
                "log_level": "INFO",
                "log_to_file": True,
                "log_file": "logs/strategy.log",
                "log_trades": True,
                "log_signals": True,
                "metrics_collection": True,
                "alert_webhook": "",
                "alert_email": ""
            }
        }

    def get_strategy_parameters(self) -> StrategyParameters:
        """Extract strategy parameters from configuration.

        Returns:
            StrategyParameters object.
        """
        params_config = self.config.get("parameters", {})

        return StrategyParameters(
            volume_period=params_config.get("volume_period", 30),
            volume_multiplier=params_config.get("volume_multiplier", 2.0),
            price_change_threshold=params_config.get("price_change_threshold", 1.5),
            capital_usage_percent=params_config.get("capital_usage_percent", 10),
            add_position_threshold=params_config.get("add_position_threshold", 2.0),
            stop_loss_threshold=params_config.get("stop_loss_threshold", 3.0),
            max_positions=params_config.get("max_positions", 3),
            min_order_size=params_config.get("min_order_size", 0.001),
            max_order_size=params_config.get("max_order_size", 1.0)
        )

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of validation errors.
        """
        errors: List[str] = []

        if not self.config:
            errors.append("Configuration is empty")
            return errors

        # Check required sections
        required_sections = ["strategy", "trading", "parameters"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")

        # Validate strategy section
        if "strategy" in self.config:
            strategy_config = self.config["strategy"]
            strategy_required = ["name", "version"]
            for field in strategy_required:
                if field not in strategy_config:
                    errors.append(f"Missing strategy field: {field}")

        # Validate trading section
        if "trading" in self.config:
            trading_config = self.config["trading"]
            trading_required = ["symbol", "timeframe"]
            for field in trading_required:
                if field not in trading_config:
                    errors.append(f"Missing trading field: {field}")

            # Validate symbol format
            if "symbol" in trading_config:
                symbol = trading_config["symbol"]
                if not isinstance(symbol, str) or "/" not in symbol:
                    errors.append(f"Invalid symbol format: {symbol}")

        # Validate parameters section
        if "parameters" in self.config:
            params_config = self.config["parameters"]
            param_fields = [
                "volume_period", "volume_multiplier", "price_change_threshold",
                "capital_usage_percent", "add_position_threshold", "stop_loss_threshold",
                "max_positions", "min_order_size", "max_order_size"
            ]

            for field in param_fields:
                if field not in params_config:
                    errors.append(f"Missing parameter field: {field}")

            # Validate parameter ranges
            if "volume_period" in params_config:
                period = params_config["volume_period"]
                if not isinstance(period, (int, float)) or period <= 0 or period > 200:
                    errors.append("volume_period must be between 1 and 200")

            if "volume_multiplier" in params_config:
                multiplier = params_config["volume_multiplier"]
                if not isinstance(multiplier, (int, float)) or multiplier <= 0 or multiplier > 10:
                    errors.append("volume_multiplier must be between 0 and 10")

            if "price_change_threshold" in params_config:
                threshold = params_config["price_change_threshold"]
                if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 50:
                    errors.append("price_change_threshold must be between 0 and 50")

            if "capital_usage_percent" in params_config:
                usage = params_config["capital_usage_percent"]
                if not isinstance(usage, (int, float)) or usage <= 0 or usage > 100:
                    errors.append("capital_usage_percent must be between 0 and 100")

            if "max_positions" in params_config:
                max_pos = params_config["max_positions"]
                if not isinstance(max_pos, int) or max_pos <= 0 or max_pos > 20:
                    errors.append("max_positions must be between 1 and 20")

        return errors

    def save_config(self, output_path: str) -> None:
        """Save configuration to file.

        Args:
            output_path: Path to save configuration.
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ Configuration saved to {output_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to save configuration: {e}")
            raise

    def merge_configs(self, override_config: Dict[str, Any]) -> None:
        """Merge override configuration into current config.

        Args:
            override_config: Configuration to merge.
        """
        def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = deep_merge(self.config, override_config)

    def get_section(self, section: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get configuration section.

        Args:
            section: Section name.
            default: Default value if section not found.

        Returns:
            Configuration section.
        """
        return self.config.get(section, default or {})

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            section: Section name.
            key: Key name.
            default: Default value.

        Returns:
            Configuration value.
        """
        return self.config.get(section, {}).get(key, default)

    def list_available_configs(self) -> List[str]:
        """List available configuration files.

        Returns:
            List of configuration file paths.
        """
        config_files = []

        for path in self.DEFAULT_CONFIG_PATHS:
            config_path = Path(path)
            if config_path.exists():
                config_files.append(str(config_path))

        return config_files

    def __str__(self) -> str:
        """String representation of configuration.

        Returns:
            Configuration summary.
        """
        if not self.config:
            return "Configuration: Empty"

        strategy_name = self.get_value("strategy", "name", "Unknown")
        symbol = self.get_value("trading", "symbol", "Unknown")
        mode = self.get_value("strategy", "mode", "Unknown")

        return f"Configuration: {strategy_name} ({symbol}) - Mode: {mode}"