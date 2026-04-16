"""
超简单版本 - 一键获取BTC最新数据
运行后数据自动保存，只需要告诉我"已获取数据"
"""
import requests
import json
from datetime import datetime


def get_data():
    """获取BTC数据"""
    print("🔄 正在获取BTC最新数据...")
    print()

    exchanges = [
        ("Binance", "https://api.binance.com/api/v3/klines"),
        ("Huobi", "https://api.huobi.pro/market/history/kline"),
        ("OKX", "https://www.okx.com/api/v5/market/history/candles")
    ]

    for name, url in exchanges:
        try:
            print(f"📡 尝试连接 {name}...")

            if name == "Binance":
                params = {"symbol": "BTCUSDT", "interval": "1h", "limit": 100}
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                latest = data[-1]
                result = {
                    "source": name,
                    "price": float(latest[4]),
                    "time": datetime.fromtimestamp(latest[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                }

            elif name == "Huobi":
                params = {"symbol": "btcusdt", "period": "1min", "size": 1}
                response = requests.get(url, params=params, timeout=10)
                result_json = response.json()
                if result_json.get('status') == 'ok':
                    latest = result_json['data'][0]
                    result = {
                        "source": name,
                        "price": float(latest['close']),
                        "time": datetime.fromtimestamp(latest['id']).strftime('%Y-%m-%d %H:%M:%S')
                    }

            elif name == "OKX":
                params = {"instId": "BTC-USDT", "bar": "1H", "limit": 1}
                response = requests.get(url, params=params, timeout=10)
                result_json = response.json()
                if result_json.get('code') == '0':
                    latest = result_json['data'][0]
                    result = {
                        "source": name,
                        "price": float(latest[4]),
                        "time": datetime.fromtimestamp(int(latest[0]) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    }

            print(f"✅ {name} 获取成功！")
            return result

        except Exception as e:
            print(f"❌ {name} 失败: {str(e)[:50]}")
            continue

    return None


def main():
    """主函数"""
    print("=" * 60)
    print("  🚀 一键获取BTC最新数据（超简单版）")
    print("=" * 60)
    print()

    # 获取数据
    result = get_data()

    if not result:
        print()
        print("❌ 所有交易所都无法连接！")
        print()
        print("请检查：")
        print("  1. 网络连接（需要VPN）")
        print("  2. 交易所API是否可用")
        return

    # 显示结果
    print()
    print("=" * 60)
    print("  ✅ 数据获取成功！")
    print("=" * 60)
    print()
    print(f"📊 数据来源: {result['source']}")
    print(f"💰 当前价格: ${result['price']:,.2f}")
    print(f"📅 数据时间: {result['time']}")
    print()

    # 保存到文件
    filename = "btc_data.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"数据来源: {result['source']}\n")
        f.write(f"当前价格: ${result['price']:,.2f}\n")
        f.write(f"数据时间: {result['time']}\n")

    print(f"✅ 数据已保存到: {filename}")
    print()

    print("=" * 60)
    print("  📋 下一步操作")
    print("=" * 60)
    print()
    print("现在只需要做一件事：")
    print()
    print("  👉 在聊天里告诉我：\"已获取数据\"")
    print()
    print("我会自动读取 btc_data.txt 文件并进行分析！")
    print()
    print("就这么简单！😊")
    print()


if __name__ == "__main__":
    main()
