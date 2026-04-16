"""
工作流可视化工具
生成DAG图和节点进度大盘
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import json


# ========== 1. DAG图生成器 ==========

class DAGVisualizer:
    """DAG图可视化工具"""

    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, node_id: str, label: str, node_type: str = "task"):
        """添加节点"""
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "status": "pending",
            "start_time": None,
            "end_time": None,
            "duration": 0
        }

    def add_edge(self, from_node: str, to_node: str):
        """添加边（依赖关系）"""
        self.edges.append({
            "from": from_node,
            "to": to_node
        })

    def update_node_status(self, node_id: str, status: str, start_time: datetime = None, end_time: datetime = None):
        """更新节点状态"""
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
            if start_time:
                self.nodes[node_id]["start_time"] = start_time
            if end_time:
                self.nodes[node_id]["end_time"] = end_time
                duration = (end_time - start_time).total_seconds() if start_time else 0
                self.nodes[node_id]["duration"] = duration

    def to_mermaid(self) -> str:
        """生成Mermaid格式的DAG图"""
        mermaid = ["graph TD"]

        # 添加节点
        for node_id, node_data in self.nodes.items():
            status_icon = {
                "pending": "⚪",
                "running": "🟡",
                "completed": "✅",
                "failed": "❌"
            }.get(node_data["status"], "⚪")

            label = f"{status_icon} {node_data['label']}"
            mermaid.append(f'    {node_id}["{label}"]')

        # 添加边
        for edge in self.edges:
            mermaid.append(f'    {edge["from"]} --> {edge["to"]}')

        return "\n".join(mermaid)

    def to_json(self) -> str:
        """生成JSON格式"""
        return json.dumps({
            "nodes": self.nodes,
            "edges": self.edges
        }, indent=2, default=str)

    def get_execution_timeline(self) -> List[Dict[str, Any]]:
        """获取执行时间线"""
        timeline = []
        for node_id, node_data in self.nodes.items():
            if node_data["start_time"] and node_data["end_time"]:
                timeline.append({
                    "node_id": node_id,
                    "label": node_data["label"],
                    "start": node_data["start_time"],
                    "end": node_data["end_time"],
                    "duration": node_data["duration"],
                    "status": node_data["status"]
                })

        # 按开始时间排序
        timeline.sort(key=lambda x: x["start"])
        return timeline


# ========== 2. 节点进度大盘 ==========

class ProgressDashboard:
    """节点进度大盘"""

    def __init__(self, dag_visualizer: DAGVisualizer):
        self.dag = dag_visualizer
        self.start_time = datetime.now()
        self.history = []

    def update(self, node_id: str, status: str, message: str = ""):
        """更新进度"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()

        self.history.append({
            "timestamp": timestamp,
            "elapsed": elapsed,
            "node_id": node_id,
            "status": status,
            "message": message
        })

    def get_progress_report(self) -> str:
        """生成进度报告"""
        total_nodes = len(self.dag.nodes)
        completed = sum(1 for n in self.dag.nodes.values() if n["status"] == "completed")
        running = sum(1 for n in self.dag.nodes.values() if n["status"] == "running")
        failed = sum(1 for n in self.dag.nodes.values() if n["status"] == "failed")
        pending = total_nodes - completed - running - failed

        percentage = (completed / total_nodes * 100) if total_nodes > 0 else 0

        report = f"""
╔════════════════════════════════════════════════════════════╗
║           📊 节点进度大盘                                    ║
╠════════════════════════════════════════════════════════════╣
║  总耗时: {(datetime.now() - self.start_time).total_seconds():.2f}秒                            ║
║  总节点: {total_nodes}                                                    ║
║  ✅ 已完成: {completed}                                                   ║
║  🟡 运行中: {running}                                                   ║
║  ⚪ 待执行: {pending}                                                   ║
║  ❌ 已失败: {failed}                                                   ║
╠════════════════════════════════════════════════════════════╣
║  进度: [{"█" * int(percentage // 2)}{"░" * (50 - int(percentage // 2))}] {percentage:.0f}%            ║
╚════════════════════════════════════════════════════════════╝

📋 节点状态:
"""
        # 添加节点详情
        for node_id, node_data in self.dag.nodes.items():
            status_icon = {
                "pending": "⚪",
                "running": "🟡",
                "completed": "✅",
                "failed": "❌"
            }.get(node_data["status"], "⚪")

            duration_str = f"{node_data['duration']:.2f}s" if node_data["duration"] > 0 else "-"
            report += f"  {status_icon} {node_data['label']:20s} {duration_str:>8s}\n"

        return report


# ========== 3. 技能池管理器 ==========

