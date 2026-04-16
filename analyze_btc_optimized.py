"""
优化版 - 带缓存和错误处理的多智能体分析
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any


class DataCache:
    """数据缓存管理"""
    def __init__(self, max_age: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_age = max_age  # 缓存有效期（秒）
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        data = self.cache.get(key)
        if data:
            age = time.time() - data['timestamp']
            if age < self.max_age:
                print(f"✅ 使用缓存数据（缓存时长: {age:.1f}秒）")
                return data['value']
            else:
                print(f"⚠️  缓存过期（{age:.1f}秒 > {self.max_age}秒）")
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """设置缓存数据"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        print(f"💾 数据已缓存")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        print("🗑️  缓存已清空")


class PerformanceMonitor:
    """性能监控"""
    def __init__(self):
        self.metrics = {
            'total_time': 0.0,
            'data_fetch_time': 0.0,
            'llm_time': 0.0,
            'tool_calls': 0,
            'tool_failures': 0
        }
        self.start_time = None
        self.llm_start = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
    
    def start_llm(self):
        """开始LLM计时"""
        self.llm_start = time.time()
    
    def end_llm(self):
        """结束LLM计时"""
        if self.llm_start:
            self.metrics['llm_time'] += time.time() - self.llm_start
            self.llm_start = None
    
    def record(self, metric: str, value: float):
        """记录指标"""
        self.metrics[metric] += value
    
    def end(self):
        """结束计时"""
        if self.start_time:
            self.metrics['total_time'] = time.time() - self.start_time
            self.start_time = None
    
    def report(self):
        """输出报告"""
        print("\n" + "=" * 70)
        print("  📊 性能报告")
        print("=" * 70)
        print(f"总耗时: {self.metrics['total_time']:.2f}秒")
        print(f"  - 数据获取: {self.metrics['data_fetch_time']:.2f}秒")
        print(f"  - LLM推理: {self.metrics['llm_time']:.2f}秒")
        print(f"  - 其他: {self.metrics['total_time'] - self.metrics['data_fetch_time'] - self.metrics['llm_time']:.2f}秒")
        print(f"\n工具调用:")
        print(f"  - 调用次数: {self.metrics['tool_calls']}")
        print(f"  - 失败次数: {self.metrics['tool_failures']}")
        if self.metrics['tool_calls'] > 0:
            success_rate = (self.metrics['tool_calls'] - self.metrics['tool_failures']) / self.metrics['tool_calls'] * 100
            print(f"  - 成功率: {success_rate:.1f}%")
        print("=" * 70 + "\n")


async def run_optimized_analysis():
    """运行优化版分析"""
    print("\n" + "=" * 70)
    print("  缠论多智能体系统 - 优化版分析")
    print("=" * 70 + "\n")
    
    # 初始化
    cache = DataCache(max_age=300)
    monitor = PerformanceMonitor()
    
    monitor.start()
    
    # 1. 数据获取阶段
    print("📡 第1步：获取BTC数据")
    print("-" * 70)
    
    data_start = time.time()
    
    # 尝试从缓存获取
    btc_data = cache.get("BTCUSDT")
    
    if not btc_data:
        # 缓存未命中，从文件读取
        print("📂 缓存未命中，从文件读取...")
        
        try:
            with open('/workspace/chanson-feishu/btc_latest_realtime_v2.json', 'r') as f:
                btc_data = json.load(f)
            
            # 更新缓存
            cache.set("BTCUSDT", btc_data)
            print(f"✅ 数据加载成功")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return None
    else:
        print(f"✅ 使用缓存数据")
    
    data_time = time.time() - data_start
    monitor.record('data_fetch_time', data_time)
    
    print(f"\n📊 数据信息:")
    print(f"   价格: ${btc_data['current_price']:,.2f}")
    print(f"   涨跌: {btc_data['change_percent']:.2f}%")
    print(f"   RSI: {btc_data['rsi']:.2f}")
    print(f"   MACD: {btc_data['macd']:.2f}")
    print(f"   数据时间: {btc_data['data_time']}")
    print(f"\n⏱️  数据获取耗时: {data_time:.2f}秒\n")
    
    # 2. 多智能体分析阶段
    print("🤖 第2步：多智能体协作分析")
    print("-" * 70)
    print("✅ 使用已有数据，跳过工具调用")
    print("✅ 直接进入LLM推理\n")
    
    # 导入服务
    from main import service, new_context
    
    # 准备输入（明确告知不调用工具）
    payload = {
        "user_request": f"""对BTCUSDT进行完整缠论分析。

【重要】请直接基于以下数据进行分析，不要调用任何外部工具获取数据。

数据信息：
- 交易对: BTCUSDT
- 当前价格: ${btc_data['current_price']}
- 涨跌幅: {btc_data['change_percent']}%
- 最高价: ${btc_data['high_24h']}
- 最低价: ${btc_data['low_24h']}
- 成交量: {btc_data['volume']}

技术指标：
- MA5: ${btc_data['ma5']}
- MA20: ${btc_data['ma20']}
- MA60: ${btc_data['ma60']}
- RSI: {btc_data['rsi']}
- MACD: {btc_data['macd']}
- MACD DIF: {btc_data['macd_dif']}
- MACD DEA: {btc_data['macd_dea']}

请进行以下分析：
1. 缠论结构分析（笔/线段/中枢）
2. 缠论动力学分析（背驰、力度）
3. 三类买卖点识别
4. 市场情绪分析
5. 风险评估
6. 交易决策建议（方向、点位、策略、风控）

请以专业研报格式输出，给出明确的、可执行的建议。
""",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "messages": [],
        "btc_data": btc_data
    }
    
    monitor.start_llm()
    
    ctx = new_context(method="optimized_analysis")
    
    try:
        result = await service.run(payload, ctx)
        monitor.end_llm()
        monitor.end()
        
        # 输出性能报告
        monitor.report()
        
        print("=" * 70)
        print("📝 分析报告")
        print("=" * 70 + "\n")
        
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            print(f"{last_message.content}\n")
            
            # 保存报告
            report_file = f"/workspace/chanson-feishu/BTC_OPTIMIZED_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            os.makedirs('/workspace/chanson-feishu', exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# BTC优化版分析报告\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**当前价格**: ${btc_data['current_price']}\n")
                f.write(f"**总耗时**: {monitor.metrics['total_time']:.2f}秒\n")
                f.write(f"**数据获取**: {monitor.metrics['data_fetch_time']:.2f}秒\n")
                f.write(f"**LLM推理**: {monitor.metrics['llm_time']:.2f}秒\n\n")
                f.write("---\n\n")
                f.write(last_message.content)
            
            print(f"📄 报告已保存: {report_file}\n")
        
        return result
        
    except Exception as e:
        monitor.end()
        print(f"\n❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    import asyncio
    asyncio.run(run_optimized_analysis())


if __name__ == "__main__":
    main()
