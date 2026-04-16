"""
简单的系统验证测试
测试单个智能体是否能正常工作
"""

import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')

def test_imports():
    """测试所有智能体是否可以导入"""
    print("=" * 60)
    print("测试1: 导入所有智能体")
    print("=" * 60)

    agents = [
        'data_collector',
        'structure_analyzer',
        'dynamics_analyzer',
        'practical_theory',
        'sentiment_analyzer',
        'cross_market_analyzer',
        'onchain_analyzer',
        'system_monitor',
        'simulation',
        'decision_maker',
        'risk_manager',
        'report_generator'
    ]

    success_count = 0
    fail_count = 0

    for agent_name in agents:
        try:
            module = __import__(f'agents.{agent_name}', fromlist=['build_agent'])
            if hasattr(module, 'build_agent'):
                print(f"✅ {agent_name}: 导入成功")
                success_count += 1
            else:
                print(f"❌ {agent_name}: 缺少build_agent函数")
                fail_count += 1
        except Exception as e:
            print(f"❌ {agent_name}: 导入失败 - {str(e)}")
            fail_count += 1

    print(f"\n总计: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def test_tools_import():
    """测试工具是否可以导入"""
    print("\n" + "=" * 60)
    print("测试2: 导入工具模块")
    print("=" * 60)

    try:
        import tools
        print("✅ tools模块导入成功")
        return True
    except Exception as e:
        print(f"❌ tools模块导入失败: {str(e)}")
        return False


def test_utils_import():
    """测试工具函数是否可以导入"""
    print("\n" + "=" * 60)
    print("测试3: 导入工具函数")
    print("=" * 60)

    utils = ['chanlun_structure', 'chanlun_dynamics']
    success_count = 0

    for util_name in utils:
        try:
            __import__(f'utils.{util_name}')
            print(f"✅ utils.{util_name}: 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ utils.{util_name}: 导入失败 - {str(e)}")

    return success_count == len(utils)


def test_storage_import():
    """测试存储模块是否可以导入"""
    print("\n" + "=" * 60)
    print("测试4: 导入存储模块")
    print("=" * 60)

    try:
        from storage.memory.memory_saver import get_memory_saver
        print("✅ storage.memory.memory_saver: 导入成功")
        return True
    except Exception as e:
        print(f"❌ storage.memory.memory_saver: 导入失败 - {str(e)}")
        return False


def test_graphs_import():
    """测试工作流模块是否可以导入"""
    print("\n" + "=" * 60)
    print("测试5: 导入工作流模块")
    print("=" * 60)

    try:
        from graphs.chanlun_graph import ChanlunState
        print("✅ graphs.chanlun_graph: 导入成功")
        return True
    except Exception as e:
        print(f"❌ graphs.chanlun_graph: 导入失败 - {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "🎯" * 30)
    print("  缠论多智能体系统 - 部署验证测试")
    print("🎯" * 30 + "\n")

    results = {
        "智能体导入": test_imports(),
        "工具导入": test_tools_import(),
        "工具函数导入": test_utils_import(),
        "存储模块导入": test_storage_import(),
        "工作流模块导入": test_graphs_import()
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 所有测试通过！系统部署成功！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())
