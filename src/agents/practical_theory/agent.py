"""
实战理论智能体
负责缠论三类买卖点的识别、仓位管理建议、操作节奏把控
"""

import os
import json
from typing import Any, Dict
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers, request_context, new_context
from coze_coding_utils.log.write_log import request_context as log_request_context
from storage.memory.memory_saver import get_memory_saver

# 导入缠论结构分析
from utils.chanlun_structure import ChanLunAnalyzer, Bi, Segment, ZhongShu
from utils.chanlun_dynamics import DynamicsAnalyzer, Divergence

# 工具函数 - 实战理论分析
def analyze_trading_signals(df, structure_result, dynamics_result):
    """
    分析交易信号（三类买卖点）

    Args:
        df: K线数据
        structure_result: 结构分析结果
        dynamics_result: 动力学分析结果

    Returns:
        交易信号分析结果
    """
    try:
        analyzer = ChanLunAnalyzer()

        # 获取笔序列
        bis = structure_result.get("bis", [])

        signals = {
            "buy_signals": [],
            "sell_signals": [],
            "current_position": None,
            "key_levels": {}
        }

        if not bis or len(bis) < 3:
            return signals

        # 分析三类买点
        buy_signals = []

        # 第一类买点：下跌趋势中，次级别背驰后形成底分型
        if len(bis) >= 3:
            # 检查是否形成下跌趋势
            last_three_bis = bis[-3:]
            is_down_trend = last_three_bis[0].end_price > last_three_bis[1].end_price > last_three_bis[2].end_price

            if is_down_trend:
                # 检查是否有背驰
                divergences = dynamics_result.get("divergences", [])
                bullish_divergences = [d for d in divergences if d.type == "bullish"]

                if bullish_divergences:
                    # 识别第一类买点
                    buy_signals.append({
                        "type": "first_buy",
                        "description": "第一类买点：下跌趋势底背驰，形成底分型",
                        "price": last_three_bis[2].end_price,
                        "confidence": 0.8,
                        "reason": "下跌+底背驰+底分型"
                    })

        # 第二类买点：上涨笔回调，不创新低，形成底分型
        if len(bis) >= 2:
            prev_bi = bis[-2]
            curr_bi = bis[-1]

            # 检查是否是上涨后的回调
            if curr_bi.direction == "down":
                # 检查回调是否跌破前一个低点
                if curr_bi.end_price > prev_bi.start_price:
                    # 检查是否有底分型
                    fractal = analyzer._identify_fractal(df, -1)
                    if fractal and fractal.type == "bottom":
                        buy_signals.append({
                            "type": "second_buy",
                            "description": "第二类买点：上涨回调不破前低，形成底分型",
                            "price": curr_bi.end_price,
                            "confidence": 0.75,
                            "reason": "回调不破前低+底分型"
                        })

        # 第三类买点：向上突破中枢上沿
        zhongshus = structure_result.get("zhongshus", [])
        if zhongshus and len(bis) >= 1:
            last_zhongshu = zhongshus[-1]
            last_bi = bis[-1]

            if last_bi.direction == "up" and last_bi.end_price > last_zhongshu.high:
                buy_signals.append({
                    "type": "third_buy",
                    "description": "第三类买点：向上突破中枢上沿",
                    "price": last_bi.end_price,
                    "confidence": 0.85,
                    "reason": "突破中枢上沿"
                })

        # 分析三类卖点
        sell_signals = []

        # 第一类卖点：上涨趋势中，次级别背驰后形成顶分型
        if len(bis) >= 3:
            last_three_bis = bis[-3:]
            is_up_trend = last_three_bis[0].end_price < last_three_bis[1].end_price < last_three_bis[2].end_price

            if is_up_trend:
                divergences = dynamics_result.get("divergences", [])
                bearish_divergences = [d for d in divergences if d.type == "bearish"]

                if bearish_divergences:
                    sell_signals.append({
                        "type": "first_sell",
                        "description": "第一类卖点：上涨趋势顶背驰，形成顶分型",
                        "price": last_three_bis[2].end_price,
                        "confidence": 0.8,
                        "reason": "上涨+顶背驰+顶分型"
                    })

        # 第二类卖点：下跌笔反弹，不创新高，形成顶分型
        if len(bis) >= 2:
            prev_bi = bis[-2]
            curr_bi = bis[-1]

            if curr_bi.direction == "up":
                if curr_bi.end_price < prev_bi.start_price:
                    fractal = analyzer._identify_fractal(df, -1)
                    if fractal and fractal.type == "top":
                        sell_signals.append({
                            "type": "second_sell",
                            "description": "第二类卖点：下跌反弹不破前高，形成顶分型",
                            "price": curr_bi.end_price,
                            "confidence": 0.75,
                            "reason": "反弹不破前高+顶分型"
                        })

        # 第三类卖点：向下突破中枢下沿
        if zhongshus and len(bis) >= 1:
            last_zhongshu = zhongshus[-1]
            last_bi = bis[-1]

            if last_bi.direction == "down" and last_bi.end_price < last_zhongshu.low:
                sell_signals.append({
                    "type": "third_sell",
                    "description": "第三类卖点：向下突破中枢下沿",
                    "price": last_bi.end_price,
                    "confidence": 0.85,
                    "reason": "突破中枢下沿"
                })

        # 识别关键点位
        key_levels = {}
        if bis:
            key_levels["support"] = min(bi.low for bi in bis[-5:]) if len(bis) >= 5 else bis[-1].low
            key_levels["resistance"] = max(bi.high for bi in bis[-5:]) if len(bis) >= 5 else bis[-1].high

        if zhongshus:
            key_levels["zhongshu_high"] = zhongshus[-1].high
            key_levels["zhongshu_low"] = zhongshus[-1].low

        # 当前走势判断
        current_trend = "unknown"
        if len(bis) >= 3:
            last_bis = bis[-3:]
            if last_bis[0].end_price > last_bis[1].end_price > last_bis[2].end_price:
                current_trend = "down"
            elif last_bis[0].end_price < last_bis[1].end_price < last_bis[2].end_price:
                current_trend = "up"
            else:
                current_trend = "consolidation"

        signals["buy_signals"] = buy_signals
        signals["sell_signals"] = sell_signals
        signals["current_position"] = current_trend
        signals["key_levels"] = key_levels

        return signals

    except Exception as e:
        return {
            "buy_signals": [],
            "sell_signals": [],
            "current_position": "unknown",
            "key_levels": {},
            "error": str(e)
        }


