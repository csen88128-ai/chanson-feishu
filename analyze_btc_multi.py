"""
缠论多智能体系统 - 多交易所API实时行情分析
支持：Binance、Huobi、OKX、CoinGecko等多个数据源
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime


class ExchangeAPI:
    """交易所API基类"""

    def __init__(self, name, symbol="BTCUSDT"):
        self.name = name
        self.symbol = symbol
        self.base_url = ""
        self.timeout = 10

    def get_klines(self, interval="1h", limit=100):
        """获取K线数据"""
        raise NotImplementedError


class BinanceAPI(ExchangeAPI):
    """Binance API"""

    def __init__(self, symbol="BTCUSDT"):
        super().__init__("Binance", symbol)
        self.base_url = "https://api.binance.com"

    def get_klines(self, interval="1h", limit=100):
        """获取Binance K线数据"""
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {'symbol': self.symbol, 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=self.timeout)

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
        except Exception as e:
            print(f"  ❌ {self.name} API失败: {str(e)}")
        return None


class HuobiAPI(ExchangeAPI):
    """Huobi（火币）API"""

    def __init__(self, symbol="BTCUSDT"):
        super().__init__("Huobi", symbol)
        self.base_url = "https://api.huobi.pro"
        # Huobi的symbol格式通常是 btcusdt

    def get_klines(self, interval="1h", limit=100):
        """获取Huobi K线数据"""
        try:
            # Huobi interval映射
            interval_map = {
                '1m': '1min', '5m': '5min', '15m': '15min',
                '30m': '30min', '1h': '60min', '4h': '4hour',
                '1d': '1day', '1w': '1week'
            }
            huobi_interval = interval_map.get(interval, '60min')

            url = f"{self.base_url}/market/history/kline"
            params = {
                'symbol': self.symbol.lower(),
                'period': huobi_interval,
                'size': limit
            }
            response = requests.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data:
                    klines = data['data']
                    if klines:
                        df = pd.DataFrame(klines)
                        df = df.rename(columns={
                            'id': 'open_time',
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'vol': 'volume'
                        })

                        df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
                        df['close_time'] = df['open_time'] + pd.Timedelta(hours=1)
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = df[col].astype(float)

                        # 按时间排序
                        df = df.sort_values('open_time').reset_index(drop=True)
                        return df
        except Exception as e:
            print(f"  ❌ {self.name} API失败: {str(e)}")
        return None


class OKXAPI(ExchangeAPI):
    """OKX API"""

    def __init__(self, symbol="BTC-USDT"):
        super().__init__("OKX", symbol)
        self.base_url = "https://www.okx.com"
        # OKX的symbol格式通常是 BTC-USDT

    def get_klines(self, interval="1h", limit=100):
        """获取OKX K线数据"""
        try:
            # OKX interval映射
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m',
                '30m': '30m', '1h': '1H', '4h': '4H',
                '1d': '1D', '1w': '1W'
            }
            okx_interval = interval_map.get(interval, '1H')

            url = f"{self.base_url}/api/v5/market/candles"
            params = {
                'instId': self.symbol,
                'bar': okx_interval,
                'limit': str(min(limit, 300))
            }
            response = requests.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data:
                    klines = data['data']
                    if klines:
                        df = pd.DataFrame(klines)
                        df = df.iloc[:, :6]  # 只取前6列
                        df.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume']

                        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                        df['close_time'] = df['open_time'] + pd.Timedelta(hours=1)
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = df[col].astype(float)

                        # 按时间排序
                        df = df.sort_values('open_time').reset_index(drop=True)
                        return df
        except Exception as e:
            print(f"  ❌ {self.name} API失败: {str(e)}")
        return None


class CoinGeckoAPI(ExchangeAPI):
    """CoinGecko API（价格聚合）"""

    def __init__(self, coin_id="bitcoin"):
        super().__init__("CoinGecko", "BTC")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coin_id = coin_id

    def get_klines(self, interval="1h", limit=100):
        """获取CoinGecko市场数据"""
        try:
            # CoinGecko获取价格数据
            url = f"{self.base_url}/coins/{self.coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': str(limit / 24),  # 转换为天数
                'interval': 'hourly' if interval == '1h' else 'daily'
            }
            response = requests.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                if data and 'prices' in data:
                    prices = data['prices'][-limit:]  # 取最后limit条
                    klines = []

                    for i, price in enumerate(prices):
                        timestamp = price[0]
                        price_value = price[1]

                        # 简化：只使用价格数据
                        kline = [
                            timestamp,
                            price_value,  # open
                            price_value,  # high
                            price_value,  # low
                            price_value,  # close
                            1,  # volume (CoinGecko不提供)
                            timestamp + 3600000,  # close_time
                            0,  # quote_volume
                            0,  # trades
                            0,  # taker_buy_base
                            0,  # taker_buy_quote
                            0
                        ]
                        klines.append(kline)

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
        except Exception as e:
            print(f"  ❌ {self.name} API失败: {str(e)}")
        return None


def get_data_from_multiple_exchanges(symbol="BTCUSDT", interval="1h", limit=100):
    """从多个交易所获取数据"""
    exchanges = [
        BinanceAPI(symbol),
        HuobiAPI(symbol),
        OKXAPI(symbol.replace("USDT", "-USDT")),
        CoinGeckoAPI("bitcoin")
    ]

    print(f"🌐 尝试从 {len(exchanges)} 个交易所获取数据...\n")

    for i, exchange in enumerate(exchanges, 1):
        print(f"[{i}/{len(exchanges)}] 尝试连接 {exchange.name} API...")
        df = exchange.get_klines(interval, limit)

        if df is not None and len(df) > 0:
            print(f"  ✅ {exchange.name} API成功！")
            print(f"  📅 数据时间: {df.iloc[-1]['close_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  📊 K线数量: {len(df)}\n")
            return df, exchange.name

    print(f"  ❌ 所有交易所API均无法连接\n")
    return None, None


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
    print("  🚀 缠论多智能体系统 - 多交易所API实时行情分析")
    print("  📊 支持平台: Binance、Huobi、OKX、CoinGecko")
    print("=" * 70 + "\n")

    print(f"🎯 分析标的: BTC/USDT")
    print(f"⏱️  分析周期: 1小时")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 从多个交易所获取数据
    df, source = get_data_from_multiple_exchanges("BTCUSDT", "1h", 100)

    if df is None:
        print("\n❌ 所有数据源均无法连接\n")
        print("💡 建议：")
        print("   1. 检查网络连接")
        print("   2. 确保VPN已开启（如果需要）")
        print("   3. 使用模拟数据分析：python analyze_btc_simple.py")
        print()

        # 如果所有API都失败，使用模拟数据
        print("\n📡 使用模拟数据展示分析流程...\n")
        from analyze_btc_simple import generate_mock_btc_data, calculate_rsi
        klines = generate_mock_btc_data(100, 65000)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'dif', 'dea', 'macd'
        ])
        df['open_time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = df['open_time'] + pd.Timedelta(hours=1)
        df = df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']]
        source = "模拟数据（网络限制）"

    # 计算指标
    print("📊 正在计算技术指标...")
    df = calculate_indicators(df)
    print("✅ 指标计算完成\n")

    # 显示分析结果
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 分析结果\n")

    latest = df.iloc[-1]
    price_change = (latest['close'] / df.iloc[-2]['close'] - 1) * 100

    # 显示数据源
    print(f"🌐 数据来源: {source}")
    print(f"📅 数据时间: {latest['close_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")

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
    print("🕐 更新时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()


if __name__ == "__main__":
    main()
