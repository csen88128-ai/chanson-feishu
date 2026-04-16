"""
策略参数优化和回测系统
包含参数优化、回测系统增强、移动止损策略、绩效评估
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import itertools
import json
from datetime import datetime
from collections import defaultdict


class OptimizationMethod(Enum):
    """优化方法"""
    GRID_SEARCH = "grid_search"         # 网格搜索
    RANDOM_SEARCH = "random_search"     # 随机搜索
    BAYESIAN = "bayesian"              # 贝叶斯优化
    GENETIC = "genetic"                # 遗传算法


@dataclass
class StrategyParameter:
    """策略参数"""
    name: str                          # 参数名称
    min_value: float                   # 最小值
    max_value: float                   # 最大值
    step: float = 1.0                  # 步长
    value_type: str = "float"          # 值类型（float/int/bool）


@dataclass
class BacktestResult:
    """回测结果"""
    total_trades: int                  # 总交易次数
    winning_trades: int                # 盈利交易次数
    losing_trades: int                 # 亏损交易次数
    win_rate: float                    # 胜率
    total_return: float                # 总收益率
    annual_return: float               # 年化收益率
    max_drawdown: float                # 最大回撤
    sharpe_ratio: float                # 夏普比率
    sortino_ratio: float               # 索提诺比率
    avg_win: float                     # 平均盈利
    avg_loss: float                    # 平均亏损
    profit_factor: float               # 盈利因子
    total_pnl: float                   # 总盈亏
    max_consecutive_losses: int        # 最大连续亏损
    parameters: Dict[str, Any]         # 使用的参数
    equity_curve: List[float] = field(default_factory=list)  # 资金曲线


class StrategyOptimizer:
    """策略参数优化器"""

    def __init__(self, objective_func: Callable[[Dict], BacktestResult],
                 parameters: List[StrategyParameter],
                 optimization_method: OptimizationMethod = OptimizationMethod.GRID_SEARCH):
        """
        初始化策略优化器

        Args:
            objective_func: 目标函数（参数 -> 回测结果）
            parameters: 参数列表
            optimization_method: 优化方法
        """
        self.objective_func = objective_func
        self.parameters = parameters
        self.optimization_method = optimization_method
        self.best_result = None
        self.all_results = []

    def optimize(self, max_iterations: int = 100) -> BacktestResult:
        """
        执行优化

        Args:
            max_iterations: 最大迭代次数

        Returns:
            最优回测结果
        """
        if self.optimization_method == OptimizationMethod.GRID_SEARCH:
            return self._grid_search()
        elif self.optimization_method == OptimizationMethod.RANDOM_SEARCH:
            return self._random_search(max_iterations)
        elif self.optimization_method == OptimizationMethod.BAYESIAN:
            return self._bayesian_optimization(max_iterations)
        elif self.optimization_method == OptimizationMethod.GENETIC:
            return self._genetic_algorithm(max_iterations)
        else:
            raise ValueError(f"不支持的优化方法: {self.optimization_method}")

    def _grid_search(self) -> BacktestResult:
        """网格搜索"""
        # 生成所有参数组合
        param_grid = {}
        for param in self.parameters:
            if param.value_type == "float":
                values = np.arange(param.min_value, param.max_value + param.step, param.step)
            else:
                values = np.arange(int(param.min_value), int(param.max_value) + 1,
                                 int(param.step))
            param_grid[param.name] = values.tolist()

        # 生成所有组合
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))

        results = []

        for combo in combinations:
            params = dict(zip(keys, combo))
            result = self.objective_func(params)
            results.append(result)

        # 找出最优结果（使用夏普比率作为优化目标）
        best_result = max(results, key=lambda x: x.sharpe_ratio)
        self.best_result = best_result
        self.all_results = results

        return best_result

    def _random_search(self, max_iterations: int) -> BacktestResult:
        """随机搜索"""
        results = []

        for _ in range(max_iterations):
            params = {}
            for param in self.parameters:
                if param.value_type == "float":
                    params[param.name] = np.random.uniform(param.min_value, param.max_value)
                else:
                    params[param.name] = np.random.randint(param.min_value, param.max_value + 1)

            result = self.objective_func(params)
            results.append(result)

        # 找出最优结果
        best_result = max(results, key=lambda x: x.sharpe_ratio)
        self.best_result = best_result
        self.all_results = results

        return best_result

    def _bayesian_optimization(self, max_iterations: int) -> BacktestResult:
        """贝叶斯优化（简化版）"""
        # 这里实现一个简化版的贝叶斯优化
        # 实际应用中可以使用scikit-optimize或optuna等库

        results = []

        # 初始随机采样
        for _ in range(min(10, max_iterations)):
            params = {}
            for param in self.parameters:
                if param.value_type == "float":
                    params[param.name] = np.random.uniform(param.min_value, param.max_value)
                else:
                    params[param.name] = np.random.randint(param.min_value, param.max_value + 1)

            result = self.objective_func(params)
            results.append(result)

        # 基于已有结果进行采样（简化版：采样最优结果附近的参数）
        remaining_iterations = max_iterations - len(results)
        if remaining_iterations > 0 and results:
            best_result = max(results, key=lambda x: x.sharpe_ratio)

            for _ in range(remaining_iterations):
                params = {}
                for param in self.parameters:
                    if param.value_type == "float":
                        # 在最优参数附近采样
                        best_value = best_result.parameters.get(param.name,
                                                             (param.min_value + param.max_value) / 2)
                        noise = np.random.normal(0, (param.max_value - param.min_value) * 0.1)
                        params[param.name] = np.clip(best_value + noise,
                                                    param.min_value, param.max_value)
                    else:
                        best_value = best_result.parameters.get(param.name,
                                                             int((param.min_value + param.max_value) / 2))
                        noise = np.random.randint(-2, 3)
                        params[param.name] = np.clip(best_value + noise,
                                                    param.min_value, param.max_value)

                result = self.objective_func(params)
                results.append(result)

        # 找出最优结果
        best_result = max(results, key=lambda x: x.sharpe_ratio)
        self.best_result = best_result
        self.all_results = results

        return best_result

    def _genetic_algorithm(self, max_iterations: int) -> BacktestResult:
        """遗传算法（简化版）"""
        # 初始化种群
        population_size = 20
        population = []

        for _ in range(population_size):
            params = {}
            for param in self.parameters:
                if param.value_type == "float":
                    params[param.name] = np.random.uniform(param.min_value, param.max_value)
                else:
                    params[param.name] = np.random.randint(param.min_value, param.max_value + 1)
            population.append(params)

        results = []

        for generation in range(max_iterations):
            # 评估种群
            generation_results = []
            for params in population:
                result = self.objective_func(params)
                generation_results.append(result)
                results.append(result)

            # 选择（锦标赛选择）
            selected = []
            for _ in range(population_size // 2):
                tournament = np.random.choice(generation_results, 3)
                winner = max(tournament, key=lambda x: x.sharpe_ratio)
                selected.append(winner.parameters)

            # 交叉
            offspring = []
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    parent1 = selected[i]
                    parent2 = selected[i + 1]
                    child1, child2 = self._crossover(parent1, parent2)
                    offspring.extend([child1, child2])

            # 变异
            for child in offspring:
                self._mutate(child)

            # 生成新一代种群
            elite_size = 2
            elite = sorted(generation_results, key=lambda x: x.sharpe_ratio, reverse=True)[:elite_size]
            population = [elite[i].parameters for i in range(elite_size)] + offspring

            # 补足种群数量
            while len(population) < population_size:
                params = {}
                for param in self.parameters:
                    if param.value_type == "float":
                        params[param.name] = np.random.uniform(param.min_value, param.max_value)
                    else:
                        params[param.name] = np.random.randint(param.min_value, param.max_value + 1)
                population.append(params)

        # 找出最优结果
        best_result = max(results, key=lambda x: x.sharpe_ratio)
        self.best_result = best_result
        self.all_results = results

        return best_result

    def _crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """交叉操作"""
        child1 = {}
        child2 = {}

        for param in self.parameters:
            if np.random.random() < 0.5:
                child1[param.name] = parent1[param.name]
                child2[param.name] = parent2[param.name]
            else:
                child1[param.name] = parent2[param.name]
                child2[param.name] = parent1[param.name]

        return child1, child2

    def _mutate(self, individual: Dict):
        """变异操作"""
        for param in self.parameters:
            if np.random.random() < 0.1:  # 10%的变异概率
                if param.value_type == "float":
                    individual[param.name] = np.random.uniform(param.min_value, param.max_value)
                else:
                    individual[param.name] = np.random.randint(param.min_value, param.max_value + 1)


class EnhancedBacktester:
    """增强版回测系统"""

    def __init__(self, initial_capital: float = 100000):
        """
        初始化回测系统

        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = [initial_capital]

    def run_backtest(self, df: pd.DataFrame,
                    signal_generator: Callable,
                    strategy_params: Dict = None,
                    position_size: float = 0.1,
                    use_trailing_stop: bool = False,
                    trailing_stop_pct: float = 0.05) -> BacktestResult:
        """
        运行回测

        Args:
            df: K线数据
            signal_generator: 信号生成函数
            strategy_params: 策略参数
            position_size: 仓位大小
            use_trailing_stop: 是否使用移动止损
            trailing_stop_pct: 移动止损百分比

        Returns:
            回测结果
        """
        if strategy_params is None:
            strategy_params = {}

        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = [self.initial_capital]

        for i in range(len(df)):
            current_price = df.iloc[i]['close']
            current_time = df.iloc[i]['timestamp']

            # 生成交易信号
            signal = signal_generator(df[:i+1], strategy_params)

            # 处理现有持仓
            self._manage_positions(current_price, current_time, use_trailing_stop, trailing_stop_pct)

            # 处理新信号
            if signal['action'] == 'buy' and not self.positions:
                # 开多仓
                position_value = self.current_capital * position_size
                quantity = position_value / current_price
                stop_loss = current_price * 0.97  # 3%止损

                position = {
                    'type': 'long',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'highest_price': current_price,  # 用于移动止损
                    'entry_time': current_time
                }
                self.positions.append(position)

            elif signal['action'] == 'sell' and not self.positions:
                # 开空仓
                position_value = self.current_capital * position_size
                quantity = position_value / current_price
                stop_loss = current_price * 1.03  # 3%止损

                position = {
                    'type': 'short',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'lowest_price': current_price,  # 用于移动止损
                    'entry_time': current_time
                }
                self.positions.append(position)

            elif signal['action'] == 'close':
                # 平仓
                self._close_all_positions(current_price, current_time)

            # 更新资金曲线
            total_value = self.current_capital
            for pos in self.positions:
                if pos['type'] == 'long':
                    pnl = (current_price - pos['entry_price']) * pos['quantity']
                else:
                    pnl = (pos['entry_price'] - current_price) * pos['quantity']
                total_value += pnl

            self.equity_curve.append(total_value)

        # 平仓所有剩余持仓
        if self.positions:
            final_price = df.iloc[-1]['close']
            final_time = df.iloc[-1]['timestamp']
            self._close_all_positions(final_price, final_time)

        # 计算回测结果
        result = self._calculate_backtest_result(strategy_params)

        return result

    def _manage_positions(self, current_price: float, current_time: str,
                         use_trailing_stop: bool, trailing_stop_pct: float):
        """管理持仓"""
        for pos in self.positions[:]:  # 复制列表以避免修改时的迭代问题
            # 检查止损
            if pos['type'] == 'long':
                if current_price <= pos['stop_loss']:
                    self._close_position(pos, current_price, current_time, reason='stop_loss')
                else:
                    # 更新移动止损
                    if use_trailing_stop and current_price > pos['highest_price']:
                        pos['highest_price'] = current_price
                        pos['stop_loss'] = current_price * (1 - trailing_stop_pct)
            else:
                if current_price >= pos['stop_loss']:
                    self._close_position(pos, current_price, current_time, reason='stop_loss')
                else:
                    # 更新移动止损
                    if use_trailing_stop and current_price < pos['lowest_price']:
                        pos['lowest_price'] = current_price
                        pos['stop_loss'] = current_price * (1 + trailing_stop_pct)

    def _close_all_positions(self, current_price: float, current_time: str):
        """平仓所有持仓"""
        for pos in self.positions[:]:
            self._close_position(pos, current_price, current_time, reason='signal')

    def _close_position(self, position: Dict, current_price: float,
                       current_time: str, reason: str):
        """平仓"""
        if position['type'] == 'long':
            pnl = (current_price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - current_price) * position['quantity']

        self.current_capital += pnl

        trade = {
            'type': position['type'],
            'entry_price': position['entry_price'],
            'exit_price': current_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'entry_time': position['entry_time'],
            'exit_time': current_time,
            'reason': reason
        }

        self.trades.append(trade)
        self.positions.remove(position)

    def _calculate_backtest_result(self, strategy_params: Dict) -> BacktestResult:
        """计算回测结果"""
        if not self.trades:
            return BacktestResult(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_return=0.0,
                annual_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                total_pnl=0.0,
                max_consecutive_losses=0,
                parameters=strategy_params,
                equity_curve=self.equity_curve
            )

        # 基本统计
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if t['pnl'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # 盈亏统计
        wins = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trades if t['pnl'] <= 0]

        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0

        total_pnl = sum(t['pnl'] for t in self.trades)
        total_wins = sum(wins)
        total_losses = abs(sum(losses))

        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        # 收益率
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital

        # 计算最大回撤
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = abs(drawdown.min())

        # 计算夏普比率（简化版）
        returns = np.diff(equity_array) / equity_array[:-1]
        returns = returns[~np.isnan(returns)]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0.0

        # 计算索提诺比率（简化版）
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-6
        sortino_ratio = np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0.0

        # 年化收益率（假设回测期为1年）
        annual_return = total_return

        # 最大连续亏损
        max_consecutive_losses = 0
        current_consecutive_losses = 0
        for t in self.trades:
            if t['pnl'] <= 0:
                current_consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
            else:
                current_consecutive_losses = 0

        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            max_consecutive_losses=max_consecutive_losses,
            parameters=strategy_params,
            equity_curve=self.equity_curve
        )


# 快捷函数
def optimize_strategy(objective_func: Callable[[Dict], BacktestResult],
                     parameters: List[StrategyParameter],
                     method: str = "grid_search",
                     max_iterations: int = 100) -> BacktestResult:
    """快捷函数：策略参数优化"""
    opt_method = OptimizationMethod(method)
    optimizer = StrategyOptimizer(objective_func, parameters, opt_method)
    return optimizer.optimize(max_iterations)


def run_backtest(df: pd.DataFrame, signal_generator: Callable,
                 strategy_params: Dict = None,
                 initial_capital: float = 100000,
                 position_size: float = 0.1,
                 use_trailing_stop: bool = False,
                 trailing_stop_pct: float = 0.05) -> BacktestResult:
    """快捷函数：运行回测"""
    backtester = EnhancedBacktester(initial_capital)
    return backtester.run_backtest(df, signal_generator, strategy_params,
                                   position_size, use_trailing_stop, trailing_stop_pct)
