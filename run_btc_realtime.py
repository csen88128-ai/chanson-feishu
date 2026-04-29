#!/usr/bin/env python3
"""
缠论 BTC 实时行情分析 — 本地独立运行

不依赖 LLM API / Coze 云平台，直接：
1. 调用 Binance API 获取 BTC 三周期实时 K 线
2. 运行缠论算法（结构分析 + 动力学分析）
3. 输出完整分析报告

用法:
    python run_btc_realtime.py
    python run_btc_realtime.py --intervals 1h,4h,1d
    python run_btc_realtime.py --symbol ETHUSDT
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# 设置本地 workspace 路径（解决 utils/__init__.py 中 decision_history 的路径依赖）
os.environ.setdefault("COZE_WORKSPACE_PATH", os.path.dirname(os.path.abspath(__file__)))

# 将 src 目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
import requests


# ═══════════════════════════════════════════
# 1. Binance 数据采集（直接 HTTP，不依赖 langchain tools）
# ═══════════════════════════════════════════

BINANCE_BASE = "https://api.binance.com/api/v3"
# 备用 endpoint（国内网络可能需要）
BINANCE_FALLBACKS = [
    "https://api1.binance.com/api/v3",
    "https://api2.binance.com/api/v3",
    "https://api3.binance.com/api/v3",
    "https://api4.binance.com/api/v3",
    "https://fapi.binance.com/api/v3",  # 有时可用
]

_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "ChanLunBot/5.1"})
    return _session


def _request_with_retry(url: str, params: dict, max_retries: int = 3, timeout: int = 15) -> requests.Response:
    """带重试和多 endpoint 切换的请求"""
    endpoints = [BINANCE_BASE] + BINANCE_FALLBACKS
    last_error = None

    for attempt in range(max_retries):
        for base in endpoints:
            try:
                full_url = f"{base}{url.replace(BINANCE_BASE, '')}" if base != BINANCE_BASE else url
                if not full_url.startswith("http"):
                    full_url = f"{base}/klines" if "/klines" in url else f"{base}/ticker/price"
                    # 简化：直接用 base + path
                    path = url.replace(BINANCE_BASE, "")
                    full_url = base + path

                resp = _get_session().get(full_url, params=params, timeout=timeout)
                resp.raise_for_status()
                return resp
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_error = e
                continue
        if attempt < max_retries - 1:
            time.sleep(1 * (attempt + 1))  # 递增等待

    raise ConnectionError(f"所有 endpoint 均失败: {last_error}")


def fetch_klines(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """从 Binance 获取 K 线数据，返回 DataFrame"""
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    resp = _request_with_retry(f"{BINANCE_BASE}/klines", params)
    raw = resp.json()

    df = pd.DataFrame(raw, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])

    # 类型转换
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df = df.drop(columns=["ignore"])

    return df


def fetch_ticker_price(symbol: str) -> float:
    """获取最新价格"""
    params = {"symbol": symbol}
    resp = _request_with_retry(f"{BINANCE_BASE}/ticker/price", params)
    return float(resp.json()["price"])


# ═══════════════════════════════════════════
# 2. 缠论算法分析
# ═══════════════════════════════════════════

def run_chanlun_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """对 DataFrame 运行完整的缠论结构+动力学分析"""
    from utils.chanlun_structure import ChanLunAnalyzer
    from utils.chanlun_dynamics import DynamicsAnalyzer

    # 结构分析
    structure_analyzer = ChanLunAnalyzer()
    structure_result = structure_analyzer.analyze(df)

    # 动力学分析（传入笔和线段数据，启用基于笔/线段的背驰识别）
    bis = structure_analyzer.bis if hasattr(structure_analyzer, "bis") else None
    segments = structure_analyzer.segments if hasattr(structure_analyzer, "segments") else None

    dynamics_analyzer = DynamicsAnalyzer()
    dynamics_result = dynamics_analyzer.analyze(df, bis=bis, segments=segments)

    return {
        "structure": structure_result,
        "dynamics": dynamics_result,
    }


# ═══════════════════════════════════════════
# 3. 报告生成
# ═══════════════════════════════════════════

def format_price(price: float) -> str:
    return f"{price:,.2f}"


def generate_report(symbol: str, current_price: float, results: Dict[str, Dict], intervals: List[str]) -> str:
    """生成可读的分析报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("=" * 72)
    lines.append("  🔶 缠论多智能体系统 v5.1 — BTC 实时行情分析报告")
    lines.append("=" * 72)
    lines.append(f"  📅 时间: {now}")
    lines.append(f"  💰 交易对: {symbol}")
    lines.append(f"  💲 当前价格: ${format_price(current_price)}")
    lines.append("")

    # 三周期汇总
    lines.append("─" * 72)
    lines.append("  📊 三周期结构总览")
    lines.append("─" * 72)
    lines.append(f"  {'周期':<6} {'K线数':<8} {'笔数':<6} {'线段数':<6} {'中枢数':<6} {'走势类型':<8} {'背驰数':<6}")
    lines.append("  " + "-" * 50)

    for iv in intervals:
        r = results.get(iv, {})
        s = r.get("structure", {})
        d = r.get("dynamics", {})
        lines.append(
            f"  {iv:<6} "
            f"{s.get('kline_count', '?'):<8} "
            f"{s.get('bis', {}).get('count', '?'):<6} "
            f"{s.get('segments', {}).get('count', '?'):<6} "
            f"{s.get('zhongshu', {}).get('count', '?'):<6} "
            f"{s.get('trend_type', '?'):<8} "
            f"{d.get('divergences', {}).get('count', '?'):<6}"
        )
    lines.append("")

    # 每个周期详细分析
    for iv in intervals:
        r = results.get(iv, {})
        s = r.get("structure", {})
        d = r.get("dynamics", {})

        lines.append("═" * 72)
        lines.append(f"  📈 {iv} 周期详细分析")
        lines.append("═" * 72)

        # ── 结构分析 ──
        lines.append("")
        lines.append("  ┌─ 结构分析 ─────────────────────────────────")
        lines.append(f"  │ K线总数: {s.get('kline_count', 'N/A')}  |  合并后: {s.get('merged_kline_count', 'N/A')}")
        lines.append(f"  │ 分型: {s.get('fractals', {}).get('count', 0)} 个 "
                     f"(顶 {s.get('fractals', {}).get('top_count', 0)} / "
                     f"底 {s.get('fractals', {}).get('bottom_count', 0)})")

        bis_info = s.get("bis", {})
        lines.append(f"  │ 笔: {bis_info.get('count', 0)} 笔 "
                     f"(上 {bis_info.get('up_count', 0)} / 下 {bis_info.get('down_count', 0)})")
        last_bi = bis_info.get("last_bi")
        if last_bi:
            lines.append(f"  │ 最后一笔: 方向={last_bi.get('direction')} "
                         f"起点={format_price(last_bi.get('start_price', 0))} "
                         f"终点={format_price(last_bi.get('end_price', 0))} "
                         f"高={format_price(last_bi.get('high', 0))} "
                         f"低={format_price(last_bi.get('low', 0))}")

        seg_info = s.get("segments", {})
        lines.append(f"  │ 线段: {seg_info.get('count', 0)} 段 "
                     f"(上 {seg_info.get('up_count', 0)} / 下 {seg_info.get('down_count', 0)})")
        last_seg = seg_info.get("last_segment")
        if last_seg:
            lines.append(f"  │ 最后线段: 方向={last_seg.get('direction')} "
                         f"起点={format_price(last_seg.get('start_price', 0))} "
                         f"终点={format_price(last_seg.get('end_price', 0))} "
                         f"高={format_price(last_seg.get('high', 0))} "
                         f"低={format_price(last_seg.get('low', 0))}")

        zs_info = s.get("zhongshu", {})
        lines.append(f"  │ 中枢: {zs_info.get('count', 0)} 个")
        latest_zs = zs_info.get("latest")
        if latest_zs:
            lines.append(f"  │ 最新中枢: "
                         f"高={format_price(latest_zs.get('high', 0))} "
                         f"低={format_price(latest_zs.get('low', 0))} "
                         f"高点={format_price(latest_zs.get('high_point', 0))} "
                         f"低点={format_price(latest_zs.get('low_point', 0))} "
                         f"级别={latest_zs.get('level_name', latest_zs.get('level', '?'))} "
                         f"组成线段数={latest_zs.get('segment_count', latest_zs.get('element_count', '?'))}")

        lines.append(f"  │ 走势类型: {s.get('trend_type', 'N/A')}")
        lines.append("  └──────────────────────────────────────────────")

        # ── 动力学分析 ──
        lines.append("")
        lines.append("  ┌─ 动力学分析 ───────────────────────────────")

        macd = d.get("macd", {})
        if macd:
            lines.append(f"  │ MACD: DIF={macd.get('dif', 'N/A')}  DEA={macd.get('dea', 'N/A')}  "
                         f"MACD柱={macd.get('macd', 'N/A')}")
            lines.append(f"  │ 状态: {macd.get('macd_state', 'N/A')}")
            lines.append(f"  │ DIF趋势: {macd.get('dif_trend', 'N/A')}  DEA趋势: {macd.get('dea_trend', 'N/A')}")
            lines.append(f"  │ 交叉: {macd.get('cross_type', 'N/A')}")
            lines.append(f"  │ 强度: {macd.get('strength', 'N/A')}")
            lines.append(f"  │ 最新价格: {format_price(macd.get('latest_price', 0))}")

        div_info = d.get("divergences", {})
        lines.append(f"  │ 背驰: {div_info.get('count', 0)} 个")
        latest_div = div_info.get("latest")
        if latest_div:
            lines.append(f"  │ 最新背驰: 类型={latest_div.get('type')} "
                         f"强度={latest_div.get('strength')} "
                         f"级别={latest_div.get('level', '?')} "
                         f"起始价={format_price(latest_div.get('start_price', 0))} "
                         f"结束价={format_price(latest_div.get('end_price', 0))}")
            if latest_div.get("macd_area") is not None:
                lines.append(f"  │ 背驰MACD面积: {latest_div.get('macd_area')}")

        # 列出所有背驰
        all_divs = div_info.get("all", [])
        if len(all_divs) > 1:
            lines.append(f"  │ ── 全部背驰 ({len(all_divs)}) ──")
            for i, dv in enumerate(all_divs):
                lines.append(f"  │   {i+1}. {dv.get('type')} {dv.get('strength')} "
                             f"[{format_price(dv.get('start_price', 0))} → "
                             f"{format_price(dv.get('end_price', 0))}] "
                             f"level={dv.get('level', '?')}")

        lines.append("  └──────────────────────────────────────────────")
        lines.append("")

    # ── 综合研判 ──
    lines.append("═" * 72)
    lines.append("  🎯 综合研判（算法层，不涉及 LLM 决策）")
    lines.append("═" * 72)
    lines.append("")

    # 多周期结构共振判断
    trend_types = {}
    zhongshu_counts = {}
    divergence_counts = {}
    for iv in intervals:
        r = results.get(iv, {})
        trend_types[iv] = r.get("structure", {}).get("trend_type", "unknown")
        zhongshu_counts[iv] = r.get("structure", {}).get("zhongshu", {}).get("count", 0)
        divergence_counts[iv] = r.get("dynamics", {}).get("divergences", {}).get("count", 0)

    lines.append(f"  走势类型: " + " | ".join(f"{iv}={trend_types[iv]}" for iv in intervals))
    lines.append(f"  中枢数量: " + " | ".join(f"{iv}={zhongshu_counts[iv]}" for iv in intervals))
    lines.append(f"  背驰数量: " + " | ".join(f"{iv}={divergence_counts[iv]}" for iv in intervals))

    # 大级别定方向
    big_iv = intervals[-1] if len(intervals) > 1 else intervals[0]
    big_trend = trend_types.get(big_iv, "unknown")
    lines.append("")
    lines.append(f"  📌 大级别({big_iv})方向: {big_trend}")

    # 背驰信号
    has_top_div = any(
        any(d.get("type") == "top" for d in results.get(iv, {}).get("dynamics", {}).get("divergences", {}).get("all", []))
        for iv in intervals
    )
    has_bottom_div = any(
        any(d.get("type") == "bottom" for d in results.get(iv, {}).get("dynamics", {}).get("divergences", {}).get("all", []))
        for iv in intervals
    )

    if has_top_div:
        lines.append("  ⚠️  顶背驰信号出现，注意回调风险")
    if has_bottom_div:
        lines.append("  ✅ 底背驰信号出现，关注买入机会")
    if not has_top_div and not has_bottom_div:
        lines.append("  ℹ️  当前无背驰信号，趋势延续中")

    lines.append("")
    lines.append("=" * 72)
    lines.append("  ⚠️  免责声明：本报告仅基于缠论算法分析，不构成投资建议")
    lines.append("  交易决策需结合 LLM 多智能体综合研判（需 LLM API 环境）")
    lines.append("=" * 72)

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 4. 主流程
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="缠论 BTC 实时行情分析")
    parser.add_argument("--symbol", default="BTCUSDT", help="交易对 (默认: BTCUSDT)")
    parser.add_argument("--intervals", default="1h,4h,1d", help="K线周期，逗号分隔 (默认: 1h,4h,1d)")
    parser.add_argument("--limit", type=int, default=500, help="每周期K线数量 (默认: 500)")
    parser.add_argument("--save-json", action="store_true", help="同时保存 JSON 格式结果")
    args = parser.parse_args()

    intervals = [x.strip() for x in args.intervals.split(",")]

    print("\n" + "=" * 72)
    print("  🔶 缠论 BTC 实时行情分析")
    print("=" * 72)
    print(f"  交易对: {args.symbol}  |  周期: {', '.join(intervals)}  |  K线数: {args.limit}")
    print("=" * 72 + "\n")

    # 1. 获取当前价格
    print("📡 获取实时价格...")
    try:
        current_price = fetch_ticker_price(args.symbol)
        print(f"   ✅ {args.symbol} 当前价格: ${format_price(current_price)}")
    except Exception as e:
        print(f"   ❌ 获取价格失败: {e}")
        current_price = 0.0

    # 2. 逐周期获取 K 线 + 运行缠论分析
    results = {}
    for iv in intervals:
        print(f"\n📡 获取 {args.symbol} {iv} K线数据...")
        try:
            df = fetch_klines(args.symbol, iv, args.limit)
            print(f"   ✅ 获取 {len(df)} 根K线  "
                  f"({df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]})")
        except Exception as e:
            print(f"   ❌ 获取K线失败: {e}")
            continue

        print(f"   🔍 运行缠论分析...")
        t0 = time.time()
        try:
            analysis = run_chanlun_analysis(df)
            elapsed = time.time() - t0
            results[iv] = analysis
            print(f"   ✅ 分析完成 ({elapsed:.2f}s)")
        except Exception as e:
            print(f"   ❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()

    if not results:
        print("\n❌ 所有周期分析均失败，无法生成报告")
        sys.exit(1)

    # 3. 生成报告
    report = generate_report(args.symbol, current_price, results, intervals)

    print("\n" + report)

    # 4. 保存报告
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(data_dir, f"btc_realtime_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 报告已保存: {report_path}")

    # 5. 可选：保存 JSON
    if args.save_json:
        json_path = os.path.join(data_dir, f"btc_realtime_{timestamp}.json")
        json_output = {
            "timestamp": timestamp,
            "symbol": args.symbol,
            "current_price": current_price,
            "intervals": intervals,
            "results": results,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        print(f"📄 JSON 已保存: {json_path}")

    return results


if __name__ == "__main__":
    main()
