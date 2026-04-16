"""
使用最新BTC数据运行多智能体协作分析
基于刚获取的Huobi API实时数据
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


async def run_multi_agent_analysis():
    """运行多智能体协作分析"""
    print_header("缠论多智能体系统 - 完整协作分析（最新数据）")

    # 读取刚获取的最新数据
    with open('/workspace/chanson-feishu/btc_latest_realtime.json', 'r') as f:
        btc_data = json.load(f)

    print("📊 最新BTC数据（来自Huobi API）:")
    print(f"   当前价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌幅: {btc_data['change_percent']:.2f}%")
    print(f"   RSI: {btc_data['rsi']:.2f} ({'正常' if 30 <= btc_data['rsi'] <= 70 else '超卖' if btc_data['rsi'] < 30 else '超买'})")
    print(f"   MACD: {btc_data['macd']:.2f} ({'金叉' if btc_data['macd'] > 0 else '死叉'})")
    print(f"   MA5: ${btc_data['ma5']:,.2f}")
    print(f"   MA20: ${btc_data['ma20']:,.2f}")
    print(f"   数据时间: {btc_data['data_time']}")
    print()

    print("🤖 多智能体协作任务：")
    print("   1. 数据采集智能体 - 已完成")
    print("   2. 结构分析智能体 - 分析笔/线段/中枢结构")
    print("   3. 动力学分析智能体 - 分析背驰、力度")
    print("   4. 实战理论智能体 - 识别三类买卖点")
    print("   5. 市场情绪智能体 - 分析市场情绪")
    print("   6. 系统监控智能体 - 检查系统健康")
    print("   7. 模拟盘智能体 - 检查模拟盘绩效")
    print("   8. 首席决策智能体 - 综合决策")
    print("   9. 风控智能体 - 风险评估")
    print(f"⏱️  预计耗时：约15-20秒\n")

    # 导入主服务
    from main import service, new_context

    # 准备输入
    payload = {
        "user_request": f"""# 缠论多智能体系统 - BTC最新数据完整分析

## 最新数据（来自Huobi API）

### 基础数据
- 交易对: BTCUSDT
- 当前价格: ${btc_data['current_price']:,.2f}
- 涨跌幅: {btc_data['change_percent']:.2f}%
- 最高价: ${btc_data['high_24h']:,.2f}
- 最低价: ${btc_data['low_24h']:,.2f}
- 成交量: {btc_data['volume']:,}
- 数据时间: {btc_data['data_time']}

### 技术指标
- MA5: ${btc_data['ma5']:,.2f}
- MA20: ${btc_data['ma20']:,.2f}
- MA60: ${btc_data['ma60']:,.2f}
- RSI: {btc_data['rsi']:.2f}
- MACD: {btc_data['macd']:.2f}
- MACD DIF: {btc_data['macd_dif']:.2f}
- MACD DEA: {btc_data['macd_dea']:.2f}

## 分析要求

请基于以上最新数据，进行完整的缠论分析：

### 1. 缠论结构分析
- 分析笔/线段/中枢结构
- 判断当前处于结构的哪个阶段
- 识别支撑位和压力位

### 2. 缠论动力学分析
- 分析MACD背驰情况
- 分析RSI状态
- 判断动能方向

### 3. 识别三类买卖点
- 根据缠论理论，识别当前可能出现的买卖点
- 判断是一类、二类还是三类买卖点

### 4. 市场情绪分析
- 结合技术指标分析市场情绪
- 判断市场处于何种状态

### 5. 风险评估
- 评估当前操作的风险等级（1-5级）
- 识别主要风险点

### 6. 交易决策建议
- **方向判断**: 明确的看多/看空/中性判断
- **关键点位**: 支撑位、阻力位、止损位、目标位
- **操作策略**: 具体的操作建议（买入、卖出、观望）
- **风险控制**: 风险控制措施
- **预期收益**: 预期收益和风险比

## 输出要求

请以专业研报格式输出，包含：
1. 核心结论（Executive Summary）
2. 详细分析（结构、动力学、买卖点、情绪、风险）
3. 交易决策建议（方向、点位、策略、风控）
4. 风险提示

**重要**：
- 这是最新实时数据
- 给出明确的、可执行的建议
- 标注不确定性（如果有）
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 开始执行多智能体协作分析（最新数据）...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 创建上下文
    ctx = new_context(method="latest_data_multi_agent")

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
            print("📝 最新分析研报：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

        # 保存研报到文件
        if "messages" in result and result["messages"]:
            report_content = result["messages"][-1].content
            report_file = f"/workspace/chanson-feishu/BTC_MULTI_AGENT_REPORT_LATEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 缠论多智能体系统 - BTC最新分析研报\n\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**执行耗时**: {duration:.2f}秒\n")
                f.write(f"**分析标的**: BTCUSDT\n")
                f.write(f"**数据来源**: Huobi API\n")
                f.write(f"**数据时间**: {btc_data['data_time']}\n")
                f.write(f"**当前价格**: ${btc_data['current_price']:,.2f}\n")
                f.write(f"**分析模式**: 多智能体协作（LLM推理驱动）\n\n")
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
    print("  缠论多智能体系统 - 最新数据分析")
    print("🚀" * 35 + "\n")

    import asyncio

    print("⚠️  即将使用最新BTC数据运行多智能体协作分析")
    print("⏱️  预计耗时：约15-20秒\n")

    asyncio.run(run_multi_agent_analysis())


if __name__ == "__main__":
    main()
