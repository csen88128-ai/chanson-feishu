"""
缠论多智能体工作流 v5.1
集成实战理论和风控审核
支持 DAG 并行执行（fan-out / fan-in）
"""
from typing import TypedDict, Annotated, Optional, Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
import json
import logging
import asyncio
import operator

logger = logging.getLogger(__name__)


# ── Reducer 函数 ──

def _merge_dicts(old: Optional[Dict], new: Optional[Dict]) -> Dict:
    """合并两个 dict，new 的 key 覆盖 old 的同名 key"""
    result = (old or {}).copy()
    if new:
        result.update(new)
    return result


def _last_value(old: Any, new: Any) -> Any:
    """取最后一个非 None 值（用于 str/Optional 字段在并行 fan-in 时的冲突解决）"""
    return new if new is not None else old


class ChanlunState(TypedDict):
    """缠论分析系统状态

    v5.1: 并行 fan-out/fan-in 需要给被多个节点同时写入的字段加 reducer。
    - dict 字段用 _merge_dicts（key 级合并）
    - str/Optional 字段用 _last_value（取最后写入值）
    - messages 用 add_messages（append 语义）
    """
    messages: Annotated[list, add_messages]
    user_request: Annotated[str, _last_value]
    symbol: Annotated[Optional[str], _last_value]
    interval: Annotated[Optional[str], _last_value]

    # 数据采集结果
    kline_data: Annotated[Optional[Dict[str, Any]], _last_value]
    data_quality: Annotated[Optional[Dict[str, Any]], _last_value]

    # 结构分析结果
    structure_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 动力学分析结果
    dynamics_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 实战理论分析结果
    practical_theory_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 风控审核结果
    risk_audit: Annotated[Optional[Dict[str, Any]], _last_value]

    # 市场情绪分析结果
    sentiment_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 跨市场联动分析结果
    cross_market_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 链上数据分析结果
    onchain_analysis: Annotated[Optional[Dict[str, Any]], _last_value]

    # 系统监控结果
    system_health: Annotated[Optional[Dict[str, Any]], _last_value]
    data_quality_report: Annotated[Optional[Dict[str, Any]], _last_value]

    # 模拟盘数据
    simulation_performance: Annotated[Optional[Dict[str, Any]], _last_value]
    open_positions: Annotated[Optional[List[Dict[str, Any]]], _last_value]

    # 最终决策
    trading_decision: Annotated[Optional[Dict[str, Any]], _last_value]

    # 研报和历史记录
    report_path: Annotated[Optional[str], _last_value]
    decision_stats: Annotated[Optional[Dict[str, Any]], _last_value]

    # ── v5.1 并行执行追踪字段（多节点同时写入，需 merge）──
    parallel_group_status: Annotated[Optional[Dict[str, str]], _merge_dicts]
    execution_timing: Annotated[Optional[Dict[str, Dict[str, Any]]], _merge_dicts]


# ========== 计时 & 进度工具 ==========

class NodeTimer:
    """节点执行计时器，自动记录到 state['execution_timing']"""

    def __init__(self, node_name: str):
        self.node_name = node_name
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"[⏱ ] {self.node_name} 开始执行")
        return self

    def __exit__(self, *exc):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        logger.info(f"[⏱ ] {self.node_name} 完成，耗时 {duration:.2f}s")
        return False


def _update_timing(state: ChanlunState, node_name: str, start_time: datetime) -> None:
    """更新节点执行计时"""
    timing = state.get("execution_timing") or {}
    timing[node_name] = {
        "start": start_time.isoformat(),
        "end": datetime.now().isoformat(),
        "duration_seconds": (datetime.now() - start_time).total_seconds(),
    }
    state["execution_timing"] = timing


def _mark_parallel_done(state: ChanlunState, node_name: str) -> None:
    """标记并行节点完成"""
    status = state.get("parallel_group_status") or {}
    status[node_name] = "completed"
    state["parallel_group_status"] = status


# ========== 节点定义 ==========


