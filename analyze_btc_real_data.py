"""
使用之前成功获取的BTC真实数据运行多智能体协作分析
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


async def run_analysis():
    """使用真实BTC数据运行分析"""
    print_header("缠论多智能体系统 - 使用真实BTC数据")

    # 使用之前成功获取的真实数据
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

    print("📊 BTC真实数据（来自Huobi API）:")
    print(f"   当前价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌幅: {btc_data['change_percent']:.2f}%")
    print(f"   RSI: {btc_data['rsi']:.2f} ({'超卖' if btc_data['rsi'] < 30 else '正常'})")
    print(f"   MACD: {btc_data['macd']:.2f}")
    print(f"   数据来源: {btc_data['data_source']}")
    print()

    # 导入主服务
    from main import service, new_context

    # 准备输入
    payload = {
        "user_request": f"""请对BTCUSDT进行完整的缠论分析。

真实数据：
- 当前价格: ${btc_data['current_price']}
- RSI: {btc_data['rsi']}
- MACD: {btc_data['macd']}
- 涨跌幅: {btc_data['change_percent']}%

请进行结构分析、动力学分析、买卖点识别，并给出明确的交易决策建议。""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }

    print("🚀 开始多智能体协作分析...\n")

    ctx = new_context(method="real_data_analysis")

    try:
        start_time = datetime.now()
        result = await service.run(payload, ctx)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"✅ 分析完成！耗时: {duration:.2f}秒\n")

        if "messages" in result and result["messages"]:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📝 分析报告：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

            # 保存报告
            report_file = f"/workspace/chanson-feishu/BTC_REAL_TIME_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# BTC实时行情分析报告\n\n")
                f.write(f"**数据来源**: Huobi API\n")
                f.write(f"**当前价格**: ${btc_data['current_price']}\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
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
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  BTC真实数据多智能体协作分析")
    print("🚀" * 35 + "\n")

    import asyncio
    asyncio.run(run_analysis())


if __name__ == "__main__":
    main()
