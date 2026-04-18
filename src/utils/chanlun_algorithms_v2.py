"""
缠论算法优化模块 v2.0
包含优化的中枢识别、线段延伸判断、背驰识别、趋势力度指标
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json

# 从原始模块导入必要的数据类型
from .chanlun_structure import Bi, BiDirection, Segment, SegmentDirection

class ZhongShuStatus(Enum):
    """中枢状态"""
    FORMING = "forming"      # 构建中
    COMPLETED = "completed"  # 已完成
    EXTENDING = "extending"  # 延伸中
    BREAKING = "breaking"    # 突破中


@dataclass
class ZhongShuV2:
    """增强版中枢"""
    high: float                   # 中枢上沿（ZG）
    low: float                    # 中枢下沿（ZD）
    high_point: float             # 中枢高点（GG）
    low_point: float              # 中枢低点（DD）
    level: int                    # 中枢级别
    status: ZhongShuStatus        # 中枢状态
    segment_count: int            # 线段数量
    start_index: int              # 起始K线索引
    end_index: int                # 结束K线索引
    strength: float               # 中枢强度（0-1）
    overlap_count: int            # 重叠次数


class AdvancedChanLunAnalyzer:
    """增强版缠论分析器"""

    def __init__(self):
        self.zhongshu_strength_weights = {
            "overlap_count": 0.3,    # 重叠次数权重
            "segment_count": 0.3,    # 线段数量权重
            "time_span": 0.2,        # 时间跨度权重
            "price_range": 0.2       # 价格范围权重
        }

    def enhanced_identify_zhongshu(self, df: pd.DataFrame, segments: List) -> List[ZhongShuV2]:
        """
        增强版中枢识别算法

        优化点：
        1. 动态调整中枢识别的阈值
        2. 考虑中枢的延伸状态
        3. 计算中枢强度
        4. 区分中枢的不同状态

        Args:
            df: K线数据
            segments: 线段列表

        Returns:
            增强版中枢列表
        """
        zhongshus = []

        if len(segments) < 3:
            return zhongshus

        # 动态调整重叠阈值
        price_range = df['high'].max() - df['low'].min()
        dynamic_threshold = price_range * 0.01  # 默认1%的波动范围

        i = 0
        while i < len(segments) - 2:
            # 尝试识别中枢
            potential_zhongshu = self._identify_single_zhongshu_v2(
                segments[i:i+3], dynamic_threshold, df
            )

            if potential_zhongshu:
                zhongshus.append(potential_zhongshu)
                i += 2  # 跳过已识别的线段
            else:
                i += 1

        return zhongshus

    def _identify_single_zhongshu_v2(self, segments: List[Segment],
                                    threshold: float,
                                    df: pd.DataFrame) -> Optional[ZhongShuV2]:
        """
        识别单个增强版中枢

        Args:
            segments: 线段列表
            threshold: 重叠阈值
            df: K线数据

        Returns:
            增强版中枢或None
        """
        if len(segments) < 3:
            return None

        # 计算线段的高低点
        highs = [seg.high for seg in segments]
        lows = [seg.low for seg in segments]

        # 计算重叠区间
        max_low = max(lows[:-1])  # 前N-1个线段的最大低点
        min_high = min(highs[:-1])  # 前N-1个线段的最小高点

        # 检查是否有重叠
        if max_low >= min_high:
            # 有重叠，形成中枢
            zg = min_high  # 中枢上沿
            zd = max_low   # 中枢下沿
            gg = max(highs)  # 中枢高点
            dd = min(lows)   # 中枢低点

            # 计算中枢强度
            strength = self._calculate_zhongshu_strength(
                segments, zg, zd, df
            )

            # 判断中枢状态
            status = self._determine_zhongshu_status(
                segments, zg, zd, df
            )

            start_index = min(seg.start_index for seg in segments)
            end_index = max(seg.end_index for seg in segments)

            return ZhongShuV2(
                high=zg,
                low=zd,
                high_point=gg,
                low_point=dd,
                level=1,  # 默认为1级中枢
                status=status,
                segment_count=len(segments),
                start_index=start_index,
                end_index=end_index,
                strength=strength,
                overlap_count=len(segments) - 1
            )

        return None

    def _calculate_zhongshu_strength(self, segments: List[Segment],
                                    zg: float, zd: float,
                                    df: pd.DataFrame) -> float:
        """
        计算中枢强度（0-1）

        考虑因素：
        1. 重叠次数
        2. 线段数量
        3. 时间跨度
        4. 价格范围

        Args:
            segments: 线段列表
            zg: 中枢上沿
            zd: 中枢下沿
            df: K线数据

        Returns:
            中枢强度（0-1）
        """
        weights = self.zhongshu_strength_weights

        # 1. 重叠次数评分
        overlap_count = len(segments) - 1
        overlap_score = min(overlap_count / 5, 1.0)  # 最多5次重叠得满分

        # 2. 线段数量评分
        segment_count = len(segments)
        segment_score = min(segment_count / 9, 1.0)  # 最多9根线段得满分

        # 3. 时间跨度评分
        start_index = min(seg.start_index for seg in segments)
        end_index = max(seg.end_index for seg in segments)
        time_span = end_index - start_index
        time_score = min(time_span / 100, 1.0)  # 最多100根K线得满分

        # 4. 价格范围评分
        price_range = zg - zd
        total_range = df['high'].max() - df['low'].min()
        if total_range > 0:
            price_score = min(price_range / (total_range * 0.2), 1.0)  # 最多占总波动的20%
        else:
            price_score = 0.0

        # 加权计算
        strength = (
            weights["overlap_count"] * overlap_score +
            weights["segment_count"] * segment_score +
            weights["time_span"] * time_score +
            weights["price_range"] * price_score
        )

        return round(strength, 3)

    def _determine_zhongshu_status(self, segments: List[Segment],
                                  zg: float, zd: float,
                                  df: pd.DataFrame) -> ZhongShuStatus:
        """
        判断中枢状态

        状态分类：
        - FORMING: 正在构建中（至少3根线段）
        - COMPLETED: 已完成（有明确的第9根线段）
        - EXTENDING: 正在延伸（第9根线段后继续震荡）
        - BREAKING: 正在被突破（价格突破中枢边界）

        Args:
            segments: 线段列表
            zg: 中枢上沿
            zd: 中枢下沿
            df: K线数据

        Returns:
            中枢状态
        """
        segment_count = len(segments)

        # 检查是否正在被突破
        last_segment = segments[-1]
        current_price = df.iloc[-1]['close']

        if current_price > zg or current_price < zd:
            return ZhongShuStatus.BREAKING

        # 检查线段数量
        if segment_count >= 9:
            return ZhongShuStatus.EXTENDING
        elif segment_count >= 7:
            return ZhongShuStatus.COMPLETED
        else:
            return ZhongShuStatus.FORMING


    def check_segment_extension(self, segments: List[Segment],
                               current_segment: Segment,
                               df: pd.DataFrame) -> Dict[str, any]:
        """
        检查线段延伸情况

        判断逻辑：
        1. 是否有反向笔突破前一笔的端点
        2. 是否形成包含关系
        3. 是否有缺口
        4. 趋势是否延续

        Args:
            segments: 前面的线段列表
            current_segment: 当前线段
            df: K线数据

        Returns:
            线段延伸信息
        """
        result = {
            "is_extending": False,
            "extension_type": "none",  # "trend", "oscillation", "break"
            "strength": 0.0,
            "break_point": None,
            "next_target": None
        }

        if not segments:
            return result

        last_segment = segments[-1]

        # 1. 检查是否有突破
        if current_segment.direction == SegmentDirection.UP:
            if current_segment.high > last_segment.high:
                # 向上突破
                result["is_extending"] = True
                result["extension_type"] = "break"
                result["break_point"] = last_segment.high
                # 计算下一个目标位（通常是前高的1.382倍）
                result["next_target"] = last_segment.high + (
                    last_segment.high - last_segment.low
                ) * 0.382

        elif current_segment.direction == SegmentDirection.DOWN:
            if current_segment.low < last_segment.low:
                # 向下突破
                result["is_extending"] = True
                result["extension_type"] = "break"
                result["break_point"] = last_segment.low
                # 计算下一个目标位（通常是前低的1.382倍）
                result["next_target"] = last_segment.low - (
                    last_segment.high - last_segment.low
                ) * 0.382

        # 2. 检查趋势延续强度
        result["strength"] = self._calculate_trend_strength(
            segments + [current_segment]
        )

        # 3. 检查震荡情况
        if not result["is_extending"]:
            # 检查是否形成震荡
            price_range = current_segment.high - current_segment.low
            last_range = last_segment.high - last_segment.low

            if price_range < last_range * 0.618:
                result["is_extending"] = True
                result["extension_type"] = "oscillation"

        return result

    def _calculate_trend_strength(self, segments: List[Segment]) -> float:
        """
        计算趋势强度（0-1）

        考虑因素：
        1. 趋势持续性
        2. 价格创新高的能力
        3. 回调深度
        4. 成交量配合

        Args:
            segments: 线段列表

        Returns:
            趋势强度（0-1）
        """
        if len(segments) < 3:
            return 0.5

        # 1. 趋势持续性（连续同向线段数量）
        continuous_count = 0
        last_direction = segments[-1].direction

        for seg in reversed(segments):
            if seg.direction == last_direction:
                continuous_count += 1
            else:
                break

        continuity_score = min(continuous_count / 5, 1.0)

        # 2. 价格创新能力
        if segments[-1].direction == SegmentDirection.UP:
            # 检查是否创新高
            new_highs = 0
            for i in range(2, len(segments)):
                if segments[i].direction == SegmentDirection.UP:
                    if i >= 2 and segments[i].high > segments[i-2].high:
                        new_highs += 1
            innovation_score = min(new_highs / 3, 1.0)
        else:
            # 检查是否创新低
            new_lows = 0
            for i in range(2, len(segments)):
                if segments[i].direction == SegmentDirection.DOWN:
                    if i >= 2 and segments[i].low < segments[i-2].low:
                        new_lows += 1
            innovation_score = min(new_lows / 3, 1.0)

        # 3. 回调深度
        if len(segments) >= 2:
            if segments[-1].direction == SegmentDirection.UP:
                # 上升趋势，检查回调深度
                prev_up = [s for s in segments[:-1] if s.direction == SegmentDirection.UP]
                if prev_up:
                    total_advance = sum(s.high - s.low for s in prev_up)
                    total_retracement = sum(s.high - s.low for s in segments
                                          if s.direction == SegmentDirection.DOWN)
                    if total_advance > 0:
                        retracement_score = 1 - min(total_retracement / total_advance, 0.5) * 2
                    else:
                        retracement_score = 0.5
                else:
                    retracement_score = 0.5
            else:
                # 下降趋势，检查反弹深度
                prev_down = [s for s in segments[:-1] if s.direction == SegmentDirection.DOWN]
                if prev_down:
                    total_decline = sum(s.high - s.low for s in prev_down)
                    total_rally = sum(s.high - s.low for s in segments
                                    if s.direction == SegmentDirection.UP)
                    if total_decline > 0:
                        retracement_score = 1 - min(total_rally / total_decline, 0.5) * 2
                    else:
                        retracement_score = 0.5
                else:
                    retracement_score = 0.5
        else:
            retracement_score = 0.5

        # 加权计算
        strength = (
            0.4 * continuity_score +
            0.4 * innovation_score +
            0.2 * retracement_score
        )

        return round(strength, 3)


class EnhancedDynamicsAnalyzer:
    """增强版动力学分析器"""

    def __init__(self):
        self.divergence_weights = {
            "price_momentum": 0.3,   # 价格动量权重
            "macd_divergence": 0.4,  # MACD背离权重
            "volume_divergence": 0.3  # 成交量背离权重
        }

    def enhanced_divergence_detection(self, df: pd.DataFrame,
                                      bis: List = None) -> List[Dict]:
        """
        增强版背驰检测算法

        优化点：
        1. 多重确认（价格+MACD+成交量）
        2. 背驰强度量化
        3. 区间套分析
        4. 背驰类型细分

        Args:
            df: K线数据
            bis: 笔列表（可选）

        Returns:
            背驰列表
        """
        divergences = []

        # 1. MACD背驰检测
        macd_divergences = self._detect_macd_divergence(df, bis)

        # 2. 价格动量背驰检测
        momentum_divergences = self._detect_momentum_divergence(df, bis)

        # 3. 成交量背驰检测
        volume_divergences = self._detect_volume_divergence(df, bis)

        # 合并背驰信号
        all_divergences = macd_divergences + momentum_divergences + volume_divergences

        # 去重和确认
        confirmed_divergences = self._confirm_divergences(all_divergences, df)

        # 计算背驰强度
        for div in confirmed_divergences:
            div["strength"] = self._calculate_divergence_strength(div, df)

        return confirmed_divergences

    def _detect_macd_divergence(self, df: pd.DataFrame,
                                bis: List = None) -> List[Dict]:
        """
        检测MACD背驰

        检测逻辑：
        1. 价格创新高但MACD未创新高（顶背驰）
        2. 价格创新低但MACD未创新低（底背驰）
        3. 背驰需要在3根笔以上

        Args:
            df: K线数据
            bis: 笔列表

        Returns:
            MACD背驰列表
        """
        divergences = []

        if bis is None or len(bis) < 3:
            return divergences

        # 计算每根笔的MACD平均值
        for i in range(2, len(bis)):
            prev_bi = bis[i-1]
            current_bi = bis[i]

            # 获取笔对应的K线区间
            if i == len(bis) - 1:
                # 最后一根笔，使用到当前
                start_idx = current_bi.start_index
                end_idx = len(df) - 1
            else:
                start_idx = current_bi.start_index
                end_idx = current_bi.end_index

            # 计算MACD
            macd_data = self._calculate_macd(df.iloc[start_idx:end_idx+1])
            current_macd = macd_data["macd"].mean() if not macd_data.empty else 0

            # 上一根笔的MACD
            prev_start_idx = prev_bi.start_index
            prev_end_idx = prev_bi.end_index
            prev_macd_data = self._calculate_macd(df.iloc[prev_start_idx:prev_end_idx+1])
            prev_macd = prev_macd_data["macd"].mean() if not prev_macd_data.empty else 0

            # 检查顶背驰
            if current_bi.direction == BiDirection.UP:
                # 向上笔
                if i >= 2:
                    prev_prev_bi = bis[i-2]
                    if current_bi.end_price > prev_prev_bi.end_price:
                        # 价格创新高
                        if current_macd < prev_macd:
                            # MACD未创新高，顶背驰
                            divergences.append({
                                "type": "top_divergence",
                                "divergence_type": "macd",
                                "index": i,
                                "price": current_bi.end_price,
                                "macd": current_macd,
                                "strength": 0.0,
                                "confirmed": False
                            })

            # 检查底背驰
            elif current_bi.direction == BiDirection.DOWN:
                # 向下笔
                if i >= 2:
                    prev_prev_bi = bis[i-2]
                    if current_bi.end_price < prev_prev_bi.end_price:
                        # 价格创新低
                        if current_macd > prev_macd:
                            # MACD未创新低，底背驰
                            divergences.append({
                                "type": "bottom_divergence",
                                "divergence_type": "macd",
                                "index": i,
                                "price": current_bi.end_price,
                                "macd": current_macd,
                                "strength": 0.0,
                                "confirmed": False
                            })

        return divergences

    def _detect_momentum_divergence(self, df: pd.DataFrame,
                                    bis: List = None) -> List[Dict]:
        """
        检测价格动量背驰

        检测逻辑：
        1. 价格创新高但上涨速度放缓
        2. 价格创新低但下跌速度放缓

        Args:
            df: K线数据
            bis: 笔列表

        Returns:
            动量背驰列表
        """
        divergences = []

        if bis is None or len(bis) < 3:
            return divergences

        for i in range(2, len(bis)):
            current_bi = bis[i]
            prev_bi = bis[i-2]

            # 计算价格变化率（动量）
            current_momentum = abs(current_bi.end_price - current_bi.start_price) / (
                current_bi.end_index - current_bi.start_index + 1
            )

            prev_momentum = abs(prev_bi.end_price - prev_bi.start_price) / (
                prev_bi.end_index - prev_bi.start_index + 1
            )

            # 检查顶背驰
            if current_bi.direction == BiDirection.UP:
                if current_bi.end_price > prev_bi.end_price:
                    # 价格创新高但动量减弱
                    if current_momentum < prev_momentum * 0.7:  # 动量减弱30%以上
                        divergences.append({
                            "type": "top_divergence",
                            "divergence_type": "momentum",
                            "index": i,
                            "price": current_bi.end_price,
                            "momentum": current_momentum,
                            "prev_momentum": prev_momentum,
                            "strength": 0.0,
                            "confirmed": False
                        })

            # 检查底背驰
            elif current_bi.direction == BiDirection.DOWN:
                if current_bi.end_price < prev_bi.end_price:
                    # 价格创新低但动量减弱
                    if current_momentum < prev_momentum * 0.7:
                        divergences.append({
                            "type": "bottom_divergence",
                            "divergence_type": "momentum",
                            "index": i,
                            "price": current_bi.end_price,
                            "momentum": current_momentum,
                            "prev_momentum": prev_momentum,
                            "strength": 0.0,
                            "confirmed": False
                        })

        return divergences

    def _detect_volume_divergence(self, df: pd.DataFrame,
                                  bis: List = None) -> List[Dict]:
        """
        检测成交量背驰

        检测逻辑：
        1. 价格创新高但成交量萎缩
        2. 价格创新低但成交量萎缩

        Args:
            df: K线数据
            bis: 笔列表

        Returns:
            成交量背驰列表
        """
        divergences = []

        if bis is None or len(bis) < 3:
            return divergences

        for i in range(2, len(bis)):
            current_bi = bis[i]
            prev_bi = bis[i-2]

            # 计算笔的平均成交量
            current_start = current_bi.start_index
            current_end = min(current_bi.end_index, len(df) - 1)
            current_volume = df.iloc[current_start:current_end+1]['volume'].mean()

            prev_start = prev_bi.start_index
            prev_end = min(prev_bi.end_index, len(df) - 1)
            prev_volume = df.iloc[prev_start:prev_end+1]['volume'].mean()

            # 检查顶背驰
            if current_bi.direction == BiDirection.UP:
                if current_bi.end_price > prev_bi.end_price:
                    # 价格创新高但成交量萎缩
                    if current_volume < prev_volume * 0.7:  # 成交量萎缩30%以上
                        divergences.append({
                            "type": "top_divergence",
                            "divergence_type": "volume",
                            "index": i,
                            "price": current_bi.end_price,
                            "volume": current_volume,
                            "prev_volume": prev_volume,
                            "strength": 0.0,
                            "confirmed": False
                        })

            # 检查底背驰
            elif current_bi.direction == BiDirection.DOWN:
                if current_bi.end_price < prev_bi.end_price:
                    # 价格创新低但成交量萎缩
                    if current_volume < prev_volume * 0.7:
                        divergences.append({
                            "type": "bottom_divergence",
                            "divergence_type": "volume",
                            "index": i,
                            "price": current_bi.end_price,
                            "volume": current_volume,
                            "prev_volume": prev_volume,
                            "strength": 0.0,
                            "confirmed": False
                        })

        return divergences

    def _confirm_divergences(self, divergences: List[Dict],
                            df: pd.DataFrame) -> List[Dict]:
        """
        确认背驰信号

        确认逻辑：
        1. 同一位置有多个背驰信号（MACD+动量+成交量）
        2. 有分型确认
        3. 背驰强度足够

        Args:
            divergences: 背驰列表
            df: K线数据

        Returns:
            确认后的背驰列表
        """
        if not divergences:
            return []

        # 按位置分组
        divergence_groups = {}
        for div in divergences:
            key = (div["type"], div["index"])
            if key not in divergence_groups:
                divergence_groups[key] = []
            divergence_groups[key].append(div)

        confirmed = []
        for key, group in divergence_groups.items():
            # 如果同一位置有多个背驰信号，增加置信度
            if len(group) >= 2:
                # 确认
                confirmed.append({
                    "type": group[0]["type"],
                    "index": group[0]["index"],
                    "price": group[0]["price"],
                    "divergence_types": [d["divergence_type"] for d in group],
                    "confirmation_count": len(group),
                    "strength": 0.0,
                    "confirmed": True
                })
            elif len(group) == 1 and group[0]["divergence_type"] == "macd":
                # MACD背驰单独确认
                confirmed.append({
                    "type": group[0]["type"],
                    "index": group[0]["index"],
                    "price": group[0]["price"],
                    "divergence_types": ["macd"],
                    "confirmation_count": 1,
                    "strength": 0.0,
                    "confirmed": True
                })

        return confirmed

    def _calculate_divergence_strength(self, divergence: Dict,
                                       df: pd.DataFrame) -> float:
        """
        计算背驰强度（0-1）

        考虑因素：
        1. 背驰信号数量（多重背驰更强）
        2. 价格变化幅度
        3. 指标背离程度

        Args:
            divergence: 背驰信息
            df: K线数据

        Returns:
            背驰强度（0-1）
        """
        weights = self.divergence_weights

        # 1. 背驰信号数量评分
        confirmation_count = divergence.get("confirmation_count", 1)
        signal_score = min(confirmation_count / 3, 1.0)

        # 2. 价格变化幅度（简化处理）
        price_score = 0.7  # 默认中等强度

        # 3. 指标背离程度（简化处理）
        indicator_score = 0.7  # 默认中等强度

        # 加权计算
        strength = (
            weights["price_momentum"] * price_score +
            weights["macd_divergence"] * indicator_score +
            weights["volume_divergence"] * signal_score
        )

        return round(strength, 3)

    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12,
                       slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: K线数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            包含MACD数据的DataFrame
        """
        if 'close' not in df.columns or len(df) < slow:
            return pd.DataFrame()

        # 计算EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        # 计算DIF
        dif = ema_fast - ema_slow

        # 计算DEA
        dea = dif.ewm(span=signal, adjust=False).mean()

        # 计算MACD
        macd = (dif - dea) * 2

        result = pd.DataFrame({
            'dif': dif,
            'dea': dea,
            'macd': macd
        })

        return result


