"""
缠论多智能体系统 - 纯LLM推理分析（不调用外部工具）
使用已获取的BTC真实数据进行完整的缠论分析
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')
import json
from datetime import datetime


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def run_llm_only_analysis():
    """使用LLM推理进行完整分析（不调用外部工具）"""
    print_header("缠论多智能体系统 - 纯LLM推理完整分析")

    # 从刚才的分析中提取的BTC真实数据
    btc_data = {
        "symbol": "BTCUSDT",
        "current_price": 73608.08,
        "change_percent": -0.23,
        "volume": 4280353,
        "high": 73900.50,
        "low": 73250.00,
        "open": 73779.00,
        "close": 73608.08,
        "ma5": 74177.17,
        "ma20": 74666.07,
        "ma60": 74441.51,
        "rsi": 26.82,
        "macd": -284.62,
        "macd_signal": -250.45,
        "macd_hist": -34.17,
        "data_time": "2026-04-16 15:00:00",
        "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_source": "Huobi API"
    }

    print("📊 BTC真实数据（已缓存）：")
    print(f"   交易对: {btc_data['symbol']}")
    print(f"   当前价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌幅: {btc_data['change_percent']:.2f}%")
    print(f"   成交量: {btc_data['volume']:,}")
    print(f"   最高价: ${btc_data['high']:,.2f}")
    print(f"   最低价: ${btc_data['low']:,.2f}")
    print(f"   开盘价: ${btc_data['open']:,.2f}")
    print(f"   收盘价: ${btc_data['close']:,.2f}")
    print()
    print("📈 技术指标：")
    print(f"   MA5: ${btc_data['ma5']:,.2f}")
    print(f"   MA20: ${btc_data['ma20']:,.2f}")
    print(f"   MA60: ${btc_data['ma60']:,.2f}")
    print(f"   RSI: {btc_data['rsi']:.2f} ({'🟢超卖' if btc_data['rsi'] < 30 else '🔴超买' if btc_data['rsi'] > 70 else '⚪正常'})")
    print(f"   MACD: {btc_data['macd']:.2f} ({'🟢金叉' if btc_data['macd'] > btc_data['macd_signal'] else '🔴死叉'})")
    print(f"   MACD信号: {btc_data['macd_signal']:.2f}")
    print(f"   MACD柱: {btc_data['macd_hist']:.2f}")
    print()
    print(f"📅 数据来源: {btc_data['data_source']}")
    print(f"📅 数据时间: {btc_data['data_time']}")
    print(f"🕐 分析时间: {btc_data['analysis_time']}\n")

    print("🤖 多智能体协作任务：")
    print("   1. 缠论结构分析 - 分析笔/线段/中枢结构")
    print("   2. 缠论动力学分析 - 分析背驰、力度")
    print("   3. 识别三类买卖点")
    print("   4. 市场情绪分析")
    print("   5. 跨市场联动分析（基于通用市场逻辑）")
    print("   6. 风险评估")
    print("   7. 给出明确的交易决策建议")
    print(f"⏱️  预计耗时：约15-20秒\n")

    # 导入主服务
    from main import service, new_context

    # 准备输入 - 使用更明确的提示，避免调用外部工具
    payload = {
        "user_request": f"""# 缠论多智能体系统 - BTC完整分析任务

## 任务描述
请作为缠论多智能体分析系统的首席分析师，基于以下提供的BTC真实数据，进行完整的缠论分析。**注意：不要调用任何外部工具，所有分析请基于以下提供的数据和通用的缠论理论进行推理。**

## 已获取的BTC真实数据（来自Huobi API）

### 基础数据
- 交易对: {btc_data['symbol']}
- 当前价格: ${btc_data['current_price']:,.2f}
- 涨跌幅: {btc_data['change_percent']:.2f}%
- 成交量: {btc_data['volume']:,}
- 最高价: ${btc_data['high']:,.2f}
- 最低价: ${btc_data['low']:,.2f}
- 开盘价: ${btc_data['open']:,.2f}
- 收盘价: ${btc_data['close']:,.2f}

