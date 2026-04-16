"""
缠论多智能体系统 - 使用本地数据运行完整协作分析
使用已获取的BTC真实数据进行完整的多智能体协作分析
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


async def run_full_analysis_with_local_data():
    """使用本地数据运行完整的多智能体协作分析"""
    print_header("缠论多智能体系统 - 完整协作分析（使用本地BTC数据）")

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
    print(f"   RSI: {btc_data['rsi']:.2f} ({'超卖' if btc_data['rsi'] < 30 else '正常'})")
    print(f"   MACD: {btc_data['macd']:.2f} ({'死叉' if btc_data['macd'] < btc_data['macd_signal'] else '金叉'})")
    print(f"   数据来源: {btc_data['data_source']}")
    print(f"   数据时间: {btc_data['data_time']}")
    print()

    print("🤖 多智能体协作框架：")
    print("   1. 数据采集智能体 - 使用本地缓存数据")
    print("   2. 结构分析智能体 - 基于价格和均线分析")
    print("   3. 动力学分析智能体 - 基于RSI/MACD分析")
    print("   4. 市场情绪智能体 - 分析市场情绪")
    print("   5. 系统监控智能体 - 检查系统健康")
    print("   6. 模拟盘智能体 - 检查模拟盘绩效")
    print("   7. 首席决策智能体 - 综合决策")
    print(f"⏱️  预计耗时：约15-20秒\n")

    # 导入主服务
    from main import service, new_context

    # 准备输入 - 将BTC数据嵌入到用户请求中
    payload = {
        "user_request": f"""
请使用缠论多智能体系统对BTCUSDT进行完整的实时行情分析。

**已获取的BTC真实数据**：
- 交易对: {btc_data['symbol']}
- 当前价格: ${btc_data['current_price']:,.2f}
- 涨跌幅: {btc_data['change_percent']:.2f}%
- 成交量: {btc_data['volume']:,}
- 最高价: ${btc_data['high']:,.2f}
- 最低价: ${btc_data['low']:,.2f}
- 开盘价: ${btc_data['open']:,.2f}
- 收盘价: ${btc_data['close']:,.2f}

**技术指标**：
- MA5: ${btc_data['ma5']:,.2f}
- MA20: ${btc_data['ma20']:,.2f}
- MA60: ${btc_data['ma60']:,.2f}
- RSI: {btc_data['rsi']:.2f}
- MACD: {btc_data['macd']:.2f}
- MACD信号: {btc_data['macd_signal']:.2f}
- MACD柱: {btc_data['macd_hist']:.2f}

请基于以上数据，进行以下分析：
1. 缠论结构分析：分析笔/线段/中枢结构
2. 缠论动力学分析：分析背驰、力度
3. 识别三类买卖点
4. 市场情绪分析
5. 跨市场联动分析
6. 风险评估
7. 给出明确的交易决策建议（方向、关键点位、操作策略、风险等级）

请生成一份完整的分析研报。
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data  # 传递原始数据
    }

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 开始执行完整的多智能体协作分析...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 创建上下文
    ctx = new_context(method="full_multi_agent_analysis_local")

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
            report_file = "/workspace/chanson-feishu/BTC_MULTI_AGENT_FULL_REPORT.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 缠论多智能体系统 - BTC完整分析研报\n\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**执行耗时**: {duration:.2f}秒\n")
                f.write(f"**分析标的**: BTCUSDT\n\n")
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
    print("  缠论多智能体系统 - 完整协作分析（本地数据）")
    print("🚀" * 35 + "\n")

    import asyncio

    print("⚠️  即将使用已获取的BTC真实数据进行完整的多智能体协作分析")
    print("⏱️  预计耗时：约15-20秒\n")

    input("按回车键开始分析...")

    asyncio.run(run_full_analysis_with_local_data())


if __name__ == "__main__":
    main()
