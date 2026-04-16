"""
缠论多智能体系统测试脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from graphs import run_chanlun_analysis


def test_chanlun_system():
    """测试缠论多智能体系统"""

    print("=" * 80)
    print("缠论多智能体分析系统 - 测试运行")
    print("=" * 80)
    print()

    # 测试用例1：BTC 1小时周期分析
    print("测试用例1: BTCUSDT 1小时周期分析")
    print("-" * 80)

    try:
        result = run_chanlun_analysis(
            user_request="请分析BTCUSDT当前的市场走势，基于缠论给出交易建议",
            symbol="BTCUSDT",
            interval="1h"
        )

        print("\n✓ 系统运行成功\n")
        print("=" * 80)
        print("分析结果摘要")
        print("=" * 80)

        # 输出各个节点的结果
        print("\n【数据采集节点】")
        if result.get("data_quality"):
            print(f"状态: {result['data_quality'].get('status')}")
            print(f"响应: {result['data_quality'].get('agent_response', '')[:200]}...")

        print("\n【系统监控节点】")
        if result.get("system_health"):
            print(f"状态: {result['system_health'].get('status')}")
            print(f"响应: {result['system_health'].get('agent_response', '')[:200]}...")

        print("\n【模拟盘检查节点】")
        if result.get("simulation_performance"):
            print(f"状态: {result['simulation_performance'].get('status')}")
            print(f"响应: {result['simulation_performance'].get('agent_response', '')[:200]}...")

        print("\n【首席决策节点】")
        if result.get("trading_decision"):
            print(f"状态: {result['trading_decision'].get('status')}")
            print("\n--- 交易决策 ---")
            print(result['trading_decision'].get('agent_response', ''))

        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ 系统运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chanlun_system()
    sys.exit(0 if success else 1)