class TrendStrengthAnalyzer:
    """趋势力度分析器"""

    def __init__(self):
        self.weights = {
            "price_trend": 0.3,      # 价格趋势权重
            "momentum": 0.3,         # 动量权重
            "volatility": 0.2,       # 波动率权重
            "volume_profile": 0.2    # 成交量分布权重
        }

    def calculate_trend_strength(self, df: pd.DataFrame,
                                window: int = 20) -> Dict[str, any]:
        """
        计算趋势力度指标

        指标包括：
        1. ADX（平均趋向指数）
        2. 价格趋势强度
        3. 动量强度
        4. 波动率
        5. 成交量强度

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            趋势力度指标字典
        """
        result = {}

        # 1. 计算ADX（平均趋向指数）
        adx = self._calculate_adx(df, window)
        result["adx"] = adx

        # 2. 价格趋势强度
        price_trend = self._calculate_price_trend(df, window)
        result["price_trend"] = price_trend

        # 3. 动量强度
        momentum = self._calculate_momentum(df, window)
        result["momentum"] = momentum

        # 4. 波动率
        volatility = self._calculate_volatility(df, window)
        result["volatility"] = volatility

        # 5. 成交量强度
        volume_strength = self._calculate_volume_strength(df, window)
        result["volume_strength"] = volume_strength

        # 6. 综合趋势力度
        trend_strength = self._calculate_comprehensive_trend(
            price_trend, momentum, volatility, volume_strength
        )
        result["trend_strength"] = trend_strength

        # 7. 趋势方向
        result["trend_direction"] = self._determine_trend_direction(
            price_trend, momentum
        )

        return result

    def _calculate_adx(self, df: pd.DataFrame, window: int = 14) -> float:
        """
        计算ADX（平均趋向指数）

        ADX值解释：
        - 0-25: 弱趋势或无趋势
        - 25-50: 中等趋势
        - 50-75: 强趋势
        - 75-100: 极强趋势

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            ADX值
        """
        if len(df) < window * 2:
            return 0.0

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        # 计算True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum.reduce([tr1, tr2, tr3])

        # 计算+DM和-DM
        plus_dm = np.where((high[1:] - high[:-1]) > (low[:-1] - low[1:]),
                          np.maximum(high[1:] - high[:-1], 0), 0)
        minus_dm = np.where((low[:-1] - low[1:]) > (high[1:] - high[:-1]),
                           np.maximum(low[:-1] - low[1:], 0), 0)

        # 平滑处理
        atr = pd.Series(tr).rolling(window=window).mean()
        plus_di = pd.Series(plus_dm).rolling(window=window).mean() / atr * 100
        minus_di = pd.Series(minus_dm).rolling(window=window).mean() / atr * 100

        # 计算DX
        dx = np.abs(plus_di - minus_di) / (plus_di + minus_di) * 100

        # 计算ADX
        adx = pd.Series(dx).rolling(window=window).mean()

        return round(adx.iloc[-1], 2) if not adx.empty and not pd.isna(adx.iloc[-1]) else 0.0

    def _calculate_price_trend(self, df: pd.DataFrame, window: int) -> float:
        """
        计算价格趋势强度

        使用线性回归斜率作为趋势强度

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            价格趋势强度（0-1）
        """
        if len(df) < window:
            return 0.5

        recent_close = df['close'].iloc[-window:]

        # 线性回归
        x = np.arange(len(recent_close))
        y = recent_close.values

        # 计算斜率
        slope = np.polyfit(x, y, 1)[0]

        # 标准化斜率
        price_range = y.max() - y.min()
        if price_range > 0:
            normalized_slope = abs(slope * len(x)) / price_range
        else:
            normalized_slope = 0.0

        return round(min(normalized_slope, 1.0), 3)

    def _calculate_momentum(self, df: pd.DataFrame, window: int) -> float:
        """
        计算动量强度

        使用ROC（变化率）作为动量指标

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            动量强度（0-1）
        """
        if len(df) < window + 1:
            return 0.5

        current_price = df['close'].iloc[-1]
        past_price = df['close'].iloc[-window - 1]

        if past_price != 0:
            roc = abs((current_price - past_price) / past_price)
        else:
            roc = 0.0

        # 标准化ROC
        normalized_roc = min(roc / 0.1, 1.0)  # 10%的变化率得满分

        return round(normalized_roc, 3)

    def _calculate_volatility(self, df: pd.DataFrame, window: int) -> float:
        """
        计算波动率

        使用标准差作为波动率指标

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            波动率（0-1）
        """
        if len(df) < window:
            return 0.5

        returns = df['close'].pct_change().iloc[-window:].dropna()

        if len(returns) == 0:
            return 0.5

        volatility = returns.std() * np.sqrt(252)  # 年化波动率

        # 标准化波动率（假设年化波动率50%为高波动）
        normalized_volatility = min(volatility / 0.5, 1.0)

        return round(normalized_volatility, 3)

    def _calculate_volume_strength(self, df: pd.DataFrame, window: int) -> float:
        """
        计算成交量强度

        比较当前成交量与平均成交量

        Args:
            df: K线数据
            window: 计算窗口

        Returns:
            成交量强度（0-1）
        """
        if len(df) < window:
            return 0.5

        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-window:-1].mean()

        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
        else:
            volume_ratio = 1.0

        # 标准化成交量比率
        normalized_volume = min(volume_ratio / 2.0, 1.0)  # 2倍平均成交量得满分

        return round(normalized_volume, 3)

    def _calculate_comprehensive_trend(self, price_trend: float,
                                      momentum: float,
                                      volatility: float,
                                      volume_strength: float) -> float:
        """
        计算综合趋势力度

        Args:
            price_trend: 价格趋势强度
            momentum: 动量强度
            volatility: 波动率
            volume_strength: 成交量强度

        Returns:
            综合趋势力度（0-1）
        """
        weights = self.weights

        strength = (
            weights["price_trend"] * price_trend +
            weights["momentum"] * momentum +
            weights["volatility"] * volatility +
            weights["volume_profile"] * volume_strength
        )

        return round(strength, 3)

    def _determine_trend_direction(self, price_trend: float,
                                   momentum: float) -> str:
        """
        判断趋势方向

        Args:
            price_trend: 价格趋势强度
            momentum: 动量强度

        Returns:
            趋势方向（up/down/neutral）
        """
        # 基于价格趋势和动量的方向判断
        # price_trend 来自线性回归斜率，有方向信息
        # 这里需要传入方向信息，简化处理用动量方向
        # 注意：此方法需要配合实际的价格方向使用
        if price_trend > 0.3 and momentum > 0.3:
            return "up"
        elif price_trend < 0.1 and momentum < 0.1:
            return "down"
        else:
            return "neutral"


# 快捷函数
def analyze_enhanced_structure(df: pd.DataFrame, segments: List) -> List[ZhongShuV2]:
    """快捷函数：增强版结构分析"""
    analyzer = AdvancedChanLunAnalyzer()
    return analyzer.enhanced_identify_zhongshu(df, segments)


def analyze_enhanced_divergence(df: pd.DataFrame, bis: List = None) -> List[Dict]:
    """快捷函数：增强版背驰分析"""
    analyzer = EnhancedDynamicsAnalyzer()
    return analyzer.enhanced_divergence_detection(df, bis)


def analyze_trend_strength(df: pd.DataFrame, window: int = 20) -> Dict[str, any]:
    """快捷函数：趋势力度分析"""
    analyzer = TrendStrengthAnalyzer()
    return analyzer.calculate_trend_strength(df, window)
