"""
缠论多智能体系统 - BTC真实实时行情分析（简化版）
只需要安装：requests pandas numpy

本地运行步骤：
1. pip install requests pandas numpy
2. python analyze_btc_local.py
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime


def get_btc_klines(symbol="BTCUSDT", interval="1h", limit=100, proxies=None):
    """从Binance获取K线数据"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    try:
        response = requests.get(url, params=params, proxies=proxies, timeout=10)
        if response.status_code == 200:
            klines = response.json()
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取数据失败: {str(e)}")
        return None


def calculate_indicators(df):
    """计算技术指标"""
    # 均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema_fast = df['close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['close'].ewm(span=26, adjust=False).mean()
    df['dif'] = ema_fast - ema_slow
    df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
    df['macd'] = (df['dif'] - df['dea']) * 2

    return df


def analyze_signals(df):
    """分析交易信号"""
    latest = df.iloc[-1]
    signals = []

    # MA信号
    if latest['close'] > latest['ma5'] and latest['close'] > latest['ma20']:
        signals.append(("🟢", "价格在MA5和MA20上方 - 看多"))
    elif latest['close'] < latest['ma5'] and latest['close'] < latest['ma20']:
        signals.append(("🔴", "价格在MA5和MA20下方 - 看空"))
    else:
        signals.append(("🟡", "价格在均线附近 - 观望"))

    # RSI信号
    if latest['rsi'] > 70:
        signals.append(("🔴", f"RSI超买（{latest['rsi']:.1f}），注意回调"))
    elif latest['rsi'] < 30:
        signals.append(("🟢", f"RSI超卖（{latest['rsi']:.1f}），可能反弹"))
    else:
        signals.append(("🟡", f"RSI正常（{latest['rsi']:.1f}）"))

    # MACD信号
    if latest['dif'] > latest['dea']:
        macd_type = "金叉" if df.iloc[-2]['dif'] <= df.iloc[-2]['dea'] else "金叉延续"
        signals.append(("🟢", f"MACD {macd_type}"))
    else:
        macd_type = "死叉" if df.iloc[-2]['dif'] >= df.iloc[-2]['dea'] else "死叉延续"
        signals.append(("🔴", f"MACD {macd_type}"))

    return signals


def main():
    """主分析函数"""
    print("\n" + "=" * 70)
    print("  🚀 缠论多智能体系统 - BTC真实实时行情分析（本地版）")
    print("=" * 70 + "\n")

    # 代理设置（如果您使用VPN，请取消下面的注释并修改端口）
    # proxies = {
    #     'http': 'http://127.0.0.1:7890',  # 修改为您的代理端口
    #     'https': 'http://127.0.0.1:7890',
    # }

    proxies = None  # 不使用代理

    # 获取数据
    print("📡 正在从Binance获取BTCUSDT实时数据...")
    print("⏳ 请稍候...\n")

    df = get_btc_klines(proxies=proxies)

    if df is None:
        print("\n❌ 无法获取数据\n")
        print("💡 请检查：")
        print("   1. 网络连接是否正常")
        print("   2. VPN是否开启（如果需要）")
        print("   3. 代理设置是否正确")
        print()
        return

    print(f"✅ 成功获取 {len(df)} 根K线数据")
    print(f"📅 数据时间: {df.iloc[-1]['close_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 计算指标
    print("📊 正在计算技术指标...")
    df = calculate_indicators(df)
    print("✅ 指标计算完成\n")

    # 分析信号
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 分析结果\n")

    latest = df.iloc[-1]
    price_change = (latest['close'] / df.iloc[-2]['close'] - 1) * 100

    # 显示价格信息
    print(f"💰 价格信息：")
    print(f"   当前价格: ${latest['close']:,.2f}")
    print(f"   涨跌幅: {price_change:+.2f}%")
    print(f"   最高价: ${latest['high']:,.2f}")
    print(f"   最低价: ${latest['low']:,.2f}")
    print(f"   成交量: {latest['volume']:,.0f}\n")

    # 显示技术指标
    print(f"📈 技术指标：")
    print(f"   MA5:  ${latest['ma5']:,.2f}")
    print(f"   MA20: ${latest['ma20']:,.2f}")
    print(f"   MA60: ${latest['ma60']:,.2f}")
    print(f"   RSI:  {latest['rsi']:.2f}")
    print(f"   DIF:  {latest['dif']:.2f}")
    print(f"   DEA:  {latest['dea']:.2f}")
    print(f"   MACD: {latest['macd']:.2f}\n")

    # 显示信号
    signals = analyze_signals(df)
    print(f"📊 技术信号：")
    for icon, signal in signals:
        print(f"   {icon} {signal}")

    # 趋势判断
    bullish = sum(1 for icon, _ in signals if icon == "🟢")
    bearish = sum(1 for icon, _ in signals if icon == "🔴")

    print()
    if bullish > bearish:
        print("🟢 趋势判断: 偏多趋势")
        print("📈 建议: 寻找做多机会，支撑位 ${:,.2f}".format(latest['ma20']))
    elif bearish > bullish:
        print("🔴 趋势判断: 偏空趋势")
        print("📉 建议: 谨慎观望或轻仓做空，阻力位 ${:,.2f}".format(latest['ma20']))
    else:
        print("🟡 趋势判断: 震荡趋势")
        print("➡️  建议: 观望为主，等待明确方向")

    # 支撑阻力
    print()
    print("📊 支撑阻力位：")
    print(f"   阻力位1: ${latest['ma5']:,.2f}")
    print(f"   阻力位2: ${latest['ma60']:,.2f}")
    print(f"   支撑位1: ${latest['ma20']:,.2f}")
    print(f"   支撑位2: ${df['close'].min():,.2f}")

    print()
    print("🌐 数据来源: Binance API")
    print("🕐 更新时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()


if __name__ == "__main__":
    main()
