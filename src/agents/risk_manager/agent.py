"""
风控智能体
负责审核交易决策的风险，拥有一票否决权
"""

import os
import json
from typing import Any, Dict, Annotated
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver


@tool
def audit_trading_decision(decision_data: str, market_data: str,
                          account_balance: float = 100000) -> str:
    """
    审核交易决策，判断是否通过风控检查

    Args:
        decision_data: 交易决策数据（JSON字符串）
        market_data: 市场数据（JSON字符串）
        account_balance: 账户余额

    Returns:
        风控审核结果
    """
    try:
        from tools.risk_tools import get_risk_manager, calculate_risk_metrics

        # 解析决策数据
        decision = json.loads(decision_data)

        # 解析市场数据
        market = json.loads(market_data)

        # 获取风控管理器
        risk_manager = get_risk_manager()

        # 检查风险限制
        approved, reason = risk_manager.check_risk_limits(decision, account_balance)

        # 计算风险评分
        risk_score = risk_manager.calculate_risk_score(decision, market)

        # 生成风控报告
        report = []
        report.append("## 风控审核报告")
        report.append("")

        # 审核结果
        report.append("### 审核结果")
        if approved:
            report.append("✅ **通过风控检查**")
        else:
            report.append("❌ **未通过风控检查 - 一票否决**")
        report.append(f"- 原因: {reason}")
        report.append("")

        # 风险评分
        report.append("### 风险评分")
        report.append(f"- 风险评分: {risk_score}/100")

        if risk_score < 30:
            risk_level = "LOW - 低风险"
        elif risk_score < 60:
            risk_level = "MEDIUM - 中等风险"
        elif risk_score < 80:
            risk_level = "HIGH - 高风险"
        else:
            risk_level = "EXTREME - 极高风险"

        report.append(f"- 风险等级: {risk_level}")
        report.append("")

        # 决策参数检查
        report.append("### 决策参数检查")
        direction = decision.get("direction", "unknown")
        confidence = decision.get("confidence", 0)
        risk_level_decision = decision.get("risk_level", "medium")
        position_size = decision.get("position_size", 0)

        report.append(f"- 交易方向: {direction}")
        report.append(f"- 置信度: {confidence * 100}%")
        report.append(f"- 决策风险等级: {risk_level_decision.upper()}")
        report.append(f"- 建议仓位: {position_size * 100:.2f}%")
        report.append("")

        # 置信度检查
        report.append("### 置信度检查")
        if confidence >= 0.8:
            report.append("- ✅ 置信度高，符合交易要求")
        elif confidence >= 0.6:
            report.append("- ⚠️ 置信度中等，建议谨慎")
        else:
            report.append("- ❌ 置信度过低，拒绝交易")
        report.append("")

        # 风险等级检查
        report.append("### 风险等级检查")
        if risk_level_decision == "low":
            report.append("- ✅ 低风险信号，可以交易")
        elif risk_level_decision == "medium":
            report.append("- ⚠️ 中等风险信号，需要谨慎")
        else:
            report.append("- ❌ 高风险信号，建议观望")
        report.append("")

        # 市场环境检查
        report.append("### 市场环境检查")

        fear_greed_index = market.get("fear_greed_index", 50)
        if fear_greed_index < 20:
            sentiment = "极度恐慌"
            sentiment_advice = "市场恐慌，可能接近底部，但需谨慎"
        elif fear_greed_index < 45:
            sentiment = "恐惧"
            sentiment_advice = "市场情绪悲观，存在机会"
        elif fear_greed_index <= 55:
            sentiment = "中性"
            sentiment_advice = "市场情绪平稳"
        elif fear_greed_index < 80:
            sentiment = "贪婪"
            sentiment_advice = "市场情绪乐观，可能存在泡沫"
        else:
            sentiment = "极度贪婪"
            sentiment_advice = "市场过热，可能接近顶部"

        report.append(f"- 恐慌贪婪指数: {fear_greed_index} ({sentiment})")
        report.append(f"- 建议: {sentiment_advice}")
        report.append("")

        # 资金管理检查
        report.append("### 资金管理检查")

        if position_size <= 0.1:
            position_advice = "✅ 仓位较小，风险可控"
        elif position_size <= 0.2:
            position_advice = "⚠️ 仓位适中，注意风险"
        elif position_size <= 0.3:
            position_advice = "⚠️ 仓位较大，需严格控制止损"
        else:
            position_advice = "❌ 仓位过大，建议降低仓位"

        report.append(f"- 仓位占比: {position_size * 100:.2f}%")
        report.append(f"- 建议: {position_advice}")
        report.append("")

        # 风控状态
        report.append("### 风控状态")
        risk_report = risk_manager.get_risk_report()
        report.append(f"- 总盈亏: ${risk_report['total_pnl']:,.2f}")
        report.append(f"- 回撤: {risk_report['drawdown_pct']:.2f}%")
        report.append(f"- 连续亏损: {risk_report['consecutive_losses']}次")
        report.append(f"- 今日交易: {risk_report['trades_today']}次")
        report.append(f"- 冷却模式: {'是' if risk_report['cooling_mode'] else '否'}")
        report.append("")

        # 风控建议
        report.append("### 风控建议")

        suggestions = []

        if not approved:
            suggestions.append(f"❌ 拒绝本次交易: {reason}")
        else:
            suggestions.append("✅ 允许本次交易")

        if risk_score >= 60:
            suggestions.append("⚠️ 风险评分较高，建议降低仓位或等待更佳信号")

        if confidence < 0.7:
            suggestions.append("⚠️ 置信度较低，建议分批入场")

        if risk_report['consecutive_losses'] >= 2:
            suggestions.append("⚠️ 连续亏损，建议降低仓位或暂停交易")

        if risk_report['drawdown_pct'] > 0.1:
            suggestions.append("⚠️ 回撤较大，建议谨慎操作")

        if fear_greed_index < 20 or fear_greed_index > 80:
            suggestions.append("⚠️ 市场情绪极端，建议观望")

        if position_size > 0.2:
            suggestions.append("⚠️ 仓位较大，建议分批入场或降低仓位")

        for suggestion in suggestions:
            report.append(f"- {suggestion}")

        report.append("")

        # 止损建议
        if approved and "entry_price" in decision:
            report.append("### 止损建议")
            entry_price = decision.get("entry_price", 0)
            direction = decision.get("direction", "long")

            # 计算建议止损
            if direction == "long":
                stop_loss = entry_price * 0.97  # 3%止损
            else:
                stop_loss = entry_price * 1.03

            report.append(f"- 入场价格: ${entry_price:.2f}")
            report.append(f"- 建议止损: ${stop_loss:.2f}")
            report.append(f"- 止损幅度: 3%")
            report.append("")

        # 最终结论
        report.append("### 最终结论")
        if approved:
            report.append(f"**✅ 允许交易**")
            report.append(f"交易决策通过风控检查，可以执行。")
            report.append(f"但需严格执行止损纪律，控制风险。")
        else:
            report.append(f"**❌ 拒绝交易**")
            report.append(f"交易决策未通过风控检查，不能执行。")
            report.append(f"原因：{reason}")

        report.append("")

        return "\n".join(report)

    except Exception as e:
        return f"风控审核失败: {str(e)}"


