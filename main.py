import ccxt
import asyncio
import json
from typing import Dict, Any


class BinanceSpotFuturesDemo:
    def __init__(self):
        """初始化币安交易所实例"""
        # 现货交易实例
        self.spot = ccxt.binance({
            'apiKey': '',  # 请填入您的API密钥
            'secret': '',  # 请填入您的API密钥
            'sandbox': True,  # 使用测试环境
            'enableRateLimit': True,
        })

        # 期货交易实例
        self.futures = ccxt.binanceusdm({  # 使用币安USDM永续合约
            'apiKey': '',  # 请填入您的API密钥
            'secret': '',  # 请填入您的API密钥
            'sandbox': False,  # 可以设置为True使用测试网络
            'enableRateLimit': True,
        })

    def print_market_info(self, exchange: ccxt.Exchange, exchange_name: str):
        """打印市场信息"""
        try:
            print(f"\n=== {exchange_name} 市场信息 ===")

            # 获取交易所信息
            markets = exchange.load_markets()
            print(f"总交易对数量: {len(markets)}")

            # 获取一些热门交易对
            popular_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            for pair in popular_pairs:
                if pair in markets:
                    ticker = exchange.fetch_ticker(pair)
                    print(f"{pair}:")
                    print(f"  最新价格: ${ticker['last']:,.2f}")
                    print(f"  24小时变化: {ticker['percentage']:.2f}%")
                    print(f"  24小时成交量: {ticker['baseVolume']:,.2f}")
        except Exception as e:
            print(f"获取{exchange_name}市场信息时出错: {e}")

    def demo_spot_trading(self):
        """演示现货交易功能"""
        try:
            print(f"\n=== 现货交易演示 ===")

            # 获取账户余额
            if self.spot.apiKey and self.spot.secret:
                balance = self.spot.fetch_balance()
                print("账户余额:")
                for currency, amount in balance['total'].items():
                    if amount > 0:
                        print(f"  {currency}: {amount}")
            else:
                print("未配置API密钥，跳过账户余额查询")

            # 获取订单簿
            orderbook = self.spot.fetch_order_book('BTC/USDT', limit=5)
            print(f"\nBTC/USDT 订单簿 (前5档):")
            print("买盘:")
            for bid in orderbook['bids']:
                print(f"  ${bid[0]:,.2f}: {bid[1]:.4f} BTC")
            print("卖盘:")
            for ask in orderbook['asks']:
                print(f"  ${ask[0]:,.2f}: {ask[1]:.4f} BTC")

        except Exception as e:
            print(f"现货交易演示出错: {e}")

    def demo_futures_trading(self):
        """演示期货交易功能"""
        try:
            print(f"\n=== 期货交易演示 ===")

            # 获取期货账户余额
            if self.futures.apiKey and self.futures.secret:
                balance = self.futures.fetch_balance()
                print("期货账户余额:")
                for currency, amount in balance['total'].items():
                    if amount > 0:
                        print(f"  {currency}: {amount}")
            else:
                print("未配置API密钥，跳过期货账户余额查询")

            # 获取永续合约市场信息
            contracts = self.futures.load_markets()
            btc_contract = 'BTC/USDT'

            if btc_contract in contracts:
                # 获取合约信息
                ticker = self.futures.fetch_ticker(btc_contract)
                print(f"\nBTC永续合约信息:")
                print(f"  标记价格: ${ticker['markPrice']:,.2f}")
                print(f"  最新价格: ${ticker['last']:,.2f}")
                print(f"  24小时变化: {ticker['percentage']:.2f}%")
                print(f"  24小时成交量: {ticker['baseVolume']:,.2f}")

                # 获取资金费率
                funding_rate = self.futures.fetch_funding_rate(btc_contract)
                if funding_rate:
                    print(f"  资金费率: {funding_rate['fundingRate'] * 100:.4f}%")
                    print(f"  下次资金时间: {funding_rate['fundingTimestamp']}")

        except Exception as e:
            print(f"期货交易演示出错: {e}")

    def demo_websocket_streams(self):
        """演示WebSocket数据流（需要ccxt.pro）"""
        print(f"\n=== WebSocket数据流演示 ===")
        print("要使用WebSocket功能，需要安装ccxt.pro库")
        print("运行命令: uv add ccxt.pro")
        print("\nWebSocket功能包括:")
        print("- 实时价格订阅")
        print("- 实时订单簿更新")
        print("- 实时成交数据")
        print("- 实时账户更新")

    def run_demo(self):
        """运行完整演示"""
        print("=== 币安现货和期货交易演示 ===")
        print("注意: 当前使用测试环境 (sandbox=True)")

        # 市场信息
        self.print_market_info(self.spot, "币安现货")
        self.print_market_info(self.futures, "币安期货")

        # 交易演示
        self.demo_spot_trading()
        self.demo_futures_trading()

        # WebSocket演示
        self.demo_websocket_streams()

        print(f"\n=== 演示完成 ===")
        print("配置说明:")
        print("1. 设置真实的API密钥来访问账户功能")
        print("2. 将sandbox设置为False来使用生产环境")
        print("3. 安装ccxt.pro来使用WebSocket功能")
        print("4. 根据需要调整交易参数和风险设置")


def main():
    """主函数"""
    demo = BinanceSpotFuturesDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()
