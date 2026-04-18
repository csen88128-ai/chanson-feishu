#!/usr/bin/env python3
"""
缠论多智能体系统 v5.1 — 本地 Mock 完整 DAG 运行

不依赖 LLM API 和 Coze 云平台，使用 mock agent 替换真实 LLM 调用，
走完整个 DAG 工作流（12 节点全链路），验证：
1. DAG fan-out/fan-in 并行调度
2. 状态在节点间正确传递
3. execution_timing 和 parallel_group_status 追踪
4. 并行加速比计算

用法:
    python run_local_mock.py
    python run_local_mock.py --symbol ETHUSDT --interval 4h
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# 将 src 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Mock Agent：替代真实 LLM，返回固定但合理的分析文本 ──

MOCK_RESPONSES = {
    "data_collector": """数据采集完成。
- 交易对: {symbol}
- K线周期: {interval}
- 数据范围: 最近 500 根K线
- 最新价格: 84,250 USDT
- 数据质量评分: 95/100
- 缺失K线: 0
- 数据已缓存至本地""",

    "structure_analyzer": """结构分析完成。
- 当前走势类型: 上涨趋势
- 笔的状态: 第7笔向上，尚未结束
- 线段状态: 第3线段向上延伸中
- 中枢状态: 形成第2个30分钟中枢，ZG=83200, ZD=82800
- 关键支撑: 82800, 81500
- 关键阻力: 85000, 86500
- 结构强弱: 中枢上方运行，结构偏强""",

    "dynamics_analyzer": """动力学分析完成。
- MACD: DIF=125.3, DEA=98.7, MACD柱=26.6（红柱放大）
- 金叉/死叉: DIF 在 DEA 上方，金叉状态持续
- 背驰判断: 当前无顶背驰迹象，动量充足
- 买卖点: 第二类买点已确认，第三类买点观察中
- 力度评估: 多头力度中等偏强""",

    "practical_theory": """实战理论分析完成。
- 第一类买点: 81500（已过，未参与）
- 第二类买点: 82800（已确认，可入场）
- 第三类买点: 83200-83500（观察中，需回踩确认）
- 仓位建议: 首仓 30%，回踩不破可加至 50%
- 操作节奏: 短线可看 85000 目标，中线看 86500
- 止损位: 82500 下方""",

    "sentiment_analyzer": """市场情绪分析完成。
- 恐慌贪婪指数: 68（贪婪）
- 资金费率: +0.012%（多头略占优）
- 爆仓数据: 过去24h多头爆仓 $12.5M，空头爆仓 $8.3M
- 持仓量变化: +2.3%，多空比 1.15
- 综合评估: 市场情绪偏多但不过热""",

    "cross_market_analyzer": """跨市场联动分析完成。
- 标普500: +0.35%，科技股走强
- 纳斯达克: +0.52%
- 黄金: +0.15%，避险情绪温和
- 美元指数(DXY): -0.08%，小幅走弱利好加密
- 加密市场: BTC主导率 52.3%，山寨季信号偏弱
- 综合判断: 宏观环境偏利好 BTC""",

    "onchain_analyzer": """链上数据分析完成。
- 交易所净流入: -$156M（净流出，利好）
- 巨鲸活动: 过去24h增持 1,200 BTC
- 活跃地址: 920K（高于30日均值）
- 算力: 620 EH/s（稳定）
- 难度调整: 下次预计 +1.2%
- 综合信号: 链上数据偏多""",

    "system_monitor": """系统监控完成。
- CPU 使用率: 23%
- 内存使用率: 45%
- 磁盘使用率: 32%
- 数据完整性: 全部正常
- 数据新鲜度: 最近5分钟内
- 系统状态: 健康""",

    "simulation_check": """模拟盘检查完成。
- 总决策数: 156
- 胜率: 62.8%
- 盈亏比: 1.85
- 总盈亏: +$12,350
- 当前持仓: 多头 BTCUSDT @83500
- 策略评估: 当前策略有效，可继续执行""",

    "decision_maker": """首席决策完成。

## 交易决策
- 交易方向: LONG（做多）
- 置信度: 72%
- 入场价格区间: 83800-84200
- 止损价格: 82500
- 止盈目标: T1=85000, T2=86500
- 建议仓位: 35%
- 风险等级: 中等