async def node_data_collector(state: ChanlunState) -> ChanlunState:
    """数据采集节点"""
    t0 = datetime.now()
    from agents.data_collector import build_agent

    agent = build_agent()

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    prompt = f"""请为 {symbol} 获取 {interval} 周期的K线数据，并检查数据质量。

要求：
1. 获取最新的500根K线
2. 检查数据完整性和质量
3. 返回数据摘要和质量报告
"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["data_quality"] = {"status": "collected", "agent_response": str(last_message.content)}

    _update_timing(state, "data_collector", t0)
    return state


async def node_structure_analyzer(state: ChanlunState) -> ChanlunState:
    """结构分析节点"""
    t0 = datetime.now()
    from agents.structure_analyzer import build_agent
    import pandas as pd
    import os
    from utils.chanlun_structure import ChanLunAnalyzer

    agent = build_agent()

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    # 获取最新数据文件
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    data_dir = os.path.join(workspace_path, "data")

    # 查找最新数据文件
    files = [f for f in os.listdir(data_dir) if f.startswith(symbol) and f.endswith('.csv')]
    if files:
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)))
        latest_file = os.path.join(data_dir, files[-1])

        # 读取数据
        df = pd.read_csv(latest_file)

        # 使用算法进行结构分析
        analyzer = ChanLunAnalyzer()
        analysis_result = await asyncio.to_thread(analyzer.analyze, df)

        # 调用智能体生成详细分析报告
        prompt = f"""请对 {symbol} {interval} 周期进行结构分析。

## 算法分析结果
```json
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}
```

请基于以上算法结果，进行详细的结构分析，包括：
1. 当前走势类型
2. 笔、线段、中枢的状态
3. 走势完成度
4. 关键支撑阻力位
5. 结构强弱判断
"""

        response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

        last_message = response["messages"][-1]
        state["messages"].append(last_message)
        state["structure_analysis"] = {
            "status": "completed",
            "algorithm_result": analysis_result,
            "agent_response": str(last_message.content)
        }
    else:
        state["structure_analysis"] = {
            "status": "failed",
            "error": "No data file found"
        }

    _update_timing(state, "structure_analyzer", t0)
    return state


async def node_dynamics_analyzer(state: ChanlunState) -> ChanlunState:
    """动力学分析节点"""
    t0 = datetime.now()
    from agents.dynamics_analyzer import build_agent
    import pandas as pd
    import os
    from utils.chanlun_dynamics import DynamicsAnalyzer

    agent = build_agent()

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    # 获取最新数据文件
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    data_dir = os.path.join(workspace_path, "data")

    # 查找最新数据文件
    files = [f for f in os.listdir(data_dir) if f.startswith(symbol) and f.endswith('.csv')]
    if files:
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)))
        latest_file = os.path.join(data_dir, files[-1])

        # 读取数据
        df = pd.read_csv(latest_file)

        # 使用算法进行动力学分析
        analyzer = DynamicsAnalyzer()
        dynamics_result = await asyncio.to_thread(analyzer.analyze, df)

        # 调用智能体生成详细分析报告
        prompt = f"""请对 {symbol} {interval} 周期进行动力学分析。

## 算法分析结果
```json
{json.dumps(dynamics_result, ensure_ascii=False, indent=2)}
```

