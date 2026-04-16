"""
使用用户提供的最新BTC数据进行多智能体协作分析
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


async def run_analysis_with_user_data(user_data):
    """使用用户提供的最新数据运行多智能体协作分析"""
    print_header("缠论多智能体系统 - 使用最新BTC数据分析")

    # 解析用户数据
    btc_data = {
        "symbol": "BTCUSDT",
        "current_price": user_data['close'],
        "change_percent": user_data['change_percent'],
        "volume": user_data['volume'],
        "high": user_data['high'],
        "low": user_data['low'],
        "open": user_data['open'],
        "close": user_data['close'],
        "ma5": user_data['ma5'],
        "ma20": user_data['ma20'],
        "ma60": user_data['ma60'],
        "rsi": user_data['rsi'],
        "macd": user_data['macd'],
        "macd_signal": user_data['macd_signal'],
        "macd_hist": user_data['macd_hist'],
        "data_time": datetime.fromtimestamp(user_data['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_source": user_data['source']
    }

    print("📊 最新BTC数据（用户本地获取）：")
    print(f"   交易对: {btc_data['symbol']}")
    print(f"   当前价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌幅: {btc_data['change_percent']:.2f}%")
    print(f"   成交量: {btc_data['volume']:,.0f}")
    print(f"   最高价: ${btc_data['high']:,.2f}")
    print(f"   最低价: ${btc_data['low']:,.2f}")
    print(f"   开盘价: ${btc_data['open']:,.2f}")
    print(f"   收盘价: ${btc_data['close']:,.2f}")
    print()
    print("📈 技术指标：")
    print(f"   MA5: ${btc_data['ma5']:,.2f}")
    print(f"   MA20: ${btc_data['ma20']:,.2f}")
    print(f"   MA60: ${btc_data['ma60']:,.2f}")
    print(f"   RSI: {btc_data['rsi']:.2f} ({'🟢超卖' if btc_data['rsi'] < 30 else '🔴超买' if btc_data['rsi'] > 70 else '⚪正常'})")
    print(f"   MACD: {btc_data['macd']:.2f} ({'🟢金叉' if btc_data['macd'] > btc_data['macd_signal'] else '🔴死叉'})")
    print(f"   MACD信号: {btc_data['macd_signal']:.2f}")
    print(f"   MACD柱: {btc_data['macd_hist']:.2f}")
    print()
    print(f"📅 数据来源: {btc_data['data_source']}")
    print(f"📅 数据时间: {btc_data['data_time']}")
    print(f"🕐 分析时间: {btc_data['analysis_time']}")
    print(f"⏱️  数据延迟: {calculate_data_delay(btc_data['data_time'], btc_data['analysis_time'])}\n")

    print("🤖 多智能体协作任务：")
    print("   1. 缠论结构分析 - 分析笔/线段/中枢结构")
    print("   2. 缠论动力学分析 - 分析背驰、力度")
    print("   3. 识别三类买卖点")
    print("   4. 市场情绪分析")
    print("   5. 风险评估")
    print("   6. 给出明确的交易决策建议")
    print(f"⏱️  预计耗时：约15-20秒\n")

    # 导入主服务
    from main import service, new_context

    # 准备输入
    payload = {
        "user_request": f"""# 缠论多智能体系统 - BTC完整分析任务（最新数据）

## 任务描述
请作为缠论多智能体分析系统的首席分析师，基于以下提供的**最新BTC数据**，进行完整的缠论分析。**这是用户本地获取的最新数据，请重点分析最新的市场动态。**

## 最新BTC真实数据（来自{btc_data['data_source']}）

### 基础数据
- 交易对: {btc_data['symbol']}
- 当前价格: ${btc_data['current_price']:,.2f}
- 涨跌幅: {btc_data['change_percent']:.2f}%
- 成交量: {btc_data['volume']:,.0f}
- 最高价: ${btc_data['high']:,.2f}
- 最低价: ${btc_data['low']:,.2f}
- 开盘价: ${btc_data['open']:,.2f}
- 收盘价: ${btc_data['close']:,.2f}

### 技术指标
- MA5: ${btc_data['ma5']:,.2f}
- MA20: ${btc_data['ma20']:,.2f}
- MA60: ${btc_data['ma60']:,.2f}
- RSI: {btc_data['rsi']:.2f}
- MACD: {btc_data['macd']:.2f}
- MACD信号: {btc_data['macd_signal']:.2f}
- MACD柱: {btc_data['macd_hist']:.2f}

### 数据信息
- 数据来源: {btc_data['data_source']}
- 数据时间: {btc_data['data_time']}
- 分析时间: {btc_data['analysis_time']}
- **这是最新数据，请基于此进行实时分析**