class SkillPool:
    """技能池管理器"""

    def __init__(self):
        self.skills = {}
        self.task_queue = []
        self.active_tasks = {}

    def register_skill(self, skill_id: str, skill_name: str, description: str):
        """注册技能"""
        self.skills[skill_id] = {
            "id": skill_id,
            "name": skill_name,
            "description": description,
            "status": "idle",
            "task_count": 0,
            "total_duration": 0
        }

    def assign_task(self, skill_id: str, task_name: str):
        """分配任务"""
        if skill_id in self.skills:
            skill = self.skills[skill_id]
            skill["status"] = "busy"
            skill["task_count"] += 1
            self.active_tasks[task_name] = {
                "skill_id": skill_id,
                "start_time": datetime.now()
            }
            print(f"🎯 任务分配: {task_name} → {skill['name']}")

    def complete_task(self, task_name: str):
        """完成任务"""
        if task_name in self.active_tasks:
            task = self.active_tasks[task_name]
            skill_id = task["skill_id"]
            if skill_id in self.skills:
                skill = self.skills[skill_id]
                skill["status"] = "idle"
                duration = (datetime.now() - task["start_time"]).total_seconds()
                skill["total_duration"] += duration
            del self.active_tasks[task_name]

    def get_pool_status(self) -> str:
        """获取技能池状态"""
        report = """
╔════════════════════════════════════════════════════════════╗
║           🎯 技能池状态                                     ║
╠════════════════════════════════════════════════════════════╣
"""

        for skill_id, skill in self.skills.items():
            status_icon = "🟢" if skill["status"] == "idle" else "🔴"
            avg_duration = (skill["total_duration"] / skill["task_count"]) if skill["task_count"] > 0 else 0

            report += f"║ {status_icon} {skill['name']:20s} 任务数: {skill['task_count']:3d}  平均耗时: {avg_duration:5.2f}s ║\n"

        report += "╚════════════════════════════════════════════════════════════╝"
        return report


# ========== 4. 演示：缠论工作流可视化 ==========

def demo_chanlun_workflow_visualization():
    """演示缠论工作流可视化"""

    print("\n" + "🎯"*60)
    print("  缠论多智能体工作流 - 可视化演示")
    print("🎯"*60 + "\n")

    # 创建DAG可视化器
    dag = DAGVisualizer()

    # 添加节点
    dag.add_node("data_collector", "数据采集")
    dag.add_node("structure_analyzer", "结构分析")
    dag.add_node("dynamics_analyzer", "动力学分析")
    dag.add_node("practical_theory", "实战理论")
    dag.add_node("sentiment_analyzer", "市场情绪")
    dag.add_node("cross_market_analyzer", "跨市场联动")
    dag.add_node("onchain_analyzer", "链上数据")
    dag.add_node("system_monitor", "系统监控")
    dag.add_node("simulation_check", "模拟盘检查")
    dag.add_node("decision_maker", "首席决策")
    dag.add_node("risk_manager", "风控审核")
    dag.add_node("report_generator", "研报生成")

    # 添加边（依赖关系）
    dag.add_edge("data_collector", "structure_analyzer")
    dag.add_edge("structure_analyzer", "dynamics_analyzer")
    dag.add_edge("dynamics_analyzer", "practical_theory")
    dag.add_edge("practical_theory", "sentiment_analyzer")
    dag.add_edge("practical_theory", "cross_market_analyzer")
    dag.add_edge("practical_theory", "onchain_analyzer")
    dag.add_edge("sentiment_analyzer", "decision_maker")
    dag.add_edge("cross_market_analyzer", "decision_maker")
    dag.add_edge("onchain_analyzer", "decision_maker")
    dag.add_edge("system_monitor", "decision_maker")
    dag.add_edge("simulation_check", "decision_maker")
    dag.add_edge("decision_maker", "risk_manager")
    dag.add_edge("risk_manager", "report_generator")

    # 创建进度大盘
    dashboard = ProgressDashboard(dag)

    # 创建技能池
    skill_pool = SkillPool()
    skill_pool.register_skill("data_collector", "数据采集智能体", "采集市场K线数据")
    skill_pool.register_skill("structure_analyzer", "结构分析智能体", "分析笔线段中枢")
    skill_pool.register_skill("dynamics_analyzer", "动力学智能体", "分析背驰和力度")
    skill_pool.register_skill("practical_theory", "实战理论智能体", "应用实战理论")
    skill_pool.register_skill("sentiment_analyzer", "市场情绪智能体", "分析市场情绪")
    skill_pool.register_skill("cross_market_analyzer", "跨市场智能体", "分析市场联动")
    skill_pool.register_skill("onchain_analyzer", "链上数据智能体", "分析链上数据")
    skill_pool.register_skill("system_monitor", "系统监控智能体", "监控系统健康")
    skill_pool.register_skill("simulation_check", "模拟盘智能体", "检查模拟盘绩效")
    skill_pool.register_skill("decision_maker", "首席决策智能体", "做出交易决策")
    skill_pool.register_skill("risk_manager", "风控智能体", "审核风险")
    skill_pool.register_skill("report_generator", "研报生成智能体", "生成分析报告")

    # 模拟执行
    print("📊 DAG图结构 (Mermaid格式):\n")
    print(dag.to_mermaid())
    print("\n")

    # 模拟节点执行
    execution_order = [
        ("data_collector", 2),
        ("structure_analyzer", 3),
        ("dynamics_analyzer", 2),
        ("practical_theory", 2),
        # 并行执行
        ("sentiment_analyzer", 3),
        ("cross_market_analyzer", 3),
        ("onchain_analyzer", 3),
        ("system_monitor", 1),
        ("simulation_check", 1),
        ("decision_maker", 2),
        ("risk_manager", 1),
        ("report_generator", 2)
    ]

    current_time = datetime.now()

    for node_id, duration in execution_order:
        # 更新DAG状态
        dag.update_node_status(node_id, "running", current_time)
        dashboard.update(node_id, "running", f"开始执行 {node_id}")
        skill_pool.assign_task(node_id, f"{node_id}_task")

        # 显示进度
        print(dashboard.get_progress_report())

        # 模拟执行时间
        import time
        time.sleep(0.5)  # 减少演示时间

        # 完成节点
        end_time = current_time + timedelta(seconds=duration)
        dag.update_node_status(node_id, "completed", current_time, end_time)
        dashboard.update(node_id, "completed", f"完成 {node_id}")
        skill_pool.complete_task(f"{node_id}_task")
        current_time = end_time

    # 显示最终进度
    print(dashboard.get_progress_report())
    print(skill_pool.get_pool_status())

    # 显示执行时间线
    print("\n📅 执行时间线:")
    timeline = dag.get_execution_timeline()
    for item in timeline:
        print(f"  {item['label']:20s} | {item['duration']:5.2f}s | {item['status']}")


