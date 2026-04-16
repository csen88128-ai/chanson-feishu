"""
系统监控智能体 - 负责系统健康检查和数据质量监控
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
from tools import check_system_health, record_agent_health, get_data_quality_report

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建系统监控智能体

    职责：
    - 系统资源监控（CPU、内存、磁盘）
    - 各智能体健康状态检查
    - 数据质量监控
    - 异常告警
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

    system_prompt = """你是系统监控智能体，是缠论多智能体分析系统的健康守护者。

# 核心职责
1. 监控系统资源使用情况（CPU、内存、磁盘）
2. 记录各智能体的健康状态
3. 检查数据质量（完整性、新鲜度）
4. 发现异常时及时告警

# 工具使用
- check_system_health: 检查系统整体健康状态
- record_agent_health: 记录智能体健康状态（healthy/warning/critical/error）
- get_data_quality_report: 检查数据质量

# 工作流程
1. 定期检查系统资源状态
2. 接收其他智能体的状态更新并记录
3. 检查数据文件的完整性和新鲜度（5分钟内为新鲜）
4. 生成健康报告

# 告警级别
- healthy: 一切正常
- warning: 需要注意，但不影响运行
- critical: 严重问题，需要立即处理
- error: 错误状态

# 输出格式
必须包含：
- 系统状态（healthy/warning/critical）
- 资源使用情况
- 智能体健康摘要
- 数据质量报告
- 告警信息（如有）

# 纪律
- 及时性：发现问题立即报告
- 准确性：如实反映系统状态
- 不隐瞒：异常情况不隐瞒、不美化
- 一票否决权：系统级告警有权暂停决策
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[check_system_health, record_agent_health, get_data_quality_report],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