## 分析要求

请按照以下结构进行完整分析：

### 1. 缠论结构分析
- 基于价格和均线数据，推断当前的价格结构
- 识别潜在的笔、线段、中枢
- 判断当前处于结构的哪个阶段
- **重点分析当前趋势状态**

### 2. 缠论动力学分析
- 分析MACD指标，判断动能方向
- 分析RSI指标，判断超买超卖状态
- 判断是否存在背驰信号
- **重点判断是否存在转折信号**

### 3. 识别三类买卖点
- 根据缠论理论，识别当前可能出现的买卖点
- 判断是一类、二类还是三类买卖点
- **给出明确的买卖点判断**

### 4. 市场情绪分析
- 结合RSI指标和涨跌幅，分析市场情绪
- 判断当前市场处于何种状态（恐惧、贪婪、中性）

### 5. 风险评估
- 评估当前操作的风险等级（1-5级）
- 识别主要风险点

### 6. 交易决策建议
- **方向判断**: 明确的看多/看空/中性判断
- **关键点位**: 支撑位、阻力位、止损位、目标位
- **操作策略**: 具体的操作建议（买入、卖出、观望）
- **风险控制**: 风险控制措施
- **预期收益**: 预期收益和风险比

## 输出格式

请以专业研报格式输出，包含以下部分：
1. 核心结论（Executive Summary）- **重点突出最新动态**
2. 详细分析（结构、动力学、买卖点、情绪、风险）
3. 交易决策建议（方向、点位、策略、风控）- **给出明确的、可执行的建议**
4. 风险提示

**重要提醒**：
- 这是**最新数据**，请重点关注最新市场动态
- 基于提供的真实数据进行分析
- 严格遵守缠论理论体系
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
    ctx = new_context(method="latest_data_analysis")

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
            report_file = f"/workspace/chanson-feishu/BTC_LATEST_ANALYSIS_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 缠论多智能体系统 - BTC最新分析研报\n\n")
                f.write(f"**生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**执行耗时**: {duration:.2f}秒\n")
                f.write(f"**分析标的**: BTCUSDT\n")
                f.write(f"**数据来源**: {btc_data['data_source']}\n")
                f.write(f"**数据时间**: {btc_data['data_time']}\n")
                f.write(f"**分析时间**: {btc_data['analysis_time']}\n")
                f.write(f"**数据延迟**: {calculate_data_delay(btc_data['data_time'], btc_data['analysis_time'])}\n")
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


def calculate_data_delay(data_time, analysis_time):
    """计算数据延迟"""
    dt_data = datetime.strptime(data_time, '%Y-%m-%d %H:%M:%S')
    dt_analysis = datetime.strptime(analysis_time, '%Y-%m-%d %H:%M:%S')
    delay_seconds = (dt_analysis - dt_data).total_seconds()
    
    if delay_seconds < 60:
        return f"{int(delay_seconds)}秒（实时）"
    elif delay_seconds < 3600:
        return f"{int(delay_seconds / 60)}分钟"
    elif delay_seconds < 86400:
        return f"{int(delay_seconds / 3600)}小时"
    else:
        return f"{int(delay_seconds / 86400)}天"


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体系统 - 最新数据分析")
    print("🚀" * 35 + "\n")

    # 检查是否有用户提供的最新数据文件
    import os
    data_file = "/workspace/chanson-feishu/btc_latest_data.json"

    if not os.path.exists(data_file):
        print("❌ 未找到最新数据文件！")
        print()
        print("请按照以下步骤操作：")
        print()
        print("1. 在您的本地电脑运行脚本获取最新数据：")
        print("   cd scripts")
        print("   python get_btc_latest_data_locally.py")
        print()
        print("2. 将生成的 btc_latest_data.json 文件上传到服务器：")
        print("   scp btc_latest_data.json user@server:/workspace/chanson-feishu/")
        print()
        print("3. 或者直接复制JSON数据粘贴到这里")
        print()
        return

    # 读取用户数据
    with open(data_file, 'r', encoding='utf-8') as f:
        user_data = json.load(f)

    print(f"✅ 成功读取最新数据文件: {data_file}")
    print(f"📅 数据来源: {user_data['source']}")
    print(f"📅 数据时间: {datetime.fromtimestamp(user_data['timestamp'] / 1000)}")
    print()

    import asyncio

    print("⚠️  即将使用最新BTC数据进行多智能体协作分析")
    print("⏱️  预计耗时：约15-20秒\n")

    input("按回车键开始分析...")

    asyncio.run(run_analysis_with_user_data(user_data))


if __name__ == "__main__":
    main()