请基于以上算法结果，进行详细的动力学分析，包括：
1. MACD状态（DIF、DEA、MACD）
2. 是否有金叉/死叉
3. 是否有背驰（顶背驰/底背驰）
4. 背驰强度
5. 市场动量和力度
6. 买卖点判断
"""

        response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

        last_message = response["messages"][-1]
        state["messages"].append(last_message)
        state["dynamics_analysis"] = {
            "status": "completed",
            "algorithm_result": dynamics_result,
            "agent_response": str(last_message.content)
        }
    else:
        state["dynamics_analysis"] = {
            "status": "failed",
            "error": "No data file found"
        }

    _update_timing(state, "dynamics_analyzer", t0)
    return state


async def node_practical_theory(state: ChanlunState) -> ChanlunState:
    """实战理论节点"""
    t0 = datetime.now()
    from agents.practical_theory import build_agent
    import os
    import json

    agent = build_agent()

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    # 获取最新数据文件
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    data_dir = os.path.join(workspace_path, "data")

    # 查找最新数据文件
    files = [f for f in os.listdir(data_dir) if f.startswith(symbol) and f.endswith('.csv')]
    if files:
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)))
        latest_file = os.path.join(data_dir, files[-1])

        # 准备结构分析结果
        structure_result_json = json.dumps(state.get("structure_analysis", {}), ensure_ascii=False)
        dynamics_result_json = json.dumps(state.get("dynamics_analysis", {}), ensure_ascii=False)

        # 调用智能体进行实战理论分析
        prompt = f"""请对 {symbol} {interval} 周期进行实战理论分析，识别三类买卖点。

## 结构分析结果
{structure_result_json}

## 动力学分析结果
{dynamics_result_json}

请基于以上分析，识别三类买卖点，并提供仓位管理和操作节奏建议。"""

        response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

        last_message = response["messages"][-1]
        state["messages"].append(last_message)
        state["practical_theory_analysis"] = {
            "status": "completed",
            "agent_response": str(last_message.content)
        }
    else:
        state["practical_theory_analysis"] = {
            "status": "failed",
            "error": "No data file found"
        }

    _update_timing(state, "practical_theory", t0)
    return state


async def node_risk_manager(state: ChanlunState) -> ChanlunState:
    """风控节点"""
    t0 = datetime.now()
    from agents.risk_manager import build_agent
    import json

    agent = build_agent()

    # 准备决策数据
    decision_data_json = json.dumps(state.get("trading_decision", {}), ensure_ascii=False)

    # 准备市场数据
    market_data_json = json.dumps({
        "fear_greed_index": 65,  # 示例值
        "funding_rate": 0.01,    # 示例值
        "volatility": 0.02      # 示例值
    }, ensure_ascii=False)

    # 调用智能体进行风控审核
    prompt = f"""请对以下交易决策进行风控审核。

## 交易决策
{decision_data_json}

## 市场数据
{market_data_json}

## 实战理论分析
{state.get("practical_theory_analysis", {}).get("agent_response", "无")}

