"""
多级别缠论多智能体分析脚本
使用500根K线（1h+4h+1d）进行专业分析
"""
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, '/workspace/chanson-feishu/src')


async def run_multi_level_analysis():
    """运行多级别分析"""
    print("\n" + "=" * 80)
    print("  🚀 缠论多智能体系统 - 多级别分析")
    print("  📊 K线数量: 500根（1h+1d）")
    print("=" * 80 + "\n")

    # 加载数据
    try:
        with open('/workspace/chanson-feishu/btc_multi_level_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ 数据文件不存在，请先运行数据获取脚本")
        return

    formatted = data['data']
    signals = data['signals']

    print("📊 数据概况")
    print("-" * 80)
    print(f"总K线数: {formatted['total_klines']}根")
    print(f"更新时间: {formatted['update_time']}\n")

    print("💰 各级别价格信息")
    print("-" * 80)

    for interval, level_data in formatted['levels'].items():
        price = level_data['price']
        ind = level_data['indicators']

        print(f"\n【{interval} 级别】")
        print(f"  📍 当前价格: ${price['current']:,.2f}")
        print(f"  📈 涨跌幅: {price['change_percent']:+.2f}%")
        print(f"  📊 K线数量: {level_data['klines_count']}根")
        print(f"  📅 数据跨度: {level_data['data_range']['start']} 至 {level_data['data_range']['end']}")

        print(f"\n  📈 技术指标:")
        ma5 = ind.get('ma5', 0)
        ma20 = ind.get('ma20', 0)
        ma60 = ind.get('ma60', 0)
        rsi = ind.get('rsi', 0)
        macd = ind.get('macd', 0)

        if ma5:
            print(f"     MA5:  ${ma5:,.2f}")
        if ma20:
            print(f"     MA20: ${ma20:,.2f}")
        if ma60:
            print(f"     MA60: ${ma60:,.2f}")
        if rsi:
            print(f"     RSI:  {rsi:.2f}")
        if macd:
            print(f"     MACD: {macd:.2f}")

    print("\n🎯 多级别信号分析")
    print("-" * 80)

    overall_trend = signals['overall_trend']
    resonance = signals['resonance']

    print(f"\n整体趋势: {overall_trend}")
    print(f"多级共振: {'✅ 是' if resonance else '❌ 否'}")

    if resonance:
        print(f"共振强度: {signals['strength']}/{len(signals['level_signals'])}")

    print(f"\n各级别详细信号:")
    for interval, level_signal in signals['level_signals'].items():
        print(f"\n  {interval} 级别:")
        print(f"     趋势: {level_signal['trend']}")
        print(f"     RSI:  {level_signal['rsi_signal']}")
        print(f"     MACD: {level_signal['macd_signal']}")

    # 获取1h级别数据用于多智能体分析
    if '1h' in formatted['levels']:
        level_1h = formatted['levels']['1h']
        btc_data = {
            'current_price': level_1h['price']['current'],
            'change_percent': level_1h['price']['change_percent'],
            'high_24h': level_1h['price']['high'],
            'low_24h': level_1h['price']['low'],
            'volume': level_1h['price'].get('volume', 0),
            'data_time': level_1h['data_range']['end'],
            'rsi': level_1h['indicators']['rsi'],
            'macd': level_1h['indicators']['macd'],
            'macd_dif': level_1h['indicators']['macd_dif'],
            'macd_dea': level_1h['indicators']['macd_dea'],
            'ma5': level_1h['indicators']['ma5'],
            'ma20': level_1h['indicators']['ma20'],
            'ma60': level_1h['indicators']['ma60']
        }

        # 导入服务
        from main import service, new_context

        # 准备输入（使用1h数据）
        payload = {
            "user_request": f"""基于多级别数据（500根K线）对BTCUSDT进行完整缠论分析。

【多级别数据概况】
- 总K线数: {formatted['total_klines']}根
- 1h级别: {formatted['levels']['1h']['klines_count']}根
- 1d级别: {formatted['levels'].get('1d', {}).get('klines_count', 0)}根

【1h级别数据】
- 交易对: BTCUSDT
- 当前价格: ${btc_data['current_price']}
- 涨跌幅: {btc_data['change_percent']}%
- 最高价: ${btc_data['high_24h']}
- 最低价: ${btc_data['low_24h']}
- 数据跨度: {formatted['levels']['1h']['data_range']['start']} 至 {formatted['levels']['1h']['data_range']['end']}
- K线数量: {formatted['levels']['1h']['klines_count']}根

【1h技术指标】
- MA5: ${btc_data['ma5']}
- MA20: ${btc_data['ma20']}
- MA60: ${btc_data['ma60']}
- RSI: {btc_data['rsi']}
- MACD: {btc_data['macd']}
- MACD DIF: {btc_data['macd_dif']}
- MACD DEA: {btc_data['macd_dea']}

【多级别信号】
- 整体趋势: {overall_trend}
- 多级共振: {'是' if resonance else '否'}

【分析要求】
基于500根K线的多级别数据，进行以下深度分析：
1. 多级别缠论结构分析（笔/线段/中枢）
2. 多级别缠论动力学分析（背驰、力度）
3. 多级别三类买卖点识别
4. 多级别市场情绪分析
5. 多级别风险评估
6. 多级别共振交易策略
7. 综合决策整合

请以专业研报格式输出，给出明确的、可执行的建议。
""",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "messages": [],
            "btc_data": btc_data,
            "multi_level_data": formatted
        }

        print("\n🤖 启动多智能体分析...")
        print("-" * 80)
        start_time = time.time()

        ctx = new_context(method="multi_level_analysis")

        try:
            result = await service.run(payload, ctx)
            elapsed = time.time() - start_time

            print(f"\n✅ 分析完成（耗时: {elapsed:.2f}秒）")
            print("=" * 80)
            print("📝 分析报告")
            print("=" * 80 + "\n")

            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                print(f"{last_message.content}\n")

                # 保存报告
                report_file = f"/workspace/chanson-feishu/BTC_MULTI_LEVEL_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write("# BTC多级别缠论分析报告\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**K线数量**: {formatted['total_klines']}根\n")
                    f.write(f"**分析耗时**: {elapsed:.2f}秒\n")
                    f.write(f"**整体趋势**: {overall_trend}\n")
                    f.write(f"**多级共振**: {'是' if resonance else '否'}\n\n")
                    f.write("---\n\n")
                    f.write(f"## 数据概况\n\n")
                    f.write(f"- 总K线数: {formatted['total_klines']}根\n")

                    for interval, level_data in formatted['levels'].items():
                        price = level_data['price']
                        f.write(f"\n### {interval} 级别\n\n")
                        f.write(f"- 当前价格: ${price['current']:,.2f}\n")
                        f.write(f"- 涨跌幅: {price['change_percent']:+.2f}%\n")
                        f.write(f"- K线数量: {level_data['klines_count']}根\n")

                    f.write("\n---\n\n")
                    f.write(last_message.content)

                print(f"📄 报告已保存: {report_file}\n")

            return result

        except Exception as e:
            print(f"\n❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    else:
        print("❌ 缺少1h级别数据")
        return None


def main():
    """主函数"""
    import asyncio
    asyncio.run(run_multi_level_analysis())


if __name__ == "__main__":
    main()
