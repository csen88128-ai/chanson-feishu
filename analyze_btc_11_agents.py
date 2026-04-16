"""
11智能体完整分析脚本
包含所有11个专业智能体
"""
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, '/workspace/chanson-feishu/src')


async def run_11_agents_analysis():
    """运行11个智能体完整分析"""
    print("\n" + "=" * 80)
    print("  🚀 缠论多智能体系统 - 11智能体完整分析")
    print("  📊 K线数量: 500根（1h+1d）")
    print("  🤖 智能体数量: 11个")
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

    # 获取1h级别数据
    if '1h' in formatted['levels']:
        level_1h = formatted['levels']['1h']
        level_1d = formatted['levels'].get('1d', {})

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
            'ma60': level_1h['indicators']['ma60'],
            'boll_upper': level_1h['indicators'].get('boll_upper', 0),
            'boll_mid': level_1h['indicators'].get('boll_mid', 0),
            'boll_lower': level_1h['indicators'].get('boll_lower', 0),
            'atr': level_1h['indicators'].get('atr', 0)
        }

        # 1d级别数据
        btc_data_1d = {
            'current_price': level_1d.get('price', {}).get('current', 0),
            'change_percent': level_1d.get('price', {}).get('change_percent', 0),
            'rsi': level_1d.get('indicators', {}).get('rsi', 0),
            'macd': level_1d.get('indicators', {}).get('macd', 0),
            'ma5': level_1d.get('indicators', {}).get('ma5', 0),
            'ma20': level_1d.get('indicators', {}).get('ma20', 0),
            'ma60': level_1d.get('indicators', {}).get('ma60', 0)
        }

        # 导入服务
        from main import service, new_context

        # 11个智能体的分析请求
        payload = {
            "user_request": f"""【11智能体完整分析 - BTCUSDT】

【数据概况】
- 交易对: BTCUSDT
- 总K线数: {formatted['total_klines']}根（专业级）
- 1h级别: {formatted['levels']['1h']['klines_count']}根
- 1d级别: {level_1d.get('klines_count', 0)}根
- 更新时间: {formatted['update_time']}

【1h级别数据】
- 当前价格: ${btc_data['current_price']}
- 涨跌幅: {btc_data['change_percent']}%
- 最高价: ${btc_data['high_24h']}
- 最低价: ${btc_data['low_24h']}
- RSI: {btc_data['rsi']}
- MACD: {btc_data['macd']}
- MA5: ${btc_data['ma5']}
- MA20: ${btc_data['ma20']}
- MA60: ${btc_data['ma60']}
- 布林带: 上${btc_data['boll_upper']} 中${btc_data['boll_mid']} 下${btc_data['boll_lower']}
- ATR: {btc_data['atr']}

【1d级别数据】
- 当前价格: ${btc_data_1d['current_price']}
- 涨跌幅: {btc_data_1d['change_percent']}%
- RSI: {btc_data_1d['rsi']}
- MACD: {btc_data_1d['macd']}
- MA5: ${btc_data_1d['ma5']}
- MA20: ${btc_data_1d['ma20']}
- MA60: ${btc_data_1d['ma60']}

【多级别信号】
- 整体趋势: {signals['overall_trend']}
- 多级共振: {'是' if signals['resonance'] else '否'}

【11个智能体分析任务】
请按照以下11个智能体进行完整分析，每个智能体给出专业结论：

【智能体1 - 缠论结构分析】
分析笔、线段、中枢的完整结构，识别各级别的结构特征和演化趋势

【智能体2 - 缠论动力学分析】
分析背驰、力度、动能变化，判断趋势的延续或反转

【智能体3 - 三类买卖点识别】
识别当前是否存在第一、第二、第三类买卖点，并给出明确判断

【智能体4 - 市场情绪分析】
基于RSI、MACD等指标分析市场情绪（恐惧/贪婪/中性）

【智能体5 - 风险评估】
评估当前交易风险，给出风险等级和主要风险点

【智能体6 - 交易策略】
根据上述分析，制定详细的交易策略（入场、出场、仓位、止盈止损）

【智能体7 - 资金管理】
制定资金管理方案（仓位分配、风险控制、复利策略）

【智能体8 - 心态管理】
提供交易心态建议（耐心、纪律、风险意识）

【智能体9 - 市场周期分析】
分析市场当前所处的周期阶段（积累、突破、拉升、出货）

【智能体10 - 综合评价】
对整体市场进行全面评价，给出综合得分和评级

【智能体11 - 决策整合】
整合所有智能体的分析结果，给出最终决策和操作建议

【输出要求】
请以专业研报格式输出，每个智能体给出独立的分析结果和结论，最后给出统一的决策建议。
""",
            "symbol": "BTCUSDT",
            "interval": "1h",
            "messages": [],
            "btc_data": btc_data,
            "btc_data_1d": btc_data_1d,
            "multi_level_data": formatted,
            "signals": signals
        }

        print("🤖 启动11智能体完整分析...")
        print("-" * 80)
        start_time = time.time()

        ctx = new_context(method="11_agents_analysis")

        try:
            result = await service.run(payload, ctx)
            elapsed = time.time() - start_time

            print(f"\n✅ 分析完成（耗时: {elapsed:.2f}秒）")
            print("=" * 80)
            print("📝 11智能体完整分析报告")
            print("=" * 80 + "\n")

            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                print(f"{last_message.content}\n")

                # 保存报告
                report_file = f"/workspace/chanson-feishu/BTC_11_AGENTS_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write("# BTC 11智能体完整分析报告\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**K线数量**: {formatted['total_klines']}根\n")
                    f.write(f"**智能体数量**: 11个\n")
                    f.write(f"**分析耗时**: {elapsed:.2f}秒\n")
                    f.write(f"**整体趋势**: {signals['overall_trend']}\n")
                    f.write(f"**多级共振**: {'是' if signals['resonance'] else '否'}\n\n")
                    f.write("---\n\n")
                    f.write(last_message.content)

                print(f"📄 报告已保存: {report_file}\n")

                # 保存为默认文件
                with open('/workspace/chanson_feishu/BTC_11_AGENTS_ANALYSIS.md', 'w', encoding='utf-8') as f:
                    f.write(last_message.content)

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
    asyncio.run(run_11_agents_analysis())


if __name__ == "__main__":
    main()
