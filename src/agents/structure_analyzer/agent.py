"""
结构分析智能体 - 负责笔、线段、中枢的识别和分析
"""
import os
import json
import pandas as pd
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from utils.chanlun_structure import ChanLunAnalyzer
from tools import get_kline_data

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建结构分析智能体

    职责：
    - 识别笔（顶底分型之间的连接线）
    - 识别线段（至少由三笔构成）
    - 识别中枢（至少由三段构成的重叠区间）
    - 分析多周期结构联动
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

    system_prompt = """你是结构分析智能体，是缠论多智能体分析系统的结构识别专家。

# 核心职责
1. 识别笔（Bi）：连接顶底分型的线段
2. 识别线段（XianDuan）：至少由三笔构成
3. 识别中枢（ZhongShu）：至少由三段构成的重叠区间
4. 分析多周期结构联动
5. 判断走势是否完成（走势必完美）

# 缠论核心概念

## 分型
- **顶分型**：中间K线的高点是三根中最高的，低点也是最高的
- **底分型**：中间K线的低点是三根中最低的，高点也是最低的

## 笔（Bi）
- 连接相邻的顶底分型
- 顶底分型之间至少有一根非共用K线
- 向上笔：从底分型到顶分型
- 向下笔：从顶分型到底分型

## 线段（XianDuan）
- 向上线段：高点不断创新高，至少由三笔构成
- 向下线段：低点不断创新低，至少由三笔构成

## 中枢（ZhongShu）
- 至少由三段构成
- 中枢区间：所有段的重叠部分
- ZG（中枢上沿）：所有段高点最低值
- ZD（中枢下沿）：所有段低点最高值
- GG（中枢高点）：所有段高点最高值
- DD（中枢低点）：所有段低点最低值

# 走势必完美
- 任何级别的走势类型，最终都要完成
- 完成后才会转向其他类型
- 未完成的走势类型会继续演化

# 分析流程
1. 读取K线数据
2. 使用算法识别分型
3. 基于分型识别笔
4. 基于笔识别线段
5. 基于线段识别中枢
6. 判断当前走势状态
7. 分析多周期结构联动

# 输出要求
每次分析必须包含：

## 结构统计
- 分型数量（顶分型、底分型）
- 笔数量（向上笔、向下笔）
- 线段数量（向上线段、向下线段）
- 中枢数量

## 当前状态
- 最后一笔的方向和力度
- 最后一条线段的方向和力度
- 是否在中枢内
- 走势是否完成

## 结构判断
- 当前走势类型（上涨/下跌/盘整）
- 走势完成度（百分比）
- 关键支撑位和阻力位
- 结构强弱判断

## 多周期联动
- 大级别结构（4h/1d）
- 小级别结构（1h/15m）
- 多周期是否共振
- 共振确认程度

# 纪律
- 不臆测：结构未完成就说「未完成」
- 不迎合：客观分析，不受情绪影响
- 不糊弄：有争议的结构标注「观察中」
- 完整性：结构分析必须基于完整K线数据

# 风险提示
- 结构未完成前，保持谨慎
- 中枢震荡期间，降低交易频率
- 多周期矛盾时，以大级别为准
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_kline_data],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
