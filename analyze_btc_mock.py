"""
缠论多智能体系统 - BTC实时行情分析脚本（带模拟数据）
"""
import sys
import json
import asyncio
import random
from datetime import datetime, timedelta
import pandas as pd
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def generate_mock_btc_data(limit=100, base_price=65000):
    """生成模拟BTC数据"""
    data = []
    current_time = datetime.now() - timedelta(hours=limit)

    current_price = base_price

    for i in range(limit):
        # 模拟价格波动
        price_change = random.uniform(-0.005, 0.005)  # -0.5% 到 +0.5% 的波动
        current_price = current_price * (1 + price_change)

        # 生成OHLCV数据
        high = current_price * random.uniform(1.0, 1.002)
        low = current_price * random.uniform(0.998, 1.0)
        open_price = low + random.uniform(0, high - low)
        close = low + random.uniform(0, high - low)

        timestamp = int(current_time.timestamp() * 1000)
        close_time = timestamp + 3600000  # 1小时后

        data.append([
            timestamp,
            open_price,
            high,
            low,
            close,
            random.uniform(100, 1000),  # volume
            close_time,
            random.uniform(1000000, 10000000),  # quote_volume
            random.randint(1000, 10000),  # trades
            random.uniform(50, 500),  # taker_buy_base
            random.uniform(500000, 5000000),  # taker_buy_quote
            0
        ])

        current_time += timedelta(hours=1)

    return data


