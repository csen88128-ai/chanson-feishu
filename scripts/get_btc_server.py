"""
服务器端获取BTC最新数据
尝试多个数据源，包括CoinGecko等公共API
"""
import requests
import json
from datetime import datetime


def get_coingecko_data():
    """从CoinGecko获取BTC数据"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        return {
            "source": "CoinGecko",
            "price": data['market_data']['current_price']['usd'],
            "change_24h": data['market_data']['price_change_percentage_24h'],
            "high_24h": data['market_data']['high_24h']['usd'],
            "low_24h": data['market_data']['low_24h']['usd'],
            "volume_24h": data['market_data']['total_volume']['usd'],
            "market_cap": data['market_data']['market_cap']['usd'],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"CoinGecko失败: {e}")
        return None


def get_coinapi_data():
    """从CoinAPI获取数据（备用）"""
    try:
        url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
        headers = {"X-CoinAPI-Key": "demo"}  # 使用demo key
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "source": "CoinAPI",
            "price": data['rate'],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"CoinAPI失败: {e}")
        return None


def get_binance_data():
    """从Binance获取数据（备用）"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": "BTCUSDT"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "source": "Binance",
            "price": float(data['lastPrice']),
            "change_24h": float(data['priceChangePercent']),
            "high_24h": float(data['highPrice']),
            "low_24h": float(data['lowPrice']),
            "volume_24h": float(data['volume']),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Binance失败: {e}")
        return None


def get_binance_ticker():
    """从Binance ticker API获取（更简单的接口）"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "source": "Binance-Ticker",
            "price": float(data['price']),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Binance Ticker失败: {e}")
        return None


def main():
    """主函数"""
    print("=" * 70)
    print("  🚀 服务器端获取BTC最新数据")
    print("=" * 70)
    print()

    # 尝试多个数据源
    sources = [
        ("CoinGecko", get_coingecko_data),
        ("Binance Ticker", get_binance_ticker),
        ("CoinAPI", get_coinapi_data),
        ("Binance 24h", get_binance_data),
    ]

    result = None
    for name, func in sources:
        print(f"[{sources.index((name, func)) + 1}/4] 尝试 {name}...")
        try:
            result = func()
            if result:
                print(f"✅ {name} 获取成功！")
                break
        except Exception as e:
            print(f"❌ {name} 失败")
        print()

    if not result:
        print("❌ 所有数据源都无法访问！")
        print()
        print("服务器可能无法访问外部网络。")
        print("建议使用本地VPN获取数据。")
        return

    # 显示结果
    print()
    print("=" * 70)
    print("  ✅ 数据获取成功！")
    print("=" * 70)
    print()
    print(f"📊 数据来源: {result['source']}")
    print(f"💰 当前价格: ${result['price']:,.2f}")
    print(f"📅 数据时间: {result['timestamp']}")
    print()

    if 'change_24h' in result:
        print(f"📈 24h涨跌: {result['change_24h']:.2f}%")
    if 'high_24h' in result:
        print(f"🔺 24h最高: ${result['high_24h']:,.2f}")
    if 'low_24h' in result:
        print(f"🔻 24h最低: ${result['low_24h']:,.2f}")
    if 'volume_24h' in result:
        print(f"📊 24h成交量: ${result['volume_24h']:,.0f}")
    if 'market_cap' in result:
        print(f"💎 市值: ${result['market_cap']:,.0f}")
    print()

    # 保存到文件
    filename = "/workspace/chanson-feishu/btc_data_server.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"数据来源: {result['source']}\n")
        f.write(f"当前价格: ${result['price']:,.2f}\n")
        f.write(f"数据时间: {result['timestamp']}\n")
        if 'change_24h' in result:
            f.write(f"24h涨跌: {result['change_24h']:.2f}%\n")
        if 'high_24h' in result:
            f.write(f"24h最高: ${result['high_24h']:,.2f}\n")
        if 'low_24h' in result:
            f.write(f"24h最低: ${result['low_24h']:,.2f}\n")
        if 'volume_24h' in result:
            f.write(f"24h成交量: ${result['volume_24h']:,.0f}\n")

    print(f"✅ 数据已保存到: {filename}")
    print()

    print("=" * 70)
    print("  ✅ 获取完成！现在运行多智能体协作分析")
    print("=" * 70)
    print()

    return result


if __name__ == "__main__":
    result = main()

    if result:
        print("🚀 准备运行多智能体协作分析...")
        print()
