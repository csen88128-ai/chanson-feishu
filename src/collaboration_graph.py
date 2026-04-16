"""
智能体协作图谱
优化执行顺序，提升并行效率
"""
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """智能体类型"""
    STRUCTURE = "structure_analysis"
    DYNAMICS = "dynamics_analysis"
    BUY_SELL = "buy_sell_points"
    SENTIMENT = "sentiment_analysis"
    RISK = "risk_assessment"
    STRATEGY = "trading_strategy"
    FUND = "fund_management"
    PSYCHOLOGY = "psychology_management"
    CYCLE = "cycle_analysis"
    EVALUATION = "comprehensive_evaluation"
    DECISION = "decision_integration"


@dataclass
class AgentNode:
    """智能体节点"""
    name: str
    agent_type: AgentType
    weight: float = 1.0  # 权重
    priority: int = 1  # 优先级
    execution_time: float = 1.0  # 预估执行时间（秒）
    dependencies: List[str] = field(default_factory=list)  # 依赖的智能体


class AgentCollaborationGraph:
    """智能体协作图谱"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.agents: Dict[str, AgentNode] = {}
        self._initialize_graph()

    def _initialize_graph(self):
        """初始化协作图谱"""
        # 定义所有智能体节点
        agents_data = [
            {
                'name': 'structure_analysis',
                'type': AgentType.STRUCTURE,
                'weight': 0.15,
                'priority': 1,
                'execution_time': 3.5,
                'dependencies': []
            },
            {
                'name': 'dynamics_analysis',
                'type': AgentType.DYNAMICS,
                'weight': 0.15,
                'priority': 1,
                'execution_time': 4.0,
                'dependencies': ['structure_analysis']
            },
            {
                'name': 'sentiment_analysis',
                'type': AgentType.SENTIMENT,
                'weight': 0.10,
                'priority': 2,
                'execution_time': 2.5,
                'dependencies': []
            },
            {
                'name': 'buy_sell_points',
                'type': AgentType.BUY_SELL,
                'weight': 0.20,
                'priority': 3,
                'execution_time': 5.0,
                'dependencies': ['structure_analysis', 'dynamics_analysis']
            },
            {
                'name': 'risk_assessment',
                'type': AgentType.RISK,
                'weight': 0.15,
                'priority': 3,
                'execution_time': 3.0,
                'dependencies': ['sentiment_analysis']
            },
            {
                'name': 'cycle_analysis',
                'type': AgentType.CYCLE,
                'weight': 0.025,
                'priority': 4,
                'execution_time': 2.0,
                'dependencies': []
            },
            {
                'name': 'trading_strategy',
                'type': AgentType.STRATEGY,
                'weight': 0.15,
                'priority': 4,
                'execution_time': 4.5,
                'dependencies': ['buy_sell_points', 'risk_assessment']
            },
            {
                'name': 'fund_management',
                'type': AgentType.FUND,
                'weight': 0.05,
                'priority': 5,
                'execution_time': 1.5,
                'dependencies': ['trading_strategy']
            },
            {
                'name': 'psychology_management',
                'type': AgentType.PSYCHOLOGY,
                'weight': 0.025,
                'priority': 5,
                'execution_time': 1.0,
                'dependencies': ['trading_strategy']
            },
            {
                'name': 'comprehensive_evaluation',
                'type': AgentType.EVALUATION,
                'weight': 0.10,
                'priority': 5,
                'execution_time': 3.5,
                'dependencies': ['fund_management', 'psychology_management', 'cycle_analysis']
            },
            {
                'name': 'decision_integration',
                'type': AgentType.DECISION,
                'weight': 0.10,
                'priority': 6,
                'execution_time': 2.5,
                'dependencies': ['comprehensive_evaluation']
            }
        ]

        # 创建智能体节点
        for agent_data in agents_data:
            # 映射 type 到 agent_type
            agent_data['agent_type'] = agent_data.pop('type')
            agent_node = AgentNode(**agent_data)
            self.agents[agent_node.name] = agent_node
            self.graph.add_node(
                agent_node.name,
                weight=agent_node.weight,
                priority=agent_node.priority,
                execution_time=agent_node.execution_time
            )

        # 创建依赖关系边
        for agent_node in self.agents.values():
            for dep in agent_node.dependencies:
                self.graph.add_edge(dep, agent_node.name)

    def topological_sort(self) -> List[str]:
        """拓扑排序

        Returns:
            拓扑排序后的智能体名称列表
        """
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError as e:
            raise ValueError(f"协作图谱存在循环依赖: {e}")

    def get_parallel_groups(self) -> List[List[str]]:
        """获取可并行执行的智能体组

        Returns:
            并行执行组列表，每个组包含可并行执行的智能体名称
        """
        topological_order = self.topological_sort()
        parallel_groups = []
        current_group = []
        processed_agents = set()

        for agent_name in topological_order:
            agent = self.agents[agent_name]
            dependencies_satisfied = all(dep in processed_agents for dep in agent.dependencies)

            if dependencies_satisfied:
                current_group.append(agent_name)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                    processed_agents.update(current_group)
                    current_group = []
                current_group.append(agent_name)

        if current_group:
            parallel_groups.append(current_group)

        return parallel_groups

    def calculate_critical_path(self) -> Tuple[List[str], float]:
        """计算关键路径和总执行时间

        Returns:
            (关键路径上的智能体列表, 总执行时间)
        """
        # 计算每个节点的最早开始时间和最晚开始时间
        earliest_start = {}
        latest_start = {}

        # 正向遍历计算最早开始时间
        for agent_name in self.topological_sort():
            agent = self.agents[agent_name]
            if not agent.dependencies:
                earliest_start[agent_name] = 0
            else:
                earliest_start[agent_name] = max(
                    earliest_start[dep] + self.agents[dep].execution_time
                    for dep in agent.dependencies
                )

        # 反向遍历计算最晚开始时间
        reversed_order = list(reversed(self.topological_sort()))
        total_time = max(
            earliest_start[agent] + self.agents[agent].execution_time
            for agent in earliest_start
        )

        for agent_name in reversed_order:
            agent = self.agents[agent_name]
            successors = [v for u, v in self.graph.edges() if u == agent_name]

            if not successors:
                latest_start[agent_name] = total_time - agent.execution_time
            else:
                latest_start[agent_name] = min(
                    latest_start[succ] - agent.execution_time
                    for succ in successors
                )

        # 找出关键路径上的节点
        critical_path = [
            agent for agent in self.topological_sort()
            if earliest_start[agent] == latest_start[agent]
        ]

        return critical_path, total_time

    def get_dependencies(self, agent_name: str) -> List[str]:
        """获取智能体的依赖

        Args:
            agent_name: 智能体名称

        Returns:
            依赖的智能体列表
        """
        if agent_name not in self.agents:
            return []
        return self.agents[agent_name].dependencies

    def get_successors(self, agent_name: str) -> List[str]:
        """获取智能体的后继

        Args:
            agent_name: 智能体名称

        Returns:
            后继智能体列表
        """
        if agent_name not in self.graph:
            return []
        return list(self.graph.successors(agent_name))

    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """获取智能体信息

        Args:
            agent_name: 智能体名称

        Returns:
            智能体信息字典，如果不存在返回None
        """
        if agent_name not in self.agents:
            return None

        agent = self.agents[agent_name]
        return {
            'name': agent.name,
            'type': agent.agent_type.value,
            'weight': agent.weight,
            'priority': agent.priority,
            'execution_time': agent.execution_time,
            'dependencies': agent.dependencies,
            'successors': self.get_successors(agent_name)
        }

    def calculate_parallel_efficiency(self) -> Dict[str, float]:
        """计算并行效率

        Returns:
            并行效率指标字典
        """
        parallel_groups = self.get_parallel_groups()
        critical_path, sequential_time = self.calculate_critical_path()

        # 估算并行执行时间（每个组取最长时间）
        parallel_time = sum(
            max(self.agents[agent].execution_time for agent in group)
            for group in parallel_groups
        )

        efficiency = {
            'sequential_time': sequential_time,
            'parallel_time': parallel_time,
            'speedup': sequential_time / parallel_time if parallel_time > 0 else 0,
            'efficiency': (sequential_time / parallel_time) / len(parallel_groups) if parallel_time > 0 and len(parallel_groups) > 0 else 0,
            'num_groups': len(parallel_groups),
            'num_agents': len(self.agents)
        }

        return efficiency

    def print_analysis(self):
        """打印分析结果"""
        print("\n" + "="*60)
        print("智能体协作图谱分析")
        print("="*60)

        # 拓扑排序
        print("\n📋 拓扑排序:")
        topological_order = self.topological_sort()
        for i, agent_name in enumerate(topological_order, 1):
            print(f"  {i}. {agent_name}")

        # 并行执行组
        print("\n🚀 可并行执行的智能体组:")
        parallel_groups = self.get_parallel_groups()
        for i, group in enumerate(parallel_groups, 1):
            group_time = sum(self.agents[agent].execution_time for agent in group)
            print(f"  组{i} (耗时: {group_time:.1f}s): {', '.join(group)}")

        # 关键路径
        print("\n🎯 关键路径:")
        critical_path, total_time = self.calculate_critical_path()
        print(f"  总执行时间: {total_time:.1f}s")
        print(f"  关键智能体: {' -> '.join(critical_path)}")

        # 并行效率
        print("\n⚡ 并行效率:")
        efficiency = self.calculate_parallel_efficiency()
        print(f"  顺序执行时间: {efficiency['sequential_time']:.1f}s")
        print(f"  并行执行时间: {efficiency['parallel_time']:.1f}s")
        print(f"  加速比: {efficiency['speedup']:.2f}x")
        print(f"  并行效率: {efficiency['efficiency']:.2%}")

        print("\n" + "="*60 + "\n")

        return {
            'topological_order': topological_order,
            'parallel_groups': parallel_groups,
            'critical_path': critical_path,
            'total_time': total_time,
            'efficiency': efficiency
        }


def create_collaboration_graph() -> AgentCollaborationGraph:
    """创建协作图谱实例

    Returns:
        协作图谱实例
    """
    return AgentCollaborationGraph()


if __name__ == "__main__":
    # 测试协作图谱
    graph = create_collaboration_graph()
    graph.print_analysis()