### 技术指标
- MA5: ${btc_data['ma5']:,.2f}
- MA20: ${btc_data['ma20']:,.2f}
- MA60: ${btc_data['ma60']:,.2f}
- RSI: {btc_data['rsi']:.2f}
- MACD: {btc_data['macd']:.2f}
- MACD信号: {btc_data['macd_signal']:.2f}
- MACD柱: {btc_data['macd_hist']:.2f}

### 数据信息
- 数据来源: {btc_data['data_source']}
- 数据时间: {btc_data['data_time']}
- 分析时间: {btc_data['analysis_time']}

## 分析要求

请按照以下结构进行完整分析：

### 1. 缠论结构分析
- 基于价格和均线数据，推断当前的价格结构
- 识别潜在的笔、线段、中枢
- 判断当前处于结构的哪个阶段

### 2. 缠论动力学分析
- 分析MACD指标，判断动能方向
- 分析RSI指标，判断超买超卖状态
- 判断是否存在背驰信号

### 3. 识别三类买卖点
- 根据缠论理论，识别当前可能出现的买卖点
- 判断是一类、二类还是三类买卖点

### 4. 市场情绪分析
- 结合RSI指标和涨跌幅，分析市场情绪
- 判断当前市场处于何种状态（恐惧、贪婪、中性）

### 5. 跨市场联动分析（基于通用市场逻辑）
- 基于成交量和技术指标，推测市场整体表现
- 分析可能的市场联动影响

### 6. 风险评估
- 评估当前操作的风险等级（1-5级）
- 识别主要风险点

### 7. 交易决策建议
- **方向判断**: 明确的看多/看空/中性判断
- **关键点位**: 支撑位、阻力位、止损位、目标位
- **操作策略**: 具体的操作建议（买入、卖出、观望）
- **风险控制**: 风险控制措施
- **预期收益**: 预期收益和风险比

## 输出格式

请以专业研报格式输出，包含以下部分：
1. 核心结论（Executive Summary）
2. 详细分析（结构、动力学、买卖点、情绪、联动、风险）
3. 交易决策建议（方向、点位、策略、风控）
4. 风险提示

**重要提醒**：
- 不要调用任何外部工具
- 基于提供的真实数据进行分析
- 严格遵守缠论理论体系
- 给出明确的、可执行的建议
- 标注不确定性（如果有）
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 开始执行完整的多智能体协作分析（纯LLM推理）...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 创建上下文
    ctx = new_context(method="llm_only_analysis")

    try:
        # 运行完整分析
        start_time = datetime.now()
        result = await service.run(payload, ctx)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ 多智能体协作分析完成！\n")

        print(f"⏱️  执行耗时: {duration:.2f}秒")
        print(f"🕐 完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 显示最终结论
        if "messages" in result and result["messages"]:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📝 最终分析研报：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

        # 保存研报到文件
        if "messages" in result and result["messages"]:
            report_content = result["messages"][-1].content
            report_file = "/workspace/chanson-feishu/BTC_MULTI_AGENT_LLM_REPORT.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 缠论多智能体系统 - BTC完整分析研报\n\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**执行耗时**: {duration:.2f}秒\n")
                f.write(f"**分析标的**: BTCUSDT\n")
                f.write(f"**数据来源**: {btc_data['data_source']}\n")
                f.write(f"**数据时间**: {btc_data['data_time']}\n")
                f.write(f"**分析模式**: 纯LLM推理（多智能体协作）\n\n")
                f.write("---\n\n")
                f.write(report_content)

            print(f"\n📄 研报已保存到: {report_file}")

        return result

    except Exception as e:
        print(f"\n❌ 多智能体协作分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - 纯LLM推理完整分析")
    print("🚀" * 35 + "\n")

    import asyncio

    print("⚠️  即将使用已获取的BTC真实数据进行完整的LLM推理分析")
    print("⏱️  预计耗时：约15-20秒\n")

    input("按回车键开始分析...")

    asyncio.run(run_llm_only_analysis())


if __name__ == "__main__":
    main()
