import asyncio
import time
from typing import Dict, Any, Optional
import json


class BinanceSpotFuturesWebSocketDemo:
    def __init__(self):
        """初始化币安WebSocket演示"""
        try:
            import ccxt.pro
            self.ccxt = ccxt.pro
            print("✅ ccxt.pro模块加载成功")
        except ImportError:
            print("❌ 需要安装ccxt.pro: pip install ccxt-pro")
            return

        # 现货WebSocket实例
        self.spot = self.ccxt.binance({
            'apiKey': '',  # 填入您的API密钥
            'secret': '',  # 填入您的Secret密钥
            'sandbox': False,  # 使用生产环境
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })

        # 期货WebSocket实例
        self.futures = self.ccxt.binance({
            'apiKey': '',  # 填入您的API密钥
            'secret': '',  # 填入您的Secret密钥
            'sandbox': False,  # 使用生产环境
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 期货模式
            }
        })

        self.running = False
        self.symbol = 'BTC/USDT'

    async def watch_ticker_demo(self, exchange_name: str, exchange):
        """演示实时价格监控"""
        print(f"\n=== {exchange_name} 实时价格监控 ===")
        try:
            while self.running:
                try:
                    ticker = await exchange.watch_ticker(self.symbol)
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"[{timestamp}] {exchange_name} {ticker['symbol']}: "
                          f"${ticker['last']:,.2f} ({ticker['percentage']:+.2f}%)")
                    await asyncio.sleep(2)  # 每2秒更新一次
                except Exception as e:
                    print(f"{exchange_name} 价格监控错误: {e}")
                    await asyncio.sleep(5)  # 错误时等待5秒
        except Exception as e:
            print(f"{exchange_name} 价格监控初始化错误: {e}")

    async def watch_orderbook_demo(self, exchange_name: str, exchange):
        """演示实时订单簿监控"""
        print(f"\n=== {exchange_name} 实时订单簿监控 ===")
        try:
            while self.running:
                try:
                    orderbook = await exchange.watch_order_book(self.symbol, limit=5)
                    timestamp = time.strftime('%H:%M:%S')

                    print(f"[{timestamp}] {exchange_name} 订单簿:")

                    # 显示最佳买盘
                    if orderbook['bids']:
                        best_bid = orderbook['bids'][0]
                        print(f"  最佳买盘: ${best_bid[0]:,.2f} ({best_bid[1]:.4f})")

                    # 显示最佳卖盘
                    if orderbook['asks']:
                        best_ask = orderbook['asks'][0]
                        print(f"  最佳卖盘: ${best_ask[0]:,.2f} ({best_ask[1]:.4f})")

                    # 计算价差
                    if orderbook['bids'] and orderbook['asks']:
                        spread = orderbook['asks'][0][0] - orderbook['bids'][0][0]
                        spread_percent = (spread / orderbook['bids'][0][0]) * 100
                        print(f"  价差: ${spread:,.2f} ({spread_percent:.4f}%)")

                    await asyncio.sleep(3)  # 每3秒更新一次
                except Exception as e:
                    print(f"{exchange_name} 订单簿监控错误: {e}")
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"{exchange_name} 订单簿监控初始化错误: {e}")

    async def watch_trades_demo(self, exchange_name: str, exchange):
        """演示实时成交监控"""
        print(f"\n=== {exchange_name} 实时成交监控 ===")
        try:
            while self.running:
                try:
                    trades = await exchange.watch_trades(self.symbol, limit=5)
                    timestamp = time.strftime('%H:%M:%S')

                    if trades:
                        print(f"[{timestamp}] {exchange_name} 最新成交:")
                        for trade in trades[-3:]:  # 显示最近3笔成交
                            side_symbol = "🟢 买入" if trade['side'] == 'buy' else "🔴 卖出"
                            print(f"  {side_symbol}: ${trade['price']:,.2f} x {trade['amount']:.4f}")

                    await asyncio.sleep(4)  # 每4秒更新一次
                except Exception as e:
                    print(f"{exchange_name} 成交监控错误: {e}")
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"{exchange_name} 成交监控初始化错误: {e}")

    async def watch_balance_demo(self, exchange_name: str, exchange):
        """演示账户余额监控（需要API密钥）"""
        if not exchange.apiKey or not exchange.secret:
            print(f"\n⚠️  {exchange_name} 账户余额监控需要配置API密钥")
            return

        print(f"\n=== {exchange_name} 账户余额监控 ===")
        try:
            while self.running:
                try:
                    balance = await exchange.watch_balance()
                    timestamp = time.strftime('%H:%M:%S')

                    print(f"[{timestamp}] {exchange_name} 账户余额:")
                    for currency, amount in balance['total'].items():
                        if amount > 0:
                            print(f"  {currency}: {amount}")

                    await asyncio.sleep(10)  # 每10秒更新一次
                except Exception as e:
                    print(f"{exchange_name} 余额监控错误: {e}")
                    await asyncio.sleep(10)
        except Exception as e:
            print(f"{exchange_name} 余额监控初始化错误: {e}")

    async def futures_funding_rate_demo(self):
        """演示期货资金费率监控"""
        print(f"\n=== 期货资金费率监控 ===")
        try:
            while self.running:
                try:
                    # 获取资金费率
                    funding_rate = await self.futures.watch_funding_rate(self.symbol)
                    if funding_rate:
                        timestamp = time.strftime('%H:%M:%S')
                        rate = funding_rate['fundingRate'] * 100
                        next_funding_time = funding_rate['fundingTimestamp']
                        next_funding_str = time.strftime('%H:%M:%S', time.localtime(next_funding_time / 1000))

                        print(f"[{timestamp}] {self.symbol} 资金费率: {rate:+.4f}%")
                        print(f"  下次结算时间: {next_funding_str}")

                    await asyncio.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    print(f"资金费率监控错误: {e}")
                    await asyncio.sleep(15)
        except Exception as e:
            print(f"资金费率监控初始化错误: {e}")

    async def arbitrage_monitor(self):
        """演示现货期货套利机会监控"""
        print(f"\n=== 现货期货套利监控 ===")
        try:
            while self.running:
                try:
                    # 同时获取现货和期货价格
                    spot_ticker = await self.spot.watch_ticker(self.symbol)
                    futures_ticker = await self.futures.watch_ticker(self.symbol)

                    spot_price = spot_ticker['last']
                    futures_price = futures_ticker['last']

                    # 计算价差
                    spread = futures_price - spot_price
                    spread_percent = (spread / spot_price) * 100

                    timestamp = time.strftime('%H:%M:%S')

                    if abs(spread_percent) > 0.1:  # 价差超过0.1%时显示
                        print(f"[{timestamp}] 套利机会:")
                        print(f"  现货价格: ${spot_price:,.2f}")
                        print(f"  期货价格: ${futures_price:,.2f}")
                        print(f"  价差: ${spread:,.2f} ({spread_percent:+.4f}%)")

                        if spread_percent > 0:
                            print(f"  建议: 期货溢价 {spread_percent:.4f}% - 可考虑正向套利")
                        else:
                            print(f"  建议: 期货贴水 {abs(spread_percent):.4f}% - 可考虑反向套利")

                    await asyncio.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    print(f"套利监控错误: {e}")
                    await asyncio.sleep(10)
        except Exception as e:
            print(f"套利监控初始化错误: {e}")

    async def run_demo(self):
        """运行完整的WebSocket演示"""
        print("=== 币安现货和期货WebSocket交易演示 ===")
        print("支持的功能:")
        print("- 实时价格监控")
        print("- 实时订单簿更新")
        print("- 实时成交数据")
        print("- 账户余额监控（需要API密钥）")
        print("- 期货资金费率监控")
        print("- 现货期货套利机会监控")

        self.running = True

        try:
            # 创建并发任务
            tasks = [
                asyncio.create_task(self.watch_ticker_demo("现货", self.spot)),
                asyncio.create_task(self.watch_ticker_demo("期货", self.futures)),
                asyncio.create_task(self.watch_orderbook_demo("现货", self.spot)),
                asyncio.create_task(self.watch_trades_demo("现货", self.spot)),
                asyncio.create_task(self.futures_funding_rate_demo()),
                asyncio.create_task(self.arbitrage_monitor()),
            ]

            # 如果配置了API密钥，启用余额监控
            if self.spot.apiKey and self.spot.secret:
                tasks.append(asyncio.create_task(self.watch_balance_demo("现货", self.spot)))

            if self.futures.apiKey and self.futures.secret:
                tasks.append(asyncio.create_task(self.watch_balance_demo("期货", self.futures)))

            print(f"\n开始监控 {self.symbol}...")
            print("按 Ctrl+C 停止演示\n")

            # 等待所有任务完成（或被中断）
            await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            print(f"\n用户中断，停止演示...")
        except Exception as e:
            print(f"演示运行错误: {e}")
        finally:
            self.running = False

            # 关闭所有连接
            await self.spot.close()
            await self.futures.close()
            print("所有WebSocket连接已关闭")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.spot.close()
        await self.futures.close()


async def main():
    """主函数"""
    async with BinanceSpotFuturesWebSocketDemo() as demo:
        await demo.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止")