## 多维度共振
- ✅ 结构分析: 上涨趋势，中枢上方运行（权重30%）
- ✅ 动力学: 金叉持续，无背驰（权重25%）
- ✅ 市场情绪: 贪婪但不极端（权重15%）
- ✅ 跨市场: 宏观偏利好（权重15%）
- ✅ 链上数据: 净流出+巨鲸增持（权重10%）
- ✅ 模拟盘: 胜率62.8%策略有效（权重5%）
- 综合得分: 7.2/10""",

    "risk_manager": """风控审核完成。
- 风控结果: ✅ 通过
- 最大单笔亏损: -1.5%（控制在2%以内）
- 仓位集中度: 35%（控制在50%以内）
- 杠杆评估: 建议不超过3x
- 熔断条件: 跌破82500自动止损
- 综合风险: 中等可控""",

    "report_generator": """研报生成完成。
- 报告ID: RPT-20260418-001
- 报告路径: /workspace/reports/BTCUSDT_1h_20260418.md
- 决策统计: 总156次 | 已执行128次 | 已平仓98次 | 胜率62.8%""",
}


class MockAgentResponse:
    """模拟 LLM Agent 返回"""
    def __init__(self, content: str):
        self.content = content


class MockAgentResult:
    """模拟 Agent.invoke 返回"""
    def __init__(self, content: str):
        self.messages = [MockAgentResponse(content)]


class MockAgent:
    """模拟 Agent，延迟返回预设响应（模拟 LLM 延迟）"""
    def __init__(self, node_name: str, symbol: str = "BTCUSDT", interval: str = "1h"):
        self.node_name = node_name
        self.symbol = symbol
        self.interval = interval

    def invoke(self, input_dict, **kwargs):
        """模拟同步调用，添加随机延迟模拟 LLM 响应时间"""
        import random
        delay = random.uniform(0.3, 1.5)  # 模拟 0.3-1.5s 的 LLM 响应
        time.sleep(delay)
        template = MOCK_RESPONSES.get(self.node_name, f"Mock {self.node_name} 完成")
        content = template.format(symbol=self.symbol, interval=self.interval)
        return MockAgentResult(content)


# ── 替换节点函数（使用 Mock Agent）──

from langchain_core.messages import HumanMessage, AIMessage


async def mock_data_collector(state):
    t0 = datetime.now()
    agent = MockAgent("data_collector", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["data_quality"] = {"status": "collected", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "data_collector", t0)
    return state


async def mock_structure_analyzer(state):
    t0 = datetime.now()
    agent = MockAgent("structure_analyzer", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["structure_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "structure_analyzer", t0)
    return state


async def mock_dynamics_analyzer(state):
    t0 = datetime.now()
    agent = MockAgent("dynamics_analyzer", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["dynamics_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "dynamics_analyzer", t0)
    return state


async def mock_practical_theory(state):
    t0 = datetime.now()
    agent = MockAgent("practical_theory", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["practical_theory_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "practical_theory", t0)
    return state


async def mock_sentiment_analyzer(state):
    t0 = datetime.now()
    agent = MockAgent("sentiment_analyzer", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["sentiment_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing, _mark_parallel_done
    _update_timing(state, "sentiment_analyzer", t0)
    _mark_parallel_done(state, "sentiment_analyzer")
    return state


async def mock_cross_market_analyzer(state):
    t0 = datetime.now()
    agent = MockAgent("cross_market_analyzer", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["cross_market_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing, _mark_parallel_done
    _update_timing(state, "cross_market_analyzer", t0)
    _mark_parallel_done(state, "cross_market_analyzer")
    return state


async def mock_onchain_analyzer(state):
    t0 = datetime.now()
    agent = MockAgent("onchain_analyzer", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["onchain_analysis"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing, _mark_parallel_done
    _update_timing(state, "onchain_analyzer", t0)
    _mark_parallel_done(state, "onchain_analyzer")
    return state


async def mock_system_monitor(state):
    t0 = datetime.now()
    agent = MockAgent("system_monitor", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["system_health"] = {"status": "checked", "agent_response": content}
    from graphs.chanlun_graph import _update_timing, _mark_parallel_done
    _update_timing(state, "system_monitor", t0)
    _mark_parallel_done(state, "system_monitor")
    return state


async def mock_simulation_check(state):
    t0 = datetime.now()
    agent = MockAgent("simulation_check", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["simulation_performance"] = {"status": "checked", "agent_response": content}
    from graphs.chanlun_graph import _update_timing, _mark_parallel_done
    _update_timing(state, "simulation_check", t0)
    _mark_parallel_done(state, "simulation_check")
    return state


async def mock_decision_maker(state):
    t0 = datetime.now()
    agent = MockAgent("decision_maker", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["trading_decision"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "decision_maker", t0)
    return state


async def mock_risk_manager(state):
    t0 = datetime.now()
    agent = MockAgent("risk_manager", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["risk_audit"] = {"status": "completed", "agent_response": content}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "risk_manager", t0)
    return state


async def mock_report_generator(state):
    t0 = datetime.now()
    agent = MockAgent("report_generator", state.get("symbol", "BTCUSDT"), state.get("interval", "1h"))
    response = await asyncio.to_thread(agent.invoke, {"messages": []})
    content = response.messages[-1].content
    state["messages"].append(AIMessage(content=content))
    state["report_path"] = f"/workspace/reports/{state.get('symbol', 'BTCUSDT')}_{state.get('interval', '1h')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    state["decision_stats"] = {"total": 156, "executed": 128, "closed": 98, "pnl": {"win_rate": 62.8, "total_pnl": 12350}}
    from graphs.chanlun_graph import _update_timing
    _update_timing(state, "report_generator", t0)
    return state


# ── 构建 Mock 工作流 ──

def build_mock_workflow():
    """构建使用 Mock Agent 的 DAG 工作流"""
    from langgraph.graph import StateGraph, END
    from graphs.chanlun_graph import ChanlunState

    workflow = StateGraph(ChanlunState)

    # 添加 mock 节点
    workflow.add_node("data_collector", mock_data_collector)
    workflow.add_node("structure_analyzer", mock_structure_analyzer)
    workflow.add_node("dynamics_analyzer", mock_dynamics_analyzer)
    workflow.add_node("practical_theory", mock_practical_theory)

    # 并行组1：辅助维度分析
    workflow.add_node("sentiment_analyzer", mock_sentiment_analyzer)
    workflow.add_node("cross_market_analyzer", mock_cross_market_analyzer)
    workflow.add_node("onchain_analyzer", mock_onchain_analyzer)

    # 并行组2：系统检查
    workflow.add_node("system_monitor", mock_system_monitor)
    workflow.add_node("simulation_check", mock_simulation_check)

    # 决策 & 风控 & 研报
    workflow.add_node("decision_maker", mock_decision_maker)
    workflow.add_node("risk_manager", mock_risk_manager)
    workflow.add_node("report_generator", mock_report_generator)

    # 设置入口
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


def run_mock_analysis(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    verbose: bool = True,
    save_report: bool = True,
):
    """运行 Mock 完整 DAG 分析"""

    if verbose:
        print("\n" + "=" * 70)
        print("  缠论多智能体系统 v5.1 — Mock 完整 DAG 运行")
        print("=" * 70)
        print(f"  交易对: {symbol}  |  周期: {interval}")
        print(f"  模式: Mock（不调用 LLM，模拟真实延迟）")
        print(f"  DAG 拓扑: 4 线性 + 5 并行 + 3 线性 = 12 节点")
        print("=" * 70 + "\n")

    workflow = build_mock_workflow()

    initial_state = {
        "messages": [],
        "user_request": "BTC 缠论分析",
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
    result = asyncio.run(workflow.ainvoke(initial_state))
    wall_end = time.time()
    wall_duration = wall_end - wall_start

    timing = result.get("execution_timing") or {}
    pgs = result.get("parallel_group_status") or {}

    if verbose:
        # ── DAG 拓扑信息 ──
        graph = workflow.get_graph()
        print("  📐 DAG 节点顺序:")
        for node in graph.nodes:
            if not node.startswith("__"):
                print(f"    - {node}")
        print()

        # ── 各节点执行耗时 ──
        print("=" * 70)
        print("  ⏱  各节点执行耗时")
        print("=" * 70)

        # 按拓扑顺序展示
        topo_order = [
            "data_collector", "structure_analyzer", "dynamics_analyzer", "practical_theory",
            "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
            "system_monitor", "simulation_check",
            "decision_maker", "risk_manager", "report_generator",
        ]
        for node_name in topo_order:
            info = timing.get(node_name, {})
            dur = info.get("duration_seconds", 0)
            is_parallel = node_name in [
                "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
                "system_monitor", "simulation_check",
            ]
            tag = " [并行]" if is_parallel else ""
            print(f"  {node_name:<25s}  {dur:>6.2f}s{tag}")

        # ── 并行效率分析 ──
        parallel_nodes = [
            "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
            "system_monitor", "simulation_check",
        ]
        parallel_total = sum(
            (timing.get(n, {}).get("duration_seconds", 0)) for n in parallel_nodes
        )
        serial_nodes = [n for n in topo_order if n not in parallel_nodes]
        serial_total = sum(
            (timing.get(n, {}).get("duration_seconds", 0)) for n in serial_nodes
        )
        parallel_wall = max(
            (timing.get(n, {}).get("duration_seconds", 0)) for n in parallel_nodes
        ) if parallel_nodes else 0

        print()
        print("-" * 70)
        print(f"  串行阶段总耗时:               {serial_total:.2f}s")
        print(f"  并行阶段串行化耗时（若不并行）: {parallel_total:.2f}s")
        print(f"  并行阶段实际耗时（最慢节点）:   {parallel_wall:.2f}s")
        print(f"  ────────────────────────────────────────")
        print(f"  实际总耗时:                    {wall_duration:.2f}s")
        print(f"  串行化总耗时（若不并行）:       {serial_total + parallel_total:.2f}s")
        if parallel_total > 0:
            speedup = (serial_total + parallel_total) / wall_duration
            saved = (serial_total + parallel_total) - wall_duration
            print(f"  🚀 并行加速比:                 {speedup:.2f}x")
            print(f"  ⏱  节省时间:                   {saved:.2f}s")
        print("=" * 70)

        # ── 并行节点完成状态 ──
        print()
        print("  📊 并行节点完成状态:")
        for node in parallel_nodes:
            status = pgs.get(node, "unknown")
            icon = "✅" if status == "completed" else "❌"
            dur = timing.get(node, {}).get("duration_seconds", 0)
            print(f"    {icon} {node:<25s}  {dur:.2f}s  [{status}]")

        # ── 交易决策摘要 ──
        decision = result.get("trading_decision", {})
        if decision and decision.get("agent_response"):
            print()
            print("=" * 70)
            print("  📋 交易决策摘要")
            print("=" * 70)
            response = decision["agent_response"]
            print(response[:600])
            if len(response) > 600:
                print(f"\n  ... (共 {len(response)} 字符，已截断)")
            print("=" * 70)

        print(f"\n  ✅ DAG 全链路运行成功！总耗时 {wall_duration:.2f}s\n")

    # ── 保存结果报告 ──
    if save_report:
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
        report_dir = os.path.abspath(report_dir)
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"mock_dag_run_{timestamp}.md")

        # 构建可读报告
        report_lines = []
        report_lines.append(f"# 缠论多智能体系统 v5.1 — Mock DAG 运行报告")
        report_lines.append(f"")
        report_lines.append(f"- **运行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"- **交易对**: {symbol}")
        report_lines.append(f"- **K线周期**: {interval}")
        report_lines.append(f"- **模式**: Mock（不调用 LLM）")
        report_lines.append(f"- **总耗时**: {wall_duration:.2f}s")
        report_lines.append(f"")
        report_lines.append(f"## DAG 拓扑")
        report_lines.append(f"")
        report_lines.append(f"```")
        report_lines.append(f"data_collector → structure_analyzer → dynamics_analyzer → practical_theory")
        report_lines.append(f"                                                  │")
        report_lines.append(f"                    ├─▶ sentiment_analyzer   ─┐")
        report_lines.append(f"                    ├─▶ cross_market_analyzer ─┤")
        report_lines.append(f"                    ├─▶ onchain_analyzer      ─┼─▶ decision_maker → risk_manager → report_generator → END")
        report_lines.append(f"                    ├─▶ system_monitor        ─┤")
        report_lines.append(f"                    └─▶ simulation_check      ─┘")
        report_lines.append(f"```")
        report_lines.append(f"")

        # 节点耗时表
        report_lines.append(f"## 各节点执行耗时")
        report_lines.append(f"")
        report_lines.append(f"| 节点 | 耗时(s) | 类型 |")
        report_lines.append(f"|------|---------|------|")
        for node_name in topo_order:
            info = timing.get(node_name, {})
            dur = info.get("duration_seconds", 0)
            is_par = node_name in parallel_nodes
            tag = "并行" if is_par else "串行"
            report_lines.append(f"| {node_name} | {dur:.2f} | {tag} |")
        report_lines.append(f"")

        # 并行效率
        report_lines.append(f"## 并行效率分析")
        report_lines.append(f"")
        report_lines.append(f"- 串行阶段总耗时: {serial_total:.2f}s")
        report_lines.append(f"- 并行阶段串行化耗时: {parallel_total:.2f}s")
        report_lines.append(f"- 并行阶段实际耗时（最慢节点）: {parallel_wall:.2f}s")
        report_lines.append(f"- 实际总耗时: {wall_duration:.2f}s")
        if parallel_total > 0:
            speedup = (serial_total + parallel_total) / wall_duration
            saved = (serial_total + parallel_total) - wall_duration
            report_lines.append(f"- **并行加速比: {speedup:.2f}x**")
            report_lines.append(f"- 节省时间: {saved:.2f}s")
        report_lines.append(f"")

        # 各维度分析摘要
        report_lines.append(f"## 各维度分析摘要")
        report_lines.append(f"")
        dimensions = [
            ("数据采集", "data_quality"),
            ("结构分析", "structure_analysis"),
            ("动力学分析", "dynamics_analysis"),
            ("实战理论", "practical_theory_analysis"),
            ("市场情绪", "sentiment_analysis"),
            ("跨市场联动", "cross_market_analysis"),
            ("链上数据", "onchain_analysis"),
            ("系统监控", "system_health"),
            ("模拟盘", "simulation_performance"),
            ("交易决策", "trading_decision"),
            ("风控审核", "risk_audit"),
        ]
        for label, key in dimensions:
            data = result.get(key, {})
            resp = data.get("agent_response", "无") if data else "无"
            status = data.get("status", "unknown") if data else "unknown"
            icon = "✅" if status in ("collected", "completed", "checked") else "❌"
            report_lines.append(f"### {icon} {label}")
            report_lines.append(f"")
            report_lines.append(f"状态: {status}")
            report_lines.append(f"")
            # 截取前300字
            if resp and resp != "无":
                report_lines.append(f"```")
                report_lines.append(resp[:300])
                if len(resp) > 300:
                    report_lines.append(f"... (共 {len(resp)} 字符)")
                report_lines.append(f"```")
            report_lines.append(f"")

        report_lines.append(f"---")
        report_lines.append(f"")
        report_lines.append(f"*报告由缠论多智能体系统 v5.1 Mock 模式自动生成*")

        report_content = "\n".join(report_lines)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        if verbose:
            print(f"  📄 报告已保存至: {report_path}")

        # 同时保存 JSON 格式的完整数据
        json_path = os.path.join(report_dir, f"mock_dag_run_{timestamp}.json")

        # 序列化结果（排除不可序列化的 messages）
        serializable_result = {}
        for k, v in result.items():
            if k == "messages":
                serializable_result[k] = [
                    {"type": type(m).__name__, "content": str(m.content)} for m in v
                ]
            elif isinstance(v, (str, int, float, bool, type(None))):
                serializable_result[k] = v
            elif isinstance(v, dict):
                serializable_result[k] = v
            elif isinstance(v, list):
                serializable_result[k] = v
            else:
                serializable_result[k] = str(v)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2, default=str)

        if verbose:
            print(f"  📦 JSON 数据已保存至: {json_path}")

        result["_report_path"] = report_path
        result["_json_path"] = json_path

    return result


def main():
    parser = argparse.ArgumentParser(description="缠论多智能体系统 v5.1 — Mock DAG 运行")
    parser.add_argument("--symbol", default="BTCUSDT", help="交易对 (默认: BTCUSDT)")
    parser.add_argument("--interval", default="1h", help="K线周期 (默认: 1h)")
    parser.add_argument("--quiet", action="store_true", help="安静模式")
    args = parser.parse_args()

    result = run_mock_analysis(
        symbol=args.symbol,
        interval=args.interval,
        verbose=not args.quiet,
        save_report=True,
    )

    return result


if __name__ == "__main__":
    main()
