"""
系统监控相关工具
"""
import os
import json
import psutil
import time
from datetime import datetime
from langchain.tools import tool
from typing import Dict, List
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.start_time = time.time()
        self.agent_health_status: Dict[str, Dict] = {}

    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "total_gb": psutil.virtual_memory().total / (1024**3)
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free_gb": psutil.disk_usage('/').free / (1024**3),
                "total_gb": psutil.disk_usage('/').total / (1024**3)
            },
            "uptime_hours": (time.time() - self.start_time) / 3600
        }

    def record_agent_status(self, agent_name: str, status: str, details: Dict = None):
        """记录智能体状态"""
        self.agent_health_status[agent_name] = {
            "status": status,  # healthy, warning, critical, error
            "last_update": datetime.now().isoformat(),
            "details": details or {}
        }

    def get_agent_health_summary(self) -> Dict:
        """获取智能体健康状态摘要"""
        if not self.agent_health_status:
            return {"status": "no_data", "agents": {}}

        total = len(self.agent_health_status)
        healthy = sum(1 for s in self.agent_health_status.values() if s["status"] == "healthy")
        warning = sum(1 for s in self.agent_health_status.values() if s["status"] == "warning")
        critical = sum(1 for s in self.agent_health_status.values() if s["status"] == "critical")
        error = sum(1 for s in self.agent_health_status.values() if s["status"] == "error")

        overall_status = "healthy"
        if critical > 0 or error > 0:
            overall_status = "critical"
        elif warning > 0:
            overall_status = "warning"

        return {
            "overall_status": overall_status,
            "total_agents": total,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "error": error,
            "agents": self.agent_health_status
        }


# 全局实例
_monitor = SystemMonitor()


@tool
def check_system_health() -> str:
    """
    检查系统健康状态

    Returns:
        系统健康状态报告 JSON
    """
    ctx = request_context.get() or new_context(method="check_system_health")

    try:
        # 获取系统指标
        metrics = _monitor.get_system_metrics()

        # 判断系统状态
        system_status = "healthy"
        alerts = []

        if metrics["cpu_percent"] > 80:
            system_status = "warning"
            alerts.append(f"CPU使用率过高: {metrics['cpu_percent']}%")

        if metrics["memory"]["percent"] > 85:
            system_status = "warning"
            alerts.append(f"内存使用率过高: {metrics['memory']['percent']}%")

        if metrics["disk"]["percent"] > 90:
            system_status = "critical"
            alerts.append(f"磁盘空间不足: {metrics['disk']['percent']}%")

        # 获取智能体健康状态
        agent_health = _monitor.get_agent_health_summary()

        report = {
            "system_status": system_status,
            "metrics": metrics,
            "agent_health": agent_health,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def record_agent_health(
    agent_name: str,
    status: str,
    message: str = "",
    execution_time: float = 0.0
) -> str:
    """
    记录智能体健康状态

    Args:
        agent_name: 智能体名称
        status: 状态 (healthy, warning, critical, error)
        message: 状态描述信息
        execution_time: 执行耗时（秒）

    Returns:
        操作结果
    """
    ctx = request_context.get() or new_context(method="record_agent_health")

    try:
        _monitor.record_agent_status(
            agent_name=agent_name,
            status=status,
            details={
                "message": message,
                "execution_time": execution_time
            }
        )

        return json.dumps({
            "success": True,
            "agent_name": agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_data_quality_report(symbol: str = "BTCUSDT") -> str:
    """
    获取数据质量报告

    Args:
        symbol: 交易对

    Returns:
        数据质量报告
    """
    ctx = request_context.get() or new_context(method="get_data_quality_report")

    try:
        # 检查本地数据文件
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        data_dir = os.path.join(workspace_path, "data")

        if not os.path.exists(data_dir):
            return json.dumps({
                "status": "warning",
                "message": "数据目录不存在",
                "data_dir": data_dir
            }, ensure_ascii=False, indent=2)

        # 获取数据文件列表
        files = [f for f in os.listdir(data_dir) if f.startswith(symbol) and f.endswith('.csv')]

        if not files:
            return json.dumps({
                "status": "warning",
                "message": "未找到数据文件",
                "symbol": symbol
            }, ensure_ascii=False, indent=2)

        # 按修改时间排序，获取最新的
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)))
        latest_file = files[-1]

        file_path = os.path.join(data_dir, latest_file)
        file_size = os.path.getsize(file_path)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

        # 检查数据新鲜度（5分钟内为新鲜）
        now = datetime.now()
        age_minutes = (now - file_mtime).total_seconds() / 60
        is_fresh = age_minutes < 5

        report = {
            "symbol": symbol,
            "status": "healthy" if is_fresh else "warning",
            "latest_file": latest_file,
            "file_size_bytes": file_size,
            "file_modified_time": file_mtime.isoformat(),
            "data_age_minutes": round(age_minutes, 2),
            "is_data_fresh": is_fresh,
            "total_files": len(files),
            "timestamp": now.isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
