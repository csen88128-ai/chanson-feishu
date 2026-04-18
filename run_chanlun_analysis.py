#!/usr/bin/env python3
"""
缠论完整分析脚本 - 实时K线数据 + 全链路缠论分析
分型→笔→线段→中枢→背驰→买卖点→增强版V2→趋势力度
"""
import sys
import os
import importlib

# 把 src 目录加到 path，但替换掉 utils/__init__.py 避免加载 decision_history
_src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
_utils_dir = os.path.join(_src_dir, 'utils')
sys.path.insert(0, _src_dir)

# 临时用空模块替换 utils 包的 __init__，避免 decision_history 加载失败
import types
_dummy_utils = types.ModuleType('utils')
_dummy_utils.__path__ = [_utils_dir]
_dummy_utils.__package__ = 'utils'
sys.modules['utils'] = _dummy_utils

from utils.chanlun_structure import ChanLunAnalyzer
from utils.chanlun_dynamics import DynamicsAnalyzer
from utils.chanlun_algorithms_v2 import (
    AdvancedChanLunAnalyzer, EnhancedDynamicsAnalyzer,
    TrendStrengthAnalyzer, analyze_enhanced_structure,
    analyze_enhanced_divergence, analyze_trend_strength
)

import json
import requests
import pandas as pd
from datetime import datetime


def get_klines(symbol='BTCUSDT', interval='1h', limit=500):
    """获取Binance K线数据"""
    session = requests.Session()
    r = session.get('https://api.binance.com/api/v3/klines',
                    params={'symbol': symbol, 'interval': interval, 'limit': limit},
                    timeout=15)
    r.raise_for_status()
    klines = r.json()

    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
        df[col] = pd.to_numeric(df[col])
    return df