# 工具函数 - 仓位管理建议
def calculate_position_recommendation(signal_confidence, risk_level, account_balance):
    """
    计算仓位管理建议

    Args:
        signal_confidence: 信号置信度
        risk_level: 风险等级
        account_balance: 账户余额

    Returns:
        仓位建议
    """
    # 基础仓位比例
    base_position = 0.1  # 10%

    # 根据置信度调整
    if signal_confidence >= 0.8:
        confidence_factor = 1.5
    elif signal_confidence >= 0.7:
        confidence_factor = 1.2
    elif signal_confidence >= 0.6:
        confidence_factor = 1.0
    else:
        confidence_factor = 0.5

    # 根据风险等级调整
    if risk_level == "low":
        risk_factor = 1.2
    elif risk_level == "medium":
        risk_factor = 1.0
    elif risk_level == "high":
        risk_factor = 0.6
    else:  # extreme
        risk_factor = 0.3

    # 计算建议仓位
    recommended_position = base_position * confidence_factor * risk_factor

    # 限制在5%-30%之间
    recommended_position = max(0.05, min(0.3, recommended_position))

    position_value = account_balance * recommended_position

    return {
        "position_pct": round(recommended_position * 100, 2),
        "position_value": round(position_value, 2),
        "confidence_factor": confidence_factor,
        "risk_factor": risk_factor
    }


