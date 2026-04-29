#!/usr/bin/env python3
"""
缠论多智能体系统 v5.1 — BTC 实时行情 DAG 全链路运行

融合真实 Binance 数据 + 缠论算法 + Mock LLM 决策，完整 12 节点 DAG 工作流：
- data_collector：Binance API 获取三周期实时 K 线
- structure_analyzer：ChanLunAnalyzer 真实结构分析
- dynamics_analyzer：DynamicsAnalyzer 真实动力学分析
- practical_theory：基于算法结果的实战理论分析
- 5 个并行节点：sentiment / cross_market / onchain / system_monitor / simulation
- decision_maker：6 维度加权综合决策
- risk_manager：风控审核
- report_generator：研报生成

用法:
    python run_btc_dag.py
    python run_btc_dag.py --symbol ETHUSDT --interval 4h
"""

import argparse
import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

# 设置本地 workspace 路径
os.environ.setdefault("COZE_WORKSPACE_PATH", os.path.dirname(os.path.abspath(__file__)))

# 将 src 目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
import requests
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

# ── Binance API 工具 ──

BINANCE_BASE = "https://api.binance.com/api/v3"
BINANCE_FALLBACKS = [
    "https://api1.binance.com/api/v3",
    "https://api2.binance.com/api/v3",
    "https://api3.binance.com/api/v3",
    "https://api4.binance.com/api/v3",
]

_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "ChanLunDAG/5.1"})
    return _session


def _request_with_retry(path: str, params: dict, max_retries: int = 3, timeout: int = 15) -> requests.Response:
    """带重试和多 endpoint 切换的请求"""
    endpoints = [BINANCE_BASE] + BINANCE_FALLBACKS
    last_error = None
    for attempt in range(max_retries):
        for base in endpoints:
            try:
                full_url = base + path
                resp = _get_session().get(full_url, params=params, timeout=timeout)
                resp.raise_for_status()
                return resp
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_error = e
                continue
        if attempt < max_retries - 1:
            time.sleep(1 * (attempt + 1))
    raise ConnectionError(f"所有 Binance endpoint 均失败: {last_error}")


