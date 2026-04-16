"""
综合优化测试脚本
测试所有优化模块并验证效果
"""
import sys
import os
import json
import time
import asyncio
from datetime import datetime

sys.path.insert(0, '/workspace/chanson-feishu/src')

from utils.data_preloader import get_preloader, initialize_preload
from utils.data_validator import get_validator, get_monitor, validate_data, validate_and_fix_data
from utils.parallel_agents import run_chanson_parallel_analysis
from utils.optimized_prompts import get_optimized_prompt, PromptFactory


class OptimizationTester:
    """优化测试器"""
    
    def __init__(self):
        self.results = {}
    
    def test_data_preloader(self):
        """测试数据预加载"""
        print(f"\n{'='*70}")
        print("  📦 测试1: 数据预加载")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        # 初始化预加载
        preloader = get_preloader()
        results = asyncio.run(initialize_preload(['BTCUSDT']))
        
        elapsed = time.time() - start_time
        
        # 获取预加载数据
        btc_data = preloader.get('BTCUSDT')
        
        print(f"\n测试结果:")
        print(f"  预加载耗时: {elapsed:.2f}秒")
        print(f"  预加载成功: {results.get('BTCUSDT', False)}")
        print(f"  数据获取成功: {btc_data is not None}")
        
        if btc_data:
            print(f"  数据价格: ${btc_data.get('current_price', 0):,.2f}")
            print(f"  数据RSI: {btc_data.get('rsi', 0):.2f}")
        
        self.results['data_preloader'] = {
            'success': results.get('BTCUSDT', False),
            'time': elapsed,
            'data_available': btc_data is not None
        }
    
    def test_data_validator(self):
        """测试数据验证"""
        print(f"\n{'='*70}")
        print("  ✅ 测试2: 数据验证")
        print(f"{'='*70}\n")
        
        # 获取测试数据
        preloader = get_preloader()
        btc_data = preloader.get('BTCUSDT')
        
        if not btc_data:
            print("⚠️  无测试数据，跳过验证测试")
            self.results['data_validator'] = {'success': False}
            return
        
        # 测试验证
        result = validate_data(btc_data)
        
        print(f"\n验证结果:")
        print(f"  是否有效: {result.is_valid}")
        print(f"  质量分数: {result.score:.1f}")
        print(f"  错误数: {len(result.errors)}")
        print(f"  警告数: {len(result.warnings)}")
        
        if result.errors:
            print(f"  错误详情:")
            for error in result.errors:
                print(f"    - {error}")
        
        if result.warnings:
            print(f"  警告详情:")
            for warning in result.warnings:
                print(f"    - {warning}")
        
        # 测试修复
        print(f"\n测试数据修复:")
        broken_data = btc_data.copy()
        broken_data['rsi'] = None  # 故意破坏数据
        broken_data['ma5'] = 0
        
        fixed_data, fix_result = validate_and_fix_data(broken_data)
        
        print(f"  修复前分数: {result.score:.1f}")
        print(f"  修复后分数: {fix_result.score:.1f}")
        print(f"  修复成功: {fix_result.is_valid}")
        
        self.results['data_validator'] = {
            'success': result.is_valid,
            'score': result.score,
            'errors': len(result.errors),
            'warnings': len(result.warnings)
        }
    
    def test_parallel_agents(self):
        """测试并行智能体"""
        print(f"\n{'='*70}")
        print("  🤖 测试3: 并行智能体")
        print(f"{'='*70}\n")
        
        # 获取测试数据
        preloader = get_preloader()
        btc_data = preloader.get('BTCUSDT')
        
        if not btc_data:
            print("⚠️  无测试数据，跳过并行测试")
            self.results['parallel_agents'] = {'success': False}
            return
        
        start_time = time.time()
        
        # 运行并行分析
        results = asyncio.run(run_chanson_parallel_analysis(btc_data))
        
        elapsed = time.time() - start_time
        
        print(f"\n并行执行结果:")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  任务数: {len(results)}")
        print(f"  成功: {sum(1 for r in results.values() if r.success)}")
        
        # 计算加速比
        total_duration = sum(r.duration for r in results.values())
        speedup = total_duration / elapsed if elapsed > 0 else 0
        
        print(f"  任务总时长: {total_duration:.2f}秒")
        print(f"  加速比: {speedup:.2f}x")
        
        # 打印详情
        print(f"\n任务详情:")
        for name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"  {status} {name}: {result.duration:.2f}秒")
        
        self.results['parallel_agents'] = {
            'success': all(r.success for r in results.values()),
            'time': elapsed,
            'tasks': len(results),
            'speedup': speedup
        }
    
    def test_optimized_prompts(self):
        """测试优化的Prompt"""
        print(f"\n{'='*70}")
        print("  📝 测试4: 优化Prompt")
        print(f"{'='*70}\n")
        
        # 获取测试数据
        preloader = get_preloader()
        btc_data = preloader.get('BTCUSDT')
        
        if not btc_data:
            print("⚠️  无测试数据，跳过Prompt测试")
            self.results['optimized_prompts'] = {'success': False}
            return
        
        # 生成不同类型的Prompt
        prompts = {}
        
        # 标准分析Prompt
        prompts['standard'] = get_optimized_prompt(
            'analysis',
            price=btc_data['current_price'],
            rsi=btc_data['rsi'],
            macd=btc_data['macd'],
            ma5=btc_data['ma5'],
            ma20=btc_data['ma20'],
            ma60=btc_data['ma60'],
            mode='standard'
        )
        
        # 快速分析Prompt
        prompts['quick'] = get_optimized_prompt(
            'analysis',
            price=btc_data['current_price'],
            rsi=btc_data['rsi'],
            macd=btc_data['macd'],
            mode='quick'
        )
        
        # 情绪分析Prompt
        prompts['sentiment'] = get_optimized_prompt(
            'sentiment',
            rsi=btc_data['rsi'],
            change_percent=btc_data['change_percent']
        )
        
        print(f"\nPrompt生成结果:")
        for name, prompt in prompts.items():
            print(f"\n{name.upper()} Prompt:")
            print(f"  字数: {len(prompt)} 字符")
            print(f"  预览: {prompt[:100]}...")
        
        self.results['optimized_prompts'] = {
            'success': True,
            'standard_length': len(prompts['standard']),
            'quick_length': len(prompts['quick']),
            'reduction': (1 - len(prompts['quick']) / len(prompts['standard'])) * 100
        }
    
    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{'='*70}")
        print("  📊 优化测试摘要")
        print(f"{'='*70}\n")
        
        print(f"测试项数: {len(self.results)}")
        print(f"成功: {sum(1 for r in self.results.values() if r.get('success', False))}/{len(self.results)}\n")
        
        for test_name, result in self.results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"{status} {test_name}")
            
            if 'time' in result:
                print(f"    耗时: {result['time']:.2f}秒")
            if 'score' in result:
                print(f"    分数: {result['score']:.1f}")
            if 'speedup' in result:
                print(f"    加速比: {result['speedup']:.2f}x")
            if 'reduction' in result:
                print(f"    精简率: {result['reduction']:.1f}%")
        
        print(f"\n{'='*70}\n")
    
    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'='*70}")
        print("  🧪 开始综合优化测试")
        print(f"{'='*70}")
        
        # 运行测试
        self.test_data_preloader()
        self.test_data_validator()
        self.test_parallel_agents()
        self.test_optimized_prompts()
        
        # 打印摘要
        self.print_summary()
        
        return self.results


def main():
    """主函数"""
    tester = OptimizationTester()
    results = tester.run_all_tests()
    
    # 保存测试结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"/workspace/chanson-feishu/OPTIMIZATION_TEST_RESULT_{timestamp}.json"
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 测试结果已保存: {result_file}\n")


if __name__ == "__main__":
    main()
