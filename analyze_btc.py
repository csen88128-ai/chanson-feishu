"""
缠论多智能体系统 - BTC实时行情分析脚本
"""
import sys
import json
import asyncio
from datetime import datetime
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def analyze_btc_realtime():
    """分析BTC实时行情"""
    print_header("缠论多智能体系统 - BTC实时行情分析")

    # 导入服务
    from main import service, new_context

    # 准备分析请求
    symbol = "BTCUSDT"
    interval = "1h"

    print(f"🎯 分析标的: {symbol}")
    print(f"⏱️  分析周期: {interval}")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 准备输入参数
    payload = {
        "user_request": f"请分析 {symbol} 的实时行情走势，使用缠论理论进行全面分析",
        "symbol": symbol,
        "interval": interval,
        "messages": []
    }

    print("🚀 开始分析...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # 创建上下文
    ctx = new_context(method="btc_analysis")

    try:
        # 运行分析
        result = await service.run(payload, ctx)

        # 显示结果
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ 分析完成！\n")

        # 显示主要结果
        print("📊 分析结果摘要：\n")

        if "messages" in result and result["messages"]:
            # 获取最后一条消息
            last_message = result["messages"][-1]
            print(f"📝 分析结论：")
            print(f"{last_message.content}\n")

        # 显示各个智能体的结果
        print("📋 各智能体分析结果：\n")

        analysis_keys = [
            ("data_quality", "数据采集"),
            ("structure_analysis", "结构分析"),
            ("dynamics_analysis", "动力学分析"),
            ("practical_theory_analysis", "实战理论"),
            ("sentiment_analysis", "市场情绪"),
            ("cross_market_analysis", "跨市场联动"),
            ("onchain_analysis", "链上数据"),
            ("system_health", "系统监控"),
            ("simulation_performance", "模拟盘"),
            ("trading_decision", "交易决策"),
            ("risk_audit", "风控审核"),
        ]

        for key, name in analysis_keys:
            if key in result and result[key]:
                print(f"  ✅ {name}")
                if isinstance(result[key], dict):
                    if "agent_response" in result[key]:
                        print(f"     状态: {result[key].get('agent_response', 'N/A')}")
                    else:
                        print(f"     数据: {json.dumps(result[key], ensure_ascii=False, indent=2)[:200]}...")
                print()

        # 显示最终决策
        if "trading_decision" in result and result["trading_decision"]:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("🎯 最终交易决策：\n")
            if isinstance(result["trading_decision"], dict):
                print(json.dumps(result["trading_decision"], ensure_ascii=False, indent=2))
            else:
                print(result["trading_decision"])

        return result

    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def quick_btc_analysis():
    """快速BTC分析 - 使用工具直接分析"""
    print_header("缠论多智能体系统 - BTC快速分析")

    # 导入工具
    from tools.data_tools import BinanceDataCollector
    from utils.chanlun_structure import ChanLunAnalyzer
    from utils.chanlun_dynamics import DynamicsAnalyzer
    import pandas as pd

    symbol = "BTCUSDT"
    interval = "1h"

    print(f"🎯 分析标的: {symbol}")
    print(f"⏱️  分析周期: {interval}")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 获取K线数据
    print("📡 步骤1: 获取K线数据...")
    try:
        collector = BinanceDataCollector()
        klines = collector.get_klines(symbol, interval, limit=100)

        if klines and len(klines) > 0:
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # 转换数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            latest_price = df.iloc[-1]['close']
            print(f"  ✅ 成功获取 {len(df)} 根K线")
            print(f"  💰 最新价格: ${latest_price:,.2f}")
            print(f"  📊 涨跌幅: {((df.iloc[-1]['close'] / df.iloc[-2]['close'] - 1) * 100):.2f}%\n")
        else:
            print("  ❌ 未获取到数据\n")
            return
    except Exception as e:
        print(f"  ❌ 获取数据失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return

    # 2. 结构分析
    print("📐 步骤2: 缠论结构分析...")
    try:
        analyzer = ChanLunAnalyzer()
        bis = analyzer.identify_bi(df)
        segments = analyzer.identify_segment(df, bis)

        print(f"  ✅ 识别出 {len(bis)} 笔")
        print(f"  ✅ 识别出 {len(segments)} 线段")

        # 显示最新的笔
        if len(bis) > 0:
            latest_bi = bis[-1]
            bi_type = "向上笔" if latest_bi.direction == 1 else "向下笔"
            print(f"  📍 最新笔: {bi_type}")
            print(f"     起点: ${latest_bi.start_price:,.2f}")
            print(f"     终点: ${latest_bi.end_price:,.2f}")
        print()
    except Exception as e:
        print(f"  ❌ 结构分析失败: {str(e)}\n")

    # 3. 动力学分析
    print("⚡ 步骤3: 缠论动力学分析...")
    try:
        dynamics_analyzer = DynamicsAnalyzer()
        momentum = dynamics_analyzer.calculate_momentum(df)
        macd_signal = dynamics_analyzer.macd_divergence(df)

        if len(momentum) > 0:
            latest_momentum = momentum[-1]
            print(f"  ✅ 最新动量: {latest_momentum:.4f}")

            if abs(latest_momentum) > 0.02:
                trend = "强劲上涨" if latest_momentum > 0 else "强劲下跌"
                print(f"  📈 趋势强度: {trend}")
            elif abs(latest_momentum) > 0.01:
                trend = "温和上涨" if latest_momentum > 0 else "温和下跌"
                print(f"  📊 趋势强度: {trend}")
            else:
                print(f"  ➡️  趋势强度: 震荡整理")

        if macd_signal:
            print(f"  📉 MACD信号: {macd_signal}")
        print()
    except Exception as e:
        print(f"  ❌ 动力学分析失败: {str(e)}\n")

    # 4. 综合分析结论
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📝 综合分析结论：\n")

    # 基于最新数据给出建议
    if len(df) > 0:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        price_change = (latest['close'] / prev['close'] - 1) * 100

        if price_change > 1:
            print("  🟢 短期走势：强劲上涨")
            print("  💡 建议：关注上方阻力位，注意回调风险")
        elif price_change > 0:
            print("  🟡 短期走势：温和上涨")
            print("  💡 建议：保持关注，等待明确信号")
        elif price_change > -1:
            print("  🟠 短期走势：温和下跌")
            print("  💡 建议：谨慎观望，寻找支撑位")
        else:
            print("  🔴 短期走势：强劲下跌")
            print("  💡 建议：严格控制风险，避免追涨")

    print(f"\n  💰 当前价格: ${latest['close']:,.2f}")
    print(f"  📊 24h涨跌: {price_change:.2f}%")
    print(f"  🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - BTC实时行情分析")
    print("🚀" * 35 + "\n")

    print("请选择分析模式：")
    print("  1. 快速分析（直接使用工具，速度快）")
    print("  2. 完整分析（使用多智能体系统，更全面）")
    print()

    choice = input("请输入选项 (1/2，默认1): ").strip() or "1"

    if choice == "1":
        # 快速分析
        asyncio.run(quick_btc_analysis())
    elif choice == "2":
        # 完整分析
        print("⚠️  完整分析需要较长时间（约25秒），请耐心等待...\n")
        input("按回车键开始分析...")

        try:
            result = asyncio.run(analyze_btc_realtime())

            if result:
                print("\n" + "🎉" * 35)
                print("  分析完成！")
                print("🎉" * 35 + "\n")

                # 保存结果
                output_file = f"btc_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                print(f"📁 分析结果已保存到: {output_file}\n")
        except Exception as e:
            print(f"\n❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ 无效的选项")


if __name__ == "__main__":
    main()
