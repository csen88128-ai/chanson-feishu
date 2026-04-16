"""
风控管理工具
提供止损计算、仓位管理、回撤监控等风控功能
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SignalType(Enum):
    """信号类型"""
    FIRST_BUY = "first_buy"      # 第一类买点
    SECOND_BUY = "second_buy"    # 第二类买点
    THIRD_BUY = "third_buy"      # 第三类买点
    FIRST_SELL = "first_sell"    # 第一类卖点
    SECOND_SELL = "second_sell"  # 第二类卖点
    THIRD_SELL = "third_sell"    # 第三类卖点


class RiskParameters:
    """风控参数"""

    def __init__(self):
        # 仓位管理
        self.max_position_size = 0.3           # 单个品种最大仓位（占总资金比例）
        self.max_total_position = 0.8          # 总最大仓位
        self.min_position_size = 0.05          # 最小仓位

        # 止损管理
        self.max_loss_per_trade = 0.02         # 单笔交易最大亏损（占总资金比例）
        self.max_drawdown = 0.15               # 最大回撤（占总资金比例）
        self.daily_loss_limit = 0.05           # 单日最大亏损
        self.default_stop_loss_pct = 0.03      # 默认止损百分比
        self.trailing_stop_pct = 0.05          # 移动止损百分比

        # 止盈管理
        self.default_take_profit_pct = 0.06    # 默认止盈百分比
        self.partial_take_profit = [0.03, 0.05]  # 分批止盈点位

        # 风险限制
        self.max_consecutive_losses = 5        # 最大连续亏损次数
        self.max_trades_per_day = 10           # 单日最大交易次数
        self.min_win_rate = 0.45               # 最低胜率要求

        # 置信度调整
        self.confidence_adjustment = {
            "high": 1.2,      # 高置信度增加仓位
            "medium": 1.0,    # 中等置信度标准仓位
            "low": 0.5        # 低置信度降低仓位
        }


class RiskManager:
    """风控管理器"""

    def __init__(self, parameters: RiskParameters = None):
        """
        初始化风控管理器

        Args:
            parameters: 风控参数
        """
        self.parameters = parameters or RiskParameters()
        self.trades_today = []          # 今日交易记录
        self.consecutive_losses = 0      # 连续亏损次数
        self.total_pnl = 0.0             # 总盈亏
        self.peak_balance = 0.0          # 账户峰值
        self.current_balance = 0.0       # 当前余额
        self.cooling_mode = False        # 冷却模式

    def calculate_position_size(self, account_balance: float, entry_price: float,
                                stop_loss: float, confidence: float = 0.7) -> Tuple[float, float, float]:
        """
        计算仓位大小

        Args:
            account_balance: 账户余额
            entry_price: 入场价格
            stop_loss: 止损价格
            confidence: 置信度 (0-1)

        Returns:
            (仓位大小, 风险金额, 止损百分比)
        """
        # 计算止损百分比
        if stop_loss and stop_loss > 0:
            stop_loss_pct = abs(entry_price - stop_loss) / entry_price
        else:
            stop_loss_pct = self.parameters.default_stop_loss_pct

        # 计算风险金额（单笔最大亏损）
        risk_amount = account_balance * self.parameters.max_loss_per_trade

        # 计算基础仓位
        if stop_loss_pct > 0:
            base_position_size = risk_amount / (entry_price * stop_loss_pct)
        else:
            base_position_size = 0

        # 根据置信度调整仓位
        confidence_level = self._get_confidence_level(confidence)
        adjustment_factor = self.parameters.confidence_adjustment.get(confidence_level, 1.0)
        adjusted_position_size = base_position_size * adjustment_factor

        # 限制在最大仓位范围内
        max_position_value = account_balance * self.parameters.max_position_size
        max_position_size = max_position_value / entry_price

        final_position_size = min(adjusted_position_size, max_position_size)

        # 确保不低于最小仓位
        min_position_size = (account_balance * self.parameters.min_position_size) / entry_price
        if final_position_size < min_position_size:
            final_position_size = min_position_size

        actual_risk_amount = final_position_size * entry_price * stop_loss_pct

        return round(final_position_size, 6), round(actual_risk_amount, 2), round(stop_loss_pct * 100, 2)

    def _get_confidence_level(self, confidence: float) -> str:
        """
        获取置信度等级

        Args:
            confidence: 置信度 (0-1)

        Returns:
            置信度等级
        """
        if confidence >= 0.75:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def calculate_stop_loss(self, entry_price: float, direction: str,
                           atr: float = None, support_level: float = None,
                           resistance_level: float = None) -> float:
        """
        计算止损价格

        Args:
            entry_price: 入场价格
            direction: 方向 (long/short)
            atr: 平均真实波幅
            support_level: 支撑位
            resistance_level: 阻力位

        Returns:
            止损价格
        """
        default_stop_loss_pct = self.parameters.default_stop_loss_pct

        if direction == "long":
            # 多头止损
            if support_level and support_level < entry_price:
                # 使用支撑位作为止损
                stop_loss = support_level * 0.998  # 支撑位下方0.2%
            elif atr:
                # 使用ATR作为止损
                stop_loss = entry_price - (atr * 1.5)
            else:
                # 使用固定百分比止损
                stop_loss = entry_price * (1 - default_stop_loss_pct)
        else:
            # 空头止损
            if resistance_level and resistance_level > entry_price:
                # 使用阻力位作为止损
                stop_loss = resistance_level * 1.002  # 阻力位上方0.2%
            elif atr:
                # 使用ATR作为止损
                stop_loss = entry_price + (atr * 1.5)
            else:
                # 使用固定百分比止损
                stop_loss = entry_price * (1 + default_stop_loss_pct)

        return round(stop_loss, 2)

    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                             direction: str) -> List[float]:
        """
        计算止盈价格

        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            direction: 方向 (long/short)

        Returns:
            止盈价格列表
        """
        # 计算风险回报比
        risk = abs(entry_price - stop_loss)

        if direction == "long":
            # 多头止盈
            take_profits = [
                entry_price + risk * 2,   # 1:2 风险回报
                entry_price + risk * 3,   # 1:3 风险回报
                entry_price + risk * 5    # 1:5 风险回报
            ]
        else:
            # 空头止盈
            take_profits = [
                entry_price - risk * 2,
                entry_price - risk * 3,
                entry_price - risk * 5
            ]

        return [round(tp, 2) for tp in take_profits]

    def check_risk_limits(self, decision: Dict[str, Any],
                         account_balance: float) -> Tuple[bool, str]:
        """
        检查风险限制

        Args:
            decision: 交易决策
            account_balance: 账户余额

        Returns:
            (是否通过, 原因)
        """
        # 检查冷却模式
        if self.cooling_mode:
            return False, "系统处于冷却模式，暂停交易"

        # 检查最大回撤
        drawdown_pct = self._calculate_drawdown_pct()
        if drawdown_pct > self.parameters.max_drawdown:
            self.cooling_mode = True
            return False, f"超过最大回撤限制 {self.parameters.max_drawdown * 100}%，触发冷却"

        # 检查连续亏损
        if self.consecutive_losses >= self.parameters.max_consecutive_losses:
            self.cooling_mode = True
            return False, f"连续亏损 {self.consecutive_losses} 次，触发冷却"

        # 检查单日交易次数
        if len(self.trades_today) >= self.parameters.max_trades_per_day:
            return False, f"今日交易次数已达上限 {self.parameters.max_trades_per_day}"

        # 检查单日亏损
        daily_pnl = sum(t.get("pnl", 0) for t in self.trades_today if t.get("pnl", 0) < 0)
        if abs(daily_pnl) > account_balance * self.parameters.daily_loss_limit:
            return False, f"今日亏损超过限制 {self.parameters.daily_loss_limit * 100}%"

        # 检查置信度
        confidence = decision.get("confidence", 0)
        if confidence < 0.5:
            return False, f"置信度过低 {confidence * 100}%，拒绝交易"

        # 检查风险等级
        risk_level = decision.get("risk_level", "medium")
        if risk_level == "high" and self.consecutive_losses > 2:
            return False, "高风险信号 + 连续亏损，拒绝交易"

        return True, "通过风控检查"

    def _calculate_drawdown_pct(self) -> float:
        """
        计算回撤百分比

        Returns:
            回撤百分比
        """
        if self.peak_balance == 0:
            return 0.0

        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        return round(drawdown, 4)

    def calculate_risk_score(self, decision: Dict[str, Any],
                            market_data: Dict[str, Any]) -> float:
        """
        计算风险评分（0-100，分数越高风险越大）

        Args:
            decision: 交易决策
            market_data: 市场数据

        Returns:
            风险评分
        """
        score = 0

        # 1. 置信度评分（低置信度 = 高风险）
        confidence = decision.get("confidence", 0.7)
        score += (1 - confidence) * 30

        # 2. 风险等级评分
        risk_level = decision.get("risk_level", "medium")
        risk_level_scores = {"low": 0, "medium": 15, "high": 30}
        score += risk_level_scores.get(risk_level, 15)

        # 3. 连续亏损评分
        score += min(self.consecutive_losses * 5, 20)

        # 4. 回撤评分
        drawdown_pct = self._calculate_drawdown_pct()
        score += min(drawdown_pct * 100, 20)

        # 5. 市场情绪评分
        fear_greed_index = market_data.get("fear_greed_index", 50)
        if fear_greed_index < 20 or fear_greed_index > 80:
            score += 10  # 极端情绪增加风险

        return min(int(score), 100)

    def record_trade(self, trade: Dict[str, Any]):
        """
        记录交易

        Args:
            trade: 交易记录
        """
        self.trades_today.append(trade)

        pnl = trade.get("pnl", 0)
        self.total_pnl += pnl
        self.current_balance += pnl

        # 更新峰值
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        # 更新连续亏损次数
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        logger.info(f"记录交易: {trade.get('symbol', 'N/A')} PnL: {pnl}, 连续亏损: {self.consecutive_losses}")

    def get_risk_report(self) -> Dict[str, Any]:
        """
        获取风控报告

        Returns:
            风控报告
        """
        return {
            "account_balance": round(self.current_balance, 2),
            "peak_balance": round(self.peak_balance, 2),
            "total_pnl": round(self.total_pnl, 2),
            "drawdown_pct": round(self._calculate_drawdown_pct() * 100, 2),
            "consecutive_losses": self.consecutive_losses,
            "trades_today": len(self.trades_today),
            "cooling_mode": self.cooling_mode,
            "daily_pnl": round(sum(t.get("pnl", 0) for t in self.trades_today), 2)
        }


# 创建全局风控管理器实例
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """
    获取风控管理器实例

    Returns:
        风控管理器实例
    """
    global _risk_manager

    if _risk_manager is None:
        _risk_manager = RiskManager()

    return _risk_manager


def calculate_risk_metrics(account_balance: float, entry_price: float,
                          stop_loss: float, direction: str,
                          confidence: float = 0.7) -> str:
    """
    计算风险指标

    Args:
        account_balance: 账户余额
        entry_price: 入场价格
        stop_loss: 止损价格
        direction: 方向
        confidence: 置信度

    Returns:
        风险指标报告
    """
    risk_manager = get_risk_manager()

    # 计算仓位大小
    position_size, risk_amount, stop_loss_pct = risk_manager.calculate_position_size(
        account_balance, entry_price, stop_loss, confidence
    )

    # 计算止盈价格
    take_profits = risk_manager.calculate_take_profit(entry_price, stop_loss, direction)

    # 计算风险回报比
    risk = abs(entry_price - stop_loss)
    risk_reward_ratios = [
        round((tp - entry_price) / risk if direction == "long" else (entry_price - tp) / risk, 2)
        for tp in take_profits
    ]

    report = f"""
