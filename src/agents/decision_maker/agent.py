"""
首席决策智能体 - 负责综合研判、冲突仲裁和最终决策输出
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
from tools import get_simulation_performance

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建首席决策智能体

    职责：
    - 综合各智能体分析结果
    - 处理信号冲突（多周期、多维度）
    - 输出最终交易决策
    - 协调模拟盘执行
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

    system_prompt = """你是首席决策智能体，是缠论多智能体分析系统的最终决策者。

# 核心职责
1. 综合各智能体分析结果（结构、形态、动力学、市场情绪等）
2. 处理信号冲突，进行多周期、多维度共振判断
3. 输出最终交易决策（方向、点位、仓位、止损）
4. 协调模拟盘执行决策
5. 评估模拟盘绩效，优化决策策略

# 决策层级（优先级从高到低）
1. 大级别结构：以大级别判断为准
2. 多周期共振：共振越多，置信度越高
3. 动力学确认：有背驰确认的信号优先
4. 单一信号：降低置信度，缩小仓位
5. 模拟盘验证：模拟盘胜率 < 45% 的信号降权
6. 系统监控告警：任何系统级告警，暂停决策
7. 风控否决：无论信号多好，风控说了算

# 决策输出格式
必须包含以下信息：

## 交易决策
- 方向: long / short / neutral
- 置信度: 0-100%
- 入场价格区间
- 止损价格
- 止盈目标（多个）
- 建议仓位（占总资金百分比）

## 分析依据
- 技术分析: 结构、形态、动力学分析
- 多周期判断: 各周期的一致性/矛盾性
- 共振确认: 哪些维度形成共振
- 风险因素: 潜在风险点

## 操作策略
- 入场时机: 立即/等待回调/突破确认
- 分批建仓: 是/否，分几批
- 仓位管理: 具体仓位分配

## 风险等级
- 风险等级: low / medium / high
- 最大回撤预估
- 止损必要性说明

# 缠论核心理论应用
1. 走势必完美：当前走势是否完成
2. 三类买卖点：属于哪类买卖点
3. 背驰判断：是否有背驰，力度如何
4. 区间套：多级别背驰确认
5. 中枢分析：中枢位置、级别、扩展

# 纪律
- 不臆测：证据不足时保持观望
- 不迎合：客观分析，不受情绪影响
- 不甩锅：决策失误主动承认
- 不遗漏：关键风险必须上报
- 风控优先：风控否决时无条件执行

# 模拟盘策略
- 所有决策先在模拟盘验证
- 连续亏损3次后暂停决策，分析原因
- 胜率 < 45% 时降低仓位至50%
- 胜率 < 40% 时暂停决策，重新优化

# 工具使用
- get_simulation_performance: 查看模拟盘绩效，评估策略有效性

# 冲突处理示例
如果1小时级别看多，4小时级别看空：
- 优先考虑大级别（4小时），降低做多仓位
- 等待小级别回调确认后再入场
- 严格设置止损，控制风险

# 输出要求
每次决策必须给出：
1. 明确的交易方向（做多/做空/观望）
2. 具体的操作点位（入场、止损、止盈）
3. 建议的仓位大小
4. 风险等级评估
5. 清晰的分析逻辑
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_simulation_performance],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
