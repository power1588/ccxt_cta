import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import ccxt
import numpy as np
import pandas as pd


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    entry_time: datetime
    highest_price: float
    stop_loss_price: float
    total_invested: float
    current_pnl: float = 0.0


@dataclass
class Order:
    """订单信息"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    status: OrderStatus
    timestamp: datetime
    order_type: str = "market"


class VolumePriceBreakoutStrategy:
    """量价突破顺势加仓策略"""

    def __init__(self, config_path: str = "strategy_config.json"):
        """初始化策略"""
        self.config = self._load_config(config_path)

        # 先设置日志
        self._setup_logging()

        # 然后初始化交易所
        self.exchange = self._init_exchange()

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
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.klines_data: pd.DataFrame = pd.DataFrame()
        self.last_kline: Optional[Dict] = None
        self.current_price: float = 0.0
        self.running = False

        # 风险管理
        self.max_positions = self.config["risk_management"]["max_positions"]
        self.max_drawdown = self.config["risk_management"]["max_drawdown"]

        # 设置日志
        self._setup_logging()

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
            "trading": {"symbol": "BTC/USDT", "timeframe": "1m", "sandbox": True},
            "parameters": {"R": 30, "N": 2.0, "M": 1.5, "Q": 10, "U": 2.0, "S": 3.0},
            "risk_management": {"max_positions": 3, "max_drawdown": 20}
        }

    def _init_exchange(self) -> ccxt.Exchange:
        """初始化交易所"""
        try:
            # 首先尝试使用ccxt.pro
            try:
                import ccxt.pro
                exchange = ccxt.pro.binance({
                    'apiKey': self.config["trading"]["api_key"],
                    'secret': self.config["trading"]["secret"],
                    'sandbox': self.config["trading"]["sandbox"],
                    'enableRateLimit': True,
                })
                print("使用 ccxt.pro 初始化交易所")
                return exchange
            except ImportError:
                pass

            # 如果没有ccxt.pro，使用ccxt
            exchange = ccxt.binance({
                'apiKey': self.config["trading"]["api_key"],
                'secret': self.config["trading"]["secret"],
                'sandbox': self.config["trading"]["sandbox"],
                'enableRateLimit': True,
            })
            print("使用 ccxt 初始化交易所")
            return exchange

        except Exception as e:
            print(f"初始化交易所失败: {e}")
            raise

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config["logging"]
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger("VolumePriceBreakout")

        if log_config["log_to_file"]:
            file_handler = logging.FileHandler(log_config["log_file"])
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)

    async def initialize_data(self):
        """初始化历史数据"""
        try:
            self.logger.info(f"正在获取 {self.symbol} 历史K线数据...")

            # 获取最近100根K线数据
            ohlcv = await self.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                limit=100
            )

            # 转换为DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # 计算技术指标
            df = self._calculate_indicators(df)

            self.klines_data = df
            self.last_kline = df.iloc[-1].to_dict()
            self.current_price = float(self.last_kline['close'])

            self.logger.info(f"历史数据初始化完成，共 {len(df)} 根K线")
            self.logger.info(f"当前价格: ${self.current_price:,.2f}")

        except Exception as e:
            self.logger.error(f"初始化历史数据失败: {e}")
            raise

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

    def check_entry_signal(self) -> Optional[Dict]:
        """检查入场信号"""
        if len(self.klines_data) < self.R + 1:
            return None

        # 获取最新K线
        latest = self.klines_data.iloc[-1]
        previous = self.klines_data.iloc[-2]

        # 入场条件检查
        volume_breakout = float(latest['volume_ratio']) >= self.N
        price_breakout = float(latest['price_change_pct']) >= self.M

        if volume_breakout and price_breakout:
            return {
                'signal': 'ENTRY',
                'price': float(latest['close']),
                'volume': float(latest['volume']),
                'volume_ratio': float(latest['volume_ratio']),
                'price_change': float(latest['price_change_pct']),
                'timestamp': latest.name
            }

        return None

    def check_add_position_signal(self, position: Position) -> bool:
        """检查加仓信号"""
        if position.side != OrderSide.BUY:
            return False

        # 价格相比入场价上涨了U%
        price_increase_pct = ((self.current_price - position.entry_price) /
                             position.entry_price * 100)

        return price_increase_pct >= self.U

    def check_exit_signal(self, position: Position) -> bool:
        """检查出场信号"""
        if position.side != OrderSide.BUY:
            return False

        # 价格相比最高价回撤了S%
        drawdown_pct = ((position.highest_price - self.current_price) /
                       position.highest_price * 100)

        return drawdown_pct >= self.S

    async def place_order(self, side: OrderSide, quantity: float, price: float = None) -> Optional[Order]:
        """下单"""
        try:
            order_type = 'market' if price is None else 'limit'

            if side == OrderSide.BUY:
                if price is None:
                    order = await self.exchange.create_market_buy_order(self.symbol, quantity)
                else:
                    order = await self.exchange.create_limit_buy_order(self.symbol, quantity, price)
            else:
                if price is None:
                    order = await self.exchange.create_market_sell_order(self.symbol, quantity)
                else:
                    order = await self.exchange.create_limit_sell_order(self.symbol, quantity, price)

            new_order = Order(
                order_id=order['id'],
                symbol=self.symbol,
                side=side,
                quantity=quantity,
                price=price or order['price'] or order.get('average', 0),
                status=OrderStatus.FILLED if order['filled'] else OrderStatus.PENDING,
                timestamp=datetime.now(),
                order_type=order_type
            )

            self.orders.append(new_order)
            self.logger.info(f"订单创建成功: {side.value} {quantity:.6f} @ ${new_order.price:.2f}")

            return new_order

        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return None

    def calculate_position_size(self) -> float:
        """计算仓位大小"""
        try:
            # 获取账户余额
            balance = self.exchange.fetch_balance()
            usdt_balance = balance['total'].get('USDT', 0)

            # 计算投资金额
            invest_amount = usdt_balance * (self.Q / 100)

            # 计算可买入数量
            position_size = invest_amount / self.current_price

            # 应用风险限制
            min_size = self.config["risk_management"]["min_order_size"]
            max_size = self.config["risk_management"]["max_order_size"]

            position_size = max(min_size, min(position_size, max_size))

            return position_size

        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return self.config["risk_management"]["min_order_size"]

    async def execute_entry(self, signal: Dict):
        """执行入场"""
        if len(self.positions) >= self.max_positions:
            self.logger.warning(f"已达最大持仓数量 {self.max_positions}，跳过入场信号")
            return

        position_size = self.calculate_position_size()

        order = await self.place_order(OrderSide.BUY, position_size)

        if order and order.status == OrderStatus.FILLED:
            # 创建新持仓
            position = Position(
                symbol=self.symbol,
                side=OrderSide.BUY,
                entry_price=order.price,
                quantity=order.quantity,
                entry_time=datetime.now(),
                highest_price=order.price,
                stop_loss_price=order.price * (1 - self.S / 100),
                total_invested=order.price * order.quantity
            )

            self.positions.append(position)

            self.logger.info(f"入场成功: {self.symbol} @ ${order.price:.2f}, 数量: {order.quantity:.6f}")
            self.logger.info(f"持仓数量: {len(self.positions)}")

    async def execute_add_position(self, position: Position):
        """执行加仓"""
        if len(self.positions) >= self.max_positions:
            return

        position_size = self.calculate_position_size()

        order = await self.place_order(OrderSide.BUY, position_size)

        if order and order.status == OrderStatus.FILLED:
            # 更新持仓信息
            total_quantity = position.quantity + order.quantity
            total_cost = position.total_invested + (order.price * order.quantity)

            position.quantity = total_quantity
            position.entry_price = total_cost / total_quantity
            position.total_invested = total_cost
            position.highest_price = max(position.highest_price, order.price)
            position.stop_loss_price = position.highest_price * (1 - self.S / 100)

            self.logger.info(f"加仓成功: {self.symbol} @ ${order.price:.2f}, 数量: {order.quantity:.6f}")
            self.logger.info(f"新持仓均价: ${position.entry_price:.2f}, 总数量: {position.quantity:.6f}")

    async def execute_exit(self, position: Position):
        """执行出场"""
        order = await self.place_order(OrderSide.SELL, position.quantity)

        if order and order.status == OrderStatus.FILLED:
            # 计算盈亏
            pnl = (order.price - position.entry_price) * position.quantity
            pnl_pct = ((order.price - position.entry_price) / position.entry_price * 100)

            self.logger.info(f"出场成功: {self.symbol} @ ${order.price:.2f}")
            self.logger.info(f"盈亏: ${pnl:.2f} ({pnl_pct:+.2f}%)")

            self.positions.remove(position)
            self.logger.info(f"剩余持仓数量: {len(self.positions)}")

    async def update_positions(self):
        """更新持仓状态"""
        for position in self.positions:
            # 更新最高价
            if self.current_price > position.highest_price:
                position.highest_price = self.current_price
                position.stop_loss_price = position.highest_price * (1 - self.S / 100)

            # 计算当前盈亏
            position.current_pnl = (self.current_price - position.entry_price) * position.quantity

            # 检查加仓信号
            if self.check_add_position_signal(position):
                self.logger.info(f"触发加仓信号: {self.symbol} @ ${self.current_price:.2f}")
                await self.execute_add_position(position)

            # 检查出场信号
            if self.check_exit_signal(position):
                self.logger.info(f"触发出场信号: {self.symbol} @ ${self.current_price:.2f}")
                await self.execute_exit(position)

    async def watch_realtime_data(self):
        """监控实时数据"""
        self.logger.info("开始监控实时数据...")

        try:
            # 使用ccxt.pro的WebSocket功能
            if hasattr(self.exchange, 'watch_ticker'):
                while self.running:
                    try:
                        # 获取实时价格
                        ticker = await self.exchange.watch_ticker(self.symbol)
                        self.current_price = float(ticker['last'])

                        # 检查入场信号
                        signal = self.check_entry_signal()
                        if signal:
                            self.logger.info(f"触发入场信号: {signal}")
                            await self.execute_entry(signal)

                        # 更新持仓
                        await self.update_positions()

                        # 短暂延迟避免过于频繁
                        await asyncio.sleep(1)

                    except Exception as e:
                        self.logger.error(f"实时数据处理错误: {e}")
                        await asyncio.sleep(5)

            # 如果没有WebSocket，使用轮询
            else:
                while self.running:
                    try:
                        ticker = self.exchange.fetch_ticker(self.symbol)
                        self.current_price = float(ticker['last'])

                        signal = self.check_entry_signal()
                        if signal:
                            self.logger.info(f"触发入场信号: {signal}")
                            await self.execute_entry(signal)

                        await self.update_positions()

                        await asyncio.sleep(5)  # 5秒轮询一次

                    except Exception as e:
                        self.logger.error(f"轮询数据错误: {e}")
                        await asyncio.sleep(10)

        except Exception as e:
            self.logger.error(f"实时数据监控失败: {e}")

    async def run(self):
        """运行策略"""
        try:
            self.logger.info("启动量价突破顺势加仓策略")
            self.logger.info(f"交易对: {self.symbol}")
            self.logger.info(f"策略参数: R={self.R}, N={self.N}, M={self.M}%, Q={self.Q}%, U={self.U}%, S={self.S}%")

            self.running = True

            # 初始化数据
            await self.initialize_data()

            # 启动实时监控
            await self.watch_realtime_data()

        except KeyboardInterrupt:
            self.logger.info("用户停止策略")
        except Exception as e:
            self.logger.error(f"策略运行异常: {e}")
        finally:
            self.running = False
            if hasattr(self.exchange, 'close'):
                await self.exchange.close()

            self.logger.info("策略已停止")

    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        total_pnl = sum(pos.current_pnl for pos in self.positions)
        total_invested = sum(pos.total_invested for pos in self.positions)

        return {
            "positions_count": len(self.positions),
            "current_price": self.current_price,
            "total_pnl": total_pnl,
            "total_invested": total_invested,
            "pnl_percentage": (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "entry_price": pos.entry_price,
                    "quantity": pos.quantity,
                    "current_price": self.current_price,
                    "pnl": pos.current_pnl,
                    "highest_price": pos.highest_price,
                    "stop_loss_price": pos.stop_loss_price
                }
                for pos in self.positions
            ]
        }


if __name__ == "__main__":
    # 示例使用
    strategy = VolumePriceBreakoutStrategy("strategy_config.json")

    # 运行策略
    asyncio.run(strategy.run())