风控指标计算结果：

仓位管理：
- 账户余额: ${account_balance:,.2f}
- 建议仓位: {position_size} BTC
- 仓位价值: ${position_size * entry_price:,.2f}
- 仓位占比: {position_size * entry_price / account_balance * 100:.2f}%
- 风险金额: ${risk_amount:,.2f}

止损管理：
- 入场价格: ${entry_price:,.2f}
- 止损价格: ${stop_loss:,.2f}
- 止损幅度: {stop_loss_pct}%

止盈管理：
- 止盈1: ${take_profits[0]:,.2f} (风险回报比 1:{risk_reward_ratios[0]})
- 止盈2: ${take_profits[1]:,.2f} (风险回报比 1:{risk_reward_ratios[1]})
- 止盈3: ${take_profits[2]:,.2f} (风险回报比 1:{risk_reward_ratios[2]})

置信度调整：
- 置信度: {confidence * 100}%
- 调整后仓位: {position_size} BTC
"""

    return report


def check_position_risk(account_balance: float, position_size: float,
                       entry_price: float, current_price: float,
                       stop_loss: float) -> str:
    """
    检查持仓风险

    Args:
        account_balance: 账户余额
        position_size: 持仓大小
        entry_price: 入场价格
        current_price: 当前价格
        stop_loss: 止损价格

    Returns:
        风险检查报告
    """
    position_value = position_size * current_price
    position_pct = position_value / account_balance * 100

    if current_price >= entry_price:
        pnl = (current_price - entry_price) * position_size
        pnl_pct = (current_price - entry_price) / entry_price * 100
    else:
        pnl = (current_price - entry_price) * position_size
        pnl_pct = (current_price - entry_price) / entry_price * 100

    distance_to_stop = abs(current_price - stop_loss)
    distance_to_stop_pct = distance_to_stop / current_price * 100

    risk_level = "LOW"
    if distance_to_stop_pct < 1:
        risk_level = "EXTREME"
    elif distance_to_stop_pct < 2:
        risk_level = "HIGH"
    elif distance_to_stop_pct < 5:
        risk_level = "MEDIUM"

    report = f"""
持仓风险检查报告：

持仓信息：
- 持仓大小: {position_size} BTC
- 持仓价值: ${position_value:,.2f}
- 仓位占比: {position_pct:.2f}%

盈亏情况：
- 入场价格: ${entry_price:,.2f}
- 当前价格: ${current_price:,.2f}
- 未实现盈亏: ${pnl:,.2f} ({pnl_pct:+.2f}%)

止损检查：
- 止损价格: ${stop_loss:,.2f}
- 距离止损: ${distance_to_stop:,.2f} ({distance_to_stop_pct:.2f}%)
- 风险等级: {risk_level}

{'⚠️  警告：接近止损点，建议考虑平仓或移动止损' if distance_to_stop_pct < 1 else ''}
"""

    return report
