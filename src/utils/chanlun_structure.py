"""
缠论结构分析算法 v2.2
实现笔、线段、中枢的自动识别

v2.2 修复（2026-04-18）：
1. 线段识别：实现特征序列破坏判断（第77课标准），替代旧版简化算法
2. 特征序列包含处理：向上线段做低低合并，向下线段做高高合并
3. 中枢识别：支持线段级/笔级双层级降级，解决0中枢问题
4. 中枢延伸：支持后续元素在[DD,GG]范围内延伸

v2.1 修复（2026-04-18）：
1. 分型识别前先处理K线包含关系
2. 笔识别：修复同类型分型合并逻辑，确保正确选择极值分型
3. 线段识别：基于特征序列（笔的端点序列）判断线段破坏
4. 中枢识别：修复ZG/ZD定义，支持中枢延伸
5. 新增：走势类型判断（上涨/下跌/盘整）
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
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


class TrendType(Enum):
    """走势类型"""
    UP = "up"            # 上涨趋势（中枢依次升高）
    DOWN = "down"        # 下跌趋势（中枢依次降低）
    CONSOLIDATION = "consolidation"  # 盘整（中枢重叠）


@dataclass
class Fractal:
    """分型"""
    index: int                    # 原始K线索引
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
    start_index: int = 0          # 起始K线索引
    end_index: int = 0            # 结束K线索引


@dataclass
class ZhongShu:
    """中枢"""
    segment_list: List[Segment]   # 组成中枢的线段列表
    high: float                   # 中枢上沿（ZG）
    low: float                    # 中枢下沿（ZD）
    high_point: float             # 中枢高点（GG）
    low_point: float              # 中枢低点（DD）
    level: int                    # 中枢级别
    start_index: int = 0          # 起始K线索引
    end_index: int = 0            # 结束K线索引


class ChanLunAnalyzer:
    """缠论结构分析器 v2.1"""

    def __init__(self):
        self.fractals: List[Fractal] = []
        self.bis: List[Bi] = []
        self.segments: List[Segment] = []
        self.zhongshu_list: List[ZhongShu] = []
        self.merged_df: Optional[pd.DataFrame] = None  # 包含处理后的K线

    def _process_inclusion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理K线包含关系（缠论预处理步骤）

        缠论包含定义：当两根K线的高点和低点存在包含关系时（一根K线的高低点
        完全在另一根K线的范围内），需要合并为一根K线。

        合并规则：
        - 上升趋势中：取两根K线的高点较高值和低点较高值（高高）
        - 下降趋势中：取两根K线的高点较低值和低点较低值（低低）

        Args:
            df: 原始K线数据

        Returns:
            处理包含关系后的K线数据
        """
        if len(df) < 2:
            return df

        merged = []
        # 第一根K线直接加入
        first = df.iloc[0].copy()
        merged.append(first)

        # 判断趋势方向（用前两根K线确定初始方向）
        trend_up = True  # 默认上升

        for i in range(1, len(df)):
            curr = df.iloc[i]
            prev = merged[-1]

            # 检查是否有包含关系
            has_inclusion = (
                (curr['high'] >= prev['high'] and curr['low'] <= prev['low']) or  # curr包含prev
                (curr['high'] <= prev['high'] and curr['low'] >= prev['low'])     # prev包含curr
            )

            if has_inclusion:
                # 合并K线
                if trend_up:
                    # 上升趋势：取高高
                    merged[-1] = prev.copy()
                    merged[-1]['high'] = max(prev['high'], curr['high'])
                    merged[-1]['low'] = max(prev['low'], curr['low'])
                else:
                    # 下降趋势：取低低
                    merged[-1] = prev.copy()
                    merged[-1]['high'] = min(prev['high'], curr['high'])
                    merged[-1]['low'] = min(prev['low'], curr['low'])
            else:
                # 无包含关系，更新趋势方向
                if curr['high'] > prev['high'] and curr['low'] > prev['low']:
                    trend_up = True
                elif curr['high'] < prev['high'] and curr['low'] < prev['low']:
                    trend_up = False
                # 否则保持当前趋势方向不变

                merged.append(curr)

        return pd.DataFrame(merged).reset_index(drop=True)

    def identify_fractals(self, df: pd.DataFrame) -> List[Fractal]:
        """
        识别分型（顶分型和底分型）

        改进：先处理K线包含关系，再识别分型

        缠论分型定义：
        - 顶分型：中间K线的高点是三根中最高的，低点也是最高的
        - 底分型：中间K线的低点是三根中最低的，高点也是最低的

        Args:
            df: K线数据，必须包含 high, low 列

        Returns:
            分型列表
        """
        # 先处理包含关系
        processed_df = self._process_inclusion(df)
        self.merged_df = processed_df

        fractals = []

        for i in range(1, len(processed_df) - 1):
            # 获取连续三根K线
            prev_k = processed_df.iloc[i - 1]
            curr_k = processed_df.iloc[i]
            next_k = processed_df.iloc[i + 1]

            # 判断顶分型：中间K线的高点和低点均高于两侧
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

            # 判断底分型：中间K线的高点和低点均低于两侧
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

        缠论笔的定义（严格版）：
        - 连接相邻的顶底分型
        - 顶底分型之间至少有一根独立K线（处理包含后间隔 >= 4）
        - 笔的方向：从底分型到顶分型为向上笔，从顶分型到底分型为向下笔
        - 同类型分型取极值：连续顶分型取最高的，连续底分型取最低的

        Args:
            df: K线数据（用于计算笔区间的高低点）
            fractals: 分型列表

        Returns:
            笔列表
        """
        if len(fractals) < 2:
            return []

        # Step 1: 合并同类型分型（连续的顶分型取最高，连续的底分型取最低）
        merged_fractals = [fractals[0]]
        for i in range(1, len(fractals)):
            last = merged_fractals[-1]
            curr = fractals[i]

            if curr.type == last.type:
                # 同类型分型，保留更极端的
                if curr.type == FractalType.TOP:
                    if curr.high > last.high:
                        merged_fractals[-1] = curr
                else:  # BOTTOM
                    if curr.low < last.low:
                        merged_fractals[-1] = curr
            else:
                # 不同类型，但要检查是否满足间隔要求
                if curr.index - last.index >= 4:
                    # 满足间隔要求，加入
                    merged_fractals.append(curr)
                else:
                    # 间隔不够，保留更极端的（覆盖前一个）
                    if curr.type == FractalType.TOP and curr.high > last.high:
                        merged_fractals[-1] = curr
                    elif curr.type == FractalType.BOTTOM and curr.low < last.low:
                        merged_fractals[-1] = curr

        # Step 2: 在合并后的分型列表中，确保顶底交替
        # 如果出现连续同类型，只保留更极端的
        final_fractals = [merged_fractals[0]]
        for i in range(1, len(merged_fractals)):
            curr = merged_fractals[i]
            last = final_fractals[-1]
            if curr.type != last.type:
                final_fractals.append(curr)
            else:
                # 仍然同类型，保留更极端的
                if curr.type == FractalType.TOP and curr.high > last.high:
                    final_fractals[-1] = curr
                elif curr.type == FractalType.BOTTOM and curr.low < last.low:
                    final_fractals[-1] = curr

        # Step 3: 根据分型构建笔
        bis = []
        for i in range(len(final_fractals) - 1):
            current = final_fractals[i]
            next_frac = final_fractals[i + 1]

            if current.type == FractalType.BOTTOM and next_frac.type == FractalType.TOP:
                direction = BiDirection.UP
                start_price = current.low
                end_price = next_frac.high
            elif current.type == FractalType.TOP and next_frac.type == FractalType.BOTTOM:
                direction = BiDirection.DOWN
                start_price = current.high
                end_price = next_frac.low
            else:
                # 不应出现同类型相邻
                continue

            # 使用处理包含后的K线数据计算笔区间的高低点
            if self.merged_df is not None:
                sub_df = self.merged_df.iloc[current.index:next_frac.index + 1]
            else:
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

        self.bis = bis
        return bis

    def identify_segments(self, bis: List[Bi]) -> List[Segment]:
        """
        识别线段（基于特征序列破坏判断）

        缠论线段定义（严格版，第77课）：
        线段的划分标准——特征序列破坏：

        1. 特征序列：将笔序列中与线段方向相反的笔称为该线段的特征序列
           - 向上线段的特征序列 = 所有向下笔
           - 向下线段的特征序列 = 所有向上笔

        2. 特征序列的包含处理：同方向特征序列元素之间做包含合并
           - 向上线段中，特征序列（向下笔）做低低合并
           - 向下线段中，特征序列（向上笔）做高高合并

        3. 线段被破坏的条件：
           - 第一种破坏（笔破坏）：特征序列的一笔直接击穿前一笔的极值
             向上线段中：某向下笔 low < 前一向下笔 low（向下笔创新低）
             向下线段中：某向上笔 high > 前一向上笔 high（向上笔创新高）
           - 第二种破坏（缺口破坏）：特征序列之间存在缺口，且后续笔确认

        4. 线段至少由3笔构成

        Args:
            bis: 笔列表

        Returns:
            线段列表
        """
        if len(bis) < 3:
            self.segments = []
            return []

        segments = self._identify_segments_by_feature_destruction(bis)
        self.segments = segments
        return segments

    def _identify_segments_by_feature_destruction(self, bis: List[Bi]) -> List[Segment]:
        """
        基于特征序列破坏的线段识别

        实现逻辑：
        1. 从第1笔开始构建线段
        2. 提取特征序列（反向笔），做包含处理
        3. 判断特征序列是否被破坏
        4. 被破坏处切分线段
        """
        if len(bis) < 3:
            return []

        segments = []
        i = 0  # 当前线段起始笔索引

        while i < len(bis) - 2:  # 至少需要3笔
            # 确定线段方向（由第一笔决定）
            seg_direction = bis[i].direction

            # 找到线段的结束位置
            end_idx = self._find_segment_end(bis, i, seg_direction)

            # 提取线段的笔列表
            seg_bis = bis[i:end_idx + 1]

            if len(seg_bis) >= 3:
                seg = self._create_segment(seg_bis)
                segments.append(seg)
                # 下一线段从 end_idx 开始（笔共享：新线段第一笔 = 旧线段最后一笔的反向）
                # 但确保至少前进1笔
                i = max(end_idx, i + 1)
            else:
                # 不足3笔，跳到下一笔
                i += 1

        # 后处理：合并方向相同的相邻线段
        merged = self._merge_same_direction_segments(segments)

        return merged

    def _find_segment_end(self, bis: List[Bi], start: int, seg_direction: BiDirection) -> int:
        """
        找到从 start 开始的线段的结束位置

        核心逻辑：构建特征序列，判断特征序列是否被破坏

        缠论线段划分标准（第77课）：
        - 向上线段的特征序列是向下笔
          特征序列破坏 = 某向下笔 low < 前一向下笔 low
        - 向下线段的特征序列是向上笔
          特征序列破坏 = 某向上笔 high > 前一向上笔 high

        特征序列破坏意味着原线段结束，新线段从破坏点开始。

        Returns:
            线段结束的笔索引（线段包含该笔）
        """
        # 提取特征序列（与线段方向相反的笔）
        feature_seq = []  # [(笔在bis中的索引, 笔对象)]
        for k in range(start + 1, len(bis)):
            if bis[k].direction != seg_direction:
                feature_seq.append((k, bis[k]))

        if len(feature_seq) < 2:
            # 特征序列不足2个，线段未结束
            return len(bis) - 1

        # 对特征序列做包含处理
        merged_features = self._merge_feature_sequence(feature_seq, seg_direction)

        # 检查特征序列是否被破坏
        for m in range(1, len(merged_features)):
            prev_indices, prev_bi = merged_features[m - 1]
            curr_indices, curr_bi = merged_features[m]

            if seg_direction == BiDirection.UP:
                # 向上线段，特征序列是向下笔
                # 第一种破坏：当前向下笔 low < 前一向下笔 low
                if curr_bi.low < prev_bi.low:
                    # 线段在当前破坏笔之前的笔处结束
                    # 即线段包含到破坏笔的前一笔（同方向笔）
                    # 破坏笔索引是 curr_indices[0]
                    # 线段结束点 = 破坏笔前一笔
                    return curr_indices[0] - 1
            else:
                # 向下线段，特征序列是向上笔
                # 第一种破坏：当前向上笔 high > 前一向上笔 high
                if curr_bi.high > prev_bi.high:
                    return curr_indices[0] - 1

        # 没有被破坏，线段延续到最后一笔
        return len(bis) - 1

    def _merge_feature_sequence(self, feature_seq: list, seg_direction: BiDirection) -> list:
        """
        对特征序列做包含处理

        缠论规定：
        - 向上线段中，特征序列（向下笔）做低低合并（取高点较低值、低点较低值）
        - 向下线段中，特征序列（向上笔）做高高合并（取高点较高值、低点较高值）

        Args:
            feature_seq: 特征序列 [(笔索引列表, 笔对象)]
            seg_direction: 线段方向

        Returns:
            合并后的特征序列 [(原始索引列表, 合并后的虚拟笔)]
        """
        if len(feature_seq) <= 1:
            return [([idx], bi) for idx, bi in feature_seq]

        merged = [([feature_seq[0][0]], feature_seq[0][1])]

        for k in range(1, len(feature_seq)):
            idx, bi = feature_seq[k]
            prev_indices, prev_bi = merged[-1]

            # 检查包含关系
            has_inclusion = (
                (bi.high >= prev_bi.high and bi.low <= prev_bi.low) or
                (bi.high <= prev_bi.high and bi.low >= prev_bi.low)
            )

            if has_inclusion:
                # 合并
                if seg_direction == BiDirection.UP:
                    # 向上线段的特征序列（向下笔）：低低合并
                    new_bi = Bi(
                        start_index=min(prev_bi.start_index, bi.start_index),
                        end_index=max(prev_bi.end_index, bi.end_index),
                        direction=prev_bi.direction,
                        start_price=min(prev_bi.start_price, bi.start_price),
                        end_price=min(prev_bi.end_price, bi.end_price),
                        high=min(prev_bi.high, bi.high),
                        low=min(prev_bi.low, bi.low),
                    )
                else:
                    # 向下线段的特征序列（向上笔）：高高合并
                    new_bi = Bi(
                        start_index=min(prev_bi.start_index, bi.start_index),
                        end_index=max(prev_bi.end_index, bi.end_index),
                        direction=prev_bi.direction,
                        start_price=max(prev_bi.start_price, bi.start_price),
                        end_price=max(prev_bi.end_price, bi.end_price),
                        high=max(prev_bi.high, bi.high),
                        low=max(prev_bi.low, bi.low),
                    )
                merged[-1] = (prev_indices + [idx], new_bi)
            else:
                merged.append(([idx], bi))

        return merged

    def _merge_same_direction_segments(self, segments: List[Segment]) -> List[Segment]:
        """合并方向相同的相邻线段"""
        if not segments:
            return segments

        merged = [segments[0]]
        for seg in segments[1:]:
            if seg.direction == merged[-1].direction:
                # 合并
                merged[-1] = Segment(
                    bi_list=merged[-1].bi_list + seg.bi_list,
                    direction=seg.direction,
                    start_price=merged[-1].start_price,
                    end_price=seg.end_price,
                    high=max(merged[-1].high, seg.high),
                    low=min(merged[-1].low, seg.low),
                    start_index=merged[-1].start_index,
                    end_index=seg.end_index,
                )
            else:
                merged.append(seg)

        return merged

    def _create_segment(self, bi_list: List[Bi]) -> Segment:
        """从笔列表创建线段"""
        # 线段方向由整体走势决定
        if bi_list[-1].end_price > bi_list[0].start_price:
            direction = SegmentDirection.UP
        else:
            direction = SegmentDirection.DOWN

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
            low=low,
            start_index=bi_list[0].start_index,
            end_index=bi_list[-1].end_index,
        )

    def identify_zhongshu(self, segments: List[Segment]) -> List[ZhongShu]:
        """
        识别中枢

        缠论中枢定义（严格版，第20/22课）：
        - 中枢由至少3条连续线段构成（且线段方向交替）
        - ZG（中枢上沿）= MIN(所有线段的高点)
        - ZD（中枢下沿）= MAX(所有线段的低点)
        - ZG > ZD 才有中枢
        - GG（中枢最高点）= MAX(所有线段的高点)
        - DD（中枢最低点）= MIN(所有线段的低点)
        - 中枢可以延伸：后续线段的高低点仍在[DD, GG]范围内

        降级策略：
        当线段不足3段时，退化为"笔级别中枢"：
        - 中枢由至少3笔构成（笔方向交替）
        - 同样计算 ZG/ZD/GG/DD
        - level=0 标记为笔级别中枢

        Args:
            segments: 线段列表

        Returns:
            中枢列表
        """
        # 优先使用线段构建中枢
        if len(segments) >= 3:
            zhongshu_list = self._build_zhongshu_from_elements(
                segments, level=1
            )
            if zhongshu_list:
                self.zhongshu_list = zhongshu_list
                return zhongshu_list

        # 降级：使用笔构建中枢
        if len(self.bis) >= 3:
            zhongshu_list = self._build_zhongshu_from_elements(
                self.bis, level=0
            )
            self.zhongshu_list = zhongshu_list
            return zhongshu_list

        self.zhongshu_list = []
        return []

    def _build_zhongshu_from_elements(self, elements: list, level: int) -> List[ZhongShu]:
        """
        从元素列表（线段或笔）构建中枢

        通用方法：线段和笔都有 high/low 属性，算法完全一致

        Args:
            elements: 元素列表（线段或笔）
            level: 中枢级别（1=线段级别, 0=笔级别）

        Returns:
            中枢列表
        """
        if len(elements) < 3:
            return []

        zhongshu_list = []
        i = 0
        used = set()

        while i < len(elements) - 2:
            if i in used:
                i += 1
                continue

            e1 = elements[i]
            e2 = elements[i + 1]
            e3 = elements[i + 2]

            # 计算重叠区间
            zg = min(e1.high, e2.high, e3.high)
            zd = max(e1.low, e2.low, e3.low)

            if zg > zd:
                gg = max(e1.high, e2.high, e3.high)
                dd = min(e1.low, e2.low, e3.low)

                current_elements = [e1, e2, e3]
                used.update([i, i + 1, i + 2])

                # 中枢延伸
                j = i + 3
                while j < len(elements):
                    next_e = elements[j]
                    if next_e.low < gg and next_e.high > dd:
                        current_elements.append(next_e)
                        used.add(j)
                        new_zg = min(zg, next_e.high)
                        new_zd = max(zd, next_e.low)
                        # 检查延伸后是否仍有重叠
                        if new_zg > new_zd:
                            zg = new_zg
                            zd = new_zd
                            gg = max(gg, next_e.high)
                            dd = min(dd, next_e.low)
                            j += 1
                        else:
                            # 延伸后无重叠，回退
                            current_elements.pop()
                            used.discard(j)
                            break
                    else:
                        break

                # 获取 start_index / end_index
                start_idx = getattr(e1, 'start_index', 0)
                end_idx = getattr(current_elements[-1], 'end_index', 0)

                # 如果元素是笔，提取 segment_list（空）但保存 bi_list
                segment_list = current_elements if level == 1 else []

                zhongshu = ZhongShu(
                    segment_list=segment_list,
                    high=zg,
                    low=zd,
                    high_point=gg,
                    low_point=dd,
                    level=level,
                    start_index=start_idx,
                    end_index=end_idx,
                )
                zhongshu._bi_list = current_elements if level == 0 else None

                zhongshu_list.append(zhongshu)
                i = j
            else:
                i += 1

        return zhongshu_list

    def determine_trend_type(self, zhongshu_list: List[ZhongShu]) -> TrendType:
        """
        判断走势类型（上涨/下跌/盘整）

        缠论走势定义：
        - 上涨趋势：后一个中枢的ZG > 前一个中枢的ZG，且ZD > 前一个中枢的ZD
        - 下跌趋势：后一个中枢的ZD < 前一个中枢的ZD，且ZG < 前一个中枢的ZG
        - 盘整：中枢之间有重叠

        Args:
            zhongshu_list: 中枢列表

        Returns:
            走势类型
        """
        if len(zhongshu_list) < 2:
            return TrendType.CONSOLIDATION

        # 比较最后两个中枢
        prev_zs = zhongshu_list[-2]
        curr_zs = zhongshu_list[-1]

        if curr_zs.high > prev_zs.high and curr_zs.low > prev_zs.low:
            return TrendType.UP
        elif curr_zs.high < prev_zs.high and curr_zs.low < prev_zs.low:
            return TrendType.DOWN
        else:
            return TrendType.CONSOLIDATION

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整分析流程

        Args:
            df: K线数据

        Returns:
            分析结果
        """
        # 1. 识别分型（含包含处理）
        fractals = self.identify_fractals(df)

        # 2. 识别笔
        bis = self.identify_bis(df, fractals)

        # 3. 识别线段
        segments = self.identify_segments(bis)

        # 4. 识别中枢
        zhongshu_list = self.identify_zhongshu(segments)

        # 5. 判断走势类型
        trend_type = self.determine_trend_type(zhongshu_list) if zhongshu_list else TrendType.CONSOLIDATION

        # 生成分析报告
        report = {
            "kline_count": len(df),
            "merged_kline_count": len(self.merged_df) if self.merged_df is not None else len(df),
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
            },
            "trend_type": trend_type.value
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
        result = {
            "high": zhongshu.high,
            "low": zhongshu.low,
            "high_point": zhongshu.high_point,
            "low_point": zhongshu.low_point,
            "level": zhongshu.level,
            "segment_count": len(zhongshu.segment_list),
            "level_name": "线段级" if zhongshu.level == 1 else "笔级",
        }
        # 如果是笔级别中枢，附加笔数量
        if zhongshu.level == 0 and hasattr(zhongshu, '_bi_list') and zhongshu._bi_list:
            result["bi_count"] = len(zhongshu._bi_list)
        return result
