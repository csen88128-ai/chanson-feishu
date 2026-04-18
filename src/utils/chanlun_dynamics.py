"""
缠论动力学分析算法 v2.1
实现MACD计算和背驰识别

v2.1 改进（2026-04-18）：
1. 新增 identify_divergence_by_bis() - 基于笔的背驰识别（推荐，减少噪音）
2. 新增 identify_divergence_by_segments() - 基于线段的背驰识别
3. analyze() 接受可选的 bis/segments 参数，优先使用基于笔/线段的方法
4. 修复 _calculate_macd_area() 的索引越界问题
5. analyze_momentum() 新增 strong_bearish 状态
6. Strength 新增 MODERATE 级别
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DivergenceType(Enum):
    """背驰类型"""
    TOP = "top"          # 顶背驰
    BOTTOM = "bottom"    # 底背驰
    NONE = "none"        # 无背驰


class Strength(Enum):
    """力度"""
    STRONG = "strong"    # 强背驰
    WEAK = "weak"        # 弱背驰
    MODERATE = "moderate"  # 中等背驰


@dataclass
class MACDPoint:
    """MACD数据点"""
    index: int
    price: float
    dif: float
    dea: float
    macd: float


@dataclass
class Divergence:
    """背驰"""
    type: DivergenceType
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    strength: Strength
    macd_area: float
    level: str = "bi"  # "bi"=笔级别, "segment"=线段级别


class DynamicsAnalyzer:
    """缠论动力学分析器"""

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        初始化MACD参数

        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.macd_points: List[MACDPoint] = []

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: K线数据，必须包含 close 列

        Returns:
            添加了 MACD, DIF, DEA 列的DataFrame
        """
        close_prices = df['close'].values

        # 计算EMA
        ema_fast = self._calculate_ema(close_prices, self.fast_period)
        ema_slow = self._calculate_ema(close_prices, self.slow_period)

        # 计算DIF
        dif = ema_fast - ema_slow

        # 计算DEA
        dea = self._calculate_ema(dif, self.signal_period)

        # 计算MACD柱状图
        macd = (dif - dea) * 2

        # 添加到DataFrame
        df = df.copy()
        df['dif'] = dif
        df['dea'] = dea
        df['macd'] = macd

        # 保存MACD数据点
        self.macd_points = [
            MACDPoint(
                index=i,
                price=close_prices[i],
                dif=dif[i],
                dea=dea[i],
                macd=macd[i]
            )
            for i in range(len(df))
        ]

        return df

    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        计算指数移动平均线（EMA）

        Args:
            data: 价格数据
            period: 周期

        Returns:
            EMA数组
        """
        ema = np.zeros_like(data)
        alpha = 2 / (period + 1)

        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

        return ema

    def identify_divergence(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> List[Divergence]:
        """
        识别背驰（旧版滑动窗口方法，保留兼容）

        ⚠️ 此方法会产生大量噪音信号，建议使用 identify_divergence_by_bis 代替

        背驰定义（缠论）：
        - 顶背驰：价格创新高，但MACD力度减弱（MACD柱状图面积缩小）
        - 底背驰：价格创新低，但MACD力度减弱（MACD柱状图负值面积缩小）

        Args:
            df: K线数据（必须包含MACD列）
            lookback: 回看窗口大小

        Returns:
            背驰列表
        """
        divergences = []

        if len(df) < lookback:
            return divergences

        # 寻找最近的局部高点和低点
        for i in range(lookback, len(df)):
            # 检查顶背驰
            top_div = self._check_top_divergence(df, i, lookback)
            if top_div:
                divergences.append(top_div)

            # 检查底背驰
            bottom_div = self._check_bottom_divergence(df, i, lookback)
            if bottom_div:
                divergences.append(bottom_div)

        return divergences

    def _check_top_divergence(
        self,
        df: pd.DataFrame,
        index: int,
        lookback: int
    ) -> Optional[Divergence]:
        """检查顶背驰"""
        # 当前高点
        current_high = df.iloc[index]['high']
        current_macd = df.iloc[index]['macd']

        # 在回看窗口中找到前一个高点
        prev_high_index = None
        prev_high = 0

        for i in range(max(0, index - lookback), index):
            if df.iloc[i]['high'] > prev_high:
                prev_high = df.iloc[i]['high']
                prev_high_index = i

        if prev_high_index is None:
            return None

        # 条件1：价格创新高
        if current_high <= prev_high:
            return None

        # 条件2：MACD力度减弱（计算面积）
        current_area = self._calculate_macd_area(df, prev_high_index, index, "top")
        prev_area = self._calculate_macd_area(df, prev_high_index - lookback, prev_high_index, "top")

        if current_area < prev_area:
            # 计算背驰强度
            strength_ratio = current_area / prev_area if prev_area > 0 else 0

            if strength_ratio < 0.5:
                strength = Strength.STRONG
            else:
                strength = Strength.WEAK

            return Divergence(
                type=DivergenceType.TOP,
                start_index=prev_high_index,
                end_index=index,
                start_price=prev_high,
                end_price=current_high,
                strength=strength,
                macd_area=current_area
            )

        return None

    def _check_bottom_divergence(
        self,
        df: pd.DataFrame,
        index: int,
        lookback: int
    ) -> Optional[Divergence]:
        """检查底背驰"""
        # 当前低点
        current_low = df.iloc[index]['low']
        current_macd = df.iloc[index]['macd']

        # 在回看窗口中找到前一个低点
        prev_low_index = None
        prev_low = float('inf')

        for i in range(max(0, index - lookback), index):
            if df.iloc[i]['low'] < prev_low:
                prev_low = df.iloc[i]['low']
                prev_low_index = i

        if prev_low_index is None:
            return None

        # 条件1：价格创新低
        if current_low >= prev_low:
            return None

        # 条件2：MACD力度减弱（计算负值面积）
        current_area = self._calculate_macd_area(df, prev_low_index, index, "bottom")
        prev_area = self._calculate_macd_area(df, prev_low_index - lookback, prev_low_index, "bottom")

        if abs(current_area) < abs(prev_area):
            # 计算背驰强度
            strength_ratio = abs(current_area) / abs(prev_area) if prev_area != 0 else 0

            if strength_ratio < 0.5:
                strength = Strength.STRONG
            else:
                strength = Strength.WEAK

            return Divergence(
                type=DivergenceType.BOTTOM,
                start_index=prev_low_index,
                end_index=index,
                start_price=prev_low,
                end_price=current_low,
                strength=strength,
                macd_area=current_area
            )

        return None

    def _calculate_macd_area(
        self,
        df: pd.DataFrame,
        start_index: int,
        end_index: int,
        direction: str
    ) -> float:
        """
        计算MACD柱状图面积

        Args:
            df: K线数据
            start_index: 起始索引
            end_index: 结束索引
            direction: "top" 或 "bottom"

        Returns:
            面积值
        """
        if start_index < 0 or end_index >= len(df) or start_index > end_index:
            return 0.0

        macd_values = df.iloc[start_index:end_index + 1]['macd'].values

        if direction == "top":
            # 顶背驰：只计算正值部分
            area = np.sum(macd_values[macd_values > 0])
        else:
            # 底背驰：只计算负值部分
            area = np.sum(macd_values[macd_values < 0])

        return area

    def analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """
        分析市场动量

        Args:
            df: K线数据（必须包含MACD列）

        Returns:
            动量分析结果
        """
        latest = df.iloc[-1]
        latest_index = len(df) - 1

        # 计算动量指标
        dif_trend = "up" if latest['dif'] > df.iloc[-2]['dif'] else "down"
        dea_trend = "up" if latest['dea'] > df.iloc[-2]['dea'] else "down"
        macd_trend = "up" if latest['macd'] > df.iloc[-2]['macd'] else "down"

        # 判断MACD状态
        macd_state = "bullish"  # 看多
        if latest['dif'] < latest['dea'] and latest['macd'] < 0:
            if latest['dif'] < 0:
                macd_state = "strong_bearish"  # 强看空（DIF<0且MACD<0）
            else:
                macd_state = "bearish"  # 看空
        elif latest['dif'] > latest['dea'] and latest['macd'] > 0:
            macd_state = "strong_bullish"  # 强看多
        elif latest['dif'] < latest['dea'] and latest['macd'] > 0:
            macd_state = "pullback"  # 回调

        # 计算力度
        strength = abs(latest['dif'] - latest['dea'])

        # 检查是否有金叉/死叉
        cross_type = "none"
        if (df.iloc[-2]['dif'] <= df.iloc[-2]['dea'] and
            latest['dif'] > latest['dea']):
            cross_type = "golden_cross"  # 金叉
        elif (df.iloc[-2]['dif'] >= df.iloc[-2]['dea'] and
              latest['dif'] < latest['dea']):
            cross_type = "death_cross"  # 死叉

        return {
            "latest_price": latest['close'],
            "dif": latest['dif'],
            "dea": latest['dea'],
            "macd": latest['macd'],
            "dif_trend": dif_trend,
            "dea_trend": dea_trend,
            "macd_trend": macd_trend,
            "macd_state": macd_state,
            "strength": strength,
            "cross_type": cross_type
        }

    def analyze(self, df: pd.DataFrame, bis: List = None, segments: List = None) -> Dict:
        """
        完整分析流程

        改进：优先使用基于笔/线段的背驰识别

        Args:
            df: K线数据
            bis: 笔列表（可选，用于基于笔的背驰识别）
            segments: 线段列表（可选，用于基于线段的背驰识别）

        Returns:
            分析结果
        """
        # 计算MACD
        df_with_macd = self.calculate_macd(df)

        # 识别背驰（优先使用基于笔的方法）
        if bis is not None:
            divergences = self.identify_divergence_by_bis(df_with_macd, bis)
            if segments:
                divergences += self.identify_divergence_by_segments(df_with_macd, segments)
        else:
            divergences = self.identify_divergence(df_with_macd)

        # 分析动量
        momentum = self.analyze_momentum(df_with_macd)

        # 生成报告
        report = {
            "macd": momentum,
            "divergences": {
                "count": len(divergences),
                "latest": self._divergence_to_dict(divergences[-1]) if divergences else None,
                "all": [self._divergence_to_dict(d) for d in divergences]
            }
        }

        return report

    # ==================== 新增：基于笔/线段的背驰识别 ====================

    def identify_divergence_by_bis(self, df_with_macd: pd.DataFrame, bis: List) -> List[Divergence]:
        """
        基于笔的背驰识别（推荐方法）

        缠论背驰定义：
        - 顶背驰：向上笔创新高，但该笔区间内MACD面积 < 前一个向上笔的MACD面积
        - 底背驰：向下笔创新低，但该笔区间内|MACD面积| < 前一个向下笔的|MACD面积|
        """
        divergences = []
        if len(bis) < 2:
            return divergences

        up_bis = [b for b in bis if b.direction.value == 'up']
        down_bis = [b for b in bis if b.direction.value == 'down']

        # 顶背驰
        for i in range(1, len(up_bis)):
            prev_bi, curr_bi = up_bis[i - 1], up_bis[i]
            if curr_bi.high <= prev_bi.high:
                continue
            prev_area = self._calc_bi_macd_area(df_with_macd, prev_bi, "top")
            curr_area = self._calc_bi_macd_area(df_with_macd, curr_bi, "top")
            if prev_area > 0 and curr_area < prev_area:
                ratio = curr_area / prev_area
                strength = Strength.STRONG if ratio < 0.3 else (Strength.MODERATE if ratio < 0.7 else Strength.WEAK)
                divergences.append(Divergence(
                    type=DivergenceType.TOP, start_index=prev_bi.start_index,
                    end_index=curr_bi.end_index, start_price=prev_bi.high,
                    end_price=curr_bi.high, strength=strength, macd_area=curr_area, level="bi"))

        # 底背驰
        for i in range(1, len(down_bis)):
            prev_bi, curr_bi = down_bis[i - 1], down_bis[i]
            if curr_bi.low >= prev_bi.low:
                continue
            prev_area = abs(self._calc_bi_macd_area(df_with_macd, prev_bi, "bottom"))
            curr_area = abs(self._calc_bi_macd_area(df_with_macd, curr_bi, "bottom"))
            if prev_area > 0 and curr_area < prev_area:
                ratio = curr_area / prev_area
                strength = Strength.STRONG if ratio < 0.3 else (Strength.MODERATE if ratio < 0.7 else Strength.WEAK)
                divergences.append(Divergence(
                    type=DivergenceType.BOTTOM, start_index=prev_bi.start_index,
                    end_index=curr_bi.end_index, start_price=prev_bi.low,
                    end_price=curr_bi.low, strength=strength, macd_area=-curr_area, level="bi"))

        return divergences

    def identify_divergence_by_segments(self, df_with_macd: pd.DataFrame, segments: List) -> List[Divergence]:
        """基于线段的背驰识别"""
        divergences = []
        if len(segments) < 2:
            return divergences

        up_segs = [s for s in segments if s.direction.value == 'up']
        down_segs = [s for s in segments if s.direction.value == 'down']

        for i in range(1, len(up_segs)):
            prev_seg, curr_seg = up_segs[i - 1], up_segs[i]
            if curr_seg.high <= prev_seg.high:
                continue
            prev_area = self._calc_seg_macd_area(df_with_macd, prev_seg, "top")
            curr_area = self._calc_seg_macd_area(df_with_macd, curr_seg, "top")
            if prev_area > 0 and curr_area < prev_area:
                ratio = curr_area / prev_area
                strength = Strength.STRONG if ratio < 0.3 else (Strength.MODERATE if ratio < 0.7 else Strength.WEAK)
                divergences.append(Divergence(
                    type=DivergenceType.TOP,
                    start_index=getattr(prev_seg, 'start_index', 0),
                    end_index=getattr(curr_seg, 'end_index', 0),
                    start_price=prev_seg.high, end_price=curr_seg.high,
                    strength=strength, macd_area=curr_area, level="segment"))

        for i in range(1, len(down_segs)):
            prev_seg, curr_seg = down_segs[i - 1], down_segs[i]
            if curr_seg.low >= prev_seg.low:
                continue
            prev_area = abs(self._calc_seg_macd_area(df_with_macd, prev_seg, "bottom"))
            curr_area = abs(self._calc_seg_macd_area(df_with_macd, curr_seg, "bottom"))
            if prev_area > 0 and curr_area < prev_area:
                ratio = curr_area / prev_area
                strength = Strength.STRONG if ratio < 0.3 else (Strength.MODERATE if ratio < 0.7 else Strength.WEAK)
                divergences.append(Divergence(
                    type=DivergenceType.BOTTOM,
                    start_index=getattr(prev_seg, 'start_index', 0),
                    end_index=getattr(curr_seg, 'end_index', 0),
                    start_price=prev_seg.low, end_price=curr_seg.low,
                    strength=strength, macd_area=-curr_area, level="segment"))

        return divergences

    def _calc_bi_macd_area(self, df: pd.DataFrame, bi, direction: str) -> float:
        """计算单笔区间内的MACD面积"""
        start = max(0, bi.start_index)
        end = min(len(df) - 1, bi.end_index)
        if start > end:
            return 0.0
        macd_values = df.iloc[start:end + 1]['macd'].values
        if len(macd_values) == 0:
            return 0.0
        if direction == "top":
            return float(np.sum(macd_values[macd_values > 0]))
        else:
            return float(np.sum(macd_values[macd_values < 0]))

    def _calc_seg_macd_area(self, df: pd.DataFrame, seg, direction: str) -> float:
        """计算线段区间内的MACD面积"""
        start = max(0, getattr(seg, 'start_index', seg.bi_list[0].start_index if hasattr(seg, 'bi_list') else 0))
        end = min(len(df) - 1, getattr(seg, 'end_index', seg.bi_list[-1].end_index if hasattr(seg, 'bi_list') else 0))
        if start > end:
            return 0.0
        macd_values = df.iloc[start:end + 1]['macd'].values
        if len(macd_values) == 0:
            return 0.0
        if direction == "top":
            return float(np.sum(macd_values[macd_values > 0]))
        else:
            return float(np.sum(macd_values[macd_values < 0]))

    def _divergence_to_dict(self, divergence: Divergence) -> Dict:
        """背驰转字典"""
        return {
            "type": divergence.type.value,
            "start_index": divergence.start_index,
            "end_index": divergence.end_index,
            "start_price": divergence.start_price,
            "end_price": divergence.end_price,
            "strength": divergence.strength.value,
            "macd_area": divergence.macd_area,
            "level": divergence.level
        }
