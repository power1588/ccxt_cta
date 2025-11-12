#!/usr/bin/env python3
"""
离线量价突破策略演示
完全基于模拟数据，无需网络连接
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class OfflineVolumePriceBreakoutStrategy:
    """离线量价突破策略演示"""

    def __init__(self, config_path: str = "strategy_config.json"):
        """初始化策略"""
        self.config = self._load_config(config_path)

        # 策略参数
        self.R = self.config["parameters"]["R"]  # 平均成交量计算周期
        self.N = self.config["parameters"]["N"]  # 成交量倍数
        self.M = self.config["parameters"]["M"]  # 价格涨幅百分比
        self.Q = self.config["parameters"]["Q"]  # 资金使用比例
        self.U = self.config["parameters"]["U"]  # 加仓涨幅百分比
        self.S = self.config["parameters"]["S"]  # 止盈止损百分比

        # 交易参数
        self.symbol = self.config["trading"]["symbol"]
        self.timeframe = self.config["trading"]["timeframe"]

        # 策略状态
        self.positions: List[Dict] = []
        self.klines_data = pd.DataFrame()
        self.current_price = 103000.0  # 模拟初始价格

        print(f"✅ 策略初始化完成")
        print(f"📊 交易对: {self.symbol}")
        print(f"📈 时间周期: {self.timeframe}")
        print(f"⚙️  策略参数: R={self.R}, N={self.N}, M={self.M}%, Q={self.Q}%, U={self.U}%, S={self.S}%")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  配置文件加载失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "strategy": {"name": "量价突破顺势加仓策略"},
            "trading": {"symbol": "BTC/USDT", "timeframe": "1m"},
            "parameters": {"R": 30, "N": 2.0, "M": 1.5, "Q": 10, "U": 2.0, "S": 3.0},
            "risk_management": {"max_positions": 3, "max_drawdown": 20}
        }

    def generate_realistic_klines(self, count: int = 200) -> pd.DataFrame:
        """生成更真实的K线数据"""
        print(f"🔧 生成 {count} 根真实感K线数据...")

        # 设置随机种子确保可重现
        np.random.seed(int(time.time()) % 1000)

        # 生成时间序列
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=count),
            end=datetime.now(),
            freq='1min'
        )

        data = []
        base_price = 103000
        current_price = base_price

        for i, timestamp in enumerate(timestamps):
            # 模拟价格波动 - 带有趋势和周期性
            base_volatility = 0.001  # 0.1%基础波动率

            # 添加趋势因素
            trend_factor = 0.0001 * np.sin(i / 50)  # 周期性趋势

            # 添加随机冲击
            if i % 30 == 0:  # 每30分钟可能有大波动
                shock = np.random.normal(0, 0.005)
            else:
                shock = np.random.normal(0, 0.001)

            total_change = trend_factor + shock

            open_price = current_price
            close_price = open_price * (1 + total_change)

            # 生成高低价格
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0005)))

            # 模拟成交量 - 基于价格变动
            base_volume = 1000
            volatility_factor = abs(total_change) * 500  # 波动越大成交量越大

            # 偶尔产生成交量突破
            if random.random() < 0.15:  # 15%概率产生大成交量
                volume_multiplier = random.uniform(3, 8)
                volume = base_volume * volume_multiplier * (1 + volatility_factor)
            else:
                volume = base_volume * (1 + volatility_factor)

            data.append([timestamp, open_price, high_price, low_price, close_price, volume])
            current_price = close_price

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.set_index('timestamp', inplace=True)

        # 计算技术指标
        df = self.calculate_indicators(df)

        print(f"✅ 生成了 {len(df)} 根K线数据")
        return df

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 计算滚动平均成交量
        df['volume_ma'] = df['volume'].rolling(window=self.R).mean()

        # 计算成交量比
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # 计算价格涨跌幅
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100)

        # 计算收盘价变化
        df['close_change'] = df['close'].pct_change()

        return df

    def check_entry_signal(self, kline: Dict) -> Optional[Dict]:
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
                'timestamp': kline.name
            }

        return None

    def calculate_position_size(self) -> float:
        """计算仓位大小"""
        # 模拟账户余额
        account_balance = 10000  # 10000 USDT
        invest_amount = account_balance * (self.Q / 100)
        position_size = invest_amount / self.current_price
        return position_size

    def execute_entry(self, signal: Dict):
        """执行入场"""
        max_positions = self.config["risk_management"]["max_positions"]
        if len(self.positions) >= max_positions:
            print(f"⚠️  已达最大持仓数量 {max_positions}，跳过入场信号")
            return

        position_size = self.calculate_position_size()

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

        print("🚨" + "="*50)
        print("🚨 入场信号执行成功！")
        print(f"💰 入场价格: ${signal['price']:,.2f}")
        print(f"📊 入场数量: {position_size:.6f} BTC")
        print(f"📈 成交量比: {signal['volume_ratio']:.2f}x")
        print(f"📊 价格变化: {signal['price_change_pct']:+.2f}%")
        print(f"💼 当前持仓数: {len(self.positions)}")
        print(f"📍 止损价格: ${position['stop_loss_price']:,.2f}")
        print("🚨" + "="*50)

    def check_add_position_signal(self, position: Dict, current_price: float) -> bool:
        """检查加仓信号"""
        price_increase_pct = ((current_price - position['entry_price']) /
                             position['entry_price'] * 100)
        return price_increase_pct >= self.U

    def check_exit_signal(self, position: Dict, current_price: float) -> bool:
        """检查出场信号"""
        drawdown_pct = ((position['highest_price'] - current_price) /
                       position['highest_price'] * 100)
        return drawdown_pct >= self.S

    def update_positions(self, current_price: float):
        """更新持仓状态"""
        positions_to_remove = []

        for position in self.positions:
            # 更新最高价和止损价
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
                position['stop_loss_price'] = position['highest_price'] * (1 - self.S / 100)

            # 检查加仓信号
            if self.check_add_position_signal(position, current_price):
                self.execute_add_position(position)

            # 检查出场信号
            if self.check_exit_signal(position, current_price):
                self.execute_exit(position)
                positions_to_remove.append(position)

        # 移除已平仓的持仓
        for position in positions_to_remove:
            if position in self.positions:
                self.positions.remove(position)

    def execute_add_position(self, position: Dict):
        """执行加仓"""
        max_positions = self.config["risk_management"]["max_positions"]
        if len(self.positions) >= max_positions:
            return

        additional_size = self.calculate_position_size()
        additional_cost = self.current_price * additional_size

        # 更新持仓信息
        total_quantity = position['quantity'] + additional_size
        total_cost = position['total_invested'] + additional_cost

        position['quantity'] = total_quantity
        position['entry_price'] = total_cost / total_quantity
        position['total_invested'] = total_cost

        print("📈" + "="*40)
        print("📈 加仓信号执行成功！")
        print(f"💰 加仓价格: ${self.current_price:,.2f}")
        print(f"📊 加仓数量: {additional_size:.6f} BTC")
        print(f"💼 新持仓均价: ${position['entry_price']:,.2f}")
        print(f"📈 总数量: {position['quantity']:.6f} BTC")
        print("📈" + "="*40)

    def execute_exit(self, position: Dict):
        """执行出场"""
        exit_price = self.current_price
        pnl = (exit_price - position['entry_price']) * position['quantity']
        pnl_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)

        print("🔴" + "="*50)
        print("🔴 出场信号执行成功！")
        print(f"💰 出场价格: ${exit_price:,.2f}")
        print(f"📊 入场价格: ${position['entry_price']:,.2f}")
        print(f"💼 持仓数量: {position['quantity']:.6f} BTC")
        print(f"📈 最高价格: ${position['highest_price']:,.2f}")
        print(f"💵 盈亏金额: ${pnl:+.2f}")
        print(f"📊 盈亏比例: {pnl_pct:+.2f}%")
        print("🔴" + "="*50)

    def print_status(self):
        """打印当前状态"""
        print("\n" + "="*60)
        print("📊 策略状态报告")
        print("="*60)

        print(f"💰 当前价格: ${self.current_price:,.2f}")
        print(f"📈 持仓数量: {len(self.positions)}")

        if self.positions:
            total_pnl = 0
            total_invested = 0

            print(f"\n📈 持仓详情:")
            for i, pos in enumerate(self.positions, 1):
                current_pnl = (self.current_price - pos['entry_price']) * pos['quantity']
                pnl_pct = ((self.current_price - pos['entry_price']) / pos['entry_price'] * 100)

                total_pnl += current_pnl
                total_invested += pos['total_invested']

                print(f"  持仓 {i}:")
                print(f"    💰 入场价: ${pos['entry_price']:,.2f}")
                print(f"    📍 当前价: ${self.current_price:,.2f}")
                print(f"    📊 数量: {pos['quantity']:.6f}")
                print(f"    ⬆️  最高价: ${pos['highest_price']:,.2f}")
                print(f"    🛑 止损价: ${pos['stop_loss_price']:,.2f}")
                print(f"    💵 盈亏: ${current_pnl:+.2f} ({pnl_pct:+.2f}%)")

            total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            print(f"\n💰 总盈亏: ${total_pnl:+.2f} ({total_pnl_pct:+.2f}%)")
            print(f"💼 总投入: ${total_invested:,.2f}")
        else:
            print("\n💼 当前无持仓")

        print("="*60)

    def run_simulation(self, duration_minutes: int = 50):
        """运行模拟"""
        print(f"\n🎯 开始离线量价突破策略模拟...")
        print(f"⏰ 模拟时长: {duration_minutes} 分钟")
        print("="*60)

        # 生成K线数据
        self.klines_data = self.generate_realistic_klines(duration_minutes + 50)

        # 从第R根K线开始，确保有足够的历史数据
        start_idx = self.R
        end_idx = min(start_idx + duration_minutes, len(self.klines_data))

        signal_count = 0
        add_position_count = 0
        exit_count = 0

        for i in range(start_idx, end_idx):
            kline = self.klines_data.iloc[i]
            self.current_price = float(kline['close'])

            print(f"\n⏰ 时间: {kline.name.strftime('%H:%M:%S')}")
            print(f"💰 价格: ${self.current_price:,.2f} ({kline['price_change_pct']:+.2f}%)")
            print(f"📊 成交量: {kline['volume']:,.0f} (比: {kline['volume_ratio']:.2f})")

            # 检查入场信号
            signal = self.check_entry_signal(kline.to_dict())
            if signal:
                signal_count += 1
                self.execute_entry(signal)

            # 更新现有持仓
            old_positions_count = len(self.positions)
            self.update_positions(self.current_price)

            # 统计操作
            if len(self.positions) > old_positions_count:
                add_position_count += 1
            elif len(self.positions) < old_positions_count:
                exit_count += 1

            # 每10分钟或有交易时打印状态
            if (i - start_idx) % 10 == 0 or signal:
                self.print_status()

            time.sleep(0.1)  # 短暂延迟

        # 最终状态和统计
        print(f"\n🏁 模拟完成!")
        print(f"📊 交易统计:")
        print(f"  🚨 入场信号: {signal_count} 次")
        print(f"  📈 加仓操作: {add_position_count} 次")
        print(f"  🔴 出场操作: {exit_count} 次")

        self.print_status()


def main():
    """主函数"""
    print("🚀 离线量价突破顺势加仓策略演示")
    print("="*60)
    print("💡 完全基于模拟数据，无需网络连接")
    print("="*60)

    # 创建策略实例
    strategy = OfflineVolumePriceBreakoutStrategy("strategy_config.json")

    # 运行模拟
    strategy.run_simulation(duration_minutes=50)

    print("\n✅ 演示完成!")
    print("\n📝 策略说明:")
    print("1. 成交量突破：成交量超过R分钟平均成交量的N倍")
    print("2. 价格突破：同时价格涨幅超过M%时触发入场")
    print("3. 顺势加仓：价格相比入场价上涨U%时加仓")
    print("4. 移动止盈：价格从最高点回撤S%时出场")

    print("\n🎮 控制参数:")
    print(f"- R={strategy.R}分钟 (成交量平均周期)")
    print(f"- N={strategy.N}倍 (成交量突破倍数)")
    print(f"- M={strategy.M}% (价格涨幅阈值)")
    print(f"- Q={strategy.Q}% (资金使用比例)")
    print(f"- U={strategy.U}% (加仓涨幅)")
    print(f"- S={strategy.S}% (止盈止损)")

    print("\n⚠️  重要提醒:")
    print("- 这是离线演示程序，使用模拟数据")
    print("- 实盘交易前请充分回测和风险评估")
    print("- 数字货币交易存在高风险，请谨慎投资")


if __name__ == "__main__":
    main()