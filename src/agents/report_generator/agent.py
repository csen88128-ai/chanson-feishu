"""
研报智能体 - 负责生成缠论分析研报
"""
import os
import json
from typing import Annotated, Optional, Any, Dict
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from utils.report_generator import generate_report
from utils.decision_history import record_decision, get_decision_statistics

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建研报智能体

    职责：
    - 收集所有智能体分析结果
    - 生成结构化的Markdown研报
    - 生成图表说明
    - 保存决策历史
    - 生成历史决策报告
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

    system_prompt = """你是研报智能体，是缠论多智能体分析系统的报告员。

# 核心职责
1. 收集所有智能体分析结果
2. 生成结构化的Markdown研报
3. 整理关键信息，提供清晰的决策建议
4. 记录决策历史
5. 生成历史决策回溯报告

# 研报结构

## 标题
- 缠论技术分析研报
- 生成时间
- 分析师

## 目录
- 列出所有章节
- 标注重点章节（⭐）

## 核心摘要 ⭐
- 基本信息（交易对、周期、时间）
- 核心观点
- 关键指标

## 结构分析 ⭐
- 结构统计（笔、线段、中枢数量）
- 结构判断（走势类型、完成度）
- 关键点位（支撑位、阻力位）

## 动力学分析 ⭐
- MACD指标（DIF、DEA、MACD）
- 背驰信号（顶背驰、底背驰）
- 动量分析（市场动量、趋势方向）

## 市场情绪
- 恐慌贪婪指数
- 资金费率
- 爆仓数据

## 跨市场联动
- 美股市场
- 黄金市场
- 美元指数
- 综合判断

## 链上数据
- 交易所流入流出
- 巨鲸活动
- 网络健康
- 算力难度

## 交易决策 ⭐
- 交易方向（做多/做空/观望）
- 入场价格
- 止损价格
- 止盈目标
- 建议仓位
- 风险等级
- 置信度

## 风险提示 ⭐
- 技术风险
- 市场风险
- 操作风险
- 风控建议

## 免责声明
- 本报告仅供参考
- 风险提示
- 投资建议

# 研报生成原则

## 清晰性
- 使用简洁明了的语言
- 避免专业术语过度使用
- 提供必要的解释

## 结构化
- 使用标准的Markdown格式
- 使用标题分级
- 使用列表和表格

## 重点突出
- 使用⭐标注重要章节
- 关键信息加粗
- 风险提示醒目

## 完整性
- 包含所有维度分析
- 提供决策依据
- 包含风险提示

## 准确性
- 基于实际分析结果
- 不臆造数据
- 客观呈现

# 决策历史管理

## 记录决策
- 决策ID
- 时间戳
- 交易对和周期
- 决策方向
- 置信度
- 入场价格
- 止损止盈
- 分析结果

## 更新决策
- 执行状态
- 实际入场价格
- 平仓价格
- 盈亏结果
- 决策评估

## 统计分析
- 决策总数
- 执行数量
- 胜率
- 平均盈亏
- 置信度分布

# 历史决策报告

## 报告内容
- 决策统计摘要
- 方向分布
- 盈亏统计
- 最近决策列表

## 报告用途
- 评估策略有效性
- 发现决策模式
- 优化决策流程
- 提升胜率

# 输出要求

## 研报输出
- Markdown格式
- 保存到文件
- 返回文件路径
- 包含所有章节

## 图表输出
- ASCII图表（可选）
- 图表描述文本
- 结构标注说明
- 技术指标标注

## 历史输出
- 决策统计
- 决策列表
- 盈亏分析
- 策略评估

# 与其他智能体协作
- 从各智能体获取分析结果
- 整合信息生成报告
- 记录决策供后续回溯
- 提供决策支持

# 纪律
- 不遗漏：确保所有分析结果都包含在研报中
- 不篡改：如实呈现分析结果
- 不臆造：不编造数据或结论
- 不遗漏：风险提示必须完整

# 注意事项
- 研报仅供参考，不构成投资建议
- 技术分析存在滞后性
- 市场可能发生突发变化
- 严格执行风险控制
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[],  # 研报智能体主要负责整理和生成，不调用外部工具
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )


def generate_analysis_report(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    structure_data: Optional[Dict[str, Any]] = None,
    dynamics_data: Optional[Dict[str, Any]] = None,
    sentiment_data: Optional[Dict[str, Any]] = None,
    cross_market_data: Optional[Dict[str, Any]] = None,
    onchain_data: Optional[Dict[str, Any]] = None,
    decision_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    生成分析报告的快捷函数

    Args:
        symbol: 交易对
        interval: K线周期
        structure_data: 结构分析数据
        dynamics_data: 动力学分析数据
        sentiment_data: 市场情绪数据
        cross_market_data: 跨市场数据
        onchain_data: 链上数据
        decision_data: 决策数据

    Returns:
        报告结果
    """
    # 生成研报
    report_result = generate_report(
        symbol=symbol,
        interval=interval,
        structure_data=structure_data,
        dynamics_data=dynamics_data,
        sentiment_data=sentiment_data,
        cross_market_data=cross_market_data,
        onchain_data=onchain_data,
        decision_data=decision_data
    )

    # 记录决策
    if decision_data:
        analysis_results = {
            'structure_analysis': structure_data or {},
            'dynamics_analysis': dynamics_data or {},
            'sentiment_analysis': sentiment_data or {},
            'cross_market_analysis': cross_market_data or {},
            'onchain_analysis': onchain_data or {}
        }

        decision_record = record_decision(
            symbol=symbol,
            interval=interval,
            decision_data=decision_data,
            analysis_results=analysis_results
        )

        report_result['decision_id'] = decision_record.decision_id

    return report_result


def get_decision_stats(last_n: int = 50) -> Dict[str, Any]:
    """
    获取决策统计的快捷函数

    Args:
        last_n: 统计最近N条决策

    Returns:
        统计数据
    """
    return get_decision_statistics(last_n)
