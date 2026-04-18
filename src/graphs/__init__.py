"""
缠论多智能体图模块 v5.1
支持 DAG 并行执行（fan-out / fan-in）
"""
from .chanlun_graph import (
    ChanlunState,
    build_chanlun_workflow,
    run_chanlun_analysis,
    run_chanlun_analysis_async,
    run_chanlun_analysis_local,
)

__all__ = [
    "ChanlunState",
    "build_chanlun_workflow",
    "run_chanlun_analysis",
    "run_chanlun_analysis_async",
    "run_chanlun_analysis_local",
]
