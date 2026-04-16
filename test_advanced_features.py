"""
测试高级功能
测试策略参数优化、回测系统、移动止损、绩效评估
"""
import sys
import os
import pandas as pd
import numpy as np
from typing import Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.strategy_optimization import (
    StrategyOptimizer,
    EnhancedBacktester,
    OptimizationMethod,
    StrategyParameter,
    BacktestResult,
    optimize_strategy,
    run_backtest
)


def generate_test_data(n=500):
    """生成测试K线数据"""
    np.random.seed(42)

    data = []
    price = 50000

    for i in range(n):
        # 生成带趋势的价格
        trend = np.sin(i / 50) * 1000 + i * 5  # 上升趋势 + 周期性波动
        noise = np.random.normal(0, 200)
        price += trend * 0.02 + noise

        price = max(price, 1000)

        high = price + abs(np.random.normal(0, 100))
        low = price - abs(np.random.normal(0, 100))
        close = price
        open_price = data[-1]['open'] if data else close

        volume = abs(np.random.normal(2000, 500))

        data.append({
            'timestamp': f"2026-04-16 {i:02d}:00:00",
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return pd.DataFrame(data)


def simple_moving_average_signal(df: pd.DataFrame, params: Dict) -> Dict:
    """
    简单的移动平均线信号生成器

    Args:
        df: K线数据
        params: 策略参数（short_ma, long_ma）

    Returns:
        交易信号
    """
    if len(df) < params['long_ma']:
        return {'action': 'hold'}

    # 计算移动平均线
    df = df.copy()
    df['short_ma'] = df['close'].rolling(window=params['short_ma']).mean()
    df['long_ma'] = df['close'].rolling(window=params['long_ma']).mean()

    # 检查是否有信号
    if df['short_ma'].iloc[-2] < df['long_ma'].iloc[-2] and df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
        return {'action': 'buy', 'reason': 'golden_cross'}
    elif df['short_ma'].iloc[-2] > df['long_ma'].iloc[-2] and df['short_ma'].iloc[-1] < df['long_ma'].iloc[-1]:
        return {'action': 'sell', 'reason': 'death_cross'}
    else:
        return {'action': 'hold'}


def test_backtest_system():
    """测试回测系统"""
    print("=" * 80)
    print("测试回测系统")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(500)
    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print()

    # 运行回测
    strategy_params = {
        'short_ma': 10,
        'long_ma': 30
    }

    backtester = EnhancedBacktester(initial_capital=100000)
    result = backtester.run_backtest(
        df=df,
        signal_generator=simple_moving_average_signal,
        strategy_params=strategy_params,
        position_size=0.2,
        use_trailing_stop=False
    )

    print(f"✓ 回测结果:")
    print(f"  - 总交易次数: {result.total_trades}")
    print(f"  - 盈利交易: {result.winning_trades}")
    print(f"  - 亏损交易: {result.losing_trades}")
    print(f"  - 胜率: {result.win_rate * 100:.2f}%")
    print(f"  - 总收益率: {result.total_return * 100:.2f}%")
    print(f"  - 年化收益率: {result.annual_return * 100:.2f}%")
    print(f"  - 最大回撤: {result.max_drawdown * 100:.2f}%")
    print(f"  - 夏普比率: {result.sharpe_ratio:.2f}")
    print(f"  - 索提诺比率: {result.sortino_ratio:.2f}")
    print(f"  - 平均盈利: ${result.avg_win:.2f}")
    print(f"  - 平均亏损: ${result.avg_loss:.2f}")
    print(f"  - 盈利因子: {result.profit_factor:.2f}")
    print(f"  - 总盈亏: ${result.total_pnl:.2f}")
    print(f"  - 最大连续亏损: {result.max_consecutive_losses}次")
    print()

    return True


def test_trailing_stop():
    """测试移动止损"""
    print("=" * 80)
    print("测试移动止损")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(500)

    # 测试带移动止损的回测
    strategy_params = {
        'short_ma': 10,
        'long_ma': 30
    }

    backtester = EnhancedBacktester(initial_capital=100000)
    result_without_trailing = backtester.run_backtest(
        df=df,
        signal_generator=simple_moving_average_signal,
        strategy_params=strategy_params,
        position_size=0.2,
        use_trailing_stop=False
    )

    backtester2 = EnhancedBacktester(initial_capital=100000)
    result_with_trailing = backtester2.run_backtest(
        df=df,
        signal_generator=simple_moving_average_signal,
        strategy_params=strategy_params,
        position_size=0.2,
        use_trailing_stop=True,
        trailing_stop_pct=0.05
    )

    print(f"✓ 移动止损对比:")
    print()
    print(f"  无移动止损:")
    print(f"    - 总收益率: {result_without_trailing.total_return * 100:.2f}%")
    print(f"    - 最大回撤: {result_without_trailing.max_drawdown * 100:.2f}%")
    print(f"    - 夏普比率: {result_without_trailing.sharpe_ratio:.2f}")
    print()
    print(f"  有移动止损:")
    print(f"    - 总收益率: {result_with_trailing.total_return * 100:.2f}%")
    print(f"    - 最大回撤: {result_with_trailing.max_drawdown * 100:.2f}%")
    print(f"    - 夏普比率: {result_with_trailing.sharpe_ratio:.2f}")
    print()

    # 对比分析
    if result_with_trailing.max_drawdown < result_without_trailing.max_drawdown:
        print(f"  ✓ 移动止损有效降低回撤: {result_without_trailing.max_drawdown * 100:.2f}% -> {result_with_trailing.max_drawdown * 100:.2f}%")

    if result_with_trailing.sharpe_ratio > result_without_trailing.sharpe_ratio:
        print(f"  ✓ 移动止损提高夏普比率: {result_without_trailing.sharpe_ratio:.2f} -> {result_with_trailing.sharpe_ratio:.2f}")

    print()

    return True


def test_grid_search_optimization():
    """测试网格搜索优化"""
    print("=" * 80)
    print("测试网格搜索优化")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(500)
    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print()

    # 定义参数空间
    parameters = [
        StrategyParameter('short_ma', 5, 20, 5, 'int'),
        StrategyParameter('long_ma', 20, 60, 10, 'int')
    ]

    # 定义目标函数
    def objective_func(params):
        backtester = EnhancedBacktester(initial_capital=100000)
        result = backtester.run_backtest(
            df=df,
            signal_generator=simple_moving_average_signal,
            strategy_params=params,
            position_size=0.2
        )
        return result

    # 执行网格搜索优化
    optimizer = StrategyOptimizer(
        objective_func=objective_func,
        parameters=parameters,
        optimization_method=OptimizationMethod.GRID_SEARCH
    )

    best_result = optimizer.optimize()

    print(f"✓ 网格搜索优化结果:")
    print(f"  - 最优参数: {best_result.parameters}")
    print(f"  - 总收益率: {best_result.total_return * 100:.2f}%")
    print(f"  - 夏普比率: {best_result.sharpe_ratio:.2f}")
    print(f"  - 最大回撤: {best_result.max_drawdown * 100:.2f}%")
    print(f"  - 胜率: {best_result.win_rate * 100:.2f}%")
    print()
    print(f"  - 测试参数组合数: {len(optimizer.all_results)}")

    # 显示前3个结果
    top_results = sorted(optimizer.all_results, key=lambda x: x.sharpe_ratio, reverse=True)[:3]
    print(f"  - 前3个最佳结果:")
    for i, r in enumerate(top_results, 1):
        print(f"    {i}. 参数: {r.parameters}, 夏普比率: {r.sharpe_ratio:.2f}, 收益率: {r.total_return * 100:.2f}%")
    print()

    return True


def test_random_search_optimization():
    """测试随机搜索优化"""
    print("=" * 80)
    print("测试随机搜索优化")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(500)

    # 定义参数空间
    parameters = [
        StrategyParameter('short_ma', 5, 20, 1, 'int'),
        StrategyParameter('long_ma', 20, 60, 1, 'int')
    ]

    # 定义目标函数
    def objective_func(params):
        backtester = EnhancedBacktester(initial_capital=100000)
        result = backtester.run_backtest(
            df=df,
            signal_generator=simple_moving_average_signal,
            strategy_params=params,
            position_size=0.2
        )
        return result

    # 执行随机搜索优化
    optimizer = StrategyOptimizer(
        objective_func=objective_func,
        parameters=parameters,
        optimization_method=OptimizationMethod.RANDOM_SEARCH
    )

    best_result = optimizer.optimize(max_iterations=20)

    print(f"✓ 随机搜索优化结果:")
    print(f"  - 最优参数: {best_result.parameters}")
    print(f"  - 总收益率: {best_result.total_return * 100:.2f}%")
    print(f"  - 夏普比率: {best_result.sharpe_ratio:.2f}")
    print(f"  - 最大回撤: {best_result.max_drawdown * 100:.2f}%")
    print(f"  - 胜率: {best_result.win_rate * 100:.2f}%")
    print(f"  - 迭代次数: {len(optimizer.all_results)}")
    print()

    return True


def test_performance_evaluation():
    """测试绩效评估"""
    print("=" * 80)
    print("测试绩效评估")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(500)

    # 测试不同策略参数
    param_sets = [
        {'short_ma': 5, 'long_ma': 20},
        {'short_ma': 10, 'long_ma': 30},
        {'short_ma': 15, 'long_ma': 40},
    ]

    results = []
    for params in param_sets:
        backtester = EnhancedBacktester(initial_capital=100000)
        result = backtester.run_backtest(
            df=df,
            signal_generator=simple_moving_average_signal,
            strategy_params=params,
            position_size=0.2,
            use_trailing_stop=True
        )
        results.append(result)

    print(f"✓ 策略参数对比:")
    print()
    print(f"  {'参数':<30} {'收益率':<12} {'夏普比率':<10} {'最大回撤':<12} {'胜率':<10}")
    print(f"  {'-' * 80}")
    for i, (params, result) in enumerate(zip(param_sets, results), 1):
        param_str = f"MA({params['short_ma']}, {params['long_ma']})"
        print(f"  {param_str:<30} {result.total_return * 100:>10.2f}% {result.sharpe_ratio:>9.2f} {result.max_drawdown * 100:>10.2f}% {result.win_rate * 100:>8.2f}%")

    # 找出最佳策略
    best_strategy = max(results, key=lambda x: x.sharpe_ratio)
    print()
    print(f"  ✓ 最佳策略: {best_strategy.parameters}")
    print(f"    - 夏普比率: {best_strategy.sharpe_ratio:.2f}")
    print(f"    - 总收益率: {best_strategy.total_return * 100:.2f}%")
    print(f"    - 最大回撤: {best_strategy.max_drawdown * 100:.2f}%")
    print()

    return True


def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 28 + "高级功能测试" + " " * 41 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # 测试回测系统
    try:
        success1 = test_backtest_system()
    except Exception as e:
        print(f"✗ 回测系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success1 = False

    print()

    # 测试移动止损
    try:
        success2 = test_trailing_stop()
    except Exception as e:
        print(f"✗ 移动止损测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success2 = False

    print()

    # 测试网格搜索优化
    try:
        success3 = test_grid_search_optimization()
    except Exception as e:
        print(f"✗ 网格搜索优化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success3 = False

    print()

    # 测试随机搜索优化
    try:
        success4 = test_random_search_optimization()
    except Exception as e:
        print(f"✗ 随机搜索优化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success4 = False

    print()

    # 测试绩效评估
    try:
        success5 = test_performance_evaluation()
    except Exception as e:
        print(f"✗ 绩效评估测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success5 = False

    print()
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"回测系统: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"移动止损: {'✓ 通过' if success2 else '✗ 失败'}")
    print(f"网格搜索优化: {'✓ 通过' if success3 else '✗ 失败'}")
    print(f"随机搜索优化: {'✓ 通过' if success4 else '✗ 失败'}")
    print(f"绩效评估: {'✓ 通过' if success5 else '✗ 失败'}")
    print()
    print("=" * 80)

    return success1 and success2 and success3 and success4 and success5


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
