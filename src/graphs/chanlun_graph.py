"""
缠论多智能体工作流 v5.0
集成实战理论和风控审核
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

    # 结构分析结果
    structure_analysis: Optional[Dict[str, Any]]

    # 动力学分析结果
    dynamics_analysis: Optional[Dict[str, Any]]

    # 实战理论分析结果 ⭐ 新增
    practical_theory_analysis: Optional[Dict[str, Any]]

    # 风控审核结果 ⭐ 新增
    risk_audit: Optional[Dict[str, Any]]

    # 市场情绪分析结果
    sentiment_analysis: Optional[Dict[str, Any]]

    # 跨市场联动分析结果
    cross_market_analysis: Optional[Dict[str, Any]]

    # 链上数据分析结果
    onchain_analysis: Optional[Dict[str, Any]]

    # 系统监控结果
    system_health: Optional[Dict[str, Any]]
    data_quality_report: Optional[Dict[str, Any]]

    # 模拟盘数据
    simulation_performance: Optional[Dict[str, Any]]
    open_positions: Optional[List[Dict[str, Any]]]

    # 最终决策
    trading_decision: Optional[Dict[str, Any]]

    # 研报和历史记录
    report_path: Optional[str]
    decision_stats: Optional[Dict[str, Any]]


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


def node_practical_theory(state: ChanlunState) -> ChanlunState:
    """实战理论节点 ⭐ 新增"""
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

        response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

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

    return state


def node_risk_manager(state: ChanlunState) -> ChanlunState:
    """风控节点 ⭐ 新增"""
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

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["risk_audit"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    return state


def node_sentiment_analyzer(state: ChanlunState) -> ChanlunState:
    """市场情绪分析节点"""
    from agents.sentiment_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行市场情绪分析。

需要分析：
1. 恐慌贪婪指数（Fear & Greed Index）
2. 资金费率（Funding Rate）
3. 爆仓数据
4. 持仓量变化

请综合分析市场情绪，并提供情绪层面的交易建议。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["sentiment_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    return state


def node_cross_market_analyzer(state: ChanlunState) -> ChanlunState:
    """跨市场联动分析节点"""
    from agents.cross_market_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行跨市场联动分析。

需要分析：
1. 美股市场（标普500、纳斯达克）
2. 黄金市场
3. 美元指数（DXY）
4. 加密货币市场内部结构

请综合分析跨市场影响，并提供宏观层面的交易建议。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["cross_market_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    return state


def node_onchain_analyzer(state: ChanlunState) -> ChanlunState:
    """链上数据分析节点"""
    from agents.onchain_analyzer import build_agent

    agent = build_agent()

    prompt = """请进行链上数据分析。

需要分析：
1. 交易所流入流出
2. 巨鲸活动动向
3. 网络健康状况（活跃地址、内存池）
4. 算力和难度变化

请综合分析链上信号，并提供链上层面的交易建议。"""

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["onchain_analysis"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
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

    response = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["trading_decision"] = {
        "status": "completed",
        "agent_response": str(last_message.content)
    }

    return state


def node_report_generator(state: ChanlunState) -> ChanlunState:
    """研报生成节点 ⭐ 新增"""
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

    return state


def build_chanlun_workflow():
    """构建缠论多智能体工作流 v5.0"""

    workflow = StateGraph(ChanlunState)

    # 添加节点
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("practical_theory", node_practical_theory)  # ⭐ 新增
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("cross_market_analyzer", node_cross_market_analyzer)
    workflow.add_node("onchain_analyzer", node_onchain_analyzer)
    workflow.add_node("system_monitor", node_system_monitor)
    workflow.add_node("simulation_check", node_simulation_check)
    workflow.add_node("decision_maker", node_decision_maker)
    workflow.add_node("risk_manager", node_risk_manager)  # ⭐ 新增
    workflow.add_node("report_generator", node_report_generator)

    # 设置入口
    workflow.set_entry_point("data_collector")

    # 定义边（执行顺序）
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "practical_theory")  # ⭐ 新增
    workflow.add_edge("practical_theory", "sentiment_analyzer")  # ⭐ 新增
    workflow.add_edge("sentiment_analyzer", "cross_market_analyzer")
    workflow.add_edge("cross_market_analyzer", "onchain_analyzer")
    workflow.add_edge("onchain_analyzer", "system_monitor")
    workflow.add_edge("system_monitor", "simulation_check")
    workflow.add_edge("simulation_check", "decision_maker")
    workflow.add_edge("decision_maker", "risk_manager")  # ⭐ 新增
    workflow.add_edge("risk_manager", "report_generator")  # ⭐ 新增
    workflow.add_edge("report_generator", END)

    return workflow.compile()


def run_chanlun_analysis(user_request: str, symbol: str = "BTCUSDT", interval: str = "1h"):
    """
    运行缠论分析 v5.0

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
        "practical_theory_analysis": None,  # ⭐ 新增
        "risk_audit": None,  # ⭐ 新增
        "sentiment_analysis": None,
        "cross_market_analysis": None,
        "onchain_analysis": None,
        "system_health": None,
        "data_quality_report": None,
        "simulation_performance": None,
        "open_positions": None,
        "trading_decision": None,
        "report_path": None,
        "decision_stats": None
    }

    # 执行工作流
    result = workflow.invoke(initial_state)

    return result