# ========== 5. 生成HTML可视化报告 ==========

def generate_html_report(dag: DAGVisualizer, dashboard: ProgressDashboard) -> str:
    """生成HTML可视化报告"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>缠论多智能体工作流可视化</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }}
        .node-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .node-card {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            transition: all 0.3s ease;
        }}
        .node-card.pending {{
            border-color: #9e9e9e;
            background: #f5f5f5;
        }}
        .node-card.running {{
            border-color: #ffeb3b;
            background: #fffde7;
            animation: pulse 1s infinite;
        }}
        .node-card.completed {{
            border-color: #4caf50;
            background: #e8f5e9;
        }}
        .node-card.failed {{
            border-color: #f44336;
            background: #ffebee;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-badge.pending {{ background: #9e9e9e; color: white; }}
        .status-badge.running {{ background: #ffeb3b; color: #333; }}
        .status-badge.completed {{ background: #4caf50; color: white; }}
        .status-badge.failed {{ background: #f44336; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 缠论多智能体工作流 - 可视化面板</h1>

        <div class="progress-bar">
            <div class="progress-fill" style="width: 75%;"></div>
        </div>

        <h2>📊 节点状态</h2>
        <div class="node-grid">
"""

    # 添加节点卡片
    for node_id, node_data in dag.nodes.items():
        html += f"""
            <div class="node-card {node_data['status']}">
                <h3>{node_data['label']} <span class="status-badge {node_data['status']}">{node_data['status']}</span></h3>
                <p>节点ID: {node_id}</p>
                <p>执行时间: {node_data['duration']:.2f}秒</p>
            </div>
"""

    html += """
        </div>

        <h2>📈 执行统计</h2>
        <ul>
            <li>总节点数: 12</li>
            <li>已完成: 9</li>
            <li>运行中: 1</li>
            <li>待执行: 2</li>
        </ul>
    </div>
</body>
</html>
"""

    return html


# ========== 6. 主入口 ==========

def main():
    """主函数"""

    demo_chanlun_workflow_visualization()

    print("\n" + "="*60)
    print("✅ 可视化演示完成！")
    print("="*60 + "\n")

    print("💡 提示:")
    print("  1. 上面的Mermaid图可以复制到 https://mermaid.live/ 中查看")
    print("  2. 进度大盘显示了每个节点的实时状态")
    print("  3. 技能池管理展示了智能体的资源分配情况")
    print("  4. 可以生成HTML报告用于Web展示")
    print()


if __name__ == "__main__":
    main()
