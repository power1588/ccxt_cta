#!/usr/bin/env python3
"""
量价突破顺势加仓策略执行器
"""

import asyncio
import argparse
import json
import signal
import sys
from pathlib import Path

from volume_price_breakout_strategy import VolumePriceBreakoutStrategy


class StrategyRunner:
    """策略运行器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.strategy = None
        self.running = False

    async def initialize(self):
        """初始化策略"""
        try:
            self.strategy = VolumePriceBreakoutStrategy(self.config_path)
            print("✅ 策略初始化成功")
            return True
        except Exception as e:
            print(f"❌ 策略初始化失败: {e}")
            return False

    async def run(self):
        """运行策略"""
        if not self.strategy:
            print("❌ 策略未初始化")
            return

        try:
            self.running = True
            print("🚀 启动量价突破顺势加仓策略...")

            # 打印策略参数
            config = self.strategy.config
            params = config["parameters"]
            print(f"📊 策略参数:")
            print(f"   R (平均成交量周期): {params['R']} 分钟")
            print(f"   N (成交量倍数): {params['N']} 倍")
            print(f"   M (价格涨幅): {params['M']}%")
            print(f"   Q (资金比例): {params['Q']}%")
            print(f"   U (加仓涨幅): {params['U']}%")
            print(f"   S (止盈止损): {params['S']}%")

            print(f"💰 交易对: {config['trading']['symbol']}")
            print(f"⏰ 时间周期: {config['trading']['timeframe']}")

            if config['trading']['sandbox']:
                print("🧪 环境: 测试网")
            else:
                print("🏭 环境: 生产网")

            print("-" * 50)

            # 运行策略
            await self.strategy.run()

        except KeyboardInterrupt:
            print("\n⚠️  用户中断，正在停止策略...")
        except Exception as e:
            print(f"❌ 策略运行异常: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        self.running = False
        if self.strategy and hasattr(self.strategy, 'exchange'):
            if hasattr(self.strategy.exchange, 'close'):
                await self.strategy.exchange.close()
        print("✅ 策略已停止")

    def print_status(self):
        """打印策略状态"""
        if not self.strategy:
            print("❌ 策略未初始化")
            return

        try:
            status = self.strategy.get_strategy_status()

            print("\n" + "=" * 50)
            print("📈 策略状态报告")
            print("=" * 50)

            print(f"当前价格: ${status['current_price']:,.2f}")
            print(f"持仓数量: {status['positions_count']}")
            print(f"总投入: ${status['total_invested']:,.2f}")
            print(f"当前盈亏: ${status['total_pnl']:,.2f}")
            print(f"盈亏比例: {status['pnl_percentage']:+.2f}%")

            if status['positions']:
                print(f"\n📊 持仓详情:")
                for i, pos in enumerate(status['positions'], 1):
                    pnl_pct = ((pos['current_price'] - pos['entry_price']) /
                             pos['entry_price'] * 100)
                    print(f"  持仓 {i}:")
                    print(f"    入场价: ${pos['entry_price']:,.2f}")
                    print(f"    当前价: ${pos['current_price']:,.2f}")
                    print(f"    数量: {pos['quantity']:.6f}")
                    print(f"    最高价: ${pos['highest_price']:,.2f}")
                    print(f"    止损价: ${pos['stop_loss_price']:,.2f}")
                    print(f"    盈亏: ${pos['pnl']:+.2f} ({pnl_pct:+.2f}%)")

            print("=" * 50)

        except Exception as e:
            print(f"❌ 获取策略状态失败: {e}")

    def validate_config(self) -> bool:
        """验证配置文件"""
        try:
            if not Path(self.config_path).exists():
                print(f"❌ 配置文件不存在: {self.config_path}")
                return False

            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # 检查必要的配置项
            required_keys = [
                "strategy", "trading", "parameters", "risk_management"
            ]

            for key in required_keys:
                if key not in config:
                    print(f"❌ 配置文件缺少必要项: {key}")
                    return False

            # 检查交易参数
            params = config["parameters"]
            required_params = ["R", "N", "M", "Q", "U", "S"]

            for param in required_params:
                if param not in params:
                    print(f"❌ 策略参数缺失: {param}")
                    return False

            # 检查参数范围
            if params["R"] <= 0 or params["R"] > 100:
                print("❌ 参数 R 必须在 (0, 100] 范围内")
                return False

            if params["N"] <= 0 or params["N"] > 10:
                print("❌ 参数 N 必须在 (0, 10] 范围内")
                return False

            if params["M"] <= 0 or params["M"] > 50:
                print("❌ 参数 M 必须在 (0, 50] 范围内")
                return False

            if params["Q"] <= 0 or params["Q"] > 100:
                print("❌ 参数 Q 必须在 (0, 100] 范围内")
                return False

            if params["U"] <= 0 or params["U"] > 50:
                print("❌ 参数 U 必须在 (0, 50] 范围内")
                return False

            if params["S"] <= 0 or params["S"] > 50:
                print("❌ 参数 S 必须在 (0, 50] 范围内")
                return False

            print("✅ 配置文件验证通过")
            return True

        except json.JSONDecodeError as e:
            print(f"❌ 配置文件JSON格式错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 配置文件验证失败: {e}")
            return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="量价突破顺势加仓策略")
    parser.add_argument(
        "--config", "-c",
        default="strategy_config.json",
        help="配置文件路径 (默认: strategy_config.json)"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="显示策略状态"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="仅验证配置文件"
    )
    parser.add_argument(
        "--backtest", "-b",
        action="store_true",
        help="运行回测模式"
    )

    args = parser.parse_args()

    runner = StrategyRunner(args.config)

    # 验证配置文件
    if not runner.validate_config():
        sys.exit(1)

    if args.validate:
        print("✅ 配置文件验证完成")
        return

    # 初始化策略
    if not await runner.initialize():
        sys.exit(1)

    if args.status:
        # 显示状态
        runner.print_status()
        return

    if args.backtest:
        # 回测模式（待实现）
        print("📊 回测模式开发中...")
        return

    # 设置信号处理
    def signal_handler(signum, frame):
        print(f"\n⚠️  收到信号 {signum}，正在停止策略...")
        asyncio.create_task(runner.cleanup())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行策略
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())