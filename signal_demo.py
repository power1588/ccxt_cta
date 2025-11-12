#!/usr/bin/env python3
"""
信号触发演示 - 专门演示入场、加仓、出场信号
"""

import json
import time
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def create_strategy_with_custom_params(R=20, N=1.5, M=0.8, Q=10, U=1.5, S=2.0):
    """创建自定义参数的策略"""
    class CustomStrategy:
        def __init__(self):
            self.R = R  # 降低R值
            self.N = N  # 降低N值
            self.M = M  # 降低M值
            self.Q = Q
            self.U = U  # 降低U值
            self.S = S  # 降低S值
            self.symbol = "BTC/USDT"
            self.positions = []
            self.current_price = 100000.0

            print(f"🎯 自定义策略参数:")
            print(f"   R={R} (成交量平均周期)")
            print(f"   N={N} (成交量突破倍数)")
            print(f"   M={M}% (价格涨幅阈值)")
            print(f"   Q={Q}% (资金使用比例)")
            print(f"   U={U}% (加仓涨幅)")
            print(f"   S={S}% (止盈止损)")

        def generate_signal_klines(self, count=30):
            """生成包含信号的K线"""
            print(f"🔧 生成 {count} 根包含信号的K线...")

            timestamps = pd.date_range(
                start=datetime.now() - timedelta(minutes=count),
                end=datetime.now(),
                freq='1min'
            )

            data = []
            current_price = 100000

            for i, timestamp in enumerate(timestamps):
                open_price = current_price

                # 每10分钟制造一次信号
                if i % 10 == 5:  # 在第5分钟制造信号
                    # 价格大幅上涨
                    price_increase = random.uniform(0.008, 0.015)  # 0.8%-1.5%
                    close_price = open_price * (1 + price_increase)

                    # 大成交量
                    volume = 5000 * random.uniform(3, 6)  # 3-6倍基础成交量
                else:
                    # 正常波动
                    price_change = np.random.normal(0, 0.002)  # 0.2%波动
                    close_price = open_price * (1 + price_change)
                    volume = 1000 * random.uniform(0.5, 1.5)  # 正常成交量

                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

                data.append([timestamp, open_price, high_price, low_price, close_price, volume])
                current_price = close_price

            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df.set_index('timestamp', inplace=True)

            # 计算指标
            df['volume_ma'] = df['volume'].rolling(window=self.R).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100)

            return df

        def check_entry_signal(self, kline, timestamp):
            """检查入场信号"""
            volume_breakout = kline['volume_ratio'] >= self.N
            price_breakout = kline['price_change_pct'] >= self.M

            if volume_breakout and price_breakout:
                return {
                    'signal': 'ENTRY',
                    'price': kline['close'],
                    'volume': kline['volume'],
                    'volume_ratio': kline['volume_ratio'],
                    'price_change': kline['price_change_pct'],
                    'timestamp': timestamp
                }
            return None

        def execute_entry(self, signal):
            """执行入场"""
            position_size = 0.01  # 0.01 BTC

            position = {
                'symbol': self.symbol,
                'entry_price': signal['price'],
                'quantity': position_size,
                'entry_time': signal['timestamp'],
                'highest_price': signal['price'],
                'stop_loss_price': signal['price'] * (1 - self.S / 100),
                'total_invested': signal['price'] * position_size
            }

            self.positions.append(position)

            print("\n🚨" + "="*60)
            print("🚨【入场信号执行成功！】")
            print(f"💰 入场价格: ${signal['price']:,.2f}")
            print(f"📊 入场数量: {position_size:.6f} BTC")
            print(f"📈 成交量比: {signal['volume_ratio']:.2f}x (阈值: {self.N}x)")
            print(f"📊 价格变化: {signal['price_change']:+.2f}% (阈值: {self.M}%)")
            print(f"📍 止损价格: ${position['stop_loss_price']:,.2f}")
            print("🚨" + "="*60)

        def check_add_position_signal(self, position, current_price):
            """检查加仓信号"""
            price_increase_pct = ((current_price - position['entry_price']) /
                                 position['entry_price'] * 100)
            return price_increase_pct >= self.U

        def execute_add_position(self, position):
            """执行加仓"""
            additional_size = 0.005  # 0.005 BTC
            additional_cost = self.current_price * additional_size

            total_quantity = position['quantity'] + additional_size
            total_cost = position['total_invested'] + additional_cost

            position['quantity'] = total_quantity
            position['entry_price'] = total_cost / total_quantity
            position['total_invested'] = total_cost

            print("\n📈" + "="*50)
            print("📈【加仓信号执行成功！】")
            print(f"💰 加仓价格: ${self.current_price:,.2f}")
            print(f"📊 加仓数量: {additional_size:.6f} BTC")
            print(f"💼 新持仓均价: ${position['entry_price']:,.2f}")
            print(f"📈 总数量: {position['quantity']:.6f} BTC")
            print("📈" + "="*50)

        def check_exit_signal(self, position, current_price):
            """检查出场信号"""
            # 更新最高价
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
                position['stop_loss_price'] = position['highest_price'] * (1 - self.S / 100)

            drawdown_pct = ((position['highest_price'] - current_price) /
                           position['highest_price'] * 100)
            return drawdown_pct >= self.S

        def execute_exit(self, position):
            """执行出场"""
            exit_price = self.current_price
            pnl = (exit_price - position['entry_price']) * position['quantity']
            pnl_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)

            print("\n🔴" + "="*60)
            print("🔴【出场信号执行成功！】")
            print(f"💰 出场价格: ${exit_price:,.2f}")
            print(f"📊 入场价格: ${position['entry_price']:,.2f}")
            print(f"💼 持仓数量: {position['quantity']:.6f} BTC")
            print(f"⬆️  最高价格: ${position['highest_price']:,.2f}")
            print(f"🛑 止损价格: ${position['stop_loss_price']:,.2f}")
            print(f"💵 盈亏金额: ${pnl:+.2f}")
            print(f"📊 盈亏比例: {pnl_pct:+.2f}%")
            print("🔴" + "="*60)

            self.positions.remove(position)

        def print_positions_status(self):
            """打印持仓状态"""
            if not self.positions:
                return

            print(f"\n📊【当前持仓状态】")
            for i, pos in enumerate(self.positions, 1):
                current_pnl = (self.current_price - pos['entry_price']) * pos['quantity']
                pnl_pct = ((self.current_price - pos['entry_price']) / pos['entry_price'] * 100)

                print(f"持仓 {i}:")
                print(f"  入场价: ${pos['entry_price']:,.2f}")
                print(f"  当前价: ${self.current_price:,.2f}")
                print(f"  数量: {pos['quantity']:.6f} BTC")
                print(f"  最高价: ${pos['highest_price']:,.2f}")
                print(f"  止损价: ${pos['stop_loss_price']:,.2f}")
                print(f"  盈亏: ${current_pnl:+.2f} ({pnl_pct:+.2f}%)")

    return CustomStrategy()


