#!/usr/bin/env python3
"""
策略测试脚本
"""

import asyncio
import sys
from pathlib import Path

from strategy_runner import StrategyRunner


async def test_strategy_initialization():
    """测试策略初始化"""
    print("🧪 测试策略初始化...")

    runner = StrategyRunner("strategy_config.json")

    # 验证配置
    if not runner.validate_config():
        print("❌ 配置验证失败")
        return False

    # 初始化策略
    if not await runner.initialize():
        print("❌ 策略初始化失败")
        return False

    print("✅ 策略初始化成功")

    # 测试数据获取
    try:
        await runner.strategy.initialize_data()
        print("✅ 历史数据获取成功")
        print(f"   获取了 {len(runner.strategy.klines_data)} 根K线")
        print(f"   当前价格: ${runner.strategy.current_price:,.2f}")

        # 显示最新几根K线的数据
        print("\n📊 最新K线数据:")
        latest_klines = runner.strategy.klines_data.tail(3)
        for i, (timestamp, row) in enumerate(latest_klines.iterrows()):
            print(f"  K线 {i+1}:")
            print(f"    时间: {timestamp}")
            print(f"    收盘: ${row['close']:,.2f}")
            print(f"    成交量: {row['volume']:,.0f}")
            print(f"    成交量比: {row['volume_ratio']:.2f}")
            print(f"    价格变化: {row['price_change_pct']:+.2f}%")

    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return False

    # 测试信号检测
    try:
        signal = runner.strategy.check_entry_signal()
        if signal:
            print(f"\n🚨 检测到入场信号:")
            print(f"   价格: ${signal['price']:,.2f}")
            print(f"   成交量比: {signal['volume_ratio']:.2f}")
            print(f"   价格变化: {signal['price_change_pct']:+.2f}%")
        else:
            print("\n✅ 当前无入场信号")

    except Exception as e:
        print(f"❌ 信号检测失败: {e}")
        return False

    # 测试仓位计算
    try:
        position_size = runner.strategy.calculate_position_size()
        print(f"\n💰 建议仓位大小: {position_size:.6f} BTC")

    except Exception as e:
        print(f"❌ 仓位计算失败: {e}")

    # 清理
    await runner.cleanup()
    print("\n✅ 测试完成")
    return True


async def test_parameter_scenarios():
    """测试不同参数场景"""
    print("\n🔬 测试不同参数场景...")

    scenarios = [
        {"name": "保守策略", "R": 30, "N": 2.5, "M": 2.0, "Q": 5, "U": 3.0, "S": 2.0},
        {"name": "激进策略", "R": 20, "N": 1.5, "M": 1.0, "Q": 15, "U": 1.5, "S": 5.0},
        {"name": "平衡策略", "R": 25, "N": 2.0, "M": 1.5, "Q": 10, "U": 2.0, "S": 3.0}
    ]

    for scenario in scenarios:
        print(f"\n📊 测试场景: {scenario['name']}")

        # 创建临时配置
        config = {
            "strategy": {"name": "测试"},
            "trading": {"symbol": "BTC/USDT", "timeframe": "1m", "sandbox": True},
            "parameters": scenario,
            "risk_management": {"max_positions": 3, "max_drawdown": 20}
        }

        # 这里可以创建临时配置文件进行测试
        print(f"   参数: R={scenario['R']}, N={scenario['N']}, M={scenario['M']}%, "
              f"Q={scenario['Q']}%, U={scenario['U']}%, S={scenario['S']}%")


def print_strategy_info():
    """打印策略信息"""
    print("""
🎯 量价突破顺势加仓策略说明

策略逻辑：
1. 入场条件：
   - 当前1分钟K线的成交量 >= R分钟平均成交量的N倍
   - 当前1分钟K线的涨幅 >= M%
   - 满足条件时使用Q%的资金买入

2. 加仓条件：
   - 持仓后价格相比入场价上涨 >= U%
   - 每次加仓使用Q%的资金

3. 出场条件：
   - 价格相比持仓期间最高价回撤 >= S%
   - 移动止盈止损策略

风险控制：
- 最大持仓数量限制
- 最小/最大订单大小限制
- 滑点和重试机制

参数说明：
- R: 计算平均成交量的周期（分钟）
- N: 成交量突破倍数
- M: 入场价格涨幅阈值（%）
- Q: 每次交易使用的资金比例（%）
- U: 加仓触发涨幅（%）
- S: 止盈止损回撤阈值（%）

使用方法：
1. 配置API密钥到 strategy_config.json
2. 根据需要调整策略参数
3. 运行: python strategy_runner.py

注意事项：
⚠️  建议先在测试网中充分测试
⚠️  实盘交易前请评估风险承受能力
⚠️  数字货币交易存在高风险，请谨慎投资
    """)


async def main():
    """主测试函数"""
    print("🧪 量价突破策略测试")
    print("=" * 50)

    # 打印策略信息
    print_strategy_info()

    # 测试策略初始化
    success = await test_strategy_initialization()

    if success:
        # 测试参数场景
        await test_parameter_scenarios()
    else:
        print("❌ 策略初始化测试失败")
        sys.exit(1)

    print("\n✅ 所有测试完成")


if __name__ == "__main__":
    asyncio.run(main())