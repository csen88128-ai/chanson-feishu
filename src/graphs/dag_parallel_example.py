"""
DAG并行化工作流实现示例
演示如何使用LangGraph实现并行执行和进度监控
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from operator import add


# ========== 1. 定义状态 ==========

class WorkflowState(TypedDict):
    """工作流状态"""
    messages: Annotated[List[BaseMessage], add]
    user_request: str
    symbol: str
    interval: str

    # 分析结果
    sentiment_result: Dict[str, Any]
    cross_market_result: Dict[str, Any]
    onchain_result: Dict[str, Any]

    # 进度跟踪
    execution_progress: Dict[str, Dict[str, Any]]
    start_time: datetime
    current_node: str


# ========== 2. 进度监控系统 ==========

class ProgressMonitor:
    """实时进度监控器"""

    def __init__(self):
        self.progress: Dict[str, Dict[str, Any]] = {}
        self.listeners: List[callable] = []

    def start_node(self, node_id: str):
        """节点开始执行"""
        self.progress[node_id] = {
            "status": "running",
            "start_time": datetime.now(),
            "progress": 0,
            "logs": []
        }
        self._notify(f"节点 {node_id} 开始执行")

    def update_progress(self, node_id: str, progress: float, message: str = ""):
        """更新节点进度"""
        if node_id in self.progress:
            self.progress[node_id]["progress"] = progress
            if message:
                self.progress[node_id]["logs"].append({
                    "time": datetime.now(),
                    "message": message
                })
            self._notify(f"节点 {node_id} 进度: {progress}% - {message}")

    def complete_node(self, node_id: str, result: Any = None):
        """节点完成"""
        if node_id in self.progress:
            self.progress[node_id]["status"] = "completed"
            self.progress[node_id]["end_time"] = datetime.now()
            self.progress[node_id]["progress"] = 100
            duration = (self.progress[node_id]["end_time"] -
                       self.progress[node_id]["start_time"]).total_seconds()
            self._notify(f"节点 {node_id} 完成，耗时 {duration:.2f}秒")
            return duration
        return 0

    def fail_node(self, node_id: str, error: str):
        """节点失败"""
        if node_id in self.progress:
            self.progress[node_id]["status"] = "failed"
            self.progress[node_id]["error"] = error
            self._notify(f"节点 {node_id} 失败: {error}")

    def get_overall_progress(self) -> Dict[str, Any]:
        """获取整体进度"""
        if not self.progress:
            return {"total": 0, "completed": 0, "running": 0, "failed": 0, "percentage": 0}

        total = len(self.progress)
        completed = sum(1 for p in self.progress.values() if p["status"] == "completed")
        running = sum(1 for p in self.progress.values() if p["status"] == "running")
        failed = sum(1 for p in self.progress.values() if p["status"] == "failed")

        return {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "percentage": (completed / total * 100) if total > 0 else 0
        }

    def _notify(self, message: str):
        """通知监听器"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        for listener in self.listeners:
            listener(message)


# 全局进度监控器实例
progress_monitor = ProgressMonitor()


# ========== 3. 并行任务执行器 ==========

async def execute_sentiment_analysis(state: WorkflowState) -> Dict[str, Any]:
    """并行执行：市场情绪分析"""
    node_id = "sentiment_analyzer"
    progress_monitor.start_node(node_id)

    try:
        progress_monitor.update_progress(node_id, 20, "获取市场情绪数据")
        await asyncio.sleep(0.5)  # 模拟网络请求

        progress_monitor.update_progress(node_id, 60, "分析情绪指标")
        await asyncio.sleep(1.0)  # 模拟分析过程

        progress_monitor.update_progress(node_id, 80, "生成情绪评分")
        await asyncio.sleep(0.5)  # 模拟评分计算

        result = {
            "sentiment": "bullish",
            "score": 0.75,
            "timestamp": datetime.now().isoformat()
        }

        progress_monitor.complete_node(node_id)
        return result

    except Exception as e:
        progress_monitor.fail_node(node_id, str(e))
        raise


