"""
性能监控系统
实时监控，及时发现问题
"""
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import json
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器 - 基础版本"""

    def __init__(self):
        self.execution_times: Dict[str, List[float]] = {}
        self.success_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}
        self.accuracy_scores: Dict[str, List[float]] = {}
        self.error_messages: Dict[str, List[str]] = {}
        self.group_execution_times: List[Dict[str, Any]] = []

    def record_success(
        self,
        agent_name: str,
        duration: float,
        accuracy: Optional[float] = None
    ):
        """记录成功执行

        Args:
            agent_name: 智能体名称
            duration: 执行时间（秒）
            accuracy: 准确度评分（0-1）
        """
        if agent_name not in self.execution_times:
            self.execution_times[agent_name] = []
            self.success_counts[agent_name] = 0
            self.failure_counts[agent_name] = 0
            self.error_messages[agent_name] = []

        self.execution_times[agent_name].append(duration)
        self.success_counts[agent_name] += 1

        if accuracy is not None:
            if agent_name not in self.accuracy_scores:
                self.accuracy_scores[agent_name] = []
            self.accuracy_scores[agent_name].append(accuracy)

    def record_failure(
        self,
        agent_name: str,
        duration: float,
        error: str
    ):
        """记录失败执行

        Args:
            agent_name: 智能体名称
            duration: 执行时间（秒）
            error: 错误信息
        """
        if agent_name not in self.execution_times:
            self.execution_times[agent_name] = []
            self.success_counts[agent_name] = 0
            self.failure_counts[agent_name] = 0
            self.error_messages[agent_name] = []

        self.execution_times[agent_name].append(duration)
        self.failure_counts[agent_name] += 1
        self.error_messages[agent_name].append(error)

    def record_group_execution(
        self,
        group: List[str],
        group_idx: int,
        duration: float
    ):
        """记录组执行

        Args:
            group: 智能体组
            group_idx: 组索引
            duration: 执行时间（秒）
        """
        self.group_execution_times.append({
            'group_idx': group_idx,
            'agents': group,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体统计信息

        Args:
            agent_name: 智能体名称

        Returns:
            统计信息字典
        """
        if agent_name not in self.execution_times:
            return {}

        times = self.execution_times[agent_name]
        successes = self.success_counts.get(agent_name, 0)
        failures = self.failure_counts.get(agent_name, 0)
        accuracies = self.accuracy_scores.get(agent_name, [])

        stats = {
            'agent_name': agent_name,
            'total_executions': len(times),
            'successes': successes,
            'failures': failures,
            'success_rate': successes / (successes + failures) if (successes + failures) > 0 else 0,
            'avg_execution_time': sum(t for t in times if t is not None) / len(times) if times else 0,
            'min_execution_time': min(t for t in times if t is not None) if times else 0,
            'max_execution_time': max(t for t in times if t is not None) if times else 0,
            'std_execution_time': (sum((t - sum(times)/len(times))**2 for t in times if t is not None) / len(times))**0.5 if times else 0,
        }

        if accuracies:
            stats['avg_accuracy'] = sum(accuracies) / len(accuracies)
            stats['min_accuracy'] = min(accuracies)
            stats['max_accuracy'] = max(accuracies)

        if failures > 0:
            stats['recent_errors'] = self.error_messages[agent_name][-3:]  # 最近3个错误

        return stats

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息

        Returns:
            所有统计信息字典
        """
        all_stats = {
            'agents': {},
            'summary': {}
        }

        total_executions = 0
        total_success = 0
        total_failure = 0

        for agent_name in self.execution_times:
            stats = self.get_agent_stats(agent_name)
            all_stats['agents'][agent_name] = stats

            total_executions += stats['total_executions']
            total_success += stats['successes']
            total_failure += stats['failures']

        all_stats['summary'] = {
            'total_executions': total_executions,
            'total_success': total_success,
            'total_failure': total_failure,
            'overall_success_rate': total_success / total_executions if total_executions > 0 else 0,
            'total_groups_executed': len(self.group_execution_times),
            'total_time': sum(group['duration'] for group in self.group_execution_times)
        }

        return all_stats

    def print_stats(self):
        """打印统计信息"""
        stats = self.get_all_stats()

        print("\n" + "="*60)
        print("性能统计报告")
        print("="*60)

        # 摘要
        print("\n📊 总体统计:")
        summary = stats['summary']
        print(f"  总执行次数: {summary['total_executions']}")
        print(f"  成功次数: {summary['total_success']}")
        print(f"  失败次数: {summary['total_failure']}")
        print(f"  成功率: {summary['overall_success_rate']:.2%}")
        print(f"  执行组数: {summary['total_groups_executed']}")
        print(f"  总耗时: {summary['total_time']:.2f}s")

        # 智能体统计
        print("\n🤖 智能体统计:")
        for agent_name, agent_stats in stats['agents'].items():
            print(f"\n  {agent_name}:")
            print(f"    执行次数: {agent_stats['total_executions']}")
            print(f"    成功率: {agent_stats['success_rate']:.2%}")
            print(f"    平均执行时间: {agent_stats['avg_execution_time']:.2f}s")
            if 'avg_accuracy' in agent_stats:
                print(f"    平均准确度: {agent_stats['avg_accuracy']:.2%}")

        print("\n" + "="*60 + "\n")


class RealTimePerformanceMonitor:
    """实时性能监控器 - 系统级监控"""

    def __init__(self, interval: float = 1.0, history_size: int = 3600):
        """
        初始化实时性能监控器

        Args:
            interval: 监控间隔（秒）
            history_size: 历史数据保留数量
        """
        self.interval = interval
        self.history_size = history_size
        self.running = False
        self.thread = None

        # 性能数据存储
        self.cpu_history: deque = deque(maxlen=history_size)
        self.memory_history: deque = deque(maxlen=history_size)
        self.disk_history: deque = deque(maxlen=history_size)
        self.network_history: deque = deque(maxlen=history_size)

        # 警告阈值
        self.cpu_warning_threshold = 80.0  # CPU使用率警告阈值（%）
        self.memory_warning_threshold = 80.0  # 内存使用率警告阈值（%）
        self.disk_warning_threshold = 90.0  # 磁盘使用率警告阈值（%）

        # 警告回调
        self.warning_callbacks = []

    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("性能监控已经在运行")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("实时性能监控已启动")

    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("实时性能监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 收集系统性能数据
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_info = psutil.virtual_memory()
                disk_info = psutil.disk_usage('/')
                network_info = psutil.net_io_counters()

                # 存储数据
                timestamp = datetime.now().isoformat()

                self.cpu_history.append({
                    'timestamp': timestamp,
                    'cpu_percent': cpu_percent
                })

                self.memory_history.append({
                    'timestamp': timestamp,
                    'memory_percent': memory_info.percent,
                    'memory_used': memory_info.used / (1024**3),  # GB
                    'memory_total': memory_info.total / (1024**3)  # GB
                })

                self.disk_history.append({
                    'timestamp': timestamp,
                    'disk_percent': disk_info.percent,
                    'disk_used': disk_info.used / (1024**3),  # GB
                    'disk_total': disk_info.total / (1024**3)  # GB
                })

                self.network_history.append({
                    'timestamp': timestamp,
                    'bytes_sent': network_info.bytes_sent,
                    'bytes_recv': network_info.bytes_recv,
                    'packets_sent': network_info.packets_sent,
                    'packets_recv': network_info.packets_recv
                })

                # 检查警告
                self._check_warnings(cpu_percent, memory_info.percent, disk_info.percent)

            except Exception as e:
                logger.error(f"监控数据收集失败: {e}")

            time.sleep(self.interval)

    def _check_warnings(self, cpu: float, memory: float, disk: float):
        """检查警告阈值"""
        warnings = []

        if cpu > self.cpu_warning_threshold:
            warnings.append({
                'type': 'cpu',
                'message': f'CPU使用率过高: {cpu:.1f}%',
                'value': cpu,
                'threshold': self.cpu_warning_threshold
            })

        if memory > self.memory_warning_threshold:
            warnings.append({
                'type': 'memory',
                'message': f'内存使用率过高: {memory:.1f}%',
                'value': memory,
                'threshold': self.memory_warning_threshold
            })

        if disk > self.disk_warning_threshold:
            warnings.append({
                'type': 'disk',
                'message': f'磁盘使用率过高: {disk:.1f}%',
                'value': disk,
                'threshold': self.disk_warning_threshold
            })

        # 触发警告回调
        if warnings:
            for callback in self.warning_callbacks:
                try:
                    callback(warnings)
                except Exception as e:
                    logger.error(f"警告回调执行失败: {e}")

    def add_warning_callback(self, callback):
        """添加警告回调

        Args:
            callback: 回调函数，接收warnings参数
        """
        self.warning_callbacks.append(callback)

    def get_system_stats(self, duration: int = 60) -> Dict[str, Any]:
        """获取系统统计信息

        Args:
            duration: 统计时长（秒）

        Returns:
            系统统计信息字典
        """
        if not self.cpu_history:
            return {}

        # 获取指定时长的数据
        now = datetime.now()
        start_time = now - timedelta(seconds=duration)

        def filter_history(history):
            return [d for d in history if datetime.fromisoformat(d['timestamp']) >= start_time]

        cpu_data = filter_history(self.cpu_history)
        memory_data = filter_history(self.memory_history)
        disk_data = filter_history(self.disk_history)

        if not cpu_data:
            return {}

        stats = {
            'duration': duration,
            'cpu': {
                'current': cpu_data[-1]['cpu_percent'],
                'avg': sum(d['cpu_percent'] for d in cpu_data) / len(cpu_data),
                'max': max(d['cpu_percent'] for d in cpu_data),
                'min': min(d['cpu_percent'] for d in cpu_data),
                'warning_threshold': self.cpu_warning_threshold
            },
            'memory': {
                'current': memory_data[-1]['memory_percent'],
                'avg': sum(d['memory_percent'] for d in memory_data) / len(memory_data),
                'max': max(d['memory_percent'] for d in memory_data),
                'min': min(d['memory_percent'] for d in memory_data),
                'current_used_gb': memory_data[-1]['memory_used'],
                'total_gb': memory_data[-1]['memory_total'],
                'warning_threshold': self.memory_warning_threshold
            },
            'disk': {
                'current': disk_data[-1]['disk_percent'],
                'current_used_gb': disk_data[-1]['disk_used'],
                'total_gb': disk_data[-1]['disk_total'],
                'warning_threshold': self.disk_warning_threshold
            },
            'uptime': len(self.cpu_history) * self.interval
        }

        return stats

    def print_system_stats(self, duration: int = 60):
        """打印系统统计信息"""
        stats = self.get_system_stats(duration)

        if not stats:
            print("\n⚠️  暂无系统性能数据")
            return

        print("\n" + "="*60)
        print(f"系统性能监控 (最近{duration}秒)")
        print("="*60)

        # CPU
        print("\n💻 CPU:")
        cpu = stats['cpu']
        status = "🔴" if cpu['current'] > cpu['warning_threshold'] else "🟢"
        print(f"  {status} 当前: {cpu['current']:.1f}%")
        print(f"     平均: {cpu['avg']:.1f}%")
        print(f"     最大: {cpu['max']:.1f}%")
        print(f"     最小: {cpu['min']:.1f}%")
        print(f"     警告阈值: {cpu['warning_threshold']:.1f}%")

        # 内存
        print("\n🧠 内存:")
        memory = stats['memory']
        status = "🔴" if memory['current'] > memory['warning_threshold'] else "🟢"
        print(f"  {status} 当前: {memory['current']:.1f}% ({memory['current_used_gb']:.1f}GB / {memory['total_gb']:.1f}GB)")
        print(f"     平均: {memory['avg']:.1f}%")
        print(f"     最大: {memory['max']:.1f}%")
        print(f"     最小: {memory['min']:.1f}%")
        print(f"     警告阈值: {memory['warning_threshold']:.1f}%")

        # 磁盘
        print("\n💾 磁盘:")
        disk = stats['disk']
        status = "🔴" if disk['current'] > disk['warning_threshold'] else "🟢"
        print(f"  {status} 使用率: {disk['current']:.1f}% ({disk['current_used_gb']:.1f}GB / {disk['total_gb']:.1f}GB)")
        print(f"     警告阈值: {disk['warning_threshold']:.1f}%")

        # 运行时间
        print(f"\n⏱️  运行时间: {stats['uptime']:.0f}秒")

        print("\n" + "="*60 + "\n")

    def export_metrics(self, filepath: str):
        """导出指标到文件

        Args:
            filepath: 文件路径
        """
        data = {
            'system_stats': {
                'cpu': list(self.cpu_history),
                'memory': list(self.memory_history),
                'disk': list(self.disk_history),
                'network': list(self.network_history)
            },
            'warning_thresholds': {
                'cpu': self.cpu_warning_threshold,
                'memory': self.memory_warning_threshold,
                'disk': self.disk_warning_threshold
            },
            'export_time': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"性能指标已导出到 {filepath}")


class AgentPerformanceTracker:
    """智能体性能追踪器"""

    def __init__(self):
        self.tracker: Dict[str, Dict] = {}

    def start_tracking(self, agent_name: str):
        """开始追踪

        Args:
            agent_name: 智能体名称
        """
        if agent_name not in self.tracker:
            self.tracker[agent_name] = {
                'start_time': None,
                'end_time': None,
                'duration': None,
                'status': 'not_started'
            }

        self.tracker[agent_name]['start_time'] = time.time()
        self.tracker[agent_name]['status'] = 'running'

    def end_tracking(self, agent_name: str, success: bool = True, error: str = None):
        """结束追踪

        Args:
            agent_name: 智能体名称
            success: 是否成功
            error: 错误信息
        """
        if agent_name not in self.tracker:
            logger.warning(f"智能体 {agent_name} 未开始追踪")
            return

        if self.tracker[agent_name]['start_time'] is None:
            logger.warning(f"智能体 {agent_name} 没有开始时间")
            return

        self.tracker[agent_name]['end_time'] = time.time()
        self.tracker[agent_name]['duration'] = self.tracker[agent_name]['end_time'] - self.tracker[agent_name]['start_time']
        self.tracker[agent_name]['status'] = 'completed' if success else 'failed'
        self.tracker[agent_name]['error'] = error

    def get_duration(self, agent_name: str) -> Optional[float]:
        """获取执行时长

        Args:
            agent_name: 智能体名称

        Returns:
            执行时长（秒），如果未完成返回None
        """
        if agent_name not in self.tracker:
            return None

        return self.tracker[agent_name].get('duration')

    def get_status(self, agent_name: str) -> str:
        """获取状态

        Args:
            agent_name: 智能体名称

        Returns:
            状态字符串
        """
        if agent_name not in self.tracker:
            return 'not_started'

        return self.tracker[agent_name].get('status', 'unknown')

    def reset(self):
        """重置追踪器"""
        self.tracker.clear()


def create_performance_monitor() -> PerformanceMonitor:
    """创建性能监控器

    Returns:
        性能监控器实例
    """
    return PerformanceMonitor()


def create_realtime_monitor(interval: float = 1.0) -> RealTimePerformanceMonitor:
    """创建实时性能监控器

    Args:
        interval: 监控间隔（秒）

    Returns:
        实时性能监控器实例
    """
    return RealTimePerformanceMonitor(interval=interval)


def create_agent_tracker() -> AgentPerformanceTracker:
    """创建智能体性能追踪器

    Returns:
        智能体性能追踪器实例
    """
    return AgentPerformanceTracker()


if __name__ == "__main__":
    # 测试性能监控
    print("测试性能监控系统...")

    # 基础性能监控
    monitor = create_performance_monitor()
    monitor.record_success('agent1', 1.5, 0.85)
    monitor.record_success('agent1', 2.0, 0.9)
    monitor.record_failure('agent2', 3.0, 'Error occurred')
    monitor.print_stats()

    # 实时性能监控
    realtime = create_realtime_monitor(interval=0.5)
    realtime.start()
    time.sleep(2)
    realtime.print_system_stats()
    realtime.stop()
