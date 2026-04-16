"""
缠论多智能体系统 - 最终部署验证脚本
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')


def print_section(title):
    """打印分段标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """主验证函数"""
    print("\n" + "🚀" * 35)
    print("  缠论多智能体分析系统 v7.0 - 部署验证")
    print("🚀" * 35)

    results = {}

    # 测试1: 智能体模块
    print_section("1. 智能体模块验证")
    agents = [
        'data_collector', 'structure_analyzer', 'dynamics_analyzer',
        'practical_theory', 'sentiment_analyzer', 'cross_market_analyzer',
        'onchain_analyzer', 'system_monitor', 'simulation',
        'decision_maker', 'risk_manager', 'report_generator'
    ]
    success_count = 0
    for agent in agents:
        try:
            __import__(f'agents.{agent}')
            print(f"  ✅ {agent}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {agent}: {str(e)[:50]}")
    results['智能体'] = f"{success_count}/{len(agents)}"

    # 测试2: 工具模块
    print_section("2. 工具模块验证")
    tools = ['data_tools', 'monitor_tools', 'sentiment_tools',
             'cross_market_tools', 'onchain_tools', 'simulation_tools',
             'risk_tools', 'real_trade_tools']
    success_count = 0
    for tool in tools:
        try:
            __import__(f'tools.{tool}')
            print(f"  ✅ {tool}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {tool}: {str(e)[:50]}")
    results['工具'] = f"{success_count}/{len(tools)}"

    # 测试3: 工具函数模块
    print_section("3. 工具函数模块验证")
    utils = ['chanlun_structure', 'chanlun_dynamics',
             'report_generator', 'decision_history']
    success_count = 0
    for util in utils:
        try:
            __import__(f'utils.{util}')
            print(f"  ✅ utils.{util}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ utils.{util}: {str(e)[:50]}")
    results['工具函数'] = f"{success_count}/{len(utils)}"

    # 测试4: 存储模块
    print_section("4. 存储模块验证")
    try:
        from storage.memory.memory_saver import get_memory_saver
        print(f"  ✅ storage.memory.memory_saver")
        results['存储'] = "1/1"
    except Exception as e:
        print(f"  ❌ storage.memory.memory_saver: {str(e)[:50]}")
        results['存储'] = "0/1"

    # 测试5: 工作流模块
    print_section("5. 工作流模块验证")
    try:
        from graphs.chanlun_graph import (
            ChanlunState, build_chanlun_workflow
        )
        print(f"  ✅ graphs.chanlun_graph")

        # 尝试构建工作流
        workflow = build_chanlun_workflow()
        print(f"  ✅ 工作流构建成功")
        print(f"     类型: {type(workflow).__name__}")
        results['工作流'] = "成功"
    except Exception as e:
        print(f"  ❌ graphs.chanlun_graph: {str(e)[:100]}")
        results['工作流'] = f"失败: {str(e)[:50]}"

    # 测试6: 配置文件
    print_section("6. 配置文件验证")
    try:
        import json
        with open('/workspace/chanson-feishu/config/agent_llm_config.json', 'r') as f:
            config = json.load(f)
        print(f"  ✅ agent_llm_config.json")
        print(f"     模型: {config.get('config', {}).get('model', 'N/A')}")
        results['配置'] = "成功"
    except Exception as e:
        print(f"  ❌ 配置文件: {str(e)[:50]}")
        results['配置'] = "失败"

    # 测试7: DAG示例
    print_section("7. DAG并行化示例验证")
    try:
        import graphs.dag_parallel_example
        print(f"  ✅ dag_parallel_example.py 可导入")
        results['DAG示例'] = "成功"
    except Exception as e:
        print(f"  ❌ dag_parallel_example: {str(e)[:50]}")
        results['DAG示例'] = "失败"

    # 测试8: 可视化工具
    print_section("8. 可视化工具验证")
    try:
        import graphs.workflow_visualizer
        print(f"  ✅ workflow_visualizer.py 可导入")
        results['可视化'] = "成功"
    except Exception as e:
        print(f"  ❌ workflow_visualizer: {str(e)[:50]}")
        results['可视化'] = "失败"

    # 最终结果
    print_section("部署验证结果汇总")
    print()
    for key, value in results.items():
        print(f"  {key:15s}: {value}")
    print()

    # 统计
    total_tests = len([r for r in results.values() if isinstance(r, str)])
    passed_tests = len([r for r in results.values() if isinstance(r, str) and '成功' in r])

    print(f"\n  总计: {passed_tests}/{total_tests} 项测试通过")

    if passed_tests == total_tests:
        print("\n  🎉 恭喜！所有测试通过！系统部署成功！\n")
        print("  📚 系统文档:")
        print("     - CHANLUN_README.md      : 系统完整说明")
        print("     - docs/                 : 详细文档目录")
        print("     - docs/DAG_*.md         : DAG并行化分析文档")
        print()
        print("  🔧 使用方式:")
        print("     1. 激活环境: source .venv/bin/activate")
        print("     2. 运行系统: python src/main.py")
        print()
        return 0
    else:
        print("\n  ⚠️  部分测试未通过，请检查上述错误信息\n")
        return 1


if __name__ == "__main__":
    exit(main())