async def quick_btc_analysis(use_mock_data=True):
    """快速BTC分析 - 使用工具直接分析"""
    print_header("缠论多智能体系统 - BTC快速分析")

    # 导入工具
    from utils.chanlun_structure import ChanLunAnalyzer
    from utils.chanlun_dynamics import DynamicsAnalyzer

    symbol = "BTCUSDT"
    interval = "1h"

    print(f"🎯 分析标的: {symbol}")
    print(f"⏱️  分析周期: {interval}")
    print(f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if use_mock_data:
        print(f"⚠️  使用模拟数据（网络环境限制）")
    print()

    # 1. 获取K线数据
    print("📡 步骤1: 获取K线数据...")
    try:
        if use_mock_data:
            # 使用模拟数据
            klines = generate_mock_btc_data(limit=100, base_price=65000)
            print(f"  ✅ 使用模拟数据生成 {len(klines)} 根K线")
        else:
            # 尝试获取真实数据
            from tools.data_tools import BinanceDataCollector
            collector = BinanceDataCollector()
            klines = collector.get_klines(symbol, interval, limit=100)
            print(f"  ✅ 成功获取 {len(klines)} 根K线（真实数据）")

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
            price_change = (df.iloc[-1]['close'] / df.iloc[-2]['close'] - 1) * 100
            print(f"  💰 最新价格: ${latest_price:,.2f}")
            print(f"  📊 涨跌幅: {price_change:.2f}%\n")
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
        bis = analyzer.identify_bis(df)
        segments = analyzer.identify_segments(df, bis)

        print(f"  ✅ 识别出 {len(bis)} 笔")
        print(f"  ✅ 识别出 {len(segments)} 线段")

        # 显示最新的笔
        if len(bis) > 0:
            latest_bi = bis[-1]
            bi_type = "向上笔" if latest_bi.direction == 1 else "向下笔"
            print(f"  📍 最新笔: {bi_type}")
            print(f"     起点: ${latest_bi.start_price:,.2f}")
            print(f"     终点: ${latest_bi.end_price:,.2f}")
            print(f"     幅度: {abs(latest_bi.end_price - latest_bi.start_price) / latest_bi.start_price * 100:.2f}%")

        # 显示最新的线段
        if len(segments) > 0:
            latest_segment = segments[-1]
            seg_type = "向上线段" if latest_segment.direction == 1 else "向下线段"
            print(f"  📍 最新线段: {seg_type}")
            print(f"     包含 {len(latest_segment.bis)} 笔")
            print(f"     起点: ${latest_segment.start_price:,.2f}")
            print(f"     终点: ${latest_segment.end_price:,.2f}")
        print()
    except Exception as e:
        print(f"  ❌ 结构分析失败: {str(e)}\n")
        import traceback
        traceback.print_exc()

    # 3. 动力学分析
    print("⚡ 步骤3: 缠论动力学分析...")
    try:
        dynamics_analyzer = DynamicsAnalyzer()
        momentum_result = dynamics_analyzer.analyze_momentum(df)
        momentum = momentum_result.get('momentum', []) if momentum_result else []
        macd_signal = dynamics_analyzer.macd_divergence(df)

        if len(momentum) > 0:
            latest_momentum = momentum[-1]
            print(f"  ✅ 最新动量: {latest_momentum:.4f}")

            if abs(latest_momentum) > 0.02:
                trend = "强劲上涨" if latest_momentum > 0 else "强劲下跌"
                trend_icon = "📈" if latest_momentum > 0 else "📉"
                print(f"  {trend_icon} 趋势强度: {trend}")
            elif abs(latest_momentum) > 0.01:
                trend = "温和上涨" if latest_momentum > 0 else "温和下跌"
                trend_icon = "📊" if latest_momentum > 0 else "📊"
                print(f"  {trend_icon} 趋势强度: {trend}")
            else:
                print(f"  ➡️  趋势强度: 震荡整理")

        if macd_signal:
            print(f"  📉 MACD信号: {macd_signal}")
        print()
    except Exception as e:
        print(f"  ❌ 动力学分析失败: {str(e)}\n")
        import traceback
        traceback.print_exc()

    # 4. 综合分析结论
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📝 综合分析结论：\n")

    # 基于最新数据给出建议
    if len(df) > 0:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        price_change = (latest['close'] / prev['close'] - 1) * 100

        # 计算技术指标
        ma5 = df['close'].rolling(window=5).mean().iloc[-1]
        ma20 = df['close'].rolling(window=20).mean().iloc[-1]

        print("  📊 技术指标分析：")
        print(f"     MA5:  ${ma5:,.2f}")
        print(f"     MA20: ${ma20:,.2f}")

        if latest['close'] > ma5 and latest['close'] > ma20:
            print(f"     🟢 价格在均线上方 - 看多信号")
        elif latest['close'] < ma5 and latest['close'] < ma20:
            print(f"     🔴 价格在均线下方 - 看空信号")
        else:
            print(f"     🟡 价格在均线附近 - 观望")

        print()
        print("  📈 趋势分析：")

        if price_change > 1:
            print("     🟢 短期走势：强劲上涨")
            print("     💡 建议：关注上方阻力位，注意回调风险")
        elif price_change > 0:
            print("     🟡 短期走势：温和上涨")
            print("     💡 建议：保持关注，等待明确信号")
        elif price_change > -1:
            print("     🟠 短期走势：温和下跌")
            print("     💡 建议：谨慎观望，寻找支撑位")
        else:
            print("     🔴 短期走势：强劲下跌")
            print("     💡 建议：严格控制风险，避免追涨")

    print(f"\n  💰 当前价格: ${latest['close']:,.2f}")
    print(f"  📊 24h涨跌: {price_change:.2f}%")
    print(f"  📊 最高价: ${latest['high']:,.2f}")
    print(f"  📊 最低价: ${latest['low']:,.2f}")
    print(f"  📊 成交量: {latest['volume']:,.2f}")
    print(f"  🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if use_mock_data:
        print(f"\n  ⚠️  注：以上分析基于模拟数据，仅供演示")

    print()


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - BTC实时行情分析")
    print("🚀" * 35 + "\n")

    print("请选择分析模式：")
    print("  1. 快速分析（使用模拟数据，速度最快）")
    print("  2. 完整分析（使用多智能体系统，更全面）")
    print()

    choice = input("请输入选项 (1/2，默认1): ").strip() or "1"

    if choice == "1":
        # 快速分析
        asyncio.run(quick_btc_analysis(use_mock_data=True))
    elif choice == "2":
        # 完整分析
        print("⚠️  完整分析需要较长时间（约25秒），请耐心等待...\n")
        input("按回车键开始分析...")

        try:
            result = asyncio.run(full_btc_analysis())

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
