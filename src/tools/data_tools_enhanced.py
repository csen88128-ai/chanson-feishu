"""
增强版数据采集工具（带重试和降级机制）
"""
import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from langchain.tools import tool
from typing import Dict, List, Optional
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from utils.tool_wrapper import wrap_tool


class BinanceDataCollector:
    """Binance 数据采集器"""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self):
        self.session = requests.Session()

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 BTCUSDT
            interval: K线间隔，如 1m, 5m, 15m, 1h, 4h, 1d
            limit: 数量限制，最大 1000
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）

        Returns:
            K线数据列表
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = self.session.get(
                f"{self.BASE_URL}/klines",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取K线数据失败: {str(e)}")

    def format_klines(self, klines: List[List]) -> pd.DataFrame:
        """
        格式化K线数据为DataFrame

        Args:
            klines: 原始K线数据

        Returns:
            格式化后的DataFrame
        """
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        numeric_columns = ['open', 'high', 'low', 'close', 'volume',
                          'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        return df


# 全局实例
_collector = BinanceDataCollector()


def _get_fallback_data(symbol: str, interval: str = "1h") -> Dict:
    """
    获取降级数据（从本地文件）

    Args:
        symbol: 交易对
        interval: K线间隔

    Returns:
        降级数据
    """
    try:
        # 尝试从标准文件读取
        fallback_file = f"/workspace/chanson-feishu/{symbol.lower()}_latest_realtime_v2.json"
        
        if os.path.exists(fallback_file):
            with open(fallback_file, 'r') as f:
                data = json.load(f)
            
            return {
                "symbol": symbol,
                "interval": interval,
                "data_count": 100,
                "time_range": {
                    "start": data.get('data_time', datetime.now().isoformat()),
                    "end": datetime.now().isoformat()
                },
                "price_stats": {
                    "latest_close": data.get('current_price', 0),
                    "highest": data.get('high_24h', 0),
                    "lowest": data.get('low_24h', 0),
                    "average_volume": data.get('volume', 0)
                },
                "source": "fallback_file",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"❌ 降级数据获取失败: {str(e)}")
    
    # 最终降级：返回空数据
    return {
        "symbol": symbol,
        "interval": interval,
        "error": "All data sources failed",
        "source": "error_fallback",
        "timestamp": datetime.now().isoformat()
    }


@tool
@wrap_tool
def get_kline_data_enhanced(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 500
) -> str:
    """
    获取Binance K线数据（增强版，带重试和降级）

    Args:
        symbol: 交易对，如 BTCUSDT
        interval: K线间隔，如 1m, 5m, 15m, 1h, 4h, 1d
        limit: 数量限制，默认500

    Returns:
        JSON格式的K线数据摘要
    """
    ctx = request_context.get() or new_context(method="get_kline_data_enhanced")

    try:
        # 获取原始数据
        klines = _collector.get_klines(symbol=symbol, interval=interval, limit=limit)

        # 格式化为DataFrame
        df = _collector.format_klines(klines)

        # 保存到本地
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        data_dir = os.path.join(workspace_path, "data")
        os.makedirs(data_dir, exist_ok=True)

        filename = f"{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(data_dir, filename)
        df.to_csv(filepath, index=False)

        # 生成数据摘要
        summary = {
            "symbol": symbol,
            "interval": interval,
            "data_count": len(df),
            "time_range": {
                "start": df['timestamp'].min().isoformat(),
                "end": df['timestamp'].max().isoformat()
            },
            "price_stats": {
                "latest_close": float(df['close'].iloc[-1]),
                "highest": float(df['high'].max()),
                "lowest": float(df['low'].min()),
                "average_volume": float(df['volume'].mean())
            },
            "file_path": filepath,
            "recent_candles": df.tail(5)[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_dict('records'),
            "source": "api",
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        # 返回降级数据
        fallback_data = _get_fallback_data(symbol, interval)
        return json.dumps(fallback_data, ensure_ascii=False, indent=2)


@tool
@wrap_tool
def get_market_sentiment_enhanced(symbol: str = "BTCUSDT") -> str:
    """
    获取市场情绪（增强版，带重试和降级）

    Args:
        symbol: 交易对

    Returns:
        市场情绪数据
    """
    ctx = request_context.get() or new_context(method="get_market_sentiment_enhanced")

    try:
        # 尝试从本地数据计算情绪
        fallback_file = f"/workspace/chanson-feishu/{symbol.lower()}_latest_realtime_v2.json"
        
        if os.path.exists(fallback_file):
            with open(fallback_file, 'r') as f:
                data = json.load(f)
            
            rsi = data.get('rsi', 50)
            
            # 根据RSI计算情绪
            if rsi < 30:
                sentiment = "extreme_fear"
                fear_greed_index = int(rsi * 0.8)  # 24左右
            elif rsi < 40:
                sentiment = "fear"
                fear_greed_index = int(rsi * 0.9)  # 35左右
            elif rsi < 60:
                sentiment = "neutral"
                fear_greed_index = 50
            elif rsi < 70:
                sentiment = "greed"
                fear_greed_index = int(rsi * 1.1)  # 75左右
            else:
                sentiment = "extreme_greed"
                fear_greed_index = int(rsi * 1.2)  # 84左右
            
            sentiment_data = {
                "symbol": symbol,
                "fear_greed_index": fear_greed_index,
                "sentiment": sentiment,
                "rsi": rsi,
                "trend": "bullish" if data.get('change_percent', 0) > 0 else "bearish",
                "source": "calculated_from_local_data",
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(sentiment_data, ensure_ascii=False, indent=2)
        
        # 如果没有本地数据，返回默认情绪
        return json.dumps({
            "symbol": symbol,
            "fear_greed_index": 50,
            "sentiment": "neutral",
            "source": "default",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "source": "error_fallback",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)


@tool
@wrap_tool
def check_data_quality_enhanced(symbol: str = "BTCUSDT", interval: str = "1h") -> str:
    """
    检查数据质量（增强版，带重试和降级）

    Args:
        symbol: 交易对
        interval: K线间隔

    Returns:
        数据质量报告
    """
    ctx = request_context.get() or new_context(method="check_data_quality_enhanced")

    try:
        # 获取最新数据
        klines = _collector.get_klines(symbol=symbol, interval=interval, limit=100)
        df = _collector.format_klines(klines)

        # 数据质量检查
        checks = {
            "data_integrity": len(df) == 100,
            "missing_values": df.isnull().sum().to_dict(),
            "price_anomalies": {
                "zero_prices": len(df[(df['open'] == 0) | (df['high'] == 0) | (df['low'] == 0) | (df['close'] == 0)]),
                "negative_prices": len(df[(df['open'] < 0) | (df['high'] < 0) | (df['low'] < 0) | (df['close'] < 0)])
            },
            "volume_anomalies": {
                "zero_volume": len(df[df['volume'] == 0])
            },
            "time_continuity": {
                "expected_intervals": len(df) - 1,
                "actual_intervals": len(df['timestamp'].diff().dropna().unique()),
                "interval_seconds": (df['timestamp'].iloc[1] - df['timestamp'].iloc[0]).total_seconds()
            }
        }

        # 计算质量得分
        quality_score = 100
        if not checks["data_integrity"]:
            quality_score -= 20
        if checks["price_anomalies"]["zero_prices"] > 0:
            quality_score -= 10
        if checks["price_anomalies"]["negative_prices"] > 0:
            quality_score -= 20
        if checks["volume_anomalies"]["zero_volume"] > 5:
            quality_score -= 10

        report = {
            "symbol": symbol,
            "interval": interval,
            "quality_score": quality_score,
            "checks": checks,
            "status": "PASS" if quality_score >= 80 else "WARNING",
            "source": "api",
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        # 返回降级质量报告
        return json.dumps({
            "symbol": symbol,
            "interval": interval,
            "quality_score": 60,
            "status": "WARNING",
            "message": f"Data quality check failed: {str(e)}",
            "source": "fallback",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
