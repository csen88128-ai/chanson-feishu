"""
缠论结构分析算法
实现笔、线段、中枢的自动识别
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class FractalType(Enum):
    """分型类型"""
    TOP = "top"      # 顶分型
    BOTTOM = "bottom"  # 底分型
    NONE = "none"    # 无分型


class BiDirection(Enum):
    """笔的方向"""
    UP = "up"        # 向上笔（从底到顶）
    DOWN = "down"    # 向下笔（从顶到底）


class SegmentDirection(Enum):
    """线段的方向"""
    UP = "up"
    DOWN = "down"


@dataclass
class Fractal:
    """分型"""
    index: int                    # K线索引
    type: FractalType             # 分型类型
    high: float                   # 高点
    low: float                    # 低点
    kline_count: int = 3          # 包含的K线数量


@dataclass
class Bi:
    """笔"""
    start_index: int              # 起始K线索引
    end_index: int                # 结束K线索引
    direction: BiDirection        # 方向
    start_price: float            # 起始价格
    end_price: float              # 结束价格
    high: float                   # 最高点
    low: float                    # 最低点


@dataclass
class Segment:
    """线段"""
    bi_list: List[Bi]             # 组成线段的笔列表
    direction: SegmentDirection   # 方向
    start_price: float            # 起始价格
    end_price: float              # 结束价格
    high: float                   # 最高点
    low: float                    # 最低点


@dataclass
class ZhongShu:
    """中枢"""
    segment_list: List[Segment]   # 组成中枢的线段列表
    high: float                   # 中枢上沿（ZG）
    low: float                    # 中枢下沿（ZD）
    high_point: float             # 中枢高点（GG）
    low_point: float              # 中枢低点（DD）
    level: int                    # 中枢级别


class ChanLunAnalyzer:
    """缠论结构分析器"""

    def __init__(self):
        self.fractals: List[Fractal] = []
        self.bis: List[Bi] = []
        self.segments: List[Segment] = []
        self.zhongshu_list: List[ZhongShu] = []

    def identify_fractals(self, df: pd.DataFrame) -> List[Fractal]:
        """
        识别分型（顶分型和底分型）

        缠论分型定义：
        - 顶分型：中间K线的高点是三根中最高的，低点也是最高的
        - 底分型：中间K线的低点是三根中最低的，高点也是最低的

        Args:
            df: K线数据，必须包含 high, low 列

        Returns:
            分型列表
        """
        fractals = []

        for i in range(1, len(df) - 1):
            # 获取连续三根K线
            prev_k = df.iloc[i - 1]
            curr_k = df.iloc[i]
            next_k = df.iloc[i + 1]

            # 判断顶分型
            if (curr_k['high'] > prev_k['high'] and
                curr_k['high'] > next_k['high'] and
                curr_k['low'] > prev_k['low'] and
                curr_k['low'] > next_k['low']):
                fractals.append(Fractal(
                    index=i,
                    type=FractalType.TOP,
                    high=curr_k['high'],
                    low=curr_k['low']
                ))

            # 判断底分型
            elif (curr_k['low'] < prev_k['low'] and
                  curr_k['low'] < next_k['low'] and
                  curr_k['high'] < prev_k['high'] and
                  curr_k['high'] < next_k['high']):
                fractals.append(Fractal(
                    index=i,
                    type=FractalType.BOTTOM,
                    high=curr_k['high'],
                    low=curr_k['low']
                ))

        self.fractals = fractals
        return fractals

    def identify_bis(self, df: pd.DataFrame, fractals: List[Fractal]) -> List[Bi]:
        """
        识别笔

        缠论笔的定义：
        - 连接相邻的顶底分型
        - 顶底分型之间至少有一根非共用K线
        - 笔的方向：从底分型到顶分型为向上笔，从顶分型到底分型为向下笔

        Args:
            df: K线数据
            fractals: 分型列表

        Returns:
            笔列表
        """
        if len(fractals) < 2:
            return []

        bis = []
        i = 0

        while i < len(fractals) - 1:
            current = fractals[i]
            next_frac = fractals[i + 1]

            # 检查分型类型是否相反
            if current.type != next_frac.type:
                # 检查间隔（至少有一根K线）
                if next_frac.index - current.index >= 2:
                    # 创建笔
                    if current.type == FractalType.BOTTOM and next_frac.type == FractalType.TOP:
                        direction = BiDirection.UP
                        start_price = current.low
                        end_price = next_frac.high
                    else:
                        direction = BiDirection.DOWN
                        start_price = current.high
                        end_price = next_frac.low

                    # 计算笔的最高点和最低点
                    sub_df = df.iloc[current.index:next_frac.index + 1]
                    high = sub_df['high'].max()
                    low = sub_df['low'].min()

                    bi = Bi(
                        start_index=current.index,
                        end_index=next_frac.index,
                        direction=direction,
                        start_price=start_price,
                        end_price=end_price,
                        high=high,
                        low=low
                    )

                    bis.append(bi)
                    i += 1  # 移动到下一个分型
                else:
                    # 间隔太小，跳过当前分型
                    i += 1
            else:
                # 同类型分型，选择更极端的一个
                if current.type == FractalType.TOP:
                    # 顶分型选更高的
                    if next_frac.high > current.high:
                        i += 1
                    else:
                        i += 1
                else:
                    # 底分型选更低的
                    if next_frac.low < current.low:
                        i += 1
                    else:
                        i += 1

        self.bis = bis
        return bis

    def identify_segments(self, bis: List[Bi]) -> List[Segment]:
        """
        识别线段

        缠论线段定义：
        - 向上线段：高点不断创新高，至少由三笔构成
        - 向下线段：低点不断创新低，至少由三笔构成

        Args:
            bis: 笔列表

        Returns:
            线段列表
        """
        if len(bis) < 3:
            return []

        segments = []
        current_segment_bis = [bis[0]]

        for i in range(1, len(bis)):
            current_bi = bis[i]
            last_bi = current_segment_bis[-1]

            # 检查方向是否一致
            if current_bi.direction == last_bi.direction:
                # 方向一致，检查是否突破
                if current_bi.direction == BiDirection.UP:
                    # 向上笔：高点是否创新高
                    if current_bi.high > last_bi.high:
                        current_segment_bis.append(current_bi)
                    else:
                        # 没有创新高，可能结束线段
                        if len(current_segment_bis) >= 3:
                            segments.append(self._create_segment(current_segment_bis))
                        current_segment_bis = [current_bi]
                else:
                    # 向下笔：低点是否创新低
                    if current_bi.low < last_bi.low:
                        current_segment_bis.append(current_bi)
                    else:
                        # 没有创新低，可能结束线段
                        if len(current_segment_bis) >= 3:
                            segments.append(self._create_segment(current_segment_bis))
                        current_segment_bis = [current_bi]
            else:
                # 方向改变，可能结束当前线段
                if len(current_segment_bis) >= 3:
                    segments.append(self._create_segment(current_segment_bis))
                current_segment_bis = [current_bi]

        # 处理最后一个线段
        if len(current_segment_bis) >= 3:
            segments.append(self._create_segment(current_segment_bis))

        self.segments = segments
        return segments

    def _create_segment(self, bi_list: List[Bi]) -> Segment:
        """从笔列表创建线段"""
        direction = SegmentDirection.UP if bi_list[0].direction == BiDirection.UP else SegmentDirection.DOWN

        start_price = bi_list[0].start_price
        end_price = bi_list[-1].end_price

        high = max(bi.high for bi in bi_list)
        low = min(bi.low for bi in bi_list)

        return Segment(
            bi_list=bi_list,
            direction=direction,
            start_price=start_price,
            end_price=end_price,
            high=high,
            low=low
        )

    def identify_zhongshu(self, segments: List[Segment]) -> List[ZhongShu]:
        """
        识别中枢

        缠论中枢定义：
        - 至少由三段构成
        - 中枢区间：所有段的重叠部分
        - ZG（中枢上沿）：所有段高点最低值
        - ZD（中枢下沿）：所有段低点最高值

        Args:
            segments: 线段列表

        Returns:
            中枢列表
        """
        if len(segments) < 3:
            return []

        zhongshu_list = []
        i = 0

        while i < len(segments) - 2:
            # 检查连续三段
            seg1 = segments[i]
            seg2 = segments[i + 1]
            seg3 = segments[i + 2]

            # 计算重叠区间
            zg = min(seg1.high, seg2.high, seg3.high)  # 中枢上沿
            zd = max(seg1.low, seg2.low, seg3.low)    # 中枢下沿

            # 检查是否有重叠
            if zg > zd:
                # 计算中枢的高点和低点
                gg = max(seg1.high, seg2.high, seg3.high)
                dd = min(seg1.low, seg2.low, seg3.low)

                zhongshu = ZhongShu(
                    segment_list=[seg1, seg2, seg3],
                    high=zg,
                    low=zd,
                    high_point=gg,
                    low_point=dd,
                    level=1  # 简化处理，都当作1级中枢
                )

                zhongshu_list.append(zhongshu)
                i += 3  # 跳过已使用的线段
            else:
                i += 1

        self.zhongshu_list = zhongshu_list
        return zhongshu_list

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整分析流程

        Args:
            df: K线数据

        Returns:
            分析结果
        """
        # 1. 识别分型
        fractals = self.identify_fractals(df)

        # 2. 识别笔
        bis = self.identify_bis(df, fractals)

        # 3. 识别线段
        segments = self.identify_segments(bis)

        # 4. 识别中枢
        zhongshu_list = self.identify_zhongshu(segments)

        # 生成分析报告
        report = {
            "kline_count": len(df),
            "fractals": {
                "count": len(fractals),
                "top_count": sum(1 for f in fractals if f.type == FractalType.TOP),
                "bottom_count": sum(1 for f in fractals if f.type == FractalType.BOTTOM)
            },
            "bis": {
                "count": len(bis),
                "up_count": sum(1 for b in bis if b.direction == BiDirection.UP),
                "down_count": sum(1 for b in bis if b.direction == BiDirection.DOWN),
                "last_bi": self._bi_to_dict(bis[-1]) if bis else None
            },
            "segments": {
                "count": len(segments),
                "up_count": sum(1 for s in segments if s.direction == SegmentDirection.UP),
                "down_count": sum(1 for s in segments if s.direction == SegmentDirection.DOWN),
                "last_segment": self._segment_to_dict(segments[-1]) if segments else None
            },
            "zhongshu": {
                "count": len(zhongshu_list),
                "latest": self._zhongshu_to_dict(zhongshu_list[-1]) if zhongshu_list else None
            }
        }

        return report

    def _bi_to_dict(self, bi: Bi) -> Dict:
        """笔转字典"""
        return {
            "direction": bi.direction.value,
            "start_price": bi.start_price,
            "end_price": bi.end_price,
            "high": bi.high,
            "low": bi.low
        }

    def _segment_to_dict(self, segment: Segment) -> Dict:
        """线段转字典"""
        return {
            "direction": segment.direction.value,
            "start_price": segment.start_price,
            "end_price": segment.end_price,
            "high": segment.high,
            "low": segment.low,
            "bi_count": len(segment.bi_list)
        }

    def _zhongshu_to_dict(self, zhongshu: ZhongShu) -> Dict:
        """中枢转字典"""
        return {
            "high": zhongshu.high,
            "low": zhongshu.low,
            "high_point": zhongshu.high_point,
            "low_point": zhongshu.low_point,
            "level": zhongshu.level,
            "segment_count": len(zhongshu.segment_list)
        }