def identify_signals(bis, zhongshus, dynamics_result):
    """
    识别缠论三类买卖点（v2.1 修正版）

    缠论买卖点定义（严格版）：
    - 第一类买点：下跌趋势中，最后一个向下笔底背驰，形成底分型确认
    - 第二类买点：第一类买点后的上涨回调，回调低点不低于第一类买点低点
    - 第三类买点：向上突破中枢上沿（ZG），且不回拉入中枢
    - 第一类卖点：上涨趋势中，最后一个向上笔顶背驰，形成顶分型确认
    - 第二类卖点：第一类卖点后的下跌反弹，反弹高点不高于第一类卖点高点
    - 第三类卖点：向下突破中枢下沿（ZD），且不回拉入中枢
    """
    buy_signals = []
    sell_signals = []

    # 需要至少3笔才能判断买卖点
    if len(bis) < 3:
        return buy_signals, sell_signals

    last_bi = bis[-1]
    last_3_bis = bis[-3:]

    # ===== 买点判断 =====

    # 第一类买点：下跌趋势 + 底背驰
    # 缠论：下跌趋势中，由次级别的第一类买点引发本级别的转折
    if last_bi.direction.value == 'down':
        # 检查下跌趋势：最近3笔的方向是否为 下-上-下
        if (last_3_bis[0].direction.value == 'down' and
            last_3_bis[1].direction.value == 'up' and
            last_3_bis[2].direction.value == 'down'):
            # 检查是否创新低
            if last_bi.low < last_3_bis[0].low:
                # 检查底背驰
                div = dynamics_result['divergences']
                has_bottom_div = False
                div_strength = 'unknown'
                if div['count'] > 0:
                    for d in div.get('all', []):
                        if d['type'] == 'bottom' and d['level'] == 'bi':
                            has_bottom_div = True
                            div_strength = d['strength']
                            break
                    # 兼容旧版divergence（没有level字段）
                    if not has_bottom_div and div['latest'] and div['latest']['type'] == 'bottom':
                        has_bottom_div = True
                        div_strength = div['latest']['strength']

                if has_bottom_div:
                    buy_signals.append({
                        'type': '第一类买点',
                        'description': '下跌趋势底背驰确认',
                        'price': round(last_bi.end_price, 2),
                        'confidence': 0.85 if div_strength == 'strong' else (0.75 if div_strength == 'moderate' else 0.65),
                        'reason': f'下跌趋势+底背驰({div_strength})+底分型',
                        'stop_loss': round(last_bi.low * 0.99, 2),  # 止损位：低点下方1%
                        'target': round(last_3_bis[1].high, 2),  # 目标位：前一个反弹高点
                    })

    # 第二类买点：上涨回调不破前低
    # 缠论：第一类买点上涨后的回调，低点不低于第一类买点低点
    if len(bis) >= 4 and last_bi.direction.value == 'down':
        # 前一笔向上，当前笔向下回调
        prev_bi = bis[-2]
        if prev_bi.direction.value == 'up':
            # 检查回调低点是否高于前一个低点
            # 找到前一个向下笔的低点
            prev_down_bis = [b for b in bis[:-2] if b.direction.value == 'down']
            if prev_down_bis and last_bi.end_price > prev_down_bis[-1].end_price:
                buy_signals.append({
                    'type': '第二类买点',
                    'description': '上涨回调不破前低',
                    'price': round(last_bi.end_price, 2),
                    'confidence': 0.75,
                    'reason': '回调不破前低，趋势延续',
                    'stop_loss': round(last_bi.low * 0.99, 2),
                    'target': round(prev_bi.high, 2),
                })

    # 第三类买点：向上突破中枢上沿
    # 缠论：走势突破中枢上沿后，回调不进入中枢
    if zhongshus and last_bi.direction.value == 'up':
        last_zs = zhongshus[-1]
        if last_bi.end_price > last_zs.high and last_bi.low > last_zs.low:
            buy_signals.append({
                'type': '第三类买点',
                'description': f'向上突破中枢上沿ZG={last_zs.high:.2f}且回调不入中枢',
                'price': round(last_bi.end_price, 2),
                'confidence': 0.85,
                'reason': '突破中枢上沿+回调不入中枢',
                'stop_loss': round(last_zs.high * 0.99, 2),  # 止损：中枢上沿下方
                'target': round(last_bi.end_price * 1.05, 2),  # 目标：5%上方
            })

    # ===== 卖点判断 =====

    # 第一类卖点：上涨趋势 + 顶背驰
    if last_bi.direction.value == 'up':
        if (last_3_bis[0].direction.value == 'up' and
            last_3_bis[1].direction.value == 'down' and
            last_3_bis[2].direction.value == 'up'):
            if last_bi.high > last_3_bis[0].high:
                div = dynamics_result['divergences']
                has_top_div = False
                div_strength = 'unknown'
                if div['count'] > 0:
                    for d in div.get('all', []):
                        if d['type'] == 'top' and d['level'] == 'bi':
                            has_top_div = True
                            div_strength = d['strength']
                            break
                    if not has_top_div and div['latest'] and div['latest']['type'] == 'top':
                        has_top_div = True
                        div_strength = div['latest']['strength']

                if has_top_div:
                    sell_signals.append({
                        'type': '第一类卖点',
                        'description': '上涨趋势顶背驰确认',
                        'price': round(last_bi.end_price, 2),
                        'confidence': 0.85 if div_strength == 'strong' else (0.75 if div_strength == 'moderate' else 0.65),
                        'reason': f'上涨趋势+顶背驰({div_strength})+顶分型',
                    })

    # 第二类卖点：下跌反弹不破前高
    if len(bis) >= 4 and last_bi.direction.value == 'up':
        prev_bi = bis[-2]
        if prev_bi.direction.value == 'down':
            prev_up_bis = [b for b in bis[:-2] if b.direction.value == 'up']
            if prev_up_bis and last_bi.end_price < prev_up_bis[-1].end_price:
                sell_signals.append({
                    'type': '第二类卖点',
                    'description': '下跌反弹不破前高',
                    'price': round(last_bi.end_price, 2),
                    'confidence': 0.75,
                    'reason': '反弹不破前高，趋势延续',
                })

    # 第三类卖点：向下突破中枢下沿
    if zhongshus and last_bi.direction.value == 'down':
        last_zs = zhongshus[-1]
        if last_bi.end_price < last_zs.low and last_bi.high < last_zs.high:
            sell_signals.append({
                'type': '第三类卖点',
                'description': f'向下突破中枢下沿ZD={last_zs.low:.2f}且反弹不入中枢',
                'price': round(last_bi.end_price, 2),
                'confidence': 0.85,
                'reason': '突破中枢下沿+反弹不入中枢',
            })

    return buy_signals, sell_signals


