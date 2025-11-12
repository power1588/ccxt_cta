#!/usr/bin/env python3
"""
量价突破顺势加仓策略演示程序
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class StrategyDemo:
    """策略演示类"""

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

        # 模拟数据
        self.current_price = 103000.0
        self.positions: List[Dict] = []
        self.klines_data = self._generate_mock_klines()

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "strategy": {"name": "量价突破顺势加仓策略"},
            "trading": {"symbol": "BTC/USDT", "timeframe": "1m"},
            "parameters": {"R": 30, "N": 2.0, "M": 1.5, "Q": 10, "U": 2.0, "S": 3.0},
            "risk_management": {"max_positions": 3, "max_drawdown": 20}
        }

    def _generate_mock_klines(self) -> pd.DataFrame:
        """生成模拟K线数据"""
        print("🔧 生成模拟K线数据...")

        # 生成100根K线数据
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=100),
            end=datetime.now(),
            freq='1min'
        )

        # 模拟价格和成交量数据
        np.random.seed(42)  # 确保结果可重现
        base_price = 100000

        data = []
        current_price = base_price

        for timestamp in timestamps:
            # 模拟价格波动
            price_change = np.random.normal(0, 0.002)  # 0.2%的波动率
            open_price = current_price
            close_price = open_price * (1 + price_change)

            # 生成高开低收
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

            # 模拟成交量（带有偶尔的突破）
            base_volume = 1000
            volume_multiplier = 1.0

            # 随机产生成交量突破
            if random.random() < 0.2:  # 20%概率出现成交量突破
                volume_multiplier = random.uniform(2, 5)

            volume = base_volume * volume_multiplier * abs(price_change) * 100

            data.append([timestamp, open_price, high_price, low_price, close_price, volume])
            current_price = close_price

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.set_index('timestamp', inplace=True)

        # 计算技术指标
        df = self._calculate_indicators(df)

        print(f"✅ 生成了 {len(df)} 根模拟K线")
        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
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
        if len(self.positions) >= self.config["risk_management"]["max_positions"]:
            print(f"⚠️  已达最大持仓数量，跳过入场信号")
            return

        position_size = self.calculate_position_size()

        position = {
            'symbol': self.config["trading"]["symbol"],
            'entry_price': signal['price'],
            'quantity': position_size,
            'entry_time': signal['timestamp'],
            'highest_price': signal['price'],
            'stop_loss_price': signal['price'] * (1 - self.S / 100),
            'total_invested': signal['price'] * position_size
        }

        self.positions.append(position)

        print(f"🚨 入场信号执行成功!")
        print(f"   价格: ${signal['price']:,.2f}")
        print(f"   数量: {position_size:.6f}")
        print(f"   成交量比: {signal['volume_ratio']:.2f}")
        print(f"   价格变化: {signal['price_change_pct']:+.2f}%")
        print(f"   当前持仓数: {len(self.positions)}")

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
        for position in self.positions:
            # 更新最高价
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
                position['stop_loss_price'] = position['highest_price'] * (1 - self.S / 100)

            # 检查加仓信号
            if self.check_add_position_signal(position, current_price):
                self.execute_add_position(position)

            # 检查出场信号
            if self.check_exit_signal(position, current_price):
                self.execute_exit(position)

    def execute_add_position(self, position: Dict):
        """执行加仓"""
        if len(self.positions) >= self.config["risk_management"]["max_positions"]:
            return

        additional_size = self.calculate_position_size()
        additional_cost = self.current_price * additional_size

        # 更新持仓信息
        total_quantity = position['quantity'] + additional_size
        total_cost = position['total_invested'] + additional_cost

        position['quantity'] = total_quantity
        position['entry_price'] = total_cost / total_quantity
        position['total_invested'] = total_cost

        print(f"📈 加仓信号执行成功!")
        print(f"   加仓价格: ${self.current_price:,.2f}")
        print(f"   加仓数量: {additional_size:.6f}")
        print(f"   新持仓均价: ${position['entry_price']:,.2f}")
        print(f"   总数量: {position['quantity']:.6f}")

    def execute_exit(self, position: Dict):
        """执行出场"""
        exit_price = self.current_price
        pnl = (exit_price - position['entry_price']) * position['quantity']
        pnl_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)

        print(f"🔴 出场信号执行成功!")
        print(f"   出场价格: ${exit_price:,.2f}")
        print(f"   入场价格: ${position['entry_price']:,.2f}")
        print(f"   数量: {position['quantity']:.6f}")
        print(f"   盈亏: ${pnl:+.2f} ({pnl_pct:+.2f}%)")

        self.positions.remove(position)

    def print_status(self):
        """打印当前状态"""
        print("\n" + "=" * 60)
        print("📊 策略状态报告")
        print("=" * 60)

        print(f"当前价格: ${self.current_price:,.2f}")
        print(f"持仓数量: {len(self.positions)}")

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
                print(f"    入场价: ${pos['entry_price']:,.2f}")
                print(f"    当前价: ${self.current_price:,.2f}")
                print(f"    数量: {pos['quantity']:.6f}")
                print(f"    最高价: ${pos['highest_price']:,.2f}")
                print(f"    止损价: ${pos['stop_loss_price']:,.2f}")
                print(f"    盈亏: ${current_pnl:+.2f} ({pnl_pct:+.2f}%)")

            total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            print(f"\n💰 总盈亏: ${total_pnl:+.2f} ({total_pnl_pct:+.2f}%)")
            print(f"💼 总投入: ${total_invested:,.2f}")

        print("=" * 60)

    def run_simulation(self, duration_minutes: int = 30):
        """运行模拟"""
        print(f"🎯 开始模拟量价突破策略...")
        print(f"📊 策略参数: R={self.R}, N={self.N}倍, M={self.M}%, Q={self.Q}%, U={self.U}%, S={self.S}%")
        print(f"⏰ 模拟时长: {duration_minutes} 分钟")
        print("=" * 60)

        # 从第R根K线开始，确保有足够的历史数据计算平均成交量
        start_idx = self.R
        end_idx = min(start_idx + duration_minutes, len(self.klines_data))

        for i in range(start_idx, end_idx):
            kline = self.klines_data.iloc[i]
            self.current_price = float(kline['close'])

            print(f"\n⏰ 时间: {kline.name.strftime('%H:%M:%S')}")
            print(f"💰 价格: ${self.current_price:,.2f} ({kline['price_change_pct']:+.2f}%)")
            print(f"📊 成交量: {kline['volume']:,.0f} (比: {kline['volume_ratio']:.2f})")

            # 检查入场信号
            signal = self.check_entry_signal(kline.to_dict())
            if signal:
                self.execute_entry(signal)

            # 更新现有持仓
            self.update_positions(self.current_price)

            # 打印当前状态
            if i % 5 == 0 or signal:  # 每5分钟或有信号时打印状态
                self.print_status()

            time.sleep(0.5)  # 模拟时间流逝

        # 最终状态
        print(f"\n🏁 模拟完成!")
        self.print_status()


def main():
    """主函数"""
    print("🚀 量价突破顺势加仓策略演示")
    print("=" * 60)

    # 创建策略实例
    strategy = StrategyDemo("strategy_config.json")

    # 运行模拟
    strategy.run_simulation(duration_minutes=20)

    print("\n✅ 演示完成!")
    print("\n📝 策略说明:")
    print("1. 成交量突破：当成交量超过R分钟平均成交量的N倍时")
    print("2. 价格突破：同时价格涨幅超过M%时触发入场")
    print("3. 顺势加仓：价格相比入场价上涨U%时加仓")
    print("4. 移动止盈：价格从最高点回撤S%时出场")

    print("\n⚠️  注意事项:")
    print("- 这是演示程序，使用模拟数据")
    print("- 实盘交易前请充分回测和风险评估")
    print("- 数字货币交易存在高风险，请谨慎投资")


if __name__ == "__main__":
    main()