@tool
def calculate_stop_loss(entry_price: float, direction: str, atr: float = 0,
                       support_level: float = 0, resistance_level: float = 0) -> str:
    """
    计算止损价格

    Args:
        entry_price: 入场价格
        direction: 方向 (long/short)
        atr: 平均真实波幅
        support_level: 支撑位
        resistance_level: 阻力位

    Returns:
        止损价格和建议
    """
    try:
        from tools.risk_tools import get_risk_manager

        risk_manager = get_risk_manager()

        stop_loss = risk_manager.calculate_stop_loss(
            entry_price, direction, atr, support_level, resistance_level
        )

        # 计算止损百分比
        if direction == "long":
            stop_loss_pct = (entry_price - stop_loss) / entry_price * 100
        else:
            stop_loss_pct = (stop_loss - entry_price) / entry_price * 100

        report = f"""
## 止损计算结果

**入场价格**: ${entry_price:.2f}
**方向**: {direction.upper()}
**止损价格**: ${stop_loss:.2f}
**止损幅度**: {stop_loss_pct:.2f}%

### 计算依据

"""
        if support_level > 0 and direction == "long":
            report += f"- 使用支撑位: ${support_level:.2f}\n"
            report += f"- 止损设置在支撑位下方0.2%\n"
        elif resistance_level > 0 and direction == "short":
            report += f"- 使用阻力位: ${resistance_level:.2f}\n"
            report += f"- 止损设置在阻力位上方0.2%\n"
        elif atr > 0:
            report += f"- 使用ATR: {atr:.2f}\n"
            report += f"- 止损设置在1.5倍ATR外\n"
        else:
            report += f"- 使用固定百分比: 3%\n"

        report += f"""
### 风险提示

- 止损是保护本金的重要手段，必须严格执行
- 不得随意调整止损位，除非向盈利方向移动
- 达到止损位必须立即离场，不得犹豫

### 建议

- 建议设置{stop_loss_pct:.2f}%的止损
- 可以考虑使用移动止损，保护利润
- 止损不应超过账户本金的2%
"""

        return report

    except Exception as e:
        return f"止损计算失败: {str(e)}"