def main():
    """主函数"""
    print("🎯 量价突破信号触发演示")
    print("="*60)
    print("💡 使用更低门槛参数，更容易触发信号")
    print("="*60)

    # 创建更容易触发信号的策略
    strategy = create_strategy_with_custom_params(
        R=20,    # 20分钟平均
        N=1.5,   # 1.5倍成交量
        M=0.8,   # 0.8%涨幅
        Q=10,    # 10%资金
        U=1.5,   # 1.5%加仓
        S=2.0    # 2%止损
    )

    # 生成包含信号的K线数据
    klines_data = strategy.generate_signal_klines(40)

    print(f"\n📈 开始模拟交易...")
    print("="*60)

    signal_count = 0
    for i, (timestamp, kline) in enumerate(klines_data.iterrows()):
        if i < 20:  # 前20根用于计算指标
            continue

        strategy.current_price = float(kline['close'])

        print(f"\n⏰ {timestamp.strftime('%H:%M:%S')}")
        print(f"💰 价格: ${strategy.current_price:,.2f} ({kline['price_change_pct']:+.2f}%)")
        print(f"📊 成交量: {kline['volume']:,.0f} (比: {kline['volume_ratio']:.2f}x)")

        # 检查入场信号
        signal = strategy.check_entry_signal(kline.to_dict(), timestamp)
        if signal:
            signal_count += 1
            strategy.execute_entry(signal)

        # 更新持仓（检查加仓和出场）
        positions_to_remove = []
        for position in strategy.positions:
            # 检查加仓
            if strategy.check_add_position_signal(position, strategy.current_price):
                strategy.execute_add_position(position)

            # 检查出場
            if strategy.check_exit_signal(position, strategy.current_price):
                strategy.execute_exit(position)
                positions_to_remove.append(position)

        # 移除已平仓持仓
        for pos in positions_to_remove:
            if pos in strategy.positions:
                strategy.positions.remove(pos)

        # 打印持仓状态
        if i % 5 == 0 or signal:
            strategy.print_positions_status()

        time.sleep(0.2)  # 短暂延迟

    # 最终统计
    print(f"\n🏁 模拟完成！")
    print(f"📊 总共触发了 {signal_count} 次入场信号")
    print(f"📈 最终持仓数量: {len(strategy.positions)}")

    if strategy.positions:
        strategy.print_positions_status()
    else:
        print("💼 所有持仓已平仓")

    print("\n✅ 演示完成！")
    print("\n💡 策略运行总结:")
    print("1. 成功检测到量价突破信号")
    print("2. 自动执行入场操作")
    print("3. 顺势加仓功能")
    print("4. 移动止盈止损机制")
    print("5. 完整的风险控制")

    print("\n🎮 如要调整参数，可以修改create_strategy_with_custom_params()的参数")


if __name__ == "__main__":
    main()