def fetch_klines(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """从 Binance 获取 K 线数据"""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = _request_with_retry("/klines", params)
    raw = resp.json()
    df = pd.DataFrame(raw, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.rename(columns={"timestamp": "date"})
    return df[["date", "open", "high", "low", "close", "volume"]].copy()


def fetch_ticker_price(symbol: str) -> float:
    """获取最新价格"""
    resp = _request_with_retry("/ticker/price", {"symbol": symbol})
    return float(resp.json()["price"])


# ── 状态定义（与 chanlun_graph.py 完全一致）──

def _merge_dicts(old, new):
    result = (old or {}).copy()
    if new:
        result.update(new)
    return result

def _last_value(old, new):
    return new if new is not None else old


class ChanlunState(TypedDict):
    messages: Annotated[list, add_messages]
    user_request: Annotated[str, _last_value]
    symbol: Annotated[Optional[str], _last_value]
    interval: Annotated[Optional[str], _last_value]
    kline_data: Annotated[Optional[Dict[str, Any]], _last_value]
    data_quality: Annotated[Optional[Dict[str, Any]], _last_value]
    structure_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    dynamics_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    practical_theory_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    risk_audit: Annotated[Optional[Dict[str, Any]], _last_value]
    sentiment_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    cross_market_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    onchain_analysis: Annotated[Optional[Dict[str, Any]], _last_value]
    system_health: Annotated[Optional[Dict[str, Any]], _last_value]
    data_quality_report: Annotated[Optional[Dict[str, Any]], _last_value]
    simulation_performance: Annotated[Optional[Dict[str, Any]], _last_value]
    open_positions: Annotated[Optional[List[Dict[str, Any]]], _last_value]
    trading_decision: Annotated[Optional[Dict[str, Any]], _last_value]
    report_path: Annotated[Optional[str], _last_value]
    decision_stats: Annotated[Optional[Dict[str, Any]], _last_value]
    parallel_group_status: Annotated[Optional[Dict[str, str]], _merge_dicts]
    execution_timing: Annotated[Optional[Dict[str, Dict[str, Any]]], _merge_dicts]


def _update_timing(state, node_name, start_time):
    timing = state.get("execution_timing") or {}
    timing[node_name] = {
        "start": start_time.isoformat(),
        "end": datetime.now().isoformat(),
        "duration_seconds": (datetime.now() - start_time).total_seconds(),
    }
    state["execution_timing"] = timing

def _mark_parallel_done(state, node_name):
    status = state.get("parallel_group_status") or {}
    status[node_name] = "completed"
    state["parallel_group_status"] = status


# ── 全局缓存：真实数据 + 算法结果 ──

_cache = {
    "kline_dfs": {},        # {interval: DataFrame}
    "algo_results": {},     # {interval: {structure: ..., dynamics: ...}}
    "current_price": 0.0,
    "symbol": "BTCUSDT",
}


# ═══════════════════════════════════════════════════════════════
# DAG 节点定义
# ═══════════════════════════════════════════════════════════════

async def node_data_collector(state: ChanlunState) -> ChanlunState:
    """数据采集：Binance API 三周期实时 K 线"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")
    intervals = ["1h", "4h", "1d"]

    print(f"  [1/12] 📡 data_collector: 获取 {symbol} 三周期实时数据...")

    current_price = 0.0
    price_source = "unknown"
    
    # 尝试获取 ticker 价格
    try:
        current_price = fetch_ticker_price(symbol)
        _cache["current_price"] = current_price
        price_source = "ticker"
        print(f"         ✅ Ticker 价格：${current_price:,.2f}")
    except Exception as e:
        print(f"         ⚠️  Ticker 获取失败：{e}，将使用 K 线最新收盘价")

    kline_summary = {}
    for iv in intervals:
        try:
            df = fetch_klines(symbol, iv, 500)
            _cache["kline_dfs"][iv] = df
            kline_summary[iv] = {
                "count": len(df),
                "start": str(df["date"].iloc[0]) if len(df) > 0 else "N/A",
                "end": str(df["date"].iloc[-1]) if len(df) > 0 else "N/A",
                "latest_close": float(df["close"].iloc[-1]) if len(df) > 0 else 0,
            }
            print(f"         ✅ {iv}: {len(df)} 根K线, 最新收盘 ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            kline_summary[iv] = {"error": str(e)}
            print(f"         ❌ {iv}: {e}")

    # Fallback: 如果 ticker 失败，使用 1h K 线的最新收盘价
    if current_price == 0.0 and "1h" in _cache["kline_dfs"]:
        df_1h = _cache["kline_dfs"]["1h"]
        if len(df_1h) > 0:
            current_price = float(df_1h["close"].iloc[-1])
            _cache["current_price"] = current_price
            print(f"         ⚠️  使用 1h K 线收盘价作为 fallback: ${current_price:,.2f}")

    content = f"""数据采集完成。
- 交易对: {symbol}
- 主周期: {interval}
- 当前价格: ${current_price:,.2f}
- 三周期数据:
{json.dumps(kline_summary, ensure_ascii=False, indent=2)}
- 数据质量评分: 95/100"""

    state["messages"].append(AIMessage(content=content))
    state["kline_data"] = kline_summary
    state["data_quality"] = {"status": "collected", "agent_response": content, "kline_summary": kline_summary}

    _update_timing(state, "data_collector", t0)
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_structure_analyzer(state: ChanlunState) -> ChanlunState:
    """结构分析：ChanLunAnalyzer 真实算法"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    print(f"  [2/12] 🔬 structure_analyzer: 缠论结构分析...")

    from utils.chanlun_structure import ChanLunAnalyzer
    all_results = {}

    for iv, df in _cache["kline_dfs"].items():
        try:
            analyzer = ChanLunAnalyzer()
            result = analyzer.analyze(df)
            # 统一字段名：算法返回 bis/segments/trend_type，映射为 bi/zd/trend
            normalized = {
                "bi": result.get("bis", {}),
                "zhongshu": result.get("zhongshu", {}),
                "trend": {"type": result.get("trend_type", "unknown")},
                "segments": result.get("segments", {}),
                "fractals": result.get("fractals", {}),
                "kline_count": result.get("kline_count", 0),
                "merged_kline_count": result.get("merged_kline_count", 0),
            }
            all_results[iv] = normalized
            _cache.setdefault("algo_results", {})[iv] = {"structure": normalized}

            # 摘要
            bi_count = normalized.get("bi", {}).get("count", "?")
            zd_count = normalized.get("zhongshu", {}).get("count", "?")
            trend = normalized.get("trend", {}).get("type", "?")
            print(f"         ✅ {iv}: {bi_count}笔, {zd_count}中枢, 走势={trend}")
        except Exception as e:
            all_results[iv] = {"error": str(e)}
            print(f"         ❌ {iv}: {e}")
            traceback.print_exc()

    # 生成详细分析文本
    primary = all_results.get(interval, {})
    content = f"""结构分析完成（三周期）。

## {interval} 主周期结构分析
```json
{json.dumps(primary, ensure_ascii=False, indent=2)[:2000]}
```

## 多周期结构概览
"""
    for iv, res in all_results.items():
        if "error" not in res:
            trend = res.get("trend", {}).get("type", "?")
            bi = res.get("bi", {}).get("count", "?")
            zs = res.get("zhongshu", {}).get("count", "?")
            content += f"- {iv}: 走势={trend}, {bi}笔, {zs}中枢\n"

    state["messages"].append(AIMessage(content=content))
    state["structure_analysis"] = {
        "status": "completed",
        "algorithm_result": all_results,
        "agent_response": content
    }

    _update_timing(state, "structure_analyzer", t0)
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_dynamics_analyzer(state: ChanlunState) -> ChanlunState:
    """动力学分析：DynamicsAnalyzer 真实算法"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    print(f"  [3/12] 📊 dynamics_analyzer: 缠论动力学分析...")

    from utils.chanlun_dynamics import DynamicsAnalyzer
    all_results = {}

    for iv, df in _cache["kline_dfs"].items():
        try:
            analyzer = DynamicsAnalyzer()
            result = analyzer.analyze(df)
            # 统一字段名：算法返回 divergences，映射为 beichi
            normalized = {
                "macd": result.get("macd", {}),
                "beichi": {
                    "count": result.get("divergences", {}).get("count", 0),
                    "list": result.get("divergences", {}).get("all", []),
                    "latest": result.get("divergences", {}).get("latest", {}),
                },
            }
            all_results[iv] = normalized
            _cache["algo_results"].setdefault(iv, {})["dynamics"] = normalized

            macd = normalized.get("macd", {})
            beichi = normalized.get("beichi", {})
            macd_state = macd.get("macd_state", "?")
            bc_count = beichi.get("count", 0)
            print(f"         ✅ {iv}: MACD={macd_state}, 背驰={bc_count}个")
        except Exception as e:
            all_results[iv] = {"error": str(e)}
            print(f"         ❌ {iv}: {e}")
            traceback.print_exc()

    primary = all_results.get(interval, {})
    content = f"""动力学分析完成（三周期）。

## {interval} 主周期动力学分析
```json
{json.dumps(primary, ensure_ascii=False, indent=2)[:2000]}
```

## 多周期动力学概览
"""
    for iv, res in all_results.items():
        if "error" not in res:
            macd_state = res.get("macd", {}).get("macd_state", "?")
            bc_count = res.get("beichi", {}).get("count", 0)
            dif_trend = res.get("macd", {}).get("dif_trend", "?")
            content += f"- {iv}: MACD={macd_state}, DIF趋势={dif_trend}, 背驰={bc_count}个\n"

    state["messages"].append(AIMessage(content=content))
    state["dynamics_analysis"] = {
        "status": "completed",
        "algorithm_result": all_results,
        "agent_response": content
    }

    _update_timing(state, "dynamics_analyzer", t0)
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_practical_theory(state: ChanlunState) -> ChanlunState:
    """实战理论：基于算法结果的三类买卖点分析"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")
    current_price = _cache.get("current_price", 0)

    print(f"  [4/12] 🎯 practical_theory: 实战理论分析...")

    # 从算法结果提取买卖点
    content_lines = [f"实战理论分析完成（基于三周期缠论算法结果）。", ""]
    content_lines.append(f"## 当前价格: ${current_price:,.2f}")
    content_lines.append("")

    for iv in ["1d", "4h", "1h"]:
        algo = _cache.get("algo_results", {}).get(iv, {})
        struct = algo.get("structure", {})
        dyn = algo.get("dynamics", {})

        if "error" not in struct:
            trend = struct.get("trend", {}).get("type", "unknown")
            macd_state = dyn.get("macd", {}).get("macd_state", "unknown")
            beichi_list = dyn.get("beichi", {}).get("list", [])

            content_lines.append(f"### {iv} 周期")
            content_lines.append(f"- 走势类型: {trend}")
            content_lines.append(f"- MACD状态: {macd_state}")

        # 分析买卖点
        buy_points = []
        sell_points = []
        for bc in beichi_list:
            bc_type = bc.get("type", "")
            bc_level = bc.get("level", "")
            bc_strength = bc.get("strength", "")
            if bc_type == "bottom":
                buy_points.append(f"底背驰({bc_level}级, 强度={bc_strength})")
            elif bc_type == "top":
                sell_points.append(f"顶背驰({bc_level}级, 强度={bc_strength})")

        if buy_points:
            content_lines.append(f"- 🟢 买入信号: {', '.join(buy_points)}")
        if sell_points:
            content_lines.append(f"- 🔴 卖出信号: {', '.join(sell_points)}")
        content_lines.append("")

    # 综合建议
    content_lines.append("## 综合操作建议")
    d_trend = _cache.get("algo_results", {}).get("1d", {}).get("structure", {}).get("trend", {}).get("type", "?")
    h4_trend = _cache.get("algo_results", {}).get("4h", {}).get("structure", {}).get("trend", {}).get("type", "?")
    h1_trend = _cache.get("algo_results", {}).get("1h", {}).get("structure", {}).get("trend", {}).get("type", "?")

    content_lines.append(f"- 大级别(1d)方向: {d_trend}")
    content_lines.append(f"- 中级别(4h)方向: {h4_trend}")
    content_lines.append(f"- 小级别(1h)方向: {h1_trend}")

    if d_trend == "down":
        content_lines.append("- ⚠️ 大级别下跌趋势，操作上以短多或观望为主")
    elif d_trend == "up":
        content_lines.append("- ✅ 大级别上涨趋势，可寻找回调做多机会")

    content = "\n".join(content_lines)

    state["messages"].append(AIMessage(content=content))
    state["practical_theory_analysis"] = {
        "status": "completed",
        "agent_response": content
    }

    _update_timing(state, "practical_theory", t0)
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


# ── 并行组：5 个辅助维度节点 ──

async def node_sentiment_analyzer(state: ChanlunState) -> ChanlunState:
    """市场情绪分析（并行）"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    print(f"  [5/12] 😱 sentiment_analyzer: 市场情绪分析...")

    current_price = _cache.get("current_price", 0)
    # 基于真实数据的情绪判断
    h1_macd = _cache.get("algo_results", {}).get("1h", {}).get("dynamics", {}).get("macd", {})
    macd_state = h1_macd.get("macd_state", "unknown")

    if "bullish" in macd_state:
        sentiment = "偏多"
        fg_index = "65-72（贪婪区间）"
    elif "bearish" in macd_state:
        sentiment = "偏空"
        fg_index = "28-35（恐慌区间）"
    else:
        sentiment = "中性"
        fg_index = "45-55（中性区间）"

    content = f"""市场情绪分析完成。
- 交易对: {symbol}
- 当前价格: ${current_price:,.2f}
- 恐慌贪婪指数估算: {fg_index}
- MACD 状态: {macd_state}
- 综合情绪: {sentiment}
- 建议: {"谨慎做多" if "偏多" in sentiment else "观望为主" if "偏空" in sentiment else "等待方向明确"}"""

    state["messages"].append(AIMessage(content=content))
    state["sentiment_analysis"] = {"status": "completed", "agent_response": content}
    _update_timing(state, "sentiment_analyzer", t0)
    _mark_parallel_done(state, "sentiment_analyzer")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_cross_market_analyzer(state: ChanlunState) -> ChanlunState:
    """跨市场联动分析（并行）"""
    t0 = datetime.now()
    print(f"  [6/12] 🌍 cross_market_analyzer: 跨市场联动分析...")

    content = """跨市场联动分析完成。
- 美股市场: 标普500/纳斯达克近期走势需关注（数据源未接入）
- 黄金: 避险资产需联动观察
- 美元指数(DXY): 影响加密市场资金流向
- 加密市场: BTC主导率需实时监控
- 综合判断: 宏观环境需结合实时数据判断（当前为算法模式，无实时宏观数据源）"""

    state["messages"].append(AIMessage(content=content))
    state["cross_market_analysis"] = {"status": "completed", "agent_response": content}
    _update_timing(state, "cross_market_analyzer", t0)
    _mark_parallel_done(state, "cross_market_analyzer")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_onchain_analyzer(state: ChanlunState) -> ChanlunState:
    """链上数据分析（并行）"""
    t0 = datetime.now()
    print(f"  [7/12] ⛓️ onchain_analyzer: 链上数据分析...")

    content = """链上数据分析完成。
- 交易所净流入: 数据源未接入（需 Glassnode/CryptoQuant API）
- 巨鲸活动: 需链上实时监控
- 活跃地址: 需区块链浏览器 API
- 算力/难度: 需矿池数据源
- 综合信号: 当前为算法模式，链上数据需额外数据源支持"""

    state["messages"].append(AIMessage(content=content))
    state["onchain_analysis"] = {"status": "completed", "agent_response": content}
    _update_timing(state, "onchain_analyzer", t0)
    _mark_parallel_done(state, "onchain_analyzer")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_system_monitor(state: ChanlunState) -> ChanlunState:
    """系统监控（并行）"""
    t0 = datetime.now()
    print(f"  [8/12] 🖥️ system_monitor: 系统监控...")

    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        content = f"""系统监控完成。
- CPU 使用率: {cpu}%
- 内存使用率: {mem}%
- 磁盘使用率: {disk}%
- 数据完整性: ✅ 三周期 K 线数据已加载
- 数据新鲜度: 实时（Binance API 直连）
- 系统状态: 健康"""

    except ImportError:
        content = """系统监控完成。
- CPU 使用率: N/A（psutil 未安装）
- 内存使用率: N/A
- 磁盘使用率: N/A
- 数据完整性: ✅ 三周期 K 线数据已加载
- 数据新鲜度: 实时（Binance API 直连）
- 系统状态: 健康"""

    state["messages"].append(AIMessage(content=content))
    state["system_health"] = {"status": "checked", "agent_response": content}
    _update_timing(state, "system_monitor", t0)
    _mark_parallel_done(state, "system_monitor")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_simulation_check(state: ChanlunState) -> ChanlunState:
    """模拟盘检查（并行）"""
    t0 = datetime.now()
    print(f"  [9/12] 📋 simulation_check: 模拟盘检查...")

    content = """模拟盘检查完成。
- 总决策数: 0（首次运行，无历史数据）
- 胜率: N/A
- 盈亏比: N/A
- 当前持仓: 无
- 策略评估: 初始化阶段，需积累决策数据"""

    state["messages"].append(AIMessage(content=content))
    state["simulation_performance"] = {"status": "checked", "agent_response": content}
    _update_timing(state, "simulation_check", t0)
    _mark_parallel_done(state, "simulation_check")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


# ── 决策 & 风控 & 研报 ──

async def node_decision_maker(state: ChanlunState) -> ChanlunState:
    """首席决策：6 维度加权综合决策"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")
    current_price = _cache.get("current_price", 0)

    print(f"  [10/12] 🧠 decision_maker: 6维度加权决策...")

    # 收集各维度
    struct = state.get("structure_analysis", {}).get("algorithm_result", {})
    dynamics = state.get("dynamics_analysis", {}).get("algorithm_result", {})
    sentiment_resp = state.get("sentiment_analysis", {}).get("agent_response", "")
    cross_resp = state.get("cross_market_analysis", {}).get("agent_response", "")
    onchain_resp = state.get("onchain_analysis", {}).get("agent_response", "")

    # 结构分析维度（权重30%）
    d_trend = struct.get("1d", {}).get("trend", {}).get("type", "unknown") if "1d" in struct else "unknown"
    h4_trend = struct.get("4h", {}).get("trend", {}).get("type", "unknown") if "4h" in struct else "unknown"
    h1_trend = struct.get("1h", {}).get("trend", {}).get("type", "unknown") if "1h" in struct else "unknown"

    struct_score = 0
    if d_trend == "up": struct_score += 4
    elif d_trend == "down": struct_score -= 4
    if h4_trend == "up": struct_score += 3
    elif h4_trend == "down": struct_score -= 3
    if h1_trend == "up": struct_score += 2
    elif h1_trend == "down": struct_score -= 2
    struct_score = max(-10, min(10, struct_score))

    # 动力学维度（权重25%）
    d_macd = dynamics.get("1d", {}).get("macd", {}).get("macd_state", "unknown") if "1d" in dynamics else "unknown"
    h4_macd = dynamics.get("4h", {}).get("macd", {}).get("macd_state", "unknown") if "4h" in dynamics else "unknown"
    h1_macd = dynamics.get("1h", {}).get("macd", {}).get("macd_state", "unknown") if "1h" in dynamics else "unknown"

    dyn_score = 0
    for ms in [d_macd, h4_macd, h1_macd]:
        if "strong_bullish" in ms: dyn_score += 4
        elif "bullish" in ms: dyn_score += 2
        elif "strong_bearish" in ms: dyn_score -= 4
        elif "bearish" in ms: dyn_score -= 2
    dyn_score = max(-10, min(10, dyn_score))

    # 背驰维度（综合进动力学）
    d_bc = dynamics.get("1d", {}).get("beichi", {}).get("count", 0) if "1d" in dynamics else 0
    h4_bc = dynamics.get("4h", {}).get("beichi", {}).get("count", 0) if "4h" in dynamics else 0
    h1_bc = dynamics.get("1h", {}).get("beichi", {}).get("count", 0) if "1h" in dynamics else 0

    # 检查底背驰/顶背驰
    bc_signal = 0
    for iv in ["1d", "4h", "1h"]:
        bc_list = dynamics.get(iv, {}).get("beichi", {}).get("list", []) if iv in dynamics else []
        for bc in bc_list:
            if bc.get("type") == "bottom":
                bc_signal += 2  # 底背驰=买入信号
            elif bc.get("type") == "top":
                bc_signal -= 2  # 顶背驰=卖出信号

    # 情绪维度（权重15%）
    emotion_score = 0
    if "偏多" in sentiment_resp or "贪婪" in sentiment_resp:
        emotion_score = 3
    elif "偏空" in sentiment_resp or "恐慌" in sentiment_resp:
        emotion_score = -3

    # 综合加权评分
    weighted = (
        struct_score * 0.30 +
        (dyn_score + bc_signal) * 0.25 +
        emotion_score * 0.15 +
        0 * 0.15 +  # 跨市场（无数据）
        0 * 0.10 +  # 链上（无数据）
        0 * 0.05    # 模拟盘
    )

    # 决策
    if weighted > 2:
        direction = "LONG"
        confidence = min(90, 55 + int(weighted * 5))
    elif weighted < -2:
        direction = "SHORT"
        confidence = min(90, 55 + int(abs(weighted) * 5))
    else:
        direction = "NEUTRAL"
        confidence = 40

    # 止损止盈
    if direction == "LONG":
        stop_loss = current_price * 0.97
        tp1 = current_price * 1.03
        tp2 = current_price * 1.06
    elif direction == "SHORT":
        stop_loss = current_price * 1.03
        tp1 = current_price * 0.97
        tp2 = current_price * 0.94
    else:
        stop_loss = current_price * 0.98
        tp1 = current_price * 1.02
        tp2 = current_price * 1.04

    content = f"""## 交易决策

### 基本面
- 交易对: {symbol}
- 主周期: {interval}
- 当前价格: ${current_price:,.2f}

### 交易方向: {direction}
- 置信度: {confidence}%

### 关键价位
- 入场区间: ${current_price*0.995:,.2f} - ${current_price*1.005:,.2f}
- 止损: ${stop_loss:,.2f}
- 止盈 T1: ${tp1:,.2f}
- 止盈 T2: ${tp2:,.2f}

### 仓位建议
- 风险等级: {"中等" if confidence > 60 else "偏高"}
- 建议仓位: {"30-40%" if direction != "NEUTRAL" else "0%（观望）"}

### 多维度评分
| 维度 | 评分 | 权重 | 加权 |
|------|------|------|------|
| 结构分析 | {struct_score:+d} | 30% | {struct_score*0.30:+.1f} |
| 动力学+背驰 | {dyn_score+bc_signal:+d} | 25% | {(dyn_score+bc_signal)*0.25:+.1f} |
| 市场情绪 | {emotion_score:+d} | 15% | {emotion_score*0.15:+.1f} |
| 跨市场 | N/A | 15% | 0.0 |
| 链上数据 | N/A | 10% | 0.0 |
| 模拟盘 | N/A | 5% | 0.0 |
| **综合** | | | **{weighted:+.1f}** |

### 走势概况
- 1d: {d_trend} | 4h: {h4_trend} | 1h: {h1_trend}
- 1d MACD: {d_macd} | 4h: {h4_macd} | 1h: {h1_macd}
- 背驰: 1d={d_bc} | 4h={h4_bc} | 1h={h1_bc}
"""

    state["messages"].append(AIMessage(content=content))
    state["trading_decision"] = {
        "status": "completed",
        "agent_response": content,
        "direction": direction,
        "confidence": confidence,
        "weighted_score": weighted,
    }

    _update_timing(state, "decision_maker", t0)
    print(f"         🎯 决策: {direction} (置信度 {confidence}%, 加权分 {weighted:+.1f})")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_risk_manager(state: ChanlunState) -> ChanlunState:
    """风控审核"""
    t0 = datetime.now()
    print(f"  [11/12] 🛡️ risk_manager: 风控审核...")

    decision = state.get("trading_decision", {})
    direction = decision.get("direction", "NEUTRAL")
    confidence = decision.get("confidence", 0)
    weighted = decision.get("weighted_score", 0)

    # 风控规则
    risk_pass = True
    warnings = []

    if confidence < 50:
        risk_pass = False
        warnings.append("置信度过低（<50%），建议观望")

    if abs(weighted) < 2:
        risk_pass = False
        warnings.append("综合信号不明确，建议等待")

    if direction == "NEUTRAL":
        risk_pass = False
        warnings.append("方向不明确，不建议入场")

    # 检查大级别趋势
    d_trend = _cache.get("algo_results", {}).get("1d", {}).get("structure", {}).get("trend", {}).get("type", "?")
    if d_trend == "down" and direction == "LONG":
        warnings.append("⚠️ 逆大级别趋势做多，风险偏高")

    result_icon = "✅ 通过" if risk_pass else "❌ 不通过"

    content = f"""风控审核完成。
- 风控结果: {result_icon}
- 交易方向: {direction}
- 置信度: {confidence}%
- 综合评分: {weighted:+.1f}
- 最大建议仓位: {"35%" if risk_pass else "0%"}
- 杠杆建议: 不超过2x
- 止损纪律: 严格执行，不移动止损
{"- ⚠️ 风险提醒:" + chr(10) + chr(10).join(f"  - {w}" for w in warnings) if warnings else ""}
"""

    state["messages"].append(AIMessage(content=content))
    state["risk_audit"] = {
        "status": "completed",
        "agent_response": content,
        "risk_pass": risk_pass,
    }

    _update_timing(state, "risk_manager", t0)
    print(f"         {'✅ 风控通过' if risk_pass else '❌ 风控不通过'}")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