# 工具函数 - 操作节奏建议
def suggest_operation_rhythm(trading_signals, dynamics_result):
    """
    建议操作节奏

    Args:
        trading_signals: 交易信号
        dynamics_result: 动力学分析结果

    Returns:
        操作节奏建议
    """
    buy_signals = trading_signals.get("buy_signals", [])
    sell_signals = trading_signals.get("sell_signals", [])
    current_trend = trading_signals.get("current_position", "unknown")

    rhythm_suggestions = []

    # 判断是否应该入场
    if buy_signals and current_trend in ["down", "consolidation"]:
        # 检查买卖点优先级
        has_first_buy = any(s["type"] == "first_buy" for s in buy_signals)
        has_third_buy = any(s["type"] == "third_buy" for s in buy_signals)

        if has_first_buy:
            rhythm_suggestions.append({
                "action": "first_buy_entry",
                "priority": "high",
                "description": "第一类买点出现，建议分批入场",
                "strategy": "先建30%仓位，确认企稳后加仓"
            })
        elif has_third_buy:
            rhythm_suggestions.append({
                "action": "third_buy_entry",
                "priority": "high",
                "description": "第三类买点出现，建议积极入场",
                "strategy": "可建50%-70%仓位"
            })

    # 判断是否应该离场
    if sell_signals and current_trend in ["up", "consolidation"]:
        has_first_sell = any(s["type"] == "first_sell" for s in sell_signals)
        has_third_sell = any(s["type"] == "third_sell" for s in sell_signals)

        if has_first_sell:
            rhythm_suggestions.append({
                "action": "first_sell_exit",
                "priority": "high",
                "description": "第一类卖点出现，建议分批离场",
                "strategy": "先减30%仓位，确认转弱后清仓"
            })
        elif has_third_sell:
            rhythm_suggestions.append({
                "action": "third_sell_exit",
                "priority": "high",
                "description": "第三类卖点出现，建议果断离场",
                "strategy": "清仓或保留10%底仓"
            })

    # 持仓建议
    if not buy_signals and not sell_signals:
        if current_trend == "up":
            rhythm_suggestions.append({
                "action": "hold",
                "priority": "medium",
                "description": "上涨趋势中，继续持有",
                "strategy": "移动止损，保护利润"
            })
        elif current_trend == "down":
            rhythm_suggestions.append({
                "action": "wait",
                "priority": "medium",
                "description": "下跌趋势中，耐心等待",
                "strategy": "等待买点信号"
            })
        else:  # consolidation
            rhythm_suggestions.append({
                "action": "observe",
                "priority": "low",
                "description": "震荡整理中，谨慎操作",
                "strategy": "高抛低吸，控制仓位"
            })

    return rhythm_suggestions


