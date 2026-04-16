"""
多智能体协作分析 - 最新数据
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')
import json
from datetime import datetime


async def run_analysis():
    """运行分析"""
    print("\n" + "=" * 70)
    print("  缠论多智能体系统 - 最新数据协作分析")
    print("=" * 70 + "\n")

    # 读取最新数据
    with open('/workspace/chanson-feishu/btc_latest_realtime_v2.json', 'r') as f:
        btc_data = json.load(f)

    print("📊 最新数据:")
    print(f"   价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌: {btc_data['change_percent']:.2f}%")
    print(f"   RSI: {btc_data['rsi']:.2f}")
    print(f"   MACD: {btc_data['macd']:.2f}")
    print(f"   数据时间: {btc_data['data_time']}\n")

    # 导入服务
    from main import service, new_context

    # 准备输入
    payload = {
        "user_request": f"""对BTCUSDT进行完整缠论分析。

最新数据：
- 价格: ${btc_data['current_price']}
- 涨跌: {btc_data['change_percent']}%
- RSI: {btc_data['rsi']}
- MACD: {btc_data['macd']}
- MA5: ${btc_data['ma5']}
- MA20: ${btc_data['ma20']}

请分析结构、动力学、买卖点，给出明确建议。
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }

    print("🚀 开始分析...\n")

    ctx = new_context(method="latest_analysis_v2")

    try:
        start_time = datetime.now()
        result = await service.run(payload, ctx)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"✅ 分析完成！耗时: {duration:.2f}秒\n")

        if "messages" in result and result["messages"]:
            print("=" * 70)
            print("📝 分析报告:")
            print("=" * 70 + "\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

            # 保存报告
            report_file = f"/workspace/chanson-feishu/BTC_MULTI_AGENT_LATEST_V2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# BTC最新数据多智能体分析报告\n\n")
                f.write(f"**数据时间**: {btc_data['data_time']}\n")
                f.write(f"**当前价格**: ${btc_data['current_price']}\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**执行耗时**: {duration:.2f}秒\n\n")
                f.write("---\n\n")
                f.write(last_message.content)

            print(f"📄 报告已保存: {report_file}\n")

        return result

    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    import asyncio
    asyncio.run(run_analysis())


if __name__ == "__main__":
    main()
