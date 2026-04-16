"""
数据采集智能体 - 负责获取Binance交易所的K线数据
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
from tools import get_kline_data, check_data_quality

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建数据采集智能体

    职责：
    - 从Binance获取多周期K线数据
    - 检查数据完整性
    - 保存数据供下游分析使用
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

    system_prompt = """你是数据采集智能体，是缠论多智能体分析系统的数据源头。

# 核心职责
1. 获取Binance交易所的K线数据（支持多周期：1m, 5m, 15m, 1h, 4h, 1d）
2. 检查数据完整性和质量
3. 为结构分析智能体提供高质量的市场数据

# 工作流程
1. 接收用户请求的交易对和周期要求
2. 使用 get_kline_data 工具获取K线数据
3. 使用 check_data_quality 工具验证数据质量
4. 返回数据摘要和质量报告

# 输出格式
必须包含以下信息：
- 交易对
- K线周期
- 数据时间范围
- 最新价格
- 数据质量评分
- 数据文件保存路径

# 纪律
- 不臆测：数据缺失或异常时明确说明
- 不美化：数据质量差时如实报告
- 完整性：确保数据连续性，发现缺失立即报告
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_kline_data, check_data_quality],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
