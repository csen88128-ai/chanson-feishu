"""
超级简单版 - 获取BTC最新数据
双击运行即可，不需要任何命令行操作
"""
import requests
import json
from datetime import datetime
import os


def main():
    """主函数"""
    print("=" * 70)
    print("  🚀 获取BTC最新数据")
    print("  正在连接交易所API...")
    print("=" * 70)
    print()

    # 尝试多个交易所
    exchanges = [
        ("CoinGecko", "https://api.coingecko.com/api/v3/simple/price"),
        ("Binance", "https://api.binance.com/api/v3/ticker/price"),
        ("OKX", "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"),
    ]

    btc_data = None
    data_source = None

    for name, url in exchanges:
        try:
            print(f"📡 正在连接 {name}...")

            if name == "CoinGecko":
                params = {
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true"
                }
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                btc_data = {
                    "source": name,
                    "price": data['bitcoin']['usd'],
                    "change_24h": data['bitcoin'].get('usd_24h_change', 0),
                    "volume_24h": data['bitcoin'].get('usd_24h_vol', 0),
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            elif name == "Binance":
                params = {"symbol": "BTCUSDT"}
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                btc_data = {
                    "source": name,
                    "price": float(data['price']),
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            elif name == "OKX":
                response = requests.get(url, timeout=10)
                result = response.json()

                if result.get('code') == '0':
                    data = result['data'][0]
                    btc_data = {
                        "source": name,
                        "price": float(data['last']),
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

            if btc_data:
                data_source = name
                print(f"✅ {name} 连接成功！")
                break

        except Exception as e:
            print(f"❌ {name} 连接失败: {str(e)[:50]}")
            print()
            continue

    if not btc_data:
        print()
        print("=" * 70)
        print("  ❌ 所有交易所都无法连接")
        print("=" * 70)
        print()
        print("请检查：")
        print("  1. 网络连接（可能需要VPN）")
        print("  2. Python是否已安装")
        print("  3. requests库是否已安装: pip install requests")
        print()
        input("按回车键退出...")
        return

    # 显示结果
    print()
    print("=" * 70)
    print("  ✅ 数据获取成功！")
    print("=" * 70)
    print()
    print(f"📊 数据来源: {btc_data['source']}")
    print(f"💰 当前价格: ${btc_data['price']:,.2f}")
    print(f"📅 获取时间: {btc_data['timestamp']}")
    if 'change_24h' in btc_data:
        print(f"📈 24h涨跌: {btc_data['change_24h']:.2f}%")
    if 'volume_24h' in btc_data:
        print(f"📊 24h成交量: ${btc_data['volume_24h']:,.0f}")
    print()

    # 保存为JSON
    json_filename = "btc_latest_data.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(btc_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到: {json_filename}")
    print()

    # 保存为TXT（方便查看）
    txt_filename = "btc_latest_data.txt"
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"数据来源: {btc_data['source']}\n")
        f.write(f"当前价格: ${btc_data['price']:,.2f}\n")
        f.write(f"获取时间: {btc_data['timestamp']}\n")
        if 'change_24h' in btc_data:
            f.write(f"24h涨跌: {btc_data['change_24h']:.2f}%\n")
        if 'volume_24h' in btc_data:
            f.write(f"24h成交量: ${btc_data['volume_24h']:,.0f}\n")

    print(f"✅ 数据已保存到: {txt_filename}")
    print()

    print("=" * 70)
    print("  📋 下一步操作")
    print("=" * 70)
    print()
    print("现在有两个选择：")
    print()
    print("选择1: 上传文件")
    print("  1. 找到文件: btc_latest_data.json")
    print("  2. 上传给AI助手")
    print()
    print("选择2: 复制数据")
    print("  1. 打开文件: btc_latest_data.json")
    print("  2. 复制里面的内容")
    print("  3. 粘贴给AI助手")
    print()
    print("就这么简单！😊")
    print()
    input("按回车键退出...")


if __name__ == "__main__":
    main()
