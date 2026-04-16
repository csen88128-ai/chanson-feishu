"""
增强版多级别K线数据获取脚本
支持多级别（1h+4h+1d）获取，总计500根K线
"""
import requests
import pandas as pd
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class MultiLevelDataCollector:
    """多级别数据采集器"""

    # API配置
    APIS = {
        "huobi": {
            "base_url": "https://api.huobi.pro",
            "endpoints": {
                "kline": "/market/history/kline"
            }
        },
        "binance": {
            "base_url": "https://api.binance.com",
            "endpoints": {
                "kline": "/api/v3/klines"
            }
        },
        "okx": {
            "base_url": "https://www.okx.com",
            "endpoints": {
                "kline": "/api/v5/market/candles"
            }
        },
        "coingecko": {
            "base_url": "https://api.coingecko.com",
            "endpoints": {
                "kline": "/api/v3/coins/markets/ohlc"
            }
        }
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0'
        })

    def get_huobi_klines(self, symbol: str, interval: str, limit: int) -> Optional[List[List]]:
        """
        获取Huobi K线数据

        Args:
            symbol: 交易对（如btcusdt）
            interval: 周期（1min, 5min, 15min, 30min, 60min, 4h, 1day, 1week, 1mon, 1year）
            limit: 数量限制（最大2000）

        Returns:
            K线数据列表
        """
        api = self.APIS["huobi"]
        url = f"{api['base_url']}{api['endpoints']['kline']}"

        params = {
            "symbol": symbol.lower(),
            "period": interval,
            "size": min(limit, 2000)
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'ok' and 'data' in data:
                # Huobi返回的数据是倒序的，需要反转
                klines = sorted(data['data'], key=lambda x: x['id'])
                return [[
                    k['id'],  # timestamp
                    k['open'],
                    k['close'],
                    k['high'],
                    k['low'],
                    k['vol'],  # volume
                    k['amount']  # quote volume
                ] for k in klines]
            else:
                print(f"  ❌ Huobi API返回错误: {data.get('err-msg', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"  ❌ Huobi API失败: {str(e)}")
            return None

    def get_binance_klines(self, symbol: str, interval: str, limit: int) -> Optional[List[List]]:
        """
        获取Binance K线数据

        Args:
            symbol: 交易对（如BTCUSDT）
            interval: 周期（1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M）
            limit: 数量限制（最大1000）

        Returns:
            K线数据列表
        """
        api = self.APIS["binance"]
        url = f"{api['base_url']}{api['endpoints']['kline']}"

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000)
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ❌ Binance API失败: {str(e)}")
            return None

    def get_okx_klines(self, symbol: str, interval: str, limit: int) -> Optional[List[List]]:
        """
        获取OKX K线数据

        Args:
            symbol: 交易对（如BTC-USDT）
            interval: 周期（1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W, 1M）
            limit: 数量限制（最大300）

        Returns:
            K线数据列表
        """
        api = self.APIS["okx"]
        url = f"{api['base_url']}{api['endpoints']['kline']}"

        params = {
            "instId": f"{symbol.upper().replace('USDT', '-USDT')}",
            "bar": interval,
            "limit": str(min(limit, 300))
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == '0' and 'data' in data:
                # OKX返回的数据是倒序的，需要反转
                klines = sorted(data['data'], key=lambda x: int(x[0]))
                return [[
                    int(k[0]),  # timestamp
                    float(k[1]),  # open
                    float(k[2]),  # high
                    float(k[3]),  # low
                    float(k[4]),  # close
                    float(k[5]),  # volume
                    float(k[6]) if len(k) > 6 else 0  # volumeCcy
                ] for k in klines]
            else:
                print(f"  ❌ OKX API返回错误: {data.get('msg', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"  ❌ OKX API失败: {str(e)}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算技术指标

        Args:
            df: K线数据DataFrame

        Returns:
            技术指标字典
        """
        indicators = {}

        # 移动平均线
        indicators['ma5'] = df['close'].rolling(window=5).mean().iloc[-1]
        indicators['ma10'] = df['close'].rolling(window=10).mean().iloc[-1]
        indicators['ma20'] = df['close'].rolling(window=20).mean().iloc[-1]
        indicators['ma30'] = df['close'].rolling(window=30).mean().iloc[-1]
        indicators['ma60'] = df['close'].rolling(window=60).mean().iloc[-1]

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = rsi.iloc[-1]

        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd = 2 * (dif - dea)

        indicators['macd'] = macd.iloc[-1]
        indicators['macd_dif'] = dif.iloc[-1]
        indicators['macd_dea'] = dea.iloc[-1]

        # 布林带
        boll_mid = df['close'].rolling(window=20).mean()
        boll_std = df['close'].rolling(window=20).std()
        indicators['boll_upper'] = (boll_mid + 2 * boll_std).iloc[-1]
        indicators['boll_mid'] = boll_mid.iloc[-1]
        indicators['boll_lower'] = (boll_mid - 2 * boll_std).iloc[-1]

        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        indicators['atr'] = true_range.rolling(window=14).mean().iloc[-1]

        return indicators

    def get_multi_level_data(
        self,
        symbol: str = "BTCUSDT",
        intervals: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        获取多级别K线数据

        Args:
            symbol: 交易对
            intervals: 周期列表，默认['1h', '4h', '1d']

        Returns:
            多级别数据字典 {interval: DataFrame}
        """
        if intervals is None:
            intervals = ['1h', '4h', '1d']

        data = {}
        interval_mapping = {
            '1h': '60min',
            '4h': '4h',
            '1d': '1day'
        }

        print(f"\n🌐 尝试从多个交易所获取多级别数据...")
        print(f"🎯 交易对: {symbol}")
        print(f"📊 级别: {', '.join(intervals)}\n")

        for interval in intervals:
            print(f"📈 获取 {interval} 级别数据...")

            klines = None

            # 尝试Huobi
            if not klines:
                print(f"  [1/4] 尝试连接 Huobi API ({interval})...")
                klines = self.get_huobi_klines(symbol, interval_mapping.get(interval, interval), 250)

            # 尝试Binance
            if not klines:
                print(f"  [2/4] 尝试连接 Binance API ({interval})...")
                klines = self.get_binance_klines(symbol, interval, 250)

            # 尝试OKX
            if not klines:
                print(f"  [3/4] 尝试连接 OKX API ({interval})...")
                klines = self.get_okx_klines(symbol, interval.upper(), 250)

            if klines:
                # 转换为DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume'
                ])

                # 转换数据类型
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
                    df[col] = pd.to_numeric(df[col])

                # 按时间排序
                df = df.sort_values('timestamp').reset_index(drop=True)

                data[interval] = df

                print(f"  ✅ {interval} 数据获取成功！")
                print(f"     📅 数据范围: {df['timestamp'].min().strftime('%Y-%m-%d %H:%M')} 至 {df['timestamp'].max().strftime('%Y-%m-%d %H:%M')}")
                print(f"     📊 K线数量: {len(df)}")
                print()
            else:
                print(f"  ❌ {interval} 数据获取失败\n")

        return data

    def format_multi_level_data(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """
        格式化多级别数据

        Args:
            data: 多级别数据字典

        Returns:
            格式化后的数据
        """
        formatted = {
            'symbol': 'BTCUSDT',
            'levels': {},
            'update_time': datetime.now().isoformat(),
            'source': 'multi_exchange'
        }

        for interval, df in data.items():
            # 计算指标
            indicators = self.calculate_indicators(df)

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            level_data = {
                'interval': interval,
                'klines_count': len(df),
                'data_range': {
                    'start': df['timestamp'].min().isoformat(),
                    'end': df['timestamp'].max().isoformat()
                },
                'price': {
                    'current': float(latest['close']),
                    'open': float(latest['open']),
                    'high': float(latest['high']),
                    'low': float(latest['low']),
                    'change': float(latest['close'] - prev['close']),
                    'change_percent': float((latest['close'] - prev['close']) / prev['close'] * 100)
                },
                'volume': float(latest['volume']),
                'indicators': {
                    'ma5': float(indicators['ma5']),
                    'ma10': float(indicators['ma10']),
                    'ma20': float(indicators['ma20']),
                    'ma30': float(indicators['ma30']),
                    'ma60': float(indicators['ma60']),
                    'rsi': float(indicators['rsi']),
                    'macd': float(indicators['macd']),
                    'macd_dif': float(indicators['macd_dif']),
                    'macd_dea': float(indicators['macd_dea']),
                    'boll_upper': float(indicators['boll_upper']),
                    'boll_mid': float(indicators['boll_mid']),
                    'boll_lower': float(indicators['boll_lower']),
                    'atr': float(indicators['atr'])
                }
            }

            formatted['levels'][interval] = level_data

        # 计算总K线数
        formatted['total_klines'] = sum(len(df) for df in data.values())

        return formatted

    def analyze_signals(self, formatted_data: Dict) -> Dict:
        """
        分析多级别信号

        Args:
            formatted_data: 格式化后的数据

        Returns:
            信号分析结果
        """
        signals = {
            'overall_trend': 'neutral',
            'level_signals': {},
            'resonance': False,
            'strength': 0
        }

        for interval, level_data in formatted_data['levels'].items():
            price = level_data['price']
            ind = level_data['indicators']

            # 判断趋势
            if price['current'] > ind['ma5'] > ind['ma20'] > ind['ma60']:
                trend = 'bullish'
            elif price['current'] < ind['ma5'] < ind['ma20'] < ind['ma60']:
                trend = 'bearish'
            else:
                trend = 'neutral'

            # 判断RSI
            if ind['rsi'] < 30:
                rsi_signal = 'oversold'
            elif ind['rsi'] > 70:
                rsi_signal = 'overbought'
            else:
                rsi_signal = 'neutral'

            # 判断MACD
            if ind['macd_dif'] > ind['macd_dea'] and ind['macd'] > 0:
                macd_signal = 'bullish_golden'
            elif ind['macd_dif'] > ind['macd_dea'] and ind['macd'] < 0:
                macd_signal = 'bullish_rebound'
            elif ind['macd_dif'] < ind['macd_dea'] and ind['macd'] > 0:
                macd_signal = 'bearish_divergence'
            else:
                macd_signal = 'bearish_death'

            level_signals = {
                'trend': trend,
                'rsi_signal': rsi_signal,
                'macd_signal': macd_signal
            }

            signals['level_signals'][interval] = level_signals

        # 判断共振
        trends = [s['trend'] for s in signals['level_signals'].values()]
        signals['resonance'] = len(set(trends)) == 1 and trends[0] != 'neutral'

        if signals['resonance']:
            signals['overall_trend'] = trends[0]
            signals['strength'] = len(trends)
        else:
            # 根据权重判断
            if '1h' in signals['level_signals']:
                signals['overall_trend'] = signals['level_signals']['1h']['trend']

        return signals


def main():
    """主函数"""
    print("=" * 80)
    print("  🚀 缠论多智能体系统 - 多级别K线数据获取（增强版）")
    print("  📊 支持级别: 1h、4h、1d")
    print("=" * 80)

    # 创建采集器
    collector = MultiLevelDataCollector()

    # 获取多级别数据
    data = collector.get_multi_level_data(
        symbol="BTCUSDT",
        intervals=['1h', '4h', '1d']
    )

    if not data:
        print("\n❌ 所有级别数据获取失败")
        return

    # 格式化数据
    formatted = collector.format_multi_level_data(data)

    # 分析信号
    signals = collector.analyze_signals(formatted)

    # 打印结果
    print("=" * 80)
    print("  📊 分析结果")
    print("=" * 80)

    print(f"\n🌐 数据源: {formatted['source']}")
    print(f"📊 总K线数: {formatted['total_klines']}根")
    print(f"🕐 更新时间: {formatted['update_time']}")

    print(f"\n💰 价格信息:")
    for interval, level_data in formatted['levels'].items():
        price = level_data['price']
        print(f"\n  {interval} 级别:")
        print(f"     当前价格: ${price['current']:,.2f}")
        print(f"     涨跌幅: {price['change_percent']:+.2f}%")
        print(f"     最高价: ${price['high']:,.2f}")
        print(f"     最低价: ${price['low']:,.2f}")
        volume = price.get('volume', 0)
        if volume:
            print(f"     成交量: {volume:,.0f}")
        else:
            print(f"     成交量: N/A")

    print(f"\n📈 技术指标:")
    for interval, level_data in formatted['levels'].items():
        ind = level_data['indicators']
        print(f"\n  {interval} 级别:")
        ma5 = ind.get('ma5', 0)
        ma20 = ind.get('ma20', 0)
        ma60 = ind.get('ma60', 0)
        rsi = ind.get('rsi', 0)
        macd = ind.get('macd', 0)

        if ma5 and not pd.isna(ma5):
            print(f"     MA5:  ${ma5:,.2f}")
        if ma20 and not pd.isna(ma20):
            print(f"     MA20: ${ma20:,.2f}")
        if ma60 and not pd.isna(ma60):
            print(f"     MA60: ${ma60:,.2f}")
        if rsi and not pd.isna(rsi):
            print(f"     RSI:  {rsi:.2f}")
        if macd and not pd.isna(macd):
            print(f"     MACD: {macd:.2f}")

    print(f"\n🎯 信号分析:")
    print(f"  整体趋势: {signals['overall_trend']}")
    print(f"  多级共振: {'✅ 是' if signals['resonance'] else '❌ 否'}")
    if signals['resonance']:
        print(f"  共振强度: {signals['strength']}/3")

    print(f"\n  各级别信号:")
    for interval, level_signal in signals['level_signals'].items():
        print(f"  {interval}:")
        print(f"     趋势: {level_signal['trend']}")
        print(f"     RSI:  {level_signal['rsi_signal']}")
        print(f"     MACD: {level_signal['macd_signal']}")

    # 保存数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/workspace/chanson-feishu/btc_multi_level_data_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'data': formatted,
            'signals': signals
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 数据已保存: {output_file}")

    # 同时保存到默认文件
    with open('/workspace/chanson-feishu/btc_multi_level_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'data': formatted,
            'signals': signals
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ 默认文件已更新: btc_multi_level_data.json\n")


if __name__ == "__main__":
    main()
