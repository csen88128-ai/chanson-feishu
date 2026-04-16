"""
快速功能测试 - 验证核心功能
"""
import sys
sys.path.insert(0, '/workspace/chanson-feishu/src')

def test_kline_data_tool():
    """测试K线数据获取工具"""
    print("=" * 60)
    print("测试1: K线数据获取工具")
    print("=" * 60)

    try:
        from tools.data_tools import get_kline_data
        result = get_kline_data("BTCUSDT", "1h", limit=10)
        if result and len(result) > 0:
            print(f"✅ 成功获取K线数据: {len(result)} 条")
            print(f"   最新价格: {result[-1]['close']}")
            return True
        else:
            print("❌ 未获取到K线数据")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_system_health_tool():
    """测试系统健康检查工具"""
    print("\n" + "=" * 60)
    print("测试2: 系统健康检查工具")
    print("=" * 60)

    try:
        from tools.monitor_tools import check_system_health
        result = check_system_health()
        if result:
            print(f"✅ 系统健康检查完成")
            print(f"   CPU使用率: {result.get('cpu_usage', 0)}%")
            print(f"   内存使用率: {result.get('memory_usage', 0)}%")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_structure_analysis():
    """测试结构分析功能"""
    print("\n" + "=" * 60)
    print("测试3: 结构分析功能")
    print("=" * 60)

    try:
        from tools.data_tools import get_kline_data
        from utils.chanlun_structure import ChanLunAnalyzer

        # 获取K线数据
        df = get_kline_data("BTCUSDT", "1h", limit=50)
        if df is None or len(df) == 0:
            print("❌ 无法获取K线数据")
            return False

        # 进行结构分析
        analyzer = ChanLunAnalyzer()
        bis = analyzer.identify_bi(df)

        if bis and len(bis) > 0:
            print(f"✅ 结构分析完成")
            print(f"   识别出 {len(bis)} 笔")
            return True
        else:
            print("❌ 未识别出笔结构")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_dynamics_analysis():
    """测试动力学分析功能"""
    print("\n" + "=" * 60)
    print("测试4: 动力学分析功能")
    print("=" * 60)

    try:
        from tools.data_tools import get_kline_data
        from utils.chanlun_dynamics import DynamicsAnalyzer

        # 获取K线数据
        df = get_kline_data("BTCUSDT", "1h", limit=50)
        if df is None or len(df) == 0:
            print("❌ 无法获取K线数据")
            return False

        # 进行动力学分析
        analyzer = DynamicsAnalyzer()
        momentum = analyzer.calculate_momentum(df)

        print(f"✅ 动力学分析完成")
        print(f"   最新动量: {momentum[-1] if momentum else 0:.4f}")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_building():
    """测试工作流构建"""
    print("\n" + "=" * 60)
    print("测试5: 工作流构建")
    print("=" * 60)

    try:
        from graphs.chanlun_graph import build_chanlun_workflow

        workflow = build_chanlun_workflow()

        if workflow:
            print(f"✅ 工作流构建成功")
            print(f"   工作流类型: {type(workflow).__name__}")
            return True
        else:
            print("❌ 工作流构建失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "🎯" * 30)
    print("  缠论多智能体系统 - 功能测试")
    print("🎯" * 30 + "\n")

    results = {
        "K线数据获取": test_kline_data_tool(),
        "系统健康检查": test_system_health_tool(),
        "结构分析": test_structure_analysis(),
        "动力学分析": test_dynamics_analysis(),
        "工作流构建": test_workflow_building()
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        if result:
            print(f"✅ {test_name}: 通过")
            passed += 1
        else:
            print(f"❌ {test_name}: 失败")
            failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("\n🎉 所有功能测试通过！系统运行正常！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
