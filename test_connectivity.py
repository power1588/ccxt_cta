#!/usr/bin/env python3
"""
网络连接测试脚本
"""

import ccxt
import asyncio
import sys
import time


def test_basic_connectivity():
    """测试基本网络连接"""
    print("🌐 测试基本网络连接...")

    try:
        exchange = ccxt.binance({
            'sandbox': True,  # 使用测试网
            'enableRateLimit': True,
        })

        # 测试获取交易所信息
        print("📊 测试获取交易所信息...")
        markets = exchange.load_markets()
        print(f"✅ 成功获取 {len(markets)} 个交易对")

        # 测试获取BTC/USDT价格
        print("💰 测试获取BTC/USDT价格...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT 当前价格: ${ticker['last']:,.2f}")

        # 测试获取K线数据
        print("📈 测试获取K线数据...")
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1m', limit=5)
        print(f"✅ 成功获取 {len(ohlcv)} 根K线数据")

        # 测试获取订单簿
        print("📊 测试获取订单簿...")
        orderbook = exchange.fetch_order_book('BTC/USDT', limit=5)
        print(f"✅ 订单簿买盘: {len(orderbook['bids'])}档，卖盘: {len(orderbook['asks'])}档")

        return True

    except Exception as e:
        print(f"❌ 基本连接测试失败: {e}")
        return False


def test_sandbox_connectivity():
    """测试沙盒环境连接"""
    print("\n🧪 测试币安测试网连接...")

    try:
        exchange = ccxt.binance({
            'sandbox': True,
            'enableRateLimit': True,
            'apiKey': '',  # 测试网可以使用空API密钥获取公开数据
            'secret': '',
        })

        # 测试获取服务器时间
        print("⏰ 测试获取服务器时间...")
        server_time = exchange.fetch_time()
        local_time = int(time.time() * 1000)
        time_diff = abs(server_time - local_time)
        print(f"✅ 服务器时间差: {time_diff}ms")

        if time_diff > 5000:  # 5秒
            print("⚠️  时间差较大，可能影响API调用")

        # 测试获取交易对信息
        print("🔍 测试获取交易对信息...")
        markets = exchange.load_markets(['BTC/USDT', 'ETH/USDT'])
        print(f"✅ 成功获取 {len(markets)} 个主要交易对")

        # 测试获取深度数据
        print("📊 测试获取市场深度...")
        orderbook = exchange.fetch_order_book('BTC/USDT')
        best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
        best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0

        if best_bid and best_ask:
            spread = best_ask - best_bid
            spread_pct = (spread / best_bid) * 100
            print(f"✅ 最佳买价: ${best_bid:,.2f}")
            print(f"✅ 最佳卖价: ${best_ask:,.2f}")
            print(f"✅ 价差: ${spread:,.2f} ({spread_pct:.3f}%)")

        return True

    except Exception as e:
        print(f"❌ 测试网连接失败: {e}")
        return False


async def test_ccxt_pro_connectivity():
    """测试ccxt.pro WebSocket连接"""
    print("\n🚀 测试ccxt.pro WebSocket连接...")

    try:
        import ccxt.pro

        exchange = ccxt.pro.binance({
            'sandbox': True,
            'enableRateLimit': True,
        })

        print("📡 测试WebSocket连接...")

        # 尝试订阅ticker数据
        try:
            # 设置超时，避免无限等待
            ticker = await asyncio.wait_for(
                exchange.watch_ticker('BTC/USDT'),
                timeout=10.0
            )
            print(f"✅ WebSocket连接成功，BTC/USDT: ${ticker['last']:,.2f}")

            # 关闭连接
            await exchange.close()
            return True

        except asyncio.TimeoutError:
            print("⚠️  WebSocket连接超时，可能是网络或防火墙问题")
            await exchange.close()
            return False

    except ImportError:
        print("⚠️  ccxt.pro未安装，跳过WebSocket测试")
        print("💡 安装方法: pip install ccxt-pro")
        return False
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        try:
            await exchange.close()
        except:
            pass
        return False


def test_different_endpoints():
    """测试不同的API端点"""
    print("\n🔗 测试不同API端点...")

    endpoints = [
        ("币安现货", "binance"),
        ("币安美国", "binanceus"),
        ("币安期货", "binanceusdm"),
    ]

    for name, exchange_id in endpoints:
        try:
            print(f"  📍 测试 {name}...")
            exchange = getattr(ccxt, exchange_id)({
                'sandbox': True,
                'enableRateLimit': True,
            })

            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"  ✅ {name}: ${ticker['last']:,.2f}")

        except Exception as e:
            print(f"  ❌ {name} 失败: {str(e)[:50]}...")


def check_network_requirements():
    """检查网络要求"""
    print("\n📋 网络要求检查:")

    print("✅ 必要条件:")
    print("   - 能够访问api.binance.com")
    print("   - 能够访问api1.binance.com")
    print("   - 能够访问data.binance.com")

    print("\n⚠️  如果在中国大陆:")
    print("   - 可能需要使用VPN")
    print("   - 可能需要配置代理")
    print("   - 建议使用币安中国域名: api.binance.cn")


async def main():
    """主测试函数"""
    print("🔍 币安API连接测试")
    print("=" * 50)

    # 检查网络要求
    check_network_requirements()

    # 基本连接测试
    basic_ok = test_basic_connectivity()

    # 沙盒环境测试
    sandbox_ok = test_sandbox_connectivity()

    # WebSocket测试
    ws_ok = await test_ccxt_pro_connectivity()

    # 不同端点测试
    test_different_endpoints()

    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"基本连接: {'✅ 通过' if basic_ok else '❌ 失败'}")
    print(f"沙盒环境: {'✅ 通过' if sandbox_ok else '❌ 失败'}")
    print(f"WebSocket: {'✅ 通过' if ws_ok else '❌ 失败'}")

    if basic_ok and sandbox_ok:
        print("\n🎉 网络连接正常，可以运行策略!")
        print("💡 运行命令: uv run strategy_demo.py")
    else:
        print("\n⚠️  网络连接存在问题，请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否需要使用VPN")
        print("3. 防火墙是否阻止API调用")
        print("4. 币安服务是否可用")


if __name__ == "__main__":
    asyncio.run(main())