def analyze_interval(interval):
    """对单个周期进行完整缠论分析"""
    print(f'\n{"="*60}')
    print(f'  📊 BTC/USDT {interval} 周期 - 缠论完整分析')
    print(f'{"="*60}')

    # 1. 获取K线
    df = get_klines('BTCUSDT', interval, 500)
    print(f'  📡 获取K线: {len(df)}根, {df["timestamp"].iloc[0]} → {df["timestamp"].iloc[-1]}')

    # 2. 基础结构分析
    analyzer = ChanLunAnalyzer()
    fractals = analyzer.identify_fractals(df)
    bis = analyzer.identify_bis(df, fractals)
    segments = analyzer.identify_segments(bis)
    zhongshus = analyzer.identify_zhongshu(segments)
    # 使用 analyzer.analyze() 获取统计摘要（不再重复计算）
    structure_result = analyzer.analyze(df)
    print(f'  📐 分型={structure_result["fractals"]["count"]}, 笔={len(bis)}, 线段={len(segments)}, 中枢={len(zhongshus)}')

    # 3. 动力学分析（传入笔和线段，使用基于笔/线段的背驰识别）
    dyn_analyzer = DynamicsAnalyzer()
    dynamics_result = dyn_analyzer.analyze(df, bis=bis, segments=segments)
    div_count = dynamics_result['divergences']['count']
    macd_state = dynamics_result['macd']['macd_state']
    cross = dynamics_result['macd']['cross_type']
    print(f'  ⚡ MACD={macd_state}, 交叉={cross}, 背驰={div_count}')

    # 4. 增强版中枢
    enhanced_zhongshus = analyze_enhanced_structure(df, segments)
    for i, zs in enumerate(enhanced_zhongshus):
        print(f'  🏛️ 中枢V2 #{i+1}: ZG={zs.high:.0f} ZD={zs.low:.0f} 状态={zs.status.value} 强度={zs.strength}')

    # 5. 增强版背驰
    enhanced_divergences = analyze_enhanced_divergence(df, bis)
    for div in enhanced_divergences:
        print(f'  🔀 增强背驰: type={div.get("type")}, kinds={div.get("divergence_types")}, confirmed={div.get("confirmed")}')

    # 6. 趋势力度
    trend = analyze_trend_strength(df, window=20)
    print(f'  💪 趋势力度: ADX={trend["adx"]}, 综合={trend["trend_strength"]}, 方向={trend["trend_direction"]}')

    # 7. 买卖点
    buy_signals, sell_signals = identify_signals(bis, zhongshus, dynamics_result)
    for s in buy_signals:
        print(f'  🟢 {s["type"]}: ${s["price"]:.0f} ({s["reason"]})')
    for s in sell_signals:
        print(f'  🔴 {s["type"]}: ${s["price"]:.0f} ({s["reason"]})')

    # 8. 当前走势判断
    price = float(df['close'].iloc[-1])
    if zhongshus:
        last_zs = zhongshus[-1]
        position = '中枢上方(偏多)' if price > last_zs.high else ('中枢下方(偏空)' if price < last_zs.low else '中枢内部(震荡)')
    else:
        position = '无中枢'

    last_bi_dir = bis[-1].direction.value if bis else 'unknown'
    last_seg_dir = segments[-1].direction.value if segments else 'unknown'
    print(f'  📍 当前位置: {position}')
    print(f'  📍 最新笔: {last_bi_dir}, 最新线段: {last_seg_dir}')
    print(f'  💰 最新价格: ${price:,.2f}')

    # 构建结果
    result = {
        'interval': interval,
        'kline_count': len(df),
        'time_range': {'start': df['timestamp'].iloc[0].isoformat(), 'end': df['timestamp'].iloc[-1].isoformat()},
        'latest_price': price,
        'price_range': {'highest': float(df['high'].max()), 'lowest': float(df['low'].min())},

        # 缠论基础结构
        'structure': {
            'fractals': structure_result['fractals'],
            'bis': {
                'count': structure_result['bis']['count'],
                'up_count': structure_result['bis']['up_count'],
                'down_count': structure_result['bis']['down_count'],
                'last_bi': structure_result['bis']['last_bi'],
                'last_5_bis': [{
                    'direction': bi.direction.value,
                    'start_price': round(bi.start_price, 2),
                    'end_price': round(bi.end_price, 2),
                    'high': round(bi.high, 2),
                    'low': round(bi.low, 2),
                } for bi in bis[-5:]],
            },
            'segments': {
                'count': structure_result['segments']['count'],
                'up_count': structure_result['segments']['up_count'],
                'down_count': structure_result['segments']['down_count'],
                'last_segment': structure_result['segments']['last_segment'],
                'last_3_segments': [{
                    'direction': seg.direction.value,
                    'start_price': round(seg.start_price, 2),
                    'end_price': round(seg.end_price, 2),
                    'high': round(seg.high, 2),
                    'low': round(seg.low, 2),
                    'bi_count': len(seg.bi_list) if hasattr(seg, 'bi_list') else 0,
                } for seg in segments[-3:]],
            },
            'zhongshu': {
                'count': structure_result['zhongshu']['count'],
                'latest': structure_result['zhongshu']['latest'],
                'all': [{
                    'ZG': round(zs.high, 2), 'ZD': round(zs.low, 2),
                    'GG': round(zs.high_point, 2), 'DD': round(zs.low_point, 2),
                    'level': zs.level,
                } for zs in zhongshus],
            }
        },

        # 动力学
        'dynamics': dynamics_result,

        # 增强版中枢
        'enhanced_zhongshus': [{
            'ZG': round(zs.high, 2), 'ZD': round(zs.low, 2),
            'GG': round(zs.high_point, 2), 'DD': round(zs.low_point, 2),
            'level': zs.level, 'status': zs.status.value,
            'segment_count': zs.segment_count, 'strength': zs.strength,
            'overlap_count': zs.overlap_count,
        } for zs in enhanced_zhongshus],

        # 增强版背驰
        'enhanced_divergences': enhanced_divergences,

        # 趋势力度
        'trend_strength': trend,

        # 买卖点
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,

        # 走势判断
        'market_structure': {
            'position': position,
            'last_bi_direction': last_bi_dir,
            'last_segment_direction': last_seg_dir,
        }
    }
    return result