@tool
def calculate_position_size(account_balance: float, entry_price: float,
                           stop_loss: float, confidence: float = 0.7) -> str:
    """
    计算仓位大小

    Args:
        account_balance: 账户余额
        entry_price: 入场价格
        stop_loss: 止损价格
        confidence: 置信度

    Returns:
        仓位大小分析
    """
    try:
        from tools.risk_tools import calculate_risk_metrics

        # 调用风险指标计算
        return calculate_risk_metrics(account_balance, entry_price, stop_loss, "long", confidence)

    except Exception as e:
        return f"仓位计算失败: {str(e)}"


LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建风控智能体

    Args:
        ctx: 请求上下文

    Returns:
        Agent实例
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

    system_prompt = """你是风控智能体，负责审核交易决策的风险，拥有一票否决权。

## 你的职责

1. **风控审核** - 对所有交易决策进行风险审核：
   - 检查置信度是否达到要求（>= 60%）
   - 检查风险等级是否可接受（非极高）
   - 检查仓位是否合理（<= 30%）
   - 检查市场环境是否适合交易
   - 检查账户状态（回撤、连续亏损、冷却模式）

2. **风险评分** - 为每个交易决策计算风险评分（0-100）：
   - 置信度评分：低置信度 = 高风险
   - 风险等级评分：高风险 = 高风险
   - 连续亏损评分：连续亏损越多 = 风险越高
   - 回撤评分：回撤越大 = 风险越高
   - 市场情绪评分：极端情绪 = 高风险

3. **否决权** - 当出现以下情况时，行使一票否决权：
   - 超过最大回撤限制（15%）
   - 连续亏损次数过多（5次）
   - 今日交易次数达到上限（10次）
   - 今日亏损超过限制（5%）
   - 置信度过低（< 50%）
   - 系统处于冷却模式

4. **风控建议** - 提供具体的风控建议：
   - 止损价格计算
   - 仓位大小建议
   - 分批入场/离场策略
   - 移动止损建议

## 风控原则

1. **本金保护第一** - 任何时候，保护本金比盈利更重要
2. **严格止损** - 止损是硬约束，不得随意调整
3. **仓位控制** - 单笔交易最大亏损不超过2%
4. **风险分散** - 不要把所有资金投入单一品种
5. **情绪控制** - 极端情绪下暂停交易
6. **纪律执行** - 风控规则必须严格执行，不得例外

## 审核流程

1. 检查系统状态（冷却模式、回撤、连续亏损）
2. 检查决策参数（置信度、风险等级、仓位）
3. 检查市场环境（恐慌贪婪指数、波动率）
4. 计算风险评分
5. 给出审核结果（通过/拒绝）
6. 提供风控建议

## 输出格式

按以下格式输出审核结果：

1. 审核结果：通过/拒绝（一票否决）
2. 风险评分：X/100
3. 风险等级：LOW/MEDIUM/HIGH/EXTREME
4. 决策参数检查：置信度、风险等级、仓位
5. 市场环境检查：恐慌贪婪指数、建议
6. 资金管理检查：仓位占比、建议
7. 风控状态：总盈亏、回撤、连续亏损
8. 风控建议：具体的操作建议
9. 止损建议：止损价格和止损幅度
10. 最终结论：允许/拒绝交易及理由

## 注意事项

- 风控拥有一票否决权，可以拒绝任何风险过高的交易
- 不要被高收益诱惑，风险控制永远是第一位
- 连续亏损后必须降低仓位或暂停交易
- 极端市场环境下要谨慎，建议观望
- 止损必须严格执行，不得抱有侥幸心理
"""

    tools = [
        audit_trading_decision,
        calculate_stop_loss,
        calculate_position_size
    ]

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
