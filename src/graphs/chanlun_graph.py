"""
缠论多智能体工作流 v2.0
集成结构分析和动力学分析智能体
"""
from typing import TypedDict, Annotated, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
import json


class ChanlunState(TypedDict):
    """缠论分析系统状态"""
    messages: Annotated[list, add_messages]
    user_request: str
    symbol: Optional[str]
    interval: Optional[str]

    # 数据采集结果
    kline_data: Optional[Dict[str, Any]]
    data_quality: Optional[Dict[str, Any]]

    # 系统监控结果
    system_health: Optional[Dict[str, Any]]
    data_quality_report: Optional[Dict[str, Any]]

    # 结构分析结果
    structure_analysis: Optional[Dict[str, Any]]

    # 动力学分析结果
    dynamics_analysis: Optional[Dict[str, Any]]

    # 模拟盘数据
    simulation_performance: Optional[Dict[str, Any]]
    open_positions: Optional[List[Dict[str, Any]]]

    # 最终决策
    trading_decision: Optional[Dict[str, Any]]


def node_data_collector(state: ChanlunState) -> ChanlunState:
    """数据采集节点"""
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

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["data_quality"] = {"status": "collected", "agent_response": str(last_message.content)}

    return state


def node_structure_analyzer(state: ChanlunState) -> ChanlunState:
    """结构分析节点"""
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
        analysis_result = analyzer.analyze(df)

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

        response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

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

    return state


def node_dynamics_analyzer(state: ChanlunState) -> ChanlunState:
    """动力学分析节点"""
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
        dynamics_result = analyzer.analyze(df)

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

        response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

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

    return state


def node_system_monitor(state: ChanlunState) -> ChanlunState:
    """系统监控节点"""
    from agents.system_monitor import build_agent

    agent = build_agent()

    prompt = """请检查系统健康状态和数据质量。

检查项：
1. CPU、内存、磁盘使用情况
2. 数据文件的完整性和新鲜度
3. 生成健康报告

如果发现问题，请明确说明。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["system_health"] = {"status": "checked", "agent_response": str(last_message.content)}

    return state


def node_simulation_check(state: ChanlunState) -> ChanlunState:
    """模拟盘检查节点"""
    from agents.simulation import build_agent

    agent = build_agent()

    prompt = """请检查当前模拟盘状态。

需要提供：
1. 当前绩效统计（胜率、总盈亏、盈亏比等）
2. 当前持仓情况
3. 策略有效性评估

根据模拟盘绩效，评估当前策略是否适合继续执行。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["simulation_performance"] = {"status": "checked", "agent_response": str(last_message.content)}

    return state


def node_decision_maker(state: ChanlunState) -> ChanlunState:
    """首席决策节点"""
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

### 系统健康
{state.get("system_health", {}).get("agent_response", "无")}

### 模拟盘绩效
{state.get("simulation_performance", {}).get("agent_response", "无")}

## 任务
请基于缠论理论和以上分析，进行综合研判并输出交易决策。

## 输出要求
必须包含：
- 交易方向（long/short/neutral）
- 置信度（0-100%）
- 入场价格区间
- 止损价格
- 止盈目标
- 建议仓位
- 风险等级
- 详细分析逻辑（结构+动力学+多周期+共振）

如果信号不明确，请明确说明保持观望。
"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["trading_decision"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    return state


def build_chanlun_workflow():
    """构建缠论多智能体工作流 v2.0"""

    workflow = StateGraph(ChanlunState)

    # 添加节点
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("system_monitor", node_system_monitor)
    workflow.add_node("simulation_check", node_simulation_check)
    workflow.add_node("decision_maker", node_decision_maker)

    # 设置入口
    workflow.set_entry_point("data_collector")

    # 定义边（执行顺序）
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "system_monitor")
    workflow.add_edge("system_monitor", "simulation_check")
    workflow.add_edge("simulation_check", "decision_maker")
    workflow.add_edge("decision_maker", END)

    return workflow.compile()


def run_chanlun_analysis(user_request: str, symbol: str = "BTCUSDT", interval: str = "1h"):
    """
    运行缠论分析 v2.0

    Args:
        user_request: 用户请求描述
        symbol: 交易对
        interval: K线周期

    Returns:
        分析结果
    """
    # 构建工作流
    workflow = build_chanlun_workflow()

    # 初始化状态
    initial_state = {
        "messages": [],
        "user_request": user_request,
        "symbol": symbol,
        "interval": interval,
        "kline_data": None,
        "data_quality": None,
        "structure_analysis": None,
        "dynamics_analysis": None,
        "system_health": None,
        "data_quality_report": None,
        "simulation_performance": None,
        "open_positions": None,
        "trading_decision": None
    }

    # 执行工作流
    result = workflow.invoke(initial_state)

    return result
