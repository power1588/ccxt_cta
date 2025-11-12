import ccxt
import asyncio
import time
import threading
from typing import Dict, Any


class BinanceSimpleDemo:
    def __init__(self):
        """初始化币安演示（使用轮询模拟实时数据）"""
        # 现货实例
        self.spot = ccxt.binance({
            'apiKey': '',  # 填入您的API密钥
            'secret': '',  # 填入您的Secret密钥
            'sandbox': False,
            'enableRateLimit': True,
        })

        # 期货实例
        self.futures = ccxt.binanceusdm({
            'apiKey': '',  # 填入您的API密钥
            'secret': '',  # 填入您的Secret密钥
            'sandbox': False,
            'enableRateLimit': True,
        })

        self.running = False
        self.symbol = 'BTC/USDT'

    def get_market_overview(self):
        """获取市场概览"""
        try:
            print("=== 市场概览 ===")

            # 现货市场
            spot_ticker = self.spot.fetch_ticker(self.symbol)
            print(f"现货 {self.symbol}:")
            print(f"  最新价格: ${spot_ticker['last']:,.2f}")
            print(f"  24小时最高: ${spot_ticker['high']:,.2f}")
            print(f"  24小时最低: ${spot_ticker['low']:,.2f}")
            print(f"  24小时变化: {spot_ticker['percentage']:+.2f}%")
            print(f"  24小时成交量: {spot_ticker['baseVolume']:,.2f} BTC")

            # 期货市场
            futures_ticker = self.futures.fetch_ticker(self.symbol)
            print(f"\n期货 {self.symbol}:")
            print(f"  最新价格: ${futures_ticker['last']:,.2f}")
            print(f"  标记价格: ${futures_ticker.get('markPrice', 0):,.2f}")
            print(f"  24小时变化: {futures_ticker['percentage']:+.2f}%")
            print(f"  24小时成交量: {futures_ticker['baseVolume']:,.2f} BTC")

            # 套利机会分析
            spot_price = spot_ticker['last']
            futures_price = futures_ticker['last']
            spread = futures_price - spot_price
            spread_percent = (spread / spot_price) * 100

            print(f"\n套利分析:")
            print(f"  价差: ${spread:,.2f} ({spread_percent:+.4f}%)")

            if abs(spread_percent) > 0.1:
                if spread_percent > 0:
                    print(f"  状态: 期货溢价 {spread_percent:.4f}% - 可考虑正向套利")
                else:
                    print(f"  状态: 期货贴水 {abs(spread_percent):.4f}% - 可考虑反向套利")
            else:
                print(f"  状态: 价差较小，暂无明显套利机会")

        except Exception as e:
            print(f"获取市场概览错误: {e}")

    def get_order_book_analysis(self):
        """获取订单簿分析"""
        try:
            print(f"\n=== 订单簿分析 ===")

            # 现货订单簿
            spot_ob = self.spot.fetch_order_book(self.symbol, limit=10)
            print(f"现货订单簿 ({self.symbol}):")

            # 计算买卖盘压力
            spot_bid_volume = sum(bid[1] for bid in spot_ob['bids'][:5])
            spot_ask_volume = sum(ask[1] for ask in spot_ob['asks'][:5])

            print(f"  买盘前5档总量: {spot_bid_volume:.4f} BTC")
            print(f"  卖盘前5档总量: {spot_ask_volume:.4f} BTC")
            print(f"  买卖盘比: {spot_bid_volume/spot_ask_volume:.2f}")

            # 期货订单簿
            futures_ob = self.futures.fetch_order_book(self.symbol, limit=10)
            print(f"\n期货订单簿 ({self.symbol}):")

            # 计算买卖盘压力
            futures_bid_volume = sum(bid[1] for bid in futures_ob['bids'][:5])
            futures_ask_volume = sum(ask[1] for ask in futures_ob['asks'][:5])

            print(f"  买盘前5档总量: {futures_bid_volume:.4f} BTC")
            print(f"  卖盘前5档总量: {futures_ask_volume:.4f} BTC")
            print(f"  买卖盘比: {futures_bid_volume/futures_ask_volume:.2f}")

        except Exception as e:
            print(f"获取订单簿分析错误: {e}")

    def get_funding_rate_info(self):
        """获取资金费率信息"""
        try:
            print(f"\n=== 资金费率信息 ===")

            funding_rate = self.futures.fetch_funding_rate(self.symbol)
            if funding_rate:
                rate = funding_rate['fundingRate'] * 100
                timestamp = funding_rate['fundingTimestamp']
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000))

                print(f"{self.symbol} 资金费率: {rate:+.4f}%")
                print(f"下次结算时间: {time_str}")

                if rate > 0:
                    print(f"说明: 多头支付给空头")
                elif rate < 0:
                    print(f"说明: 空头支付给多头")
                else:
                    print(f"说明: 无资金费率")
            else:
                print(f"无法获取 {self.symbol} 的资金费率信息")

        except Exception as e:
            print(f"获取资金费率信息错误: {e}")

    def get_account_info(self):
        """获取账户信息（需要API密钥）"""
        try:
            print(f"\n=== 账户信息 ===")

            if not self.spot.apiKey or not self.spot.secret:
                print("未配置API密钥，跳过账户信息查询")
                print("如需查看账户信息，请在代码中设置apiKey和secret")
                return

            # 现货账户
            spot_balance = self.spot.fetch_balance()
            print("现货账户余额:")
            for currency, amount in spot_balance['total'].items():
                if amount > 0:
                    print(f"  {currency}: {amount}")

            # 期货账户
            futures_balance = self.futures.fetch_balance()
            print(f"\n期货账户余额:")
            for currency, amount in futures_balance['total'].items():
                if amount > 0:
                    print(f"  {currency}: {amount}")

            # 获取持仓信息
            positions = self.futures.fetch_positions()
            active_positions = [pos for pos in positions if float(pos['contracts']) != 0]

            if active_positions:
                print(f"\n当前持仓:")
                for pos in active_positions:
                    side = "多头" if pos['side'] == 'long' else "空头"
                    print(f"  {pos['symbol']}: {side} {pos['contracts']} {pos['contractType']}")
            else:
                print(f"\n当前无持仓")

        except Exception as e:
            print(f"获取账户信息错误: {e}")

    def simulate_real_time_updates(self, duration=30):
        """模拟实时数据更新"""
        print(f"\n=== 模拟实时数据更新 (运行{duration}秒) ===")
        print("每3秒更新一次价格信息...")

        start_time = time.time()
        update_count = 0

        try:
            while time.time() - start_time < duration:
                try:
                    # 获取最新价格
                    spot_ticker = self.spot.fetch_ticker(self.symbol)
                    futures_ticker = self.futures.fetch_ticker(self.symbol)

                    timestamp = time.strftime('%H:%M:%S')
                    spot_price = spot_ticker['last']
                    futures_price = futures_ticker['last']
                    spread = futures_price - spot_price

                    update_count += 1
                    print(f"[{timestamp}] 第{update_count}次更新:")
                    print(f"  现货: ${spot_price:,.2f} ({spot_ticker['percentage']:+.2f}%)")
                    print(f"  期货: ${futures_price:,.2f} ({futures_ticker['percentage']:+.2f}%)")
                    print(f"  价差: ${spread:,.2f}")

                    time.sleep(3)  # 每3秒更新一次

                except KeyboardInterrupt:
                    print(f"\n用户中断")
                    break
                except Exception as e:
                    print(f"更新错误: {e}")
                    time.sleep(5)

        except Exception as e:
            print(f"实时更新错误: {e}")

        print(f"\n模拟实时更新完成，共更新{update_count}次")

    def run_comprehensive_demo(self):
        """运行综合演示"""
        print("=== 币安现货和期货综合演示 ===")
        print("监控交易对:", self.symbol)
        print("注意: 这是基于轮询的演示，要获得真正的实时数据需要ccxt.pro")

        try:
            # 1. 市场概览
            self.get_market_overview()

            # 2. 订单簿分析
            self.get_order_book_analysis()

            # 3. 资金费率信息
            self.get_funding_rate_info()

            # 4. 账户信息
            self.get_account_info()

            # 5. 模拟实时更新
            self.simulate_real_time_updates(30)  # 运行30秒

        except KeyboardInterrupt:
            print(f"\n演示被用户中断")
        except Exception as e:
            print(f"演示运行错误: {e}")

        print(f"\n=== 演示完成 ===")
        print("要获得WebSocket实时数据，请:")
        print("1. 安装 ccxt-pro: pip install ccxt-pro")
        print("2. 使用 ccxt.pro.binance() 替代 ccxt.binance()")


def main():
    """主函数"""
    demo = BinanceSimpleDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main()