def main():
    results = {}
    for interval in ['1h', '4h', '1d']:
        try:
            results[f'BTC_{interval}'] = analyze_interval(interval)
        except Exception as e:
            results[f'BTC_{interval}'] = {'error': str(e)}
            import traceback
            traceback.print_exc()

    results['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 保存
    import os
    os.makedirs('data', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = f'data/chanlun_analysis_{ts}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f'\n📁 分析结果已保存到: {json_path}')

    # 打印最终摘要
    print(f'\n{"="*60}')
    print(f'  📋 缠论多周期综合分析摘要')
    print(f'{"="*60}')
    for key in ['BTC_1h', 'BTC_4h', 'BTC_1d']:
        if key in results and 'error' not in results[key]:
            r = results[key]
            ms = r.get('market_structure', {})
            buy = r.get('buy_signals', [])
            sell = r.get('sell_signals', [])
            dyn = r.get('dynamics', {}).get('macd', {})
            ts_data = r.get('trend_strength', {})
            print(f'  {key}: 价格=${r["latest_price"]:,.0f} 位置={ms.get("position","?")} '
                  f'MACD={dyn.get("macd_state","?")} 趋势力度={ts_data.get("trend_strength",0):.2f} '
                  f'买点={len(buy)} 卖点={len(sell)}')
    print(f'{"="*60}')

    return results


if __name__ == '__main__':
    main()
