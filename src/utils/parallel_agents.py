"""
异步智能体并行处理模块
实现多智能体的并行执行和结果整合
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass


@dataclass
class AgentTask:
    """智能体任务"""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class AgentResult:
    """智能体结果"""
    name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ParallelAgentExecutor:
    """并行智能体执行器"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化并行执行器
        
        Args:
            max_concurrent: 最大并发数
        """
        self.max_concurrent = max_concurrent
        self.results: Dict[str, AgentResult] = {}
    
    async def execute(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """
        并行执行多个智能体任务
        
        Args:
            tasks: 智能体任务列表
            
        Returns:
            执行结果字典 {agent_name: AgentResult}
        """
        print(f"\n{'='*70}")
        print(f"  🤖 开始并行执行智能体任务（{len(tasks)}个任务）")
        print(f"  最大并发数: {self.max_concurrent}")
        print(f"{'='*70}\n")
        
        self.results = {}
        start_time = time.time()
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 创建所有任务
        async_tasks = [
            self._execute_task(task, semaphore)
            for task in tasks
        ]
        
        # 等待所有任务完成
        await asyncio.gather(*async_tasks)
        
        elapsed = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in self.results.values() if r.success)
        total_duration = sum(r.duration for r in self.results.values())
        
        print(f"\n{'='*70}")
        print(f"  ✅ 所有任务执行完成")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  成功: {success_count}/{len(tasks)}")
        print(f"  任务总耗时: {total_duration:.2f}秒")
        print(f"  并行加速比: {total_duration / elapsed:.2f}x")
        print(f"{'='*70}\n")
        
        return self.results
    
    async def _execute_task(self, task: AgentTask, semaphore: asyncio.Semaphore):
        """
        执行单个任务
        
        Args:
            task: 智能体任务
            semaphore: 信号量
        """
        async with semaphore:
            print(f"🔄 执行任务: {task.name}")
            start_time = time.time()
            
            try:
                # 执行任务（带超时）
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
                
                duration = time.time() - start_time
                
                self.results[task.name] = AgentResult(
                    name=task.name,
                    success=True,
                    result=result,
                    duration=duration
                )
                
                print(f"  ✅ {task.name} 完成（{duration:.2f}秒）")
                
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                
                self.results[task.name] = AgentResult(
                    name=task.name,
                    success=False,
                    error=f"任务超时（{task.timeout}秒）",
                    duration=duration
                )
                
                print(f"  ⏰ {task.name} 超时（{duration:.2f}秒）")
                
            except Exception as e:
                duration = time.time() - start_time
                
                self.results[task.name] = AgentResult(
                    name=task.name,
                    success=False,
                    error=str(e),
                    duration=duration
                )
                
                print(f"  ❌ {task.name} 失败: {str(e)}（{duration:.2f}秒）")
    
    def get_results(self) -> Dict[str, AgentResult]:
        """获取所有结果"""
        return self.results
    
    def get_successful_results(self) -> Dict[str, AgentResult]:
        """获取成功的任务结果"""
        return {
            name: result
            for name, result in self.results.items()
            if result.success
        }
    
    def get_failed_results(self) -> Dict[str, AgentResult]:
        """获取失败的任务结果"""
        return {
            name: result
            for name, result in self.results.items()
            if not result.success
        }
    
    def print_results_summary(self):
        """打印结果摘要"""
        print(f"\n{'='*70}")
        print("  📊 任务执行摘要")
        print(f"{'='*70}\n")
        
        success_count = sum(1 for r in self.results.values() if r.success)
        total_count = len(self.results)
        
        print(f"总任务数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        
        if self.results:
            avg_duration = sum(r.duration for r in self.results.values()) / len(self.results)
            print(f"平均耗时: {avg_duration:.2f}秒")
        
        print(f"\n任务详情:")
        for name, result in self.results.items():
            status = "✅" if result.success else "❌"
            print(f"  {status} {name}: {result.duration:.2f}秒")
            if not result.success:
                print(f"      错误: {result.error}")
        
        print(f"{'='*70}\n")


# 全局执行器实例
_global_executor: Optional[ParallelAgentExecutor] = None


def get_executor() -> ParallelAgentExecutor:
    """
    获取全局执行器实例
    
    Returns:
        并行执行器实例
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = ParallelAgentExecutor(max_concurrent=5)
    return _global_executor


async def execute_parallel_agents(
    tasks: List[AgentTask],
    max_concurrent: int = 5
) -> Dict[str, AgentResult]:
    """
    并行执行多个智能体（便捷接口）
    
    Args:
        tasks: 智能体任务列表
        max_concurrent: 最大并发数
        
    Returns:
        执行结果字典
    """
    executor = get_executor()
    executor.max_concurrent = max_concurrent
    return await executor.execute(tasks)


def create_agent_task(
    name: str,
    func: Callable,
    *args,
    timeout: float = 30.0,
    **kwargs
) -> AgentTask:
    """
    创建智能体任务（便捷接口）
    
    Args:
        name: 任务名称
        func: 任务函数
        *args: 位置参数
        timeout: 超时时间（秒）
        **kwargs: 关键字参数
        
    Returns:
        智能体任务
    """
    return AgentTask(
        name=name,
        func=func,
        args=args,
        kwargs=kwargs,
        timeout=timeout
    )


# 示例：缠论分析智能体任务
async def analyze_structure_async(btc_data: Dict) -> str:
    """缠论结构分析（异步）"""
    # 模拟分析
    await asyncio.sleep(2)
    return "缠论结构分析结果"


async def analyze_dynamics_async(btc_data: Dict) -> str:
    """缠论动力学分析（异步）"""
    await asyncio.sleep(2)
    return "缠论动力学分析结果"


async def analyze_buy_sell_points_async(btc_data: Dict) -> str:
    """买卖点分析（异步）"""
    await asyncio.sleep(2)
    return "买卖点分析结果"


async def analyze_sentiment_async(btc_data: Dict) -> str:
    """市场情绪分析（异步）"""
    await asyncio.sleep(1)
    return "市场情绪分析结果"


async def analyze_risk_async(btc_data: Dict) -> str:
    """风险评估（异步）"""
    await asyncio.sleep(1)
    return "风险评估结果"


async def analyze_strategy_async(btc_data: Dict) -> str:
    """交易策略（异步）"""
    await asyncio.sleep(2)
    return "交易策略结果"


async def analyze_decision_async(btc_data: Dict) -> str:
    """决策整合（异步）"""
    await asyncio.sleep(2)
    return "决策整合结果"


async def run_chanson_parallel_analysis(btc_data: Dict) -> Dict[str, AgentResult]:
    """
    运行缠论并行分析
    
    Args:
        btc_data: BTC数据
        
    Returns:
        分析结果
    """
    # 创建所有智能体任务
    tasks = [
        create_agent_task("缠论结构分析", analyze_structure_async, btc_data),
        create_agent_task("缠论动力学分析", analyze_dynamics_async, btc_data),
        create_agent_task("买卖点分析", analyze_buy_sell_points_async, btc_data),
        create_agent_task("市场情绪分析", analyze_sentiment_async, btc_data),
        create_agent_task("风险评估", analyze_risk_async, btc_data),
        create_agent_task("交易策略", analyze_strategy_async, btc_data),
        create_agent_task("决策整合", analyze_decision_async, btc_data),
    ]
    
    # 并行执行
    results = await execute_parallel_agents(tasks, max_concurrent=7)
    
    return results
