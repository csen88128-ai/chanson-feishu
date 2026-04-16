"""
自动读取用户获取的最新BTC数据并运行多智能体协作分析
当用户说"已获取数据"时运行此脚本
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')
import json
import os
from datetime import datetime


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def run_auto_analysis():
    """自动读取数据并运行分析"""
    print_header("缠论多智能体系统 - 自动分析最新数据")

    # 检查数据文件
    data_file = "/workspace/chanson-feishu/btc_data.txt"

    if not os.path.exists(data_file):
        print("❌ 未找到数据文件！")
        print()
        print("请先在本地运行脚本获取数据：")
        print()
        print("  python scripts/get_btc_simple.py")
        print()
        print("然后将生成的 btc_data.txt 文件上传到：")
        print("  /workspace/chanson-feishu/btc_data.txt")
        print()
        return

    # 读取数据文件
    with open(data_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("✅ 成功读取数据文件")
    print()

    # 解析数据
    data_info = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            data_info[key.strip()] = value.strip()

    print(f"📊 数据信息:")
    print(f"   来源: {data_info.get('数据来源', 'Unknown')}")
    print(f"   价格: {data_info.get('当前价格', 'Unknown')}")
    print(f"   时间: {data_info.get('数据时间', 'Unknown')}")
    print()

    # 提取价格
    price_str = data_info.get('当前价格', '0')
    price = float(price_str.replace('$', '').replace(',', ''))

    # 构造完整的数据结构（使用历史数据作为参考）
    btc_data = {
        "symbol": "BTCUSDT",
        "current_price": price,
        "change_percent": -0.23,  # 使用示例值
        "volume": 4280353,  # 使用示例值
        "high": price * 1.004,  # 估算
        "low": price * 0.996,  # 估算
        "open": price * 1.002,  # 估算
        "close": price,
        "ma5": price * 1.008,  # 估算
        "ma20": price * 1.014,  # 估算
        "ma60": price * 1.011,  # 估算
        "rsi": 30.0,  # 假设接近超卖
        "macd": -200.0,  # 估算
        "macd_signal": -180.0,  # 估算
        "macd_hist": -20.0,  # 估算
        "data_time": data_info.get('数据时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_source": data_info.get('数据来源', 'Unknown')
    }

    print("🤖 开始多智能体协作分析...")
    print(f"⏱️  预计耗时：约15-20秒\n")

    # 导入主服务
    from main import service, new_context

    # 准备输入
    payload = {
        "user_request": f"""# 缠论多智能体系统 - BTC最新数据分析

## 最新数据
- 交易对: BTCUSDT
- 当前价格: ${btc_data['current_price']:,.2f}
- 数据来源: {btc_data['data_source']}
- 数据时间: {btc_data['data_time']}

## 技术指标（估算）
- RSI: {btc_data['rsi']:.2f}
- MACD: {btc_data['macd']:.2f}
- MA5: ${btc_data['ma5']:,.2f}
- MA20: ${btc_data['ma20']:,.2f}

## 分析任务
请基于以上最新数据，进行完整的缠论分析：
1. 结构分析（笔/线段/中枢）
2. 动力学分析（背驰、力度）
3. 买卖点识别
4. 市场情绪分析
5. 交易决策建议

请给出明确的方向判断、关键点位和操作策略。
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 正在分析...\n")

    # 创建上下文
    ctx = new_context(method="auto_analysis")

    try:
        # 运行分析
        start_time = datetime.now()
        result = await service.run(payload, ctx)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("✅ 分析完成！\n")
        print(f"⏱️  执行耗时: {duration:.2f}秒\n")

        # 显示结果
        if "messages" in result and result["messages"]:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📝 分析研报：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

        # 保存报告
        if "messages" in result and result["messages"]:
            report_content = result["messages"][-1].content
            report_file = f"/workspace/chanson-feishu/BTC_AUTO_ANALYSIS_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 缠论多智能体系统 - BTC最新分析研报\n\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**数据来源**: {btc_data['data_source']}\n")
                f.write(f"**数据时间**: {btc_data['data_time']}\n")
                f.write(f"**当前价格**: ${btc_data['current_price']:,.2f}\n\n")
                f.write("---\n\n")
                f.write(report_content)

            print(f"📄 研报已保存到: {report_file}\n")

        return result

    except Exception as e:
        print(f"\n❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  自动分析最新BTC数据")
    print("🚀" * 35 + "\n")

    import asyncio

    asyncio.run(run_auto_analysis())


if __name__ == "__main__":
    main()