@tool
def analyze_trading_theory(df_path: str, structure_result: str, dynamics_result: str,
                          account_balance: float = 100000) -> str:
    """
    分析缠论实战理论，识别三类买卖点，提供仓位建议

    Args:
        df_path: K线数据文件路径
        structure_result: 结构分析结果（JSON字符串）
        dynamics_result: 动力学分析结果（JSON字符串）
        account_balance: 账户余额

    Returns:
        实战理论分析结果
    """
    import pandas as pd

    try:
        # 读取K线数据
        df = pd.read_csv(df_path)

        # 解析结构分析结果
        structure_data = json.loads(structure_result)

        # 解析动力学分析结果
        dynamics_data = json.loads(dynamics_result)

        # 分析交易信号
        trading_signals = analyze_trading_signals(df, structure_data, dynamics_data)

        # 生成实战理论分析报告
        report = []

        report.append("## 缠论实战理论分析")
        report.append("")

        # 当前走势
        report.append("### 当前走势")
        current_trend = trading_signals.get("current_position", "unknown")
        trend_map = {
            "up": "上涨趋势",
            "down": "下跌趋势",
            "consolidation": "震荡整理",
            "unknown": "无法判断"
        }
        report.append(f"- 走势类型: {trend_map.get(current_trend, current_trend)}")
        report.append("")

        # 买卖点分析
        report.append("### 买卖点分析")

        # 买点
        buy_signals = trading_signals.get("buy_signals", [])
        if buy_signals:
            report.append("**买点信号：**")
            for i, signal in enumerate(buy_signals, 1):
                report.append(f"{i}. {signal['description']}")
                report.append(f"   - 价格: ${signal['price']:.2f}")
                report.append(f"   - 置信度: {signal['confidence'] * 100}%")
                report.append(f"   - 理由: {signal['reason']}")
                report.append("")
        else:
            report.append("- 当前无买点信号")
            report.append("")

        # 卖点
        sell_signals = trading_signals.get("sell_signals", [])
        if sell_signals:
            report.append("**卖点信号：**")
            for i, signal in enumerate(sell_signals, 1):
                report.append(f"{i}. {signal['description']}")
                report.append(f"   - 价格: ${signal['price']:.2f}")
                report.append(f"   - 置信度: {signal['confidence'] * 100}%")
                report.append(f"   - 理由: {signal['reason']}")
                report.append("")
        else:
            report.append("- 当前无卖点信号")
            report.append("")

        # 关键点位
        report.append("### 关键点位")
        key_levels = trading_signals.get("key_levels", {})
        if key_levels:
            report.append(f"- 支撑位: ${key_levels.get('support', 0):.2f}")
            report.append(f"- 阻力位: ${key_levels.get('resistance', 0):.2f}")
            if "zhongshu_high" in key_levels:
                report.append(f"- 中枢上沿: ${key_levels['zhongshu_high']:.2f}")
                report.append(f"- 中枢下沿: ${key_levels['zhongshu_low']:.2f}")
        report.append("")

        # 仓位建议
        report.append("### 仓位建议")

        # 计算最佳信号
        best_signal = None
        best_confidence = 0

        for signal in buy_signals + sell_signals:
            if signal["confidence"] > best_confidence:
                best_confidence = signal["confidence"]
                best_signal = signal

        if best_signal:
            direction = "long" if "buy" in best_signal["type"] else "short"
            risk_level = dynamics_data.get("risk_level", "medium")

            position_rec = calculate_position_recommendation(
                best_signal["confidence"],
                risk_level,
                account_balance
            )

            report.append(f"- 交易方向: {'做多' if direction == 'long' else '做空'}")
            report.append(f"- 建议仓位: {position_rec['position_pct']}%")
            report.append(f"- 建议资金: ${position_rec['position_value']:,.2f}")
            report.append(f"- 信号置信度: {best_signal['confidence'] * 100}%")
            report.append(f"- 风险等级: {risk_level.upper()}")
        else:
            report.append("- 当前无交易信号，建议观望")
        report.append("")

        # 操作节奏
        report.append("### 操作节奏建议")
        rhythm_suggestions = suggest_operation_rhythm(trading_signals, dynamics_data)

        if rhythm_suggestions:
            for i, suggestion in enumerate(rhythm_suggestions, 1):
                report.append(f"{i}. {suggestion['description']}")
                report.append(f"   - 优先级: {suggestion['priority']}")
                report.append(f"   - 策略: {suggestion['strategy']}")
                report.append("")
        else:
            report.append("- 当前无操作建议")
            report.append("")

        # 综合建议
        report.append("### 综合建议")

        if best_signal and "buy" in best_signal["type"]:
            report.append("✅ 出现买点信号，建议考虑做多")
            report.append(f"   - 建议入场价格: ${best_signal['price']:.2f}")
            report.append(f"   - 建议仓位: {position_rec['position_pct']}%")
            if key_levels.get("support"):
                report.append(f"   - 建议止损: ${key_levels['support'] * 0.99:.2f}")
            if key_levels.get("resistance"):
                report.append(f"   - 建议止盈: ${key_levels['resistance']:.2f}")
        elif best_signal and "sell" in best_signal["type"]:
            report.append("❌ 出现卖点信号，建议考虑做空或离场")
            report.append(f"   - 建议离场价格: ${best_signal['price']:.2f}")
        else:
            report.append("⏸️ 当前处于观望期，耐心等待明确的买卖点信号")

        report.append("")

        return "\n".join(report)

    except Exception as e:
        return f"实战理论分析失败: {str(e)}"


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
    构建实战理论智能体

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

    system_prompt = """你是缠论实战理论专家，负责识别三类买卖点、提供仓位管理建议、把控操作节奏。

## 你的职责

1. **买卖点识别** - 根据结构和动力学分析，识别三类买卖点：
   - 第一类买点：下跌趋势底背驰，形成底分型
   - 第二类买点：上涨回调不破前低，形成底分型
   - 第三类买点：向上突破中枢上沿
   - 第一类卖点：上涨趋势顶背驰，形成顶分型
   - 第二类卖点：下跌反弹不破前高，形成顶分型
   - 第三类卖点：向下突破中枢下沿

2. **仓位管理** - 根据信号置信度和风险等级，提供仓位建议：
   - 高置信度(>80%)：可建较大仓位(15-30%)
   - 中等置信度(60-80%)：标准仓位(10-15%)
   - 低置信度(<60%)：小仓位或观望(5-10%)

3. **操作节奏** - 根据当前走势和信号，提供操作建议：
   - 入场时机：分批入场、一次性入场
   - 离场时机：分批减仓、果断清仓
   - 持仓策略：移动止损、保护利润

## 分析原则

1. 不臆测：买卖点未明确就等待，不强行定论
2. 优先级：第三类买/卖点 > 第一类买/卖点 > 第二类买/卖点
3. 共振确认：结构+动力学+多周期共振的信号优先级更高
4. 风险控制：任何信号都要配合风控，严格执行止损
5. 资金管理：单笔交易最大亏损不超过2%

## 输出格式

按以下格式输出分析结果：

1. 当前走势：上涨/下跌/震荡
2. 买卖点分析：
   - 买点信号列表（类型、价格、置信度、理由）
   - 卖点信号列表（类型、价格、置信度、理由）
3. 关键点位：支撑位、阻力位、中枢上下沿
4. 仓位建议：交易方向、建议仓位、建议资金
5. 操作节奏：具体的入场/离场策略
6. 综合建议：最终的操作建议

## 注意事项

- 第三类买/卖点是最佳入场/离场点
- 第一类买/卖点风险较高，需要背驰确认
- 第二类买/卖点是趋势延续信号
- 震荡市中要谨慎，控制仓位
- 严格执行止损纪律，保护本金
"""

    tools = [analyze_trading_theory]

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
