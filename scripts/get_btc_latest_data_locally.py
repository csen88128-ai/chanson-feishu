"""
本地获取BTC最新数据脚本
在有VPN的环境下运行，获取最新的BTC数据
"""
import requests
import json
from datetime import datetime
import pandas as pd


def get_binance_data():
    """从Binance获取BTC数据"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 100
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 解析最新数据
        latest = data[-1]
        return {
            "source": "Binance",
            "timestamp": latest[0],
            "open": float(latest[1]),
            "high": float(latest[2]),
            "low": float(latest[3]),
            "close": float(latest[4]),
            "volume": float(latest[5]),
            "all_data": data
        }
    except Exception as e:
        print(f"Binance获取失败: {e}")
        return None


def get_huobi_data():
    """从Huobi获取BTC数据"""
    try:
        url = "https://api.huobi.pro/market/history/kline"
        params = {
            "symbol": "btcusdt",
            "period": "1min",
            "size": 100
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get('status') == 'ok':
            data = result['data']
            # 按时间排序，取最新的
            data_sorted = sorted(data, key=lambda x: x['id'], reverse=True)
            latest = data_sorted[0]

            return {
                "source": "Huobi",
                "timestamp": latest['id'],
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "close": float(latest['close']),
                "volume": float(latest['vol']),
                "all_data": data_sorted
            }
    except Exception as e:
        print(f"Huobi获取失败: {e}")
        return None


def get_okx_data():
    """从OKX获取BTC数据"""
    try:
        url = "https://www.okx.com/api/v5/market/history/candles"
        params = {
            "instId": "BTC-USDT",
            "bar": "1H",
            "limit": 100
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == '0':
            data = result['data']
            latest = data[0]

            return {
                "source": "OKX",
                "timestamp": int(latest[0]),
                "open": float(latest[1]),
                "high": float(latest[2]),
                "low": float(latest[3]),
                "close": float(latest[4]),
                "volume": float(latest[5]),
                "all_data": data
            }
    except Exception as e:
        print(f"OKX获取失败: {e}")
        return None


def calculate_indicators(data, all_data):
    """计算技术指标"""
    # 转换为DataFrame计算指标
    df = pd.DataFrame(all_data)

    # 计算5日、20日、60日均线
    closes = df.iloc[:, 4].astype(float)  # 收盘价列
    data['ma5'] = closes.tail(5).mean()
    data['ma20'] = closes.tail(20).mean()
    data['ma60'] = closes.tail(60).mean()

    # 计算RSI
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    data['rsi'] = rsi

    # 计算MACD
    ema12 = closes.ewm(span=12).mean().iloc[-1]
    ema26 = closes.ewm(span=26).mean().iloc[-1]
    data['macd'] = ema12 - ema26
    data['macd_signal'] = data['macd'] * 0.8  # 简化的信号线
    data['macd_hist'] = data['macd'] - data['macd_signal']

    # 计算涨跌幅
    data['change_percent'] = ((data['close'] - data['open']) / data['open']) * 100

    return data


def main():
    """主函数"""
    print("=" * 70)
    print("  获取BTC最新数据（本地运行，需要VPN）")
    print("=" * 70)
    print()

    # 尝试从多个交易所获取数据
    exchanges = [get_binance_data, get_huobi_data, get_okx_data]
    exchange_names = ["Binance", "Huobi", "OKX"]

    latest_data = None
    source = None

    for i, (get_func, name) in enumerate(zip(exchanges, exchange_names)):
        print(f"[{i+1}/3] 尝试从 {name} 获取数据...")
        data = get_func()
        if data:
            print(f"✅ {name} 获取成功！")
            latest_data = data
            source = name
            break
        else:
            print(f"❌ {name} 获取失败，尝试下一个...")
        print()

    if not latest_data:
        print("❌ 所有交易所都获取失败！")
        print("请检查：")
        print("  1. 网络连接（需要VPN）")
        print("  2. 交易所API是否可用")
        return

    # 计算技术指标
    print("📊 计算技术指标...")
    latest_data = calculate_indicators(latest_data, latest_data['all_data'])

    # 格式化输出
    print()
    print("=" * 70)
    print("  ✅ BTC最新数据获取成功！")
    print("=" * 70)
    print()

    print(f"📅 数据来源: {source}")
    print(f"📅 数据时间: {datetime.fromtimestamp(latest_data['timestamp'] / 1000)}")
    print()

    print("💰 价格数据:")
    print(f"   当前价格: ${latest_data['close']:,.2f}")
    print(f"   涨跌幅: {latest_data['change_percent']:.2f}%")
    print(f"   开盘价: ${latest_data['open']:,.2f}")
    print(f"   最高价: ${latest_data['high']:,.2f}")
    print(f"   最低价: ${latest_data['low']:,.2f}")
    print(f"   成交量: {latest_data['volume']:,.0f}")
    print()

    print("📈 技术指标:")
    print(f"   MA5: ${latest_data['ma5']:,.2f}")
    print(f"   MA20: ${latest_data['ma20']:,.2f}")
    print(f"   MA60: ${latest_data['ma60']:,.2f}")
    print(f"   RSI: {latest_data['rsi']:.2f}")
    print(f"   MACD: {latest_data['macd']:.2f}")
    print(f"   MACD信号: {latest_data['macd_signal']:.2f}")
    print(f"   MACD柱: {latest_data['macd_hist']:.2f}")
    print()

    # 保存到文件
    output_file = "btc_latest_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(latest_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到: {output_file}")
    print()

    # 生成可以直接复制的数据格式
    print("=" * 70)
    print("  复制以下数据发送给Agent进行分析")
    print("=" * 70)
    print()

    data_str = json.dumps(latest_data, ensure_ascii=False)
    print(data_str)
    print()

    print("=" * 70)
    print("  使用方法：")
    print("=" * 70)
    print()
    print("方法1: 直接复制上面的JSON数据发送给Agent")
    print()
    print("方法2: 发送文件 btc_latest_data.json 给Agent")
    print()
    print("方法3: 运行以下命令将数据发送给服务器：")
    print(f"  scp btc_latest_data.json user@server:/workspace/chanson-feishu/")
    print()


if __name__ == "__main__":
    main()
