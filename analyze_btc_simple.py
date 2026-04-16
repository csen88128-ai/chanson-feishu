"""
缠论多智能体系统 - BTC实时行情快速分析脚本
"""
import sys
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def generate_mock_btc_data(limit=100, base_price=65000):
    """生成模拟BTC数据（包含必要的指标）"""
    data = []
    current_time = datetime.now() - timedelta(hours=limit)

    current_price = base_price
    dif = 0
    dea = 0
    macd = 0

    for i in range(limit):
        # 模拟价格波动
        price_change = random.uniform(-0.005, 0.005)
        current_price = current_price * (1 + price_change)

        # 生成OHLCV数据
        high = current_price * random.uniform(1.0, 1.002)
        low = current_price * random.uniform(0.998, 1.0)
        open_price = low + random.uniform(0, high - low)
        close = low + random.uniform(0, high - low)

        # 计算MACD（简化版）
        ema12 = close * 0.15 + (data[-1][4] if data else close) * 0.85
        ema26 = close * 0.075 + (data[-1][4] if data else close) * 0.925
        dif = ema12 - ema26
        dea = dif * 0.2 + (dea if data else 0) * 0.8
        macd = (dif - dea) * 2

        timestamp = int(current_time.timestamp() * 1000)

        data.append([
            timestamp,
            open_price,
            high,
            low,
            close,
            random.uniform(100, 1000),  # volume
            dif,
            dea,
            macd
        ])

        current_time += timedelta(hours=1)

    return data


