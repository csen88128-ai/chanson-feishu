#!/usr/bin/env python3
"""
缠论多智能体系统 v5.1 — 本地运行入口

直接在本地执行 DAG 并行工作流，无需启动 FastAPI 服务。

用法:
    # 默认 BTCUSDT 1h 分析
    python run_local.py

    # 指定交易对和周期
    python run_local.py --symbol ETHUSDT --interval 4h

    # 安静模式（不打印执行过程）
    python run_local.py --quiet

    # 仅运行并行阶段测试（跳过数据采集和结构分析，使用 mock 数据）
    python run_local.py --test-parallel
"""

import argparse
import sys
import os

# 将 src 目录加入 sys.path，确保模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="缠论多智能体系统 v5.1 本地运行")
    parser.add_argument("--symbol", default="BTCUSDT", help="交易对 (默认: BTCUSDT)")
    parser.add_argument("--interval", default="1h", help="K线周期 (默认: 1h)")
    parser.add_argument("--request", default="BTC 缠论分析", help="分析请求描述")
    parser.add_argument("--quiet", action="store_true", help="安静模式，不打印执行过程")
    parser.add_argument(
        "--test-parallel", action="store_true",
        help="仅测试并行调度（使用 mock 数据，不调用 LLM）"
    )
    args = parser.parse_args()

    if args.test_parallel:
        _run_parallel_test(args)
    else:
        _run_full_analysis(args)


def _run_full_analysis(args):
    """运行完整分析"""
    from graphs.chanlun_graph import run_chanlun_analysis_local

    result = run_chanlun_analysis_local(
        user_request=args.request,
        symbol=args.symbol,
        interval=args.interval,
        verbose=not args.quiet,
    )

    if not args.quiet:
        # 打印决策摘要
        decision = result.get("trading_decision", {})
        if decision and decision.get("agent_response"):
            print("\n" + "=" * 60)
            print("  📋 交易决策摘要")
            print("=" * 60)
            response = decision["agent_response"]
            # 截取前 500 字符展示
            print(response[:500])
            if len(response) > 500:
                print(f"\n  ... (共 {len(response)} 字符，已截断)")
            print("=" * 60 + "\n")

        # 打印报告路径
        report_path = result.get("report_path")
        if report_path:
            print(f"📄 研报已保存至: {report_path}")

    return result


def _run_parallel_test(args):
    """仅测试 DAG 并行调度（不调用 LLM，使用 mock 数据）"""
    import asyncio
    from datetime import datetime
    from graphs.chanlun_graph import ChanlunState, build_chanlun_workflow

    print("\n" + "=" * 60)
    print("  🧪 DAG 并行调度测试（Mock 模式）")
    print("=" * 60)
    print("  跳过数据采集和 LLM 调用，仅验证并行拓扑正确性\n")

    # 构建工作流
    workflow = build_chanlun_workflow()

    # 构建 mock 初始状态
    initial_state = {
        "messages": [],
        "user_request": "并行测试",
        "symbol": args.symbol,
        "interval": args.interval,
        "kline_data": {"mock": True},
        "data_quality": {"status": "mock", "agent_response": "Mock 数据采集完成"},
        "structure_analysis": {"status": "mock", "agent_response": "Mock 结构分析完成"},
        "dynamics_analysis": {"status": "mock", "agent_response": "Mock 动力学分析完成"},
        "practical_theory_analysis": None,
        "risk_audit": None,
        "sentiment_analysis": None,
        "cross_market_analysis": None,
        "onchain_analysis": None,
        "system_health": None,
        "data_quality_report": None,
        "simulation_performance": None,
        "open_positions": None,
        "trading_decision": None,
        "report_path": None,
        "decision_stats": None,
        "parallel_group_status": {},
        "execution_timing": {},
    }

    # 打印 DAG 拓扑
    graph = workflow.get_graph()
    print("  📐 DAG 节点:")
    for node in graph.nodes:
        print(f"    - {node}")
    print()

    print("  🔗 DAG 边:")
    for edge in graph.edges:
        print(f"    {edge[0]} → {edge[1]}")
    print()

    # 验证 fan-out 边数量
    practical_out_edges = [e for e in graph.edges if e[0] == "practical_theory"]
    decision_in_edges = [e for e in graph.edges if e[1] == "decision_maker"]

    print(f"  ✅ practical_theory fan-out 边数: {len(practical_out_edges)} (期望: 5)")
    print(f"  ✅ decision_maker fan-in 边数:   {len(decision_in_edges)} (期望: 5)")

    fan_out_ok = len(practical_out_edges) == 5
    fan_in_ok = len(decision_in_edges) == 5

    if fan_out_ok and fan_in_ok:
        print("\n  🎉 DAG 并行拓扑验证通过！fan-out/fan-in 结构正确。")
    else:
        print("\n  ❌ DAG 并行拓扑异常！请检查边的定义。")
        sys.exit(1)

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
