"""
缠论多智能体系统 - BTC真实实时行情分析
尝试连接Binance API获取真实数据
"""
import sys
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def get_real_btc_data(symbol="BTCUSDT", interval="1h", limit=100):
    """从Binance获取真实K线数据"""
    print(f"📡 正在连接Binance API获取 {symbol} 的实时数据...")
    print(f"   交易对: {symbol}")
    print(f"   周期: {interval}")
    print(f"   数量: {limit} 根K线")
    print()

    try:
        # Binance API端点
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        # 设置超时
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            klines = response.json()

            if klines and len(klines) > 0:
                # 转换为DataFrame
                df = pd.DataFrame(klines, columns=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])

                # 转换数据类型
                df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
                    df[col] = df[col].astype(float)

                print(f"✅ 成功获取 {len(df)} 根K线数据")
                print(f"📅 数据时间范围:")
                print(f"   起始: {df.iloc[0]['open_time']}")
                print(f"   结束: {df.iloc[-1]['close_time']}")
                print()

                return df
            else:
                print("❌ 未获取到数据\n")
                return None
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            print(f"   响应: {response.text}\n")
            return None

    except requests.exceptions.Timeout:
        print("❌ 连接超时，无法访问Binance API\n")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，网络可能不可用\n")
        return None
    except Exception as e:
        print(f"❌ 获取数据失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2
    return dif, dea, macd


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


def analyze_btc_realtime():
    """实时分析BTC行情"""
    print_header("缠论多智能体系统 - BTC真实实时行情分析")

    symbol = "BTCUSDT"
    interval = "1h"

    print(f"🎯 分析标的: {symbol}")
    print(f"⏱️  分析周期: {interval}")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 获取真实K线数据
    df = get_real_btc_data(symbol, interval, limit=100)

    if df is None:
        print("❌ 无法获取真实数据，请检查网络连接")
        print("\n💡 建议：")
        print("   1. 检查网络连接")
        print("   2. 检查VPN是否正常工作")
        print("   3. 使用模拟数据分析：python analyze_btc_simple.py")
        print()
        return

    # 2. 计算技术指标
    print("📊 步骤2: 计算技术指标...")
    try:
        # 计算均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()

        # 计算RSI
        df['rsi'] = calculate_rsi(df['close'], 14)

        # 计算MACD
        df['dif'], df['dea'], df['macd'] = calculate_macd(df['close'])

        print(f"  ✅ MA5:  ${df['ma5'].iloc[-1]:,.2f}")
        print(f"  ✅ MA20: ${df['ma20'].iloc[-1]:,.2f}")
        print(f"  ✅ MA60: ${df['ma60'].iloc[-1]:,.2f}")
        print(f"  ✅ RSI:  {df['rsi'].iloc[-1]:.2f}")
        print(f"  ✅ DIF:  {df['dif'].iloc[-1]:.2f}")
        print(f"  ✅ DEA:  {df['dea'].iloc[-1]:.2f}")
        print(f"  ✅ MACD: {df['macd'].iloc[-1]:.2f}\n")
    except Exception as e:
        print(f"  ❌ 技术指标计算失败: {str(e)}\n")
        return

    # 3. 缠论结构分析
    print("📐 步骤3: 缠论结构分析...")
    try:
        df['fractal'] = identify_fractals(df)

        # 统计顶底分型
        tops = df[df['fractal'] == 'top'].shape[0]
        bottoms = df[df['fractal'] == 'bottom'].shape[0]

        print(f"  ✅ 识别顶分型: {tops} 个")
        print(f"  ✅ 识别底分型: {bottoms} 个")

        # 显示最新的分型
        recent_fractals = df[df['fractal'] != 'none'].tail(5)
        if len(recent_fractals) > 0:
            print(f"  📍 最近分型:")
            for idx, row in recent_fractals.iterrows():
                fractal_type = "🔴 顶分型" if row['fractal'] == 'top' else "🟢 底分型"
                price = row['high'] if row['fractal'] == 'top' else row['low']
                time_str = row['open_time'].strftime('%m-%d %H:%M')
                print(f"     {fractal_type} - ${price:,.2f} - {time_str}")
        print()
    except Exception as e:
        print(f"  ❌ 结构分析失败: {str(e)}\n")

    # 4. 综合分析
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
        signals.append(("🔴", "RSI超买（>70），注意回调"))
    elif latest['rsi'] < 30:
        signals.append(("🟢", "RSI超卖（<30），可能反弹"))
    else:
        signals.append(("🟡", "RSI正常区间（30-70）"))

    # MACD信号
    if latest['dif'] > latest['dea']:
        macd_status = "金叉" if df.iloc[-2]['dif'] <= df.iloc[-2]['dea'] else "金叉延续"
        signals.append(("🟢", f"MACD {macd_status} - 看多"))
    else:
        macd_status = "死叉" if df.iloc[-2]['dif'] >= df.iloc[-2]['dea'] else "死叉延续"
        signals.append(("🔴", f"MACD {macd_status} - 看空"))

    # 显示信号
    print("  📊 技术信号：\n")
    for icon, signal in signals:
        print(f"     {icon} {signal}")

    # 趋势判断
    print()
    print("  📈 趋势判断：")

    bullish_signals = sum(1 for icon, _ in signals if icon == "🟢")
    bearish_signals = sum(1 for icon, _ in signals if icon == "🔴")

    if bullish_signals > bearish_signals:
        trend = "🟢 偏多趋势"
        suggestion = "📈 建议：寻找做多机会，注意控制风险，支撑位：${:,.2f}".format(latest['ma20'])
    elif bearish_signals > bullish_signals:
        trend = "🔴 偏空趋势"
        suggestion = "📉 建议：谨慎观望或轻仓做空，严格控制风险，阻力位：${:,.2f}".format(latest['ma20'])
    else:
        trend = "🟡 震荡趋势"
        suggestion = "➡️  建议：观望为主，等待明确方向"

    print(f"     {trend}")
    print(f"     {suggestion}")

    # 支撑阻力位
    print()
    print("  📊 支撑阻力位：\n")
    print(f"     阻力位1: ${latest['ma5']:,.2f} (MA5)")
    print(f"     阻力位2: ${latest['ma60']:,.2f} (MA60)")
    print(f"     支撑位1: ${latest['ma20']:,.2f} (MA20)")
    print(f"     支撑位2: ${df['close'].min():,.2f} (近期低点)")

    # 价格分析
    print()
    print("  💰 价格分析：\n")
    print(f"     当前价格: ${latest['close']:,.2f}")
    print(f"     涨跌幅: {price_change:+.2f}%")
    print(f"     最高价: ${latest['high']:,.2f}")
    print(f"     最低价: ${latest['low']:,.2f}")
    print(f"     成交量: {latest['volume']:,.0f}")
    print(f"     振幅: {((latest['high'] - latest['low']) / latest['low'] * 100):.2f}%")
    print(f"     更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 数据来源说明
    print()
    print("  🌐 数据来源: Binance API（真实实时数据）")
    print(f"  📅 数据时间: {latest['close_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - BTC真实实时行情分析")
    print("🚀" * 35 + "\n")

    analyze_btc_realtime()

    print("\n" + "🎉" * 35)
    print("  分析完成！")
    print("🎉" * 35 + "\n")


if __name__ == "__main__":
    main()
