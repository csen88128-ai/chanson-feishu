"""
缠论多智能体系统 - 完整多智能体协作分析
使用12个智能体的完整工作流进行分析
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def run_full_multi_agent_analysis():
    """运行完整的多智能体协作分析"""
    print_header("缠论多智能体系统 - 完整多智能体协作分析")

    # 导入主服务
    from main import service, new_context

    print("🤖 使用12个智能体协作框架进行分析")
    print("📋 智能体列表：")
    agents = [
        "1. 数据采集智能体",
        "2. 结构分析智能体",
        "3. 动力学分析智能体",
        "4. 实战理论智能体",
        "5. 市场情绪智能体",
        "6. 跨市场联动智能体",
        "7. 链上数据智能体",
        "8. 系统监控智能体",
        "9. 模拟盘智能体",
        "10. 首席决策智能体",
        "11. 风控智能体",
        "12. 研报生成智能体"
    ]

    for agent in agents:
        print(f"   {agent}")

    print(f"\n⏱️  预计耗时：约25秒（串行执行）")
    print(f"🌐 使用数据源：多交易所API（Binance、Huobi、OKX、CoinGecko）")
    print(f"🎯 分析标的：BTCUSDT")
    print(f"⏰ 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 准备输入
    payload = {
        "user_request": "请使用缠论多智能体系统对BTCUSDT进行完整的实时行情分析，包括结构分析、动力学分析、市场情绪、跨市场联动、链上数据等多个维度的综合分析，并给出交易决策建议。",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": []
    }

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 开始执行完整的多智能体协作分析...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 创建上下文
    ctx = new_context(method="full_multi_agent_analysis")

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

        # 显示各个智能体的结果
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📊 各智能体分析结果：")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        analysis_keys = [
            ("data_quality", "1️⃣ 数据采集智能体"),
            ("structure_analysis", "2️⃣ 结构分析智能体"),
            ("dynamics_analysis", "3️⃣ 动力学分析智能体"),
            ("practical_theory_analysis", "4️⃣ 实战理论智能体"),
            ("sentiment_analysis", "5️⃣ 市场情绪智能体"),
            ("cross_market_analysis", "6️⃣ 跨市场联动智能体"),
            ("onchain_analysis", "7️⃣ 链上数据智能体"),
            ("system_health", "8️⃣ 系统监控智能体"),
            ("simulation_performance", "9️⃣ 模拟盘智能体"),
            ("trading_decision", "🔟 首席决策智能体"),
            ("risk_audit", "1️⃣1️⃣ 风控智能体"),
        ]

        for key, name in analysis_keys:
            if key in result and result[key]:
                print(f"【{name}】")
                if isinstance(result[key], dict):
                    if "agent_response" in result[key]:
                        response = result[key].get('agent_response', '')
                        # 限制显示长度
                        if len(str(response)) > 500:
                            response = str(response)[:500] + "..."
                        print(f"   {response}\n")
                    else:
                        print(f"   数据: {json.dumps(result[key], ensure_ascii=False, indent=2)[:300]}...\n")
                else:
                    print(f"   {result[key]}\n")

        # 显示最终结论
        if "messages" in result and result["messages"]:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📝 最终分析结论：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

        return result

    except Exception as e:
        print(f"\n❌ 多智能体协作分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def run_quick_multi_agent_analysis():
    """运行快速的多智能体分析（只使用关键智能体）"""
    print_header("缠论多智能体系统 - 快速多智能体分析（关键智能体）")

    from main import service, new_context

    print("🤖 使用关键智能体进行快速分析")
    print("📋 使用的智能体：")
    print("   1. 数据采集智能体")
    print("   2. 结构分析智能体")
    print("   3. 动力学分析智能体")
    print("   4. 首席决策智能体")
    print(f"\n⏱️  预计耗时：约10秒\n")

    # 准备输入
    payload = {
        "user_request": "请对BTCUSDT进行缠论结构分析、动力学分析，并给出交易决策建议。",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": []
    }

    print("🚀 开始快速分析...\n")

    ctx = new_context(method="quick_multi_agent_analysis")

    try:
        result = await service.run(payload, ctx)

        print("✅ 快速分析完成！\n")

        if "messages" in result and result["messages"]:
            print("📝 分析结论：\n")
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")

        return result

    except Exception as e:
        print(f"❌ 快速分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - 多智能体协作分析")
    print("🚀" * 35 + "\n")

    print("请选择分析模式：")
    print("  1. 完整多智能体协作（12个智能体，约25秒）")
    print("  2. 快速多智能体分析（4个关键智能体，约10秒）")
    print("  3. 简化版分析（单脚本，约3秒）")
    print()

    choice = input("请输入选项 (1/2/3，默认2): ").strip() or "2"

    if choice == "1":
        import asyncio
        print("\n⚠️  完整分析需要约25秒，请耐心等待...\n")
        input("按回车键开始分析...")
        asyncio.run(run_full_multi_agent_analysis())

    elif choice == "2":
        import asyncio
        asyncio.run(run_quick_multi_agent_analysis())

    elif choice == "3":
        print("\n运行简化版分析...\n")
        from analyze_btc_multi import main as simple_main
        simple_main()

    else:
        print("❌ 无效的选项")


if __name__ == "__main__":
    main()