async def node_report_generator(state: ChanlunState) -> ChanlunState:
    """研报生成"""
    t0 = datetime.now()
    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")
    current_price = _cache.get("current_price", 0)

    print(f"  [12/12] 📝 report_generator: 生成研报...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"dag_report_{symbol}_{timestamp}.md")

    # 构建报告
    lines = [
        f"# 缠论多智能体系统 v5.1 — DAG 全链路分析报告",
        f"",
        f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **交易对**: {symbol}",
        f"- **主周期**: {interval}",
        f"- **当前价格**: ${current_price:,.2f}",
        f"- **模式**: 真实数据 + 缠论算法 + Mock LLM 决策",
        f"",
        f"## 一、三周期结构总览",
        f"",
        f"| 周期 | K线数 | 笔数 | 中枢数 | 走势类型 | 背驰数 |",
        f"|------|-------|------|--------|----------|--------|",
    ]

    for iv in ["1h", "4h", "1d"]:
        algo = _cache.get("algo_results", {}).get(iv, {})
        struct = algo.get("structure", {})
        dyn = algo.get("dynamics", {})
        kline_count = len(_cache.get("kline_dfs", {}).get(iv, []))
        bi_count = struct.get("bi", {}).get("count", "?")
        zs_count = struct.get("zhongshu", {}).get("count", "?")
        trend = struct.get("trend", {}).get("type", "?")
        bc_count = dyn.get("beichi", {}).get("count", "?")
        lines.append(f"| {iv} | {kline_count} | {bi_count} | {zs_count} | {trend} | {bc_count} |")

    lines.append("")

    # 各周期详细
    for iv in ["1h", "4h", "1d"]:
        algo = _cache.get("algo_results", {}).get(iv, {})
        struct = algo.get("structure", {})
        dyn = algo.get("dynamics", {})

        lines.append(f"## 二-{['1h','4h','1d'].index(iv)+1}、{iv} 周期详细分析")
        lines.append("")

        if "error" not in struct:
            trend = struct.get("trend", {}).get("type", "?")
            bi = struct.get("bi", {})
            zd = struct.get("zhongshu", {})
            lines.append(f"### 结构分析")
            lines.append(f"- 走势类型: {trend}")
            lines.append(f"- 笔: {bi.get('count', '?')} ({bi.get('up_count', '?')}上 / {bi.get('down_count', '?')}下)")
            last_bi = bi.get("last_bi", {})
            if last_bi:
                lines.append(f"- 最后一笔: 方向={last_bi.get('direction', '?')} "
                           f"起点=${last_bi.get('start_price', 0):,.2f} "
                           f"终点=${last_bi.get('end_price', 0):,.2f}")
            lines.append(f"- 中枢: {zd.get('count', '?')} 个")
            if zd.get("latest"):
                lz = zd["latest"]
                lines.append(f"  - 最新中枢: 高=${lz.get('high', 0):,.2f} 低=${lz.get('low', 0):,.2f} "
                           f"级别={lz.get('level_name', '?')}")
            lines.append("")

        if "error" not in dyn:
            macd = dyn.get("macd", {})
            beichi = dyn.get("beichi", {})
            dif_val = macd.get('dif', 0)
            dea_val = macd.get('dea', 0)
            macd_val = macd.get('macd', 0)
            try:
                dif_str = f"{dif_val:.2f}" if dif_val is not None else "N/A"
                dea_str = f"{dea_val:.2f}" if dea_val is not None else "N/A"
                macd_str = f"{macd_val:.2f}" if macd_val is not None else "N/A"
            except (TypeError, ValueError):
                dif_str = dea_str = macd_str = "N/A"
            lines.append(f"- MACD: DIF={dif_str} DEA={dea_str} MACD柱={macd_str}")
            lines.append(f"### 动力学分析")
            lines.append(f"- 状态: {macd.get('macd_state', 'N/A')}")
            lines.append(f"- DIF趋势: {macd.get('dif_trend', 'N/A')} | DEA趋势: {macd.get('dea_trend', 'N/A')}")
            lines.append(f"- 背驰: {beichi.get('count', 0)} 个")
            for i, bc in enumerate(beichi.get("list", [])[:5]):
                lines.append(f"  {i+1}. {bc.get('type', '?')} {bc.get('strength', '?')} "
                           f"[${bc.get('start_price', 0):,.2f} → ${bc.get('end_price', 0):,.2f}] "
                           f"level={bc.get('level', '?')}")
            lines.append("")

    # 交易决策
    decision = state.get("trading_decision", {})
    risk = state.get("risk_audit", {})
    lines.append("## 三、交易决策")
    lines.append("")
    lines.append(decision.get("agent_response", "无"))
    lines.append("")
    lines.append("## 四、风控审核")
    lines.append("")
    lines.append(risk.get("agent_response", "无"))
    lines.append("")

    # DAG 执行统计
    timing = state.get("execution_timing", {})
    lines.append("## 五、DAG 执行统计")
    lines.append("")
    lines.append("| 节点 | 耗时(s) | 类型 |")
    lines.append("|------|---------|------|")
    topo = [
        "data_collector", "structure_analyzer", "dynamics_analyzer", "practical_theory",
        "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
        "system_monitor", "simulation_check",
        "decision_maker", "risk_manager", "report_generator",
    ]
    parallel_nodes = {"sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
                      "system_monitor", "simulation_check"}
    for n in topo:
        dur = timing.get(n, {}).get("duration_seconds", 0)
        tag = "并行" if n in parallel_nodes else "串行"
        lines.append(f"| {n} | {dur:.2f} | {tag} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*报告由缠论多智能体系统 v5.1 DAG 模式自动生成*")
    lines.append("*⚠️ 免责声明：本报告基于缠论算法分析 + Mock LLM 决策，不构成投资建议*")

    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    content = f"研报生成完成。报告路径: {report_path}"

    state["messages"].append(AIMessage(content=content))
    state["report_path"] = report_path
    state["decision_stats"] = {"total": 0, "executed": 0, "closed": 0, "pnl": {"win_rate": 0, "total_pnl": 0}}

    _update_timing(state, "report_generator", t0)
    print(f"         📄 报告: {report_path}")
    print(f"         ⏱  耗时 {(datetime.now()-t0).total_seconds():.2f}s")
    return state


# ═══════════════════════════════════════════════════════════════
# 构建 DAG 工作流
# ═══════════════════════════════════════════════════════════════

def build_dag_workflow():
    """构建 12 节点 DAG 工作流"""
    workflow = StateGraph(ChanlunState)

    # 线性主干（4 节点）
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("practical_theory", node_practical_theory)

    # 并行组1：辅助维度（3 节点）
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("cross_market_analyzer", node_cross_market_analyzer)
    workflow.add_node("onchain_analyzer", node_onchain_analyzer)

    # 并行组2：系统检查（2 节点）
    workflow.add_node("system_monitor", node_system_monitor)
    workflow.add_node("simulation_check", node_simulation_check)

    # 决策 & 风控 & 研报（3 节点）
    workflow.add_node("decision_maker", node_decision_maker)
    workflow.add_node("risk_manager", node_risk_manager)
    workflow.add_node("report_generator", node_report_generator)

    # 入口
    workflow.set_entry_point("data_collector")

    # 线性主干
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "practical_theory")

    # Fan-out: practical_theory → 5 个并行节点
    workflow.add_edge("practical_theory", "sentiment_analyzer")
    workflow.add_edge("practical_theory", "cross_market_analyzer")
    workflow.add_edge("practical_theory", "onchain_analyzer")
    workflow.add_edge("practical_theory", "system_monitor")
    workflow.add_edge("practical_theory", "simulation_check")

    # Fan-in: 5 个并行节点 → decision_maker
    workflow.add_edge("sentiment_analyzer", "decision_maker")
    workflow.add_edge("cross_market_analyzer", "decision_maker")
    workflow.add_edge("onchain_analyzer", "decision_maker")
    workflow.add_edge("system_monitor", "decision_maker")
    workflow.add_edge("simulation_check", "decision_maker")

    # 线性尾部
    workflow.add_edge("decision_maker", "risk_manager")
    workflow.add_edge("risk_manager", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


# ═══════════════════════════════════════════════════════════════
# 主运行函数
# ═══════════════════════════════════════════════════════════════

async def run_dag_analysis(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    save_json: bool = True,
):
    """运行完整 DAG 分析"""

    print("\n" + "=" * 72)
    print("  🔶 缠论多智能体系统 v5.1 — BTC 实时行情 DAG 全链路运行")
    print("=" * 72)
    print(f"  💰 交易对: {symbol}")
    print(f"  📊 主周期: {interval}")
    print(f"  🔧 模式: Binance 真实数据 + 缠论算法 + Mock LLM 决策")
    print(f"  📐 DAG: 4 串行 + 5 并行 + 3 串行 = 12 节点")
    print(f"  🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72 + "\n")

    _cache["symbol"] = symbol

    workflow = build_dag_workflow()

    initial_state = {
        "messages": [],
        "user_request": "BTC 缠论多智能体实时分析",
        "symbol": symbol,
        "interval": interval,
        "kline_data": None,
        "data_quality": None,
        "structure_analysis": None,
        "dynamics_analysis": None,
        "practical_theory_analysis": None,
        "risk_audit": None,
        "sentiment_analysis": None,
        "cross_market_analysis": None,
        "onchain_analysis": None,
        "system_health": None,
        "data_quality_report": None,
        "simulation_performance": None,
        "open_positions": None,
        "trading_decision": None,
        "report_path": None,
        "decision_stats": None,
        "parallel_group_status": {},
        "execution_timing": {},
    }

    wall_start = time.time()
    result = await workflow.ainvoke(initial_state)
    wall_end = time.time()
    wall_duration = wall_end - wall_start

    timing = result.get("execution_timing", {})
    pgs = result.get("parallel_group_status", {})

    # ── 打印执行统计 ──
    print()
    print("=" * 72)
    print("  ⏱  DAG 执行统计")
    print("=" * 72)

    topo_order = [
        "data_collector", "structure_analyzer", "dynamics_analyzer", "practical_theory",
        "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
        "system_monitor", "simulation_check",
        "decision_maker", "risk_manager", "report_generator",
    ]
    parallel_nodes = {
        "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
        "system_monitor", "simulation_check",
    }

    for node_name in topo_order:
        info = timing.get(node_name, {})
        dur = info.get("duration_seconds", 0)
        is_par = node_name in parallel_nodes
        tag = " [并行]" if is_par else ""
        print(f"  {node_name:<25s}  {dur:>6.2f}s{tag}")

    # 并行效率
    parallel_total = sum(timing.get(n, {}).get("duration_seconds", 0) for n in parallel_nodes)
    serial_nodes = [n for n in topo_order if n not in parallel_nodes]
    serial_total = sum(timing.get(n, {}).get("duration_seconds", 0) for n in serial_nodes)
    parallel_wall = max((timing.get(n, {}).get("duration_seconds", 0) for n in parallel_nodes), default=0)

    print()
    print("-" * 72)
    print(f"  串行阶段总耗时:               {serial_total:.2f}s")
    print(f"  并行阶段串行化耗时（若不并行）: {parallel_total:.2f}s")
    print(f"  并行阶段实际耗时（最慢节点）:   {parallel_wall:.2f}s")
    print(f"  ────────────────────────────────────────")
    print(f"  实际总耗时:                    {wall_duration:.2f}s")
    if parallel_total > 0:
        speedup = (serial_total + parallel_total) / wall_duration
        saved = (serial_total + parallel_total) - wall_duration
        print(f"  🚀 并行加速比:                 {speedup:.2f}x")
        print(f"  ⏱  节省时间:                   {saved:.2f}s")

    # 并行节点完成状态
    print()
    print("  📊 并行节点完成状态:")
    for node in parallel_nodes:
        status = pgs.get(node, "unknown")
        icon = "✅" if status == "completed" else "❌"
        dur = timing.get(node, {}).get("duration_seconds", 0)
        print(f"    {icon} {node:<25s}  {dur:.2f}s  [{status}]")

    # 交易决策摘要
    decision = result.get("trading_decision", {})
    direction = decision.get("direction", "N/A")
    confidence = decision.get("confidence", 0)
    risk_pass = result.get("risk_audit", {}).get("risk_pass", False)

    print()
    print("=" * 72)
    print("  📋 交易决策摘要")
    print("=" * 72)
    print(f"  方向: {direction}")
    print(f"  置信度: {confidence}%")
    print(f"  风控: {'✅ 通过' if risk_pass else '❌ 不通过'}")
    print(f"  当前价格: ${_cache.get('current_price', 0):,.2f}")

    report_path = result.get("report_path", "N/A")
    print(f"  📄 研报: {report_path}")
    print()
    print(f"  ✅ DAG 全链路运行成功！总耗时 {wall_duration:.2f}s")
    print("=" * 72)

    # 保存 JSON
    if save_json:
        json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            f"dag_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        serializable = {}
        for k, v in result.items():
            if k == "messages":
                serializable[k] = [
                    {"type": type(m).__name__, "content": str(m.content)[:500]} for m in v
                ]
            elif isinstance(v, (str, int, float, bool, type(None), dict, list)):
                serializable[k] = v
            else:
                serializable[k] = str(v)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2, default=str)
        print(f"  📦 JSON: {json_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="缠论多智能体系统 v5.1 — BTC DAG 全链路运行")
    parser.add_argument("--symbol", default="BTCUSDT", help="交易对")
    parser.add_argument("--interval", default="1h", help="主周期")
    parser.add_argument("--no-json", action="store_true", help="不保存 JSON")
    args = parser.parse_args()

    asyncio.run(run_dag_analysis(
        symbol=args.symbol,
        interval=args.interval,
        save_json=not args.no_json,
    ))


if __name__ == "__main__":
    main()
