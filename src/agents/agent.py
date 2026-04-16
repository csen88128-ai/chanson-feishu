"""
缠论多智能体系统 - 主Agent
负责协调和调度智能体的协作
"""
import os
import json
from typing import Annotated, List, Dict, Any, Optional
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
import logging
logger = logging.getLogger(__name__)
from coze_coding_utils.runtime_ctx.context import default_headers, new_context
from storage.memory.memory_saver import get_memory_saver

# 导入可用的工具（使用正确的函数名）
from tools.data_tools import get_kline_data, check_data_quality
from tools.monitor_tools import check_system_health
from tools.simulation_tools import get_simulation_performance
from tools.sentiment_tools import get_market_sentiment, get_liquidation_data, get_open_interest
from tools.cross_market_tools import get_cross_market_data, get_crypto_market_dominance
from tools.onchain_tools import get_onchain_data, get_hashrate_difficulty

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

# 配置文件路径
LLM_CONFIG = "config/agent_llm_config.json"


def build_agent(ctx=None):
    """构建缠论多智能体系统的主Agent"""

    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/chanson-feishu")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    # 创建大语言模型
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

    # 定义可用的工具（使用实际存在的工具）
    tools = [
        get_kline_data,
        check_data_quality,
        check_system_health,
        get_simulation_performance,
        get_market_sentiment,
        get_liquidation_data,
        get_open_interest,
        get_cross_market_data,
        get_crypto_market_dominance,
        get_onchain_data,
        get_hashrate_difficulty
    ]

    # 构建Agent
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

    return agent
