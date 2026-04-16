"""
测试缠论结构分析和动力学分析算法
"""
import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.chanlun_structure import ChanLunAnalyzer
from utils.chanlun_dynamics import DynamicsAnalyzer


def generate_test_data(n=200):
    """生成测试用的K线数据"""
    np.random.seed(42)

    # 生成随机游走价格
    prices = []
    price = 50000

    for i in range(n):
        change = np.random.normal(0, 200)
        price += change

        # 生成OHLC
        high = price + abs(np.random.normal(0, 50))
        low = price - abs(np.random.normal(0, 50))
        close = price
        open_price = prices[-1]['close'] if prices else close

        prices.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': abs(np.random.normal(1000, 200))
        })

    df = pd.DataFrame(prices)
    return df


def test_structure_analysis():
    """测试结构分析算法"""
    print("=" * 80)
    print("测试结构分析算法")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)
    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print()

    # 创建分析器
    analyzer = ChanLunAnalyzer()

    # 识别分型
    fractals = analyzer.identify_fractals(df)
    print(f"✓ 识别分型: {len(fractals)} 个")
    print(f"  - 顶分型: {sum(1 for f in fractals if f.type.name == 'TOP')}")
    print(f"  - 底分型: {sum(1 for f in fractals if f.type.name == 'BOTTOM')}")
    print()

    # 识别笔
    bis = analyzer.identify_bis(df, fractals)
    print(f"✓ 识别笔: {len(bis)} 根")
    if bis:
        print(f"  - 向上笔: {sum(1 for b in bis if b.direction.name == 'UP')}")
        print(f"  - 向下笔: {sum(1 for b in bis if b.direction.name == 'DOWN')}")
        print(f"  - 最后一笔: {bis[-1].direction.name} ({bis[-1].start_price} -> {bis[-1].end_price})")
    print()

    # 识别线段
    segments = analyzer.identify_segments(bis)
    print(f"✓ 识别线段: {len(segments)} 条")
    if segments:
        print(f"  - 向上线段: {sum(1 for s in segments if s.direction.name == 'UP')}")
        print(f"  - 向下线段: {sum(1 for s in segments if s.direction.name == 'DOWN')}")
        print(f"  - 最后一条线段: {segments[-1].direction.name}")
        print(f"  - 包含笔数: {len(segments[-1].bi_list)}")
    print()

    # 识别中枢
    zhongshu_list = analyzer.identify_zhongshu(segments)
    print(f"✓ 识别中枢: {len(zhongshu_list)} 个")
    if zhongshu_list:
        latest = zhongshu_list[-1]
        print(f"  - 中枢区间: [{latest.low:.2f}, {latest.high:.2f}]")
        print(f"  - 中枢高点: {latest.high_point:.2f}")
        print(f"  - 中枢低点: {latest.low_point:.2f}")
        print(f"  - 包含线段数: {len(latest.segment_list)}")
    print()

    # 完整分析
    report = analyzer.analyze(df)
    print("✓ 完整分析报告:")
    print(f"  - K线数量: {report['kline_count']}")
    print(f"  - 分型数量: {report['fractals']['count']}")
    print(f"  - 笔数量: {report['bis']['count']}")
    print(f"  - 线段数量: {report['segments']['count']}")
    print(f"  - 中枢数量: {report['zhongshu']['count']}")
    print()

    return True


def test_dynamics_analysis():
    """测试动力学分析算法"""
    print("=" * 80)
    print("测试动力学分析算法")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)
    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print()

    # 创建分析器
    analyzer = DynamicsAnalyzer()

    # 计算MACD
    df_with_macd = analyzer.calculate_macd(df)
    print(f"✓ 计算MACD指标")
    print(f"  - DIF: {df_with_macd['dif'].iloc[-1]:.2f}")
    print(f"  - DEA: {df_with_macd['dea'].iloc[-1]:.2f}")
    print(f"  - MACD: {df_with_macd['macd'].iloc[-1]:.2f}")
    print()

    # 识别背驰
    divergences = analyzer.identify_divergence(df_with_macd)
    print(f"✓ 识别背驰: {len(divergences)} 个")
    if divergences:
        for i, div in enumerate(divergences[-3:]):  # 显示最近3个
            print(f"  - 背驰 {i+1}: {div.type.value} ({div.strength.value})")
            print(f"    价格: {div.start_price:.2f} -> {div.end_price:.2f}")
            print(f"    MACD面积: {div.macd_area:.2f}")
    print()

    # 分析动量
    momentum = analyzer.analyze_momentum(df_with_macd)
    print(f"✓ 分析市场动量")
    print(f"  - MACD状态: {momentum['macd_state']}")
    print(f"  - DIF趋势: {momentum['dif_trend']}")
    print(f"  - DEA趋势: {momentum['dea_trend']}")
    print(f"  - MACD趋势: {momentum['macd_trend']}")
    print(f"  - 力度: {momentum['strength']:.2f}")
    print(f"  - 交叉类型: {momentum['cross_type']}")
    print()

    # 完整分析
    report = analyzer.analyze(df)
    print("✓ 完整分析报告:")
    print(f"  - MACD状态: {report['macd']['macd_state']}")
    print(f"  - 力度: {report['macd']['strength']:.2f}")
    print(f"  - 背驰数量: {report['divergences']['count']}")
    print()

    return True


def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "缠论核心算法测试" + " " * 42 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # 测试结构分析
    try:
        success1 = test_structure_analysis()
    except Exception as e:
        print(f"✗ 结构分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success1 = False

    print()

    # 测试动力学分析
    try:
        success2 = test_dynamics_analysis()
    except Exception as e:
        print(f"✗ 动力学分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success2 = False

    print()
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"结构分析算法: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"动力学分析算法: {'✓ 通过' if success2 else '✗ 失败'}")
    print()
    print("=" * 80)

    return success1 and success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
