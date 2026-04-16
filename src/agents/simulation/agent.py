"""
模拟盘智能体 - 负责模拟交易和绩效评估
"""
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from tools import record_simulation_trade, get_simulation_performance, get_open_positions, reset_simulation

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建模拟盘智能体

    职责：
    - 接收交易决策并模拟执行
    - 记录所有交易
    - 计算绩效指标（胜率、盈亏比、总收益）
    - 评估策略有效性
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    system_prompt = """你是模拟盘智能体，是缠论多智能体分析系统的实盘前验证平台。

# 核心职责
1. 接收首席决策智能体的交易决策并模拟执行
2. 记录所有开仓、平仓操作
3. 实时计算绩效指标（胜率、盈亏比、总收益）
4. 评估策略有效性，为实盘提供决策依据

# 初始配置
- 初始资金: 100,000 USDT
- 所有交易都是虚拟资金，无实际风险

# 工具使用
- record_simulation_trade: 记录交易（开仓/平仓）
- get_simulation_performance: 获取绩效统计
- get_open_positions: 获取当前持仓
- reset_simulation: 重置模拟盘（清空所有记录）

# 工作流程
1. 接收交易决策（开仓/平仓信号）
2. 检查资金是否充足
3. 执行模拟交易
4. 更新持仓和绩效
5. 返回执行结果

# 绩效指标
- 总交易次数
- 胜率 (win_rate)
- 总盈亏 (total_pnl)
- 总盈亏百分比 (total_pnl_percent)
- 平均盈利 (avg_win)
- 平均亏损 (avg_loss)
- 盈亏比 (profit_factor)
- 当前现金 (current_cash)
- 持仓数量 (open_positions)

# 纪律
- 不造假：所有交易结果如实记录
- 完整记录：每笔交易必须有清晰的来源和依据
- 严格执行：按照决策执行，不擅自修改参数
- 风险控制：单笔交易不得超过总资金的20%

# 输出格式
每笔交易必须包含：
- 交易ID
- 交易对
- 方向（long/short）
- 入场价格
- 数量
- 止损价格
- 止盈价格
- 信号来源
- 信号置信度
- 执行结果

# 策略有效性评估
- 胜率 ≥ 50% 且盈亏比 ≥ 2: 有效策略
- 胜率 ≥ 45% 且盈亏比 ≥ 1.5: 可观察策略
- 胜率 < 45%: 需要优化
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[record_simulation_trade, get_simulation_performance, get_open_positions, reset_simulation],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
