"""
获取BTC实时数据 - 多方案尝试
尝试所有可能的途径获取最新BTC数据
"""
import socket
import urllib.request
import urllib.error
import json
from datetime import datetime


def test_internet_connection():
    """测试网络连接"""
    print("=" * 70)
    print("  第1步：测试网络连接")
    print("=" * 70)
    print()

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("✅ 网络连接正常")
        print()
        return True
    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        print()
        return False


def get_btc_via_http():
    """方案1：使用urllib获取CoinGecko数据"""
    print("=" * 70)
    print("  方案1：CoinGecko API（HTTP）")
    print("=" * 70)
    print()

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true"
        }

        # 构造URL
        from urllib.parse import urlencode
        full_url = f"{url}?{urlencode(params)}"

        print(f"📡 正在请求: {full_url}")
        request = urllib.request.Request(
            full_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

            result = {
                "source": "CoinGecko",
                "price": data['bitcoin']['usd'],
                "change_24h": data['bitcoin'].get('usd_24h_change', 0),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "method": "HTTP"
            }

            print("✅ 获取成功！")
            print(f"   价格: ${result['price']:,.2f}")
            print(f"   24h涨跌: {result['change_24h']:.2f}%")
            print()

            return result

    except urllib.error.URLError as e:
        print(f"❌ 请求失败: {e}")
        print()
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return None


def get_btc_via_requests():
    """方案2：使用requests获取Binance数据"""
    print("=" * 70)
    print("  方案2：Binance API（requests）")
    print("=" * 70)
    print()

    try:
        import requests

        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}

        print(f"📡 正在请求: {url}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = {
            "source": "Binance",
            "price": float(data['price']),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "method": "requests"
        }

        print("✅ 获取成功！")
        print(f"   价格: ${result['price']:,.2f}")
        print()

        return result

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print()
        return None


def get_btc_via_binance_websocket():
    """方案3：Binance WebSocket"""
    print("=" * 70)
    print("  方案3：Binance WebSocket")
    print("=" * 70)
    print()

    try:
        import requests

        # 使用Binance的ticker 24h接口（更简单）
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": "BTCUSDT"}

        print(f"📡 正在请求: {url}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = {
            "source": "Binance-24h",
            "price": float(data['lastPrice']),
            "change_24h": float(data['priceChangePercent']),
            "high_24h": float(data['highPrice']),
            "low_24h": float(data['lowPrice']),
            "volume_24h": float(data['volume']),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "method": "Binance 24h ticker"
        }

        print("✅ 获取成功！")
        print(f"   价格: ${result['price']:,.2f}")
        print(f"   24h涨跌: {result['change_24h']:.2f}%")
        print()

        return result

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print()
        return None


def get_btc_via_coinmarketcap():
    """方案4：CoinMarketCap公共API"""
    print("=" * 70)
    print("  方案4：CoinMarketCap公共API")
    print("=" * 70)
    print()

    try:
        import requests

        url = "https://coinmarketcap.com/api/v2/ticker/1/"

        print(f"📡 正在请求: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = {
            "source": "CoinMarketCap",
            "price": float(data['data']['quotes']['USD']['price']),
            "change_24h": float(data['data']['quotes']['USD']['percent_change_24h']),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "method": "CoinMarketCap"
        }

        print("✅ 获取成功！")
        print(f"   价格: ${result['price']:,.2f}")
        print(f"   24h涨跌: {result['change_24h']:.2f}%")
        print()

        return result

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print()
        return None


def get_btc_via_local_cache():
    """方案5：使用本地缓存数据（如果所有方案都失败）"""
    print("=" * 70)
    print("  方案5：本地缓存数据（备用）")
    print("=" * 70)
    print()

    try:
        # 读取之前获取的真实数据
        cache_file = "/workspace/chanson-feishu/btc_cache.json"

        import os
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            print("✅ 使用缓存数据")
            print(f"   价格: ${cached_data['price']:,.2f}")
            print(f"   缓存时间: {cached_data['timestamp']}")
            print()

            return cached_data
        else:
            print("❌ 无缓存数据")
            print()
            return None

    except Exception as e:
        print(f"❌ 读取缓存失败: {e}")
        print()
        return None


def save_result(result):
    """保存结果"""
    if not result:
        return

    # 保存为JSON
    json_file = "/workspace/chanson-feishu/btc_latest.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 保存为TXT
    txt_file = "/workspace/chanson-feishu/btc_latest.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"数据来源: {result['source']}\n")
        f.write(f"获取方式: {result.get('method', 'N/A')}\n")
        f.write(f"当前价格: ${result['price']:,.2f}\n")
        f.write(f"获取时间: {result['timestamp']}\n")
        if 'change_24h' in result:
            f.write(f"24h涨跌: {result['change_24h']:.2f}%\n")
        if 'high_24h' in result:
            f.write(f"24h最高: ${result['high_24h']:,.2f}\n")
        if 'low_24h' in result:
            f.write(f"24h最低: ${result['low_24h']:,.2f}\n")

    print("=" * 70)
    print("  数据已保存")
    print("=" * 70)
    print()
    print(f"📄 JSON文件: {json_file}")
    print(f"📄 TXT文件: {txt_file}")
    print()


def main():
    """主函数"""
    print()
    print("🚀" * 35)
    print("  获取BTC实时数据 - 多方案尝试")
    print("🚀" * 35)
    print()

    # 测试网络连接
    if not test_internet_connection():
        print("⚠️  网络连接测试失败，但将继续尝试获取数据...")
        print()

    # 按顺序尝试多个方案
    methods = [
        ("CoinGecko (HTTP)", get_btc_via_http),
        ("Binance (requests)", get_btc_via_requests),
        ("Binance 24h ticker", get_btc_via_binance_websocket),
        ("CoinMarketCap", get_btc_via_coinmarketcap),
        ("本地缓存", get_btc_via_local_cache),
    ]

    result = None
    successful_method = None

    for method_name, method_func in methods:
        print(f"\n尝试方法: {method_name}")
        result = method_func()

        if result:
            successful_method = method_name
            break

        print(f"⏭️  方法失败，尝试下一个...")
        print()

    # 最终结果
    print()
    print("=" * 70)
    print("  最终结果")
    print("=" * 70)
    print()

    if result:
        print("✅ 成功获取BTC数据！")
        print()
        print(f"📊 来源: {result['source']}")
        print(f"📡 方法: {successful_method}")
        print(f"💰 价格: ${result['price']:,.2f}")
        if 'change_24h' in result:
            print(f"📈 24h涨跌: {result['change_24h']:.2f}%")
        print(f"📅 时间: {result['timestamp']}")
        print()

        # 保存结果
        save_result(result)

        print("=" * 70)
        print("  ✅ 第一步完成：BTC数据获取成功")
        print("=" * 70)
        print()
        print("💡 下一步：运行多智能体分析")
        print()
        print("如需运行分析，请告诉我：\"运行多智能体分析\"")
        print()

        return True
    else:
        print("❌ 所有方案均失败")
        print()
        print("可能的原因：")
        print("  1. 服务器网络完全隔离")
        print("  2. 防火墙阻止了所有外部请求")
        print("  3. DNS解析失败")
        print()
        print("建议方案：")
        print("  1. 检查服务器网络配置")
        print("  2. 配置代理或VPN")
        print("  3. 使用本地数据文件")
        print()

        return False


if __name__ == "__main__":
    success = main()

    if not success:
        print("=" * 70)
        print("  ❌ 第一步失败：无法获取BTC数据")
        print("=" * 70)