请进行风控审核，判断是否通过风控检查，并给出风控建议。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["risk_audit"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    _update_timing(state, "risk_manager", t0)
    return state


async def node_sentiment_analyzer(state: ChanlunState) -> ChanlunState:
    """市场情绪分析节点（并行组1）"""
    t0 = datetime.now()
    from agents.sentiment_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行市场情绪分析。

需要分析：
1. 恐慌贪婪指数（Fear & Greed Index）
2. 资金费率（Funding Rate）
3. 爆仓数据
4. 持仓量变化

请综合分析市场情绪，并提供情绪层面的交易建议。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["sentiment_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    _update_timing(state, "sentiment_analyzer", t0)
    _mark_parallel_done(state, "sentiment_analyzer")
    return state


async def node_cross_market_analyzer(state: ChanlunState) -> ChanlunState:
    """跨市场联动分析节点（并行组1）"""
    t0 = datetime.now()
    from agents.cross_market_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行跨市场联动分析。

需要分析：
1. 美股市场（标普500、纳斯达克）
2. 黄金市场
3. 美元指数（DXY）
4. 加密货币市场内部结构

请综合分析跨市场影响，并提供宏观层面的交易建议。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["cross_market_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    _update_timing(state, "cross_market_analyzer", t0)
    _mark_parallel_done(state, "cross_market_analyzer")
    return state


async def node_onchain_analyzer(state: ChanlunState) -> ChanlunState:
    """链上数据分析节点（并行组1）"""
    t0 = datetime.now()
    from agents.onchain_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行链上数据分析。

需要分析：
1. 交易所流入流出
2. 巨鲸活动动向
3. 网络健康状况（活跃地址、内存池）
4. 算力和难度变化

请综合分析链上信号，并提供链上层面的交易建议。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["onchain_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    _update_timing(state, "onchain_analyzer", t0)
    _mark_parallel_done(state, "onchain_analyzer")
    return state


async def node_system_monitor(state: ChanlunState) -> ChanlunState:
    """系统监控节点（并行组2）"""
    t0 = datetime.now()
    from agents.system_monitor import build_agent

    agent = build_agent()

    prompt = """请检查系统健康状态和数据质量。

检查项：
1. CPU、内存、磁盘使用情况
2. 数据文件的完整性和新鲜度
3. 生成健康报告

如果发现问题，请明确说明。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["system_health"] = {"status": "checked", "agent_response": str(last_message.content)}

    _update_timing(state, "system_monitor", t0)
    _mark_parallel_done(state, "system_monitor")
    return state


async def node_simulation_check(state: ChanlunState) -> ChanlunState:
    """模拟盘检查节点（并行组2）"""
    t0 = datetime.now()
    from agents.simulation import build_agent

    agent = build_agent()

    prompt = """请检查当前模拟盘状态。

需要提供：
1. 当前绩效统计（胜率、总盈亏、盈亏比等）
2. 当前持仓情况
3. 策略有效性评估

根据模拟盘绩效，评估当前策略是否适合继续执行。"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["simulation_performance"] = {"status": "checked", "agent_response": str(last_message.content)}

    _update_timing(state, "simulation_check", t0)
    _mark_parallel_done(state, "simulation_check")
    return state


async def node_decision_maker(state: ChanlunState) -> ChanlunState:
    """首席决策节点"""
    t0 = datetime.now()
    from agents.decision_maker import build_agent

    agent = build_agent()

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    # 收集所有分析结果
    prompt = f"""你是首席决策智能体，请基于以下信息做出交易决策。

## 基本信息
- 交易对: {symbol}
- K线周期: {interval}
- 用户需求: {state.get("user_request", "市场分析")}

## 已收集信息

### 数据采集
{state.get("data_quality", {}).get("agent_response", "无")}

### 结构分析
{state.get("structure_analysis", {}).get("agent_response", "无")}

### 动力学分析
{state.get("dynamics_analysis", {}).get("agent_response", "无")}

### 市场情绪分析
{state.get("sentiment_analysis", {}).get("agent_response", "无")}

### 跨市场联动分析
{state.get("cross_market_analysis", {}).get("agent_response", "无")}

### 链上数据分析
{state.get("onchain_analysis", {}).get("agent_response", "无")}

### 系统健康
{state.get("system_health", {}).get("agent_response", "无")}

### 模拟盘绩效
{state.get("simulation_performance", {}).get("agent_response", "无")}

## 任务
请基于缠论理论和以上所有维度的分析，进行综合研判并输出交易决策。

## 维度权重
- 结构分析：30%
- 动力学分析：25%
- 市场情绪分析：15%
- 跨市场联动分析：15%
- 链上数据分析：10%
- 模拟盘绩效：5%

## 输出要求
必须包含：
- 交易方向（long/short/neutral）
- 置信度（0-100%）
- 入场价格区间
- 止损价格
- 止盈目标
- 建议仓位
- 风险等级
- 详细分析逻辑（结构+动力学+情绪+跨市场+链上+模拟盘）
- 多维度共振确认

如果信号不明确，请明确说明保持观望。
"""

    response = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["trading_decision"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    _update_timing(state, "decision_maker", t0)
    return state


async def node_report_generator(state: ChanlunState) -> ChanlunState:
    """研报生成节点"""
    t0 = datetime.now()
    from agents.report_generator import generate_analysis_report, get_decision_stats
    import os

    symbol = state.get("symbol", "BTCUSDT")
    interval = state.get("interval", "1h")

    # 生成研报
    report_result = generate_analysis_report(
        symbol=symbol,
        interval=interval,
        structure_data=state.get("structure_analysis"),
        dynamics_data=state.get("dynamics_analysis"),
        sentiment_data=state.get("sentiment_analysis"),
        cross_market_data=state.get("cross_market_analysis"),
        onchain_data=state.get("onchain_analysis"),
        decision_data=state.get("trading_decision")
    )

    # 获取决策统计
    decision_stats = get_decision_stats(last_n=50)

    # 保存报告路径
    state["report_path"] = report_result.get("save_path")
    state["decision_stats"] = decision_stats

    # 添加报告信息到消息
    report_message = f"""
## 研报生成完成

- **报告路径**: {report_result.get('save_path')}
- **决策ID**: {report_result.get('decision_id', 'N/A')}

## 历史决策统计

- **总决策数**: {decision_stats.get('total', 0)}
- **已执行**: {decision_stats.get('executed', 0)}
- **已平仓**: {decision_stats.get('closed', 0)}
- **胜率**: {decision_stats.get('pnl', {}).get('win_rate', 0)}%
- **总盈亏**: {decision_stats.get('pnl', {}).get('total_pnl', 0)}

研报已保存到文件，请查看详细内容。
"""

    state["messages"].append(AIMessage(content=report_message))

    _update_timing(state, "report_generator", t0)
    return state


def build_chanlun_workflow():
    """构建缠论多智能体工作流 v5.1（DAG 并行版）

    DAG 拓扑：
        data_collector
            │
            ▼
        structure_analyzer
            │
            ▼
        dynamics_analyzer
            │
            ▼
        practical_theory
            │
            ├─▶ sentiment_analyzer   ┐
            ├─▶ cross_market_analyzer├──▶ 并行组1（辅助维度）
            ├─▶ onchain_analyzer     ┘
            ├─▶ system_monitor       ┐
            └─▶ simulation_check     ┘──▶ 并行组2（系统检查）
            │                         (5 节点全部完成后 ↓)
            ▼
        decision_maker
            │
            ▼
        risk_manager
            │
            ▼
        report_generator
            │
            ▼
           END
    """

    workflow = StateGraph(ChanlunState)

    # ── 添加节点 ──
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("practical_theory", node_practical_theory)

    # 并行组1：辅助维度分析
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("cross_market_analyzer", node_cross_market_analyzer)
    workflow.add_node("onchain_analyzer", node_onchain_analyzer)

    # 并行组2：系统检查
    workflow.add_node("system_monitor", node_system_monitor)
    workflow.add_node("simulation_check", node_simulation_check)

    # 决策 & 风控 & 研报
    workflow.add_node("decision_maker", node_decision_maker)
    workflow.add_node("risk_manager", node_risk_manager)
    workflow.add_node("report_generator", node_report_generator)

    # ── 设置入口 ──
    workflow.set_entry_point("data_collector")

    # ── 线性主干 ──
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "practical_theory")

    # ── Fan-out: practical_theory → 5 个并行节点 ──
    workflow.add_edge("practical_theory", "sentiment_analyzer")
    workflow.add_edge("practical_theory", "cross_market_analyzer")
    workflow.add_edge("practical_theory", "onchain_analyzer")
    workflow.add_edge("practical_theory", "system_monitor")
    workflow.add_edge("practical_theory", "simulation_check")

    # ── Fan-in: 5 个并行节点 → decision_maker ──
    workflow.add_edge("sentiment_analyzer", "decision_maker")
    workflow.add_edge("cross_market_analyzer", "decision_maker")
    workflow.add_edge("onchain_analyzer", "decision_maker")
    workflow.add_edge("system_monitor", "decision_maker")
    workflow.add_edge("simulation_check", "decision_maker")

    # ── 线性尾部 ──
    workflow.add_edge("decision_maker", "risk_manager")
    workflow.add_edge("risk_manager", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


def run_chanlun_analysis(user_request: str, symbol: str = "BTCUSDT", interval: str = "1h"):
    """
    运行缠论分析 v5.1（同步，兼容旧调用方式）

    Args:
        user_request: 用户请求描述
        symbol: 交易对
        interval: K线周期

    Returns:
        分析结果
    """
    workflow = build_chanlun_workflow()

    initial_state = _build_initial_state(user_request, symbol, interval)

    # 同步执行（LangGraph 会在内部调度 async 节点）
    result = workflow.invoke(initial_state)
    return result


async def run_chanlun_analysis_async(user_request: str, symbol: str = "BTCUSDT", interval: str = "1h"):
    """
    运行缠论分析 v5.1（异步，支持并行调度）

    Args:
        user_request: 用户请求描述
        symbol: 交易对
        interval: K线周期

    Returns:
        分析结果
    """
    workflow = build_chanlun_workflow()

    initial_state = _build_initial_state(user_request, symbol, interval)

    # 异步执行，LangGraph 自动并行调度 fan-out 分支
    result = await workflow.ainvoke(initial_state)
    return result


def run_chanlun_analysis_local(
    user_request: str = "BTC 缠论分析",
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    verbose: bool = True,
):
    """
    本地运行缠论分析 v5.1（独立脚本入口）

    无需 FastAPI 服务，直接在本地执行工作流。
    使用 ainvoke 以启用 LangGraph 的并行调度。

    Args:
        user_request: 分析请求描述
        symbol: 交易对
        interval: K线周期
        verbose: 是否打印执行过程

    Returns:
        分析结果 dict，含 execution_timing 和 parallel_group_status
    """
    import time

    if verbose:
        print("\n" + "=" * 60)
        print("  缠论多智能体系统 v5.1 — DAG 并行执行")
        print("=" * 60)
        print(f"  交易对: {symbol}  |  周期: {interval}")
        print(f"  请求: {user_request}")
        print("=" * 60 + "\n")

    workflow = build_chanlun_workflow()
    initial_state = _build_initial_state(user_request, symbol, interval)

    wall_start = time.time()

    # 使用 asyncio.run 驱动异步执行（启用并行）
    result = asyncio.run(workflow.ainvoke(initial_state))

    wall_end = time.time()
    wall_duration = wall_end - wall_start

    if verbose:
        # ── 执行耗时汇总 ──
        timing = result.get("execution_timing") or {}
        print("\n" + "=" * 60)
        print("  ⏱  执行耗时汇总")
        print("=" * 60)

        for node_name, info in timing.items():
            dur = info.get("duration_seconds", 0)
            print(f"  {node_name:<25s}  {dur:>6.2f}s")

        # ── 并行效率分析 ──
        # 并行组：sentiment / cross_market / onchain / system_monitor / simulation_check
        parallel_nodes = [
            "sentiment_analyzer", "cross_market_analyzer", "onchain_analyzer",
            "system_monitor", "simulation_check",
        ]
        parallel_total = sum(
            (timing.get(n, {}).get("duration_seconds", 0)) for n in parallel_nodes
        )
        serial_total = sum(
            (timing.get(n, {}).get("duration_seconds", 0))
            for n in timing if n not in parallel_nodes
        )

        print("\n" + "-" * 60)
        print(f"  并行阶段串行耗时（若不并行）: {parallel_total:.2f}s")
        print(f"  实际总耗时:                    {wall_duration:.2f}s")
        if parallel_total > 0:
            print(f"  并行加速比:                    {parallel_total / max(wall_duration - serial_total, 0.01):.2f}x")
        print(f"  预估节省时间:                  {max(parallel_total - (wall_duration - serial_total), 0):.2f}s")
        print("=" * 60 + "\n")

        # ── 并行节点完成状态 ──
        pgs = result.get("parallel_group_status") or {}
        print("  📊 并行节点完成状态:")
        for node, status in pgs.items():
            icon = "✅" if status == "completed" else "❌"
            print(f"    {icon} {node}: {status}")
        print()

    return result


def _build_initial_state(user_request: str, symbol: str, interval: str) -> Dict[str, Any]:
    """构建工作流初始状态"""
    return {
        "messages": [],
        "user_request": user_request,
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
        # v5.1 新增
        "parallel_group_status": {},
        "execution_timing": {},
    }