def analyze_btc_realtime():
    """分析BTC实时行情"""
    print_header("缠论多智能体系统 - BTC实时行情分析")

    symbol = "BTCUSDT"
    interval = "1h"

    print(f"🎯 分析标的: {symbol}")
    print(f"⏱️  分析周期: {interval}")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚠️  使用模拟数据（网络环境限制）")
    print()

    # 1. 获取K线数据
    print("📡 步骤1: 获取K线数据...")
    try:
        klines = generate_mock_btc_data(limit=100, base_price=65000)

        # 转换为DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'dif', 'dea', 'macd'
        ])

        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume', 'dif', 'dea', 'macd']:
            df[col] = df[col].astype(float)

        latest_price = df.iloc[-1]['close']
        price_change = (df.iloc[-1]['close'] / df.iloc[-2]['close'] - 1) * 100
        print(f"  ✅ 成功获取 {len(df)} 根K线")
        print(f"  💰 最新价格: ${latest_price:,.2f}")
        print(f"  📊 涨跌幅: {price_change:.2f}%\n")
    except Exception as e:
        print(f"  ❌ 获取数据失败: {str(e)}\n")
        return

    # 2. 技术指标分析
    print("📊 步骤2: 技术指标分析...")
    try:
        # 计算均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['rsi'] = calculate_rsi(df['close'], 14)

        print(f"  ✅ MA5:  ${df['ma5'].iloc[-1]:,.2f}")
        print(f"  ✅ MA20: ${df['ma20'].iloc[-1]:,.2f}")
        print(f"  ✅ RSI:  {df['rsi'].iloc[-1]:.2f}")
        print(f"  ✅ DIF:  {df['dif'].iloc[-1]:.2f}")
        print(f"  ✅ DEA:  {df['dea'].iloc[-1]:.2f}")
        print(f"  ✅ MACD: {df['macd'].iloc[-1]:.2f}\n")
    except Exception as e:
        print(f"  ❌ 技术指标计算失败: {str(e)}\n")

    # 3. 缠论结构分析（简化版）
    print("📐 步骤3: 缠论结构分析（简化版）...")
    try:
        # 识别顶分型和底分型
        df['fractal'] = identify_fractals(df)

        # 统计顶底分型
        tops = df[df['fractal'] == 'top'].shape[0]
        bottoms = df[df['fractal'] == 'bottom'].shape[0]

        print(f"  ✅ 识别顶分型: {tops} 个")
        print(f"  ✅ 识别底分型: {bottoms} 个")

        # 识别最新分型
        recent_fractals = df[df['fractal'] != 'none'].tail(2)
        if len(recent_fractals) > 0:
            print(f"  📍 最新分型:")
            for _, row in recent_fractals.iterrows():
                fractal_type = "🔴 顶分型" if row['fractal'] == 'top' else "🟢 底分型"
                print(f"     {fractal_type} - 价格: ${row['high'] if row['fractal'] == 'top' else row['low']:,.2f}")
        print()
    except Exception as e:
        print(f"  ❌ 结构分析失败: {str(e)}\n")

    # 4. 综合分析结论
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📝 综合分析结论：\n")

    latest = df.iloc[-1]
    price_change = (latest['close'] / df.iloc[-2]['close'] - 1) * 100

    # 多空信号分析
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
        signals.append(("🔴", "RSI超买，注意回调"))
    elif latest['rsi'] < 30:
        signals.append(("🟢", "RSI超卖，可能反弹"))
    else:
        signals.append(("🟡", "RSI在正常区间"))

    # MACD信号
    if latest['dif'] > latest['dea']:
        signals.append(("🟢", "MACD金叉 - 看多信号"))
    else:
        signals.append(("🔴", "MACD死叉 - 看空信号"))

    # 显示信号
    print("  📊 技术信号：\n")
    for icon, signal in signals:
        print(f"     {icon} {signal}")

    print()
    print("  📈 趋势判断：")

    # 综合趋势判断
    bullish_signals = sum(1 for icon, _ in signals if icon == "🟢")
    bearish_signals = sum(1 for icon, _ in signals if icon == "🔴")

    if bullish_signals > bearish_signals:
        trend = "🟢 偏多"
        suggestion = "📈 建议寻找做多机会，注意控制风险"
    elif bearish_signals > bullish_signals:
        trend = "🔴 偏空"
        suggestion = "📉 建议谨慎观望或轻仓做空，严格控制风险"
    else:
        trend = "🟡 震荡"
        suggestion = "➡️  建议观望，等待明确方向"

    print(f"     {trend}")
    print(f"     {suggestion}")

    # 价格分析
    print()
    print("  💰 价格分析：\n")
    print(f"     当前价格: ${latest['close']:,.2f}")
    print(f"     24h涨跌: {price_change:.2f}%")
    print(f"     最高价: ${latest['high']:,.2f}")
    print(f"     最低价: ${latest['low']:,.2f}")
    print(f"     成交量: {latest['volume']:,.2f}")
    print(f"     更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n  ⚠️  注：以上分析基于模拟数据，仅供演示")
    print()


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def identify_fractals(df, lookback=2):
    """识别顶底分型"""
    fractals = ['none'] * len(df)

    for i in range(lookback, len(df) - lookback):
        # 识别顶分型
        if (df.iloc[i]['high'] > df.iloc[i-1]['high'] and
            df.iloc[i]['high'] > df.iloc[i-2]['high'] and
            df.iloc[i]['high'] > df.iloc[i+1]['high'] and
            df.iloc[i]['high'] > df.iloc[i+2]['high']):
            fractals[i] = 'top'

        # 识别底分型
        elif (df.iloc[i]['low'] < df.iloc[i-1]['low'] and
              df.iloc[i]['low'] < df.iloc[i-2]['low'] and
              df.iloc[i]['low'] < df.iloc[i+1]['low'] and
              df.iloc[i]['low'] < df.iloc[i+2]['low']):
            fractals[i] = 'bottom'

    return fractals


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - BTC实时行情分析")
    print("🚀" * 35 + "\n")

    analyze_btc_realtime()

    print("\n" + "🎉" * 35)
    print("  分析完成！")
    print("🎉" * 35 + "\n")


if __name__ == "__main__":
    main()
