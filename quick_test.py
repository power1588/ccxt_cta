#!/usr/bin/env python3
"""
快速测试币安现货连接
"""

import ccxt
import asyncio


def test_binance_spot():
    """测试币安现货连接"""
    print("🚀 测试币安现货连接...")

    try:
        # 不使用沙盒模式，直接连接主网获取公开数据
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # 明确指定现货
            }
        })

        print("📊 获取交易所信息...")
        markets = exchange.load_markets()
        print(f"✅ 成功获取 {len(markets)} 个交易对")

        print("💰 获取BTC/USDT价格...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT: ${ticker['last']:,.2f}")
        print(f"   24h变化: {ticker['percentage']:+.2f}%")
        print(f"   24h成交量: {ticker['baseVolume']:,.2f} BTC")

        print("📈 获取K线数据...")
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1m', limit=5)
        print(f"✅ 获取了 {len(ohlcv)} 根1分钟K线")

        print("📊 获取订单簿...")
        orderbook = exchange.fetch_order_book('BTC/USDT', limit=3)
        print(f"✅ 买盘最佳: ${orderbook['bids'][0][0]:,.2f}")
        print(f"✅ 卖盘最佳: ${orderbook['asks'][0][0]:,.2f}")

        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


async def test_strategy_init():
    """测试策略初始化"""
    print("\n🎯 测试策略初始化...")

    try:
        from volume_price_breakout_strategy import VolumePriceBreakoutStrategy

        strategy = VolumePriceBreakoutStrategy("strategy_config.json")
        print("✅ 策略初始化成功")

        # 测试数据获取
        await strategy.initialize_data()
        print("✅ 历史数据获取成功")
        print(f"   当前价格: ${strategy.current_price:,.2f}")
        print(f"   K线数量: {len(strategy.klines_data)}")

        # 清理
        if hasattr(strategy.exchange, 'close'):
            await strategy.exchange.close()

        return True

    except Exception as e:
        print(f"❌ 策略初始化失败: {e}")
        return False


def main():
    """主函数"""
    print("🧪 币安现货快速测试")
    print("=" * 40)

    # 测试基本连接
    basic_ok = test_binance_spot()

    # 测试策略
    if basic_ok:
        strategy_ok = asyncio.run(test_strategy_init())
    else:
        strategy_ok = False

    # 总结
    print("\n" + "=" * 40)
    print("📊 测试结果:")
    print(f"基本连接: {'✅' if basic_ok else '❌'}")
    print(f"策略测试: {'✅' if strategy_ok else '❌'}")

    if basic_ok:
        print("\n🎉 网络连接正常！")
        print("💡 运行演示: uv run strategy_demo.py")
        print("💡 运行测试: uv run test_strategy.py")
    else:
        print("\n⚠️  网络连接问题")


if __name__ == "__main__":
    main()