async def execute_cross_market_analysis(state: WorkflowState) -> Dict[str, Any]:
    """并行执行：跨市场联动分析"""
    node_id = "cross_market_analyzer"
    progress_monitor.start_node(node_id)

    try:
        progress_monitor.update_progress(node_id, 25, "获取跨市场数据")
        await asyncio.sleep(0.5)

        progress_monitor.update_progress(node_id, 50, "分析市场联动性")
        await asyncio.sleep(1.0)

        progress_monitor.update_progress(node_id, 75, "计算相关性系数")
        await asyncio.sleep(0.5)

        result = {
            "correlation": 0.65,
            "trend": "同步上涨",
            "timestamp": datetime.now().isoformat()
        }

        progress_monitor.complete_node(node_id)
        return result

    except Exception as e:
        progress_monitor.fail_node(node_id, str(e))
        raise


async def execute_onchain_analysis(state: WorkflowState) -> Dict[str, Any]:
    """并行执行：链上数据分析"""
    node_id = "onchain_analyzer"
    progress_monitor.start_node(node_id)

    try:
        progress_monitor.update_progress(node_id, 30, "获取链上数据")
        await asyncio.sleep(0.5)

        progress_monitor.update_progress(node_id, 60, "分析资金流向")
        await asyncio.sleep(1.0)

        progress_monitor.update_progress(node_id, 90, "计算链上指标")
        await asyncio.sleep(0.5)

        result = {
            "net_flow": "inflow",
            "flow_amount": 12500000,
            "timestamp": datetime.now().isoformat()
        }

        progress_monitor.complete_node(node_id)
        return result

    except Exception as e:
        progress_monitor.fail_node(node_id, str(e))
        raise


# ========== 4. 并行执行节点 ==========

async def node_parallel_analysis(state: WorkflowState) -> WorkflowState:
    """并行执行所有辅助维度分析"""
    print("\n" + "="*60)
    print("🚀 开始并行执行辅助维度分析...")
    print("="*60)

    # 使用 asyncio.gather 并行执行多个异步任务
    results = await asyncio.gather(
        execute_sentiment_analysis(state),
        execute_cross_market_analysis(state),
        execute_onchain_analysis(state),
        return_exceptions=True  # 即使某个任务失败，其他任务继续执行
    )

    # 处理结果
    sentiment_result, cross_market_result, onchain_result = results

    # 检查是否有失败的任务
    if isinstance(sentiment_result, Exception):
        sentiment_result = {"error": str(sentiment_result)}
    if isinstance(cross_market_result, Exception):
        cross_market_result = {"error": str(cross_market_result)}
    if isinstance(onchain_result, Exception):
        onchain_result = {"error": str(onchain_result)}

    # 更新状态
    state["sentiment_result"] = sentiment_result
    state["cross_market_result"] = cross_market_result
    state["onchain_result"] = onchain_result

    # 打印并行执行总结
    print("\n" + "="*60)
    print("✅ 并行执行完成！")
    print(f"   - 市场情绪: {'成功' if 'error' not in sentiment_result else '失败'}")
    print(f"   - 跨市场:   {'成功' if 'error' not in cross_market_result else '失败'}")
    print(f"   - 链上数据: {'成功' if 'error' not in onchain_result else '失败'}")
    print("="*60 + "\n")

    return state


# ========== 5. 构建并行工作流 ==========

def build_parallel_workflow():
    """构建支持并行执行的工作流"""

    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("parallel_analysis", node_parallel_analysis)

    # 设置入口和出口
    workflow.set_entry_point("parallel_analysis")
    workflow.add_edge("parallel_analysis", END)

    return workflow.compile()


# ========== 6. 运行示例 ==========

async def run_parallel_analysis_demo():
    """运行并行分析演示"""

    print("\n" + "🎯"*60)
    print("  缠论多智能体系统 - DAG并行化演示")
    print("🎯"*60 + "\n")

    # 构建工作流
    workflow = build_parallel_workflow()

    # 初始化状态
    initial_state: WorkflowState = {
        "messages": [],
        "user_request": "市场分析",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "sentiment_result": {},
        "cross_market_result": {},
        "onchain_result": {},
        "execution_progress": {},
        "start_time": datetime.now(),
        "current_node": ""
    }

    # 添加进度监听器
    def progress_listener(message: str):
        pass  # 可以在这里实现WebSocket推送

    progress_monitor.listeners.append(progress_listener)

    # 运行工作流
    print("⏱️  开始计时...\n")
    start_time = datetime.now()

    result = await workflow.ainvoke(initial_state)

    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    # 打印最终结果
    print("\n" + "="*60)
    print("📊 执行结果汇总")
    print("="*60)
    print(f"✨ 总耗时: {total_time:.2f}秒")
    print(f"📈 节点状态: {progress_monitor.get_overall_progress()}")
    print("\n详细结果:")
    print(f"  - 市场情绪: {result['sentiment_result']}")
    print(f"  - 跨市场:   {result['cross_market_result']}")
    print(f"  - 链上数据: {result['onchain_result']}")
    print("="*60 + "\n")

    # 性能对比
    print("⚡ 性能对比:")
    print("  - 串行执行: ~9秒 (3秒 + 3秒 + 3秒)")
    print(f"  - 并行执行: {total_time:.2f}秒")
    print(f"  - 性能提升: {(9/total_time):.2f}x")
    print(f"  - 时间节省: {((9-total_time)/9)*100:.1f}%")
    print()


# ========== 7. 任务分发器示例 ==========

class TaskDispatcher:
    """智能任务分发器"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.workers = []
        self.is_running = False

    async def start(self):
        """启动任务分发器"""
        self.is_running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        print(f"✅ 任务分发器已启动，工作节点数: {self.max_workers}")

    async def stop(self):
        """停止任务分发器"""
        self.is_running = False
        for _ in self.workers:
            await self.task_queue.put(None)  # 发送停止信号
        await asyncio.gather(*self.workers, return_exceptions=True)
        print("✅ 任务分发器已停止")

    async def submit_task(self, task_name: str, task_func, *args, **kwargs):
        """提交任务到队列"""
        task = {
            "name": task_name,
            "func": task_func,
            "args": args,
            "kwargs": kwargs
        }
        await self.task_queue.put(task)
        print(f"📤 任务已提交: {task_name}")

    async def _worker(self, worker_id: int):
        """工作节点"""
        print(f"🔧 工作节点 {worker_id} 已就绪")
        while self.is_running:
            task = await self.task_queue.get()

            if task is None:  # 停止信号
                break

            try:
                task_name = task["name"]
                task_func = task["func"]
                task_args = task["args"]
                task_kwargs = task["kwargs"]

                print(f"🚀 [工作节点 {worker_id}] 执行任务: {task_name}")
                result = await task_func(*task_args, **task_kwargs)
                print(f"✅ [工作节点 {worker_id}] 任务完成: {task_name}")

            except Exception as e:
                print(f"❌ [工作节点 {worker_id}] 任务失败: {task_name}, 错误: {e}")
            finally:
                self.task_queue.task_done()


# ========== 8. 演示任务分发器 ==========

async def demo_task_dispatcher():
    """演示任务分发器"""

    print("\n" + "🎯"*60)
    print("  任务分发器演示")
    print("🎯"*60 + "\n")

    dispatcher = TaskDispatcher(max_workers=3)
    await dispatcher.start()

    # 提交多个任务
    await dispatcher.submit_task("情绪分析", execute_sentiment_analysis, {})
    await dispatcher.submit_task("跨市场分析", execute_cross_market_analysis, {})
    await dispatcher.submit_task("链上分析", execute_onchain_analysis, {})

    # 等待所有任务完成
    await dispatcher.task_queue.join()

    await dispatcher.stop()

    print("\n✅ 所有任务已完成\n")


# ========== 9. 主入口 ==========

async def main():
    """主函数"""

    # 演示1: 并行执行
    await run_parallel_analysis_demo()

    # 演示2: 任务分发器
    await demo_task_dispatcher()

    print("🎉 所有演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
