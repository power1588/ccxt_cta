"""
Main entry point for the CCXT CTA Strategy.

This module provides command-line interface for running the
volume price breakout strategy with various modes and configurations.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from src import VolumePriceBreakoutStrategy, __version__, __author__


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration.

    Args:
        level: Logging level.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def validate_config(config_path: str) -> bool:
    """Validate strategy configuration.

    Args:
        config_path: Path to configuration file.

    Returns:
        True if valid, False otherwise.
    """
    try:
        if not Path(config_path).exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Check required sections
        required_sections = ["strategy", "trading", "parameters"]
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing required configuration section: {section}")
                return False

        # Check required parameters
        required_params = [
            "volume_period", "volume_multiplier", "price_change_threshold",
            "capital_usage_percent", "add_position_threshold", "stop_loss_threshold"
        ]
        for param in required_params:
            if param not in config["parameters"]:
                print(f"❌ Missing required parameter: {param}")
                return False

        # Validate parameter ranges
        params = config["parameters"]
        if params["volume_period"] <= 0 or params["volume_period"] > 200:
            print("❌ volume_period must be between 1 and 200")
            return False

        if params["volume_multiplier"] <= 0 or params["volume_multiplier"] > 10:
            print("❌ volume_multiplier must be between 0 and 10")
            return False

        if not 0 <= params["price_change_threshold"] <= 50:
            print("❌ price_change_threshold must be between 0 and 50")
            return False

        if not 0 < params["capital_usage_percent"] <= 100:
            print("❌ capital_usage_percent must be between 0 and 100")
            return False

        print("✅ Configuration validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def print_strategy_info(config_path: str) -> None:
    """Print strategy information.

    Args:
        config_path: Path to configuration file.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        params = config["parameters"]
        trading = config["trading"]

        print("📊 Strategy Information")
        print("=" * 50)
        print(f"Name: {config['strategy']['name']}")
        print(f"Symbol: {trading['symbol']}")
        print(f"Timeframe: {trading['timeframe']}")
        print(f"Exchange: {trading['exchange']}")
        print(f"Sandbox: {trading.get('sandbox', False)}")
        print()
        print("📈 Parameters:")
        print(f"  Volume Period (R): {params['volume_period']} minutes")
        print(f"  Volume Multiplier (N): {params['volume_multiplier']}x")
        print(f"  Price Change (M): {params['price_change_threshold']}%")
        print(f"  Capital Usage (Q): {params['capital_usage_percent']}%")
        print(f"  Add Position (U): {params['add_position_threshold']}%")
        print(f"  Stop Loss (S): {params['stop_loss_threshold']}%")
        print(f"  Max Positions: {params['max_positions']}")

    except Exception as e:
        print(f"❌ Failed to read configuration: {e}")


async def run_offline_demo(config_path: str) -> None:
    """Run offline strategy demonstration.

    Args:
        config_path: Path to configuration file.
    """
    print("🎯 Running Offline Strategy Demo")
    print("=" * 50)

    try:
        from src.demos.offline_strategy import OfflineStrategyDemo

        demo = OfflineStrategyDemo(config_path)
        demo.run_simulation(duration_minutes=30)

    except Exception as e:
        print(f"❌ Offline demo failed: {e}")
        sys.exit(1)


async def run_signal_demo(config_path: str) -> None:
    """Run signal demonstration.

    Args:
        config_path: Path to configuration file.
    """
    print("🎯 Running Signal Demo")
    print("=" * 50)

    try:
        from src.demos.signal_demo import main as signal_demo_main

        signal_demo_main()

    except Exception as e:
        print(f"❌ Signal demo failed: {e}")
        sys.exit(1)


async def run_live_strategy(config_path: str, dry_run: bool = False) -> None:
    """Run live strategy.

    Args:
        config_path: Path to configuration file.
        dry_run: Whether to run in dry-run mode.
    """
    print("🚀 Starting Live Strategy")
    print("=" * 50)

    if dry_run:
        print("🧪 Running in DRY-RUN mode - No actual trades")

    try:
        strategy = VolumePriceBreakoutStrategy(config_path)

        # Print strategy info
        print_strategy_info(config_path)

        # Start strategy
        await strategy.run()

    except Exception as e:
        print(f"❌ Strategy execution failed: {e}")
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser.

    Returns:
        ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="CCXT CTA Volume Price Breakout Strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Run offline demo with default config
  python -m src.main --demo

  # Run signal demo
  python -m src.main --signal-demo

  # Run live strategy
  python -m src.main --live

  # Run in dry-run mode
  python -m src.main --live --dry-run

  # Use custom configuration
  python -m src.main --live --config custom_config.json

  # Validate configuration
  python -m src.main --validate-config --config strategy_config.json

Author: {__author__}
Version: {__version__}
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--config", "-c",
        default="strategy_config.json",
        help="Path to strategy configuration file (default: strategy_config.json)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run offline strategy demonstration"
    )

    parser.add_argument(
        "--signal-demo",
        action="store_true",
        help="Run signal demonstration"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live strategy"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual trades)"
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file"
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Print strategy information"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Handle different modes
    try:
        if args.validate_config:
            success = validate_config(args.config)
            sys.exit(0 if success else 1)

        elif args.info:
            print_strategy_info(args.config)

        elif args.demo:
            asyncio.run(run_offline_demo(args.config))

        elif args.signal_demo:
            asyncio.run(run_signal_demo(args.config))

        elif args.live:
            if not validate_config(args.config):
                sys.exit(1)
            asyncio.run(run_live_strategy(args.config, args.dry_run))

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️ Strategy interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()