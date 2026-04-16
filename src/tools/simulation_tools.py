"""
模拟盘交易相关工具
"""
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


class SimulationTrader:
    """模拟盘交易器"""

    def __init__(self):
        self.initial_capital = 100000.0  # 初始资金 10万 USDT
        self.trades: List[Dict] = []
        self.positions: Dict[str, Dict] = {}  # 当前持仓
        self.cash = self.initial_capital

    def open_position(
        self,
        symbol: str,
        side: str,  # "long" or "short"
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        confidence: Optional[float] = None,
        signal_source: Optional[str] = None
    ) -> Dict:
        """开仓"""
        if side not in ["long", "short"]:
            raise ValueError("side must be 'long' or 'short'")

        # 计算所需资金
        required_margin = entry_price * quantity

        if required_margin > self.cash:
            return {
                "success": False,
                "error": "insufficient_funds",
                "required": required_margin,
                "available": self.cash
            }

        # 扣除资金
        self.cash -= required_margin

        # 创建持仓记录
        position_id = f"{symbol}_{side}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        position = {
            "position_id": position_id,
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "margin": required_margin,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "signal_source": signal_source,
            "open_time": datetime.now().isoformat(),
            "status": "open"
        }

        self.positions[position_id] = position

        return {
            "success": True,
            "position_id": position_id,
            "position": position,
            "remaining_cash": self.cash
        }

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "manual"
    ) -> Dict:
        """平仓"""
        if position_id not in self.positions:
            return {
                "success": False,
                "error": "position_not_found",
                "position_id": position_id
            }

        position = self.positions[position_id]

        if position["status"] != "open":
            return {
                "success": False,
                "error": "position_not_open",
                "current_status": position["status"]
            }

        # 计算盈亏
        if position["side"] == "long":
            pnl = (exit_price - position["entry_price"]) * position["quantity"]
        else:  # short
            pnl = (position["entry_price"] - exit_price) * position["quantity"]

        pnl_percent = (pnl / position["margin"]) * 100

        # 返还本金 + 盈亏
        self.cash += position["margin"] + pnl

        # 记录交易
        trade = {
            "position_id": position_id,
            "symbol": position["symbol"],
            "side": position["side"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "quantity": position["quantity"],
            "margin": position["margin"],
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "open_time": position["open_time"],
            "close_time": datetime.now().isoformat(),
            "reason": reason,
            "confidence": position.get("confidence"),
            "signal_source": position.get("signal_source")
        }

        self.trades.append(trade)

        # 删除持仓
        del self.positions[position_id]

        return {
            "success": True,
            "trade": trade,
            "remaining_cash": self.cash
        }

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """获取投资组合总价值"""
        total = self.cash

        for pos in self.positions.values():
            if pos["status"] == "open":
                if pos["side"] == "long":
                    unrealized_pnl = (current_prices.get(pos["symbol"], pos["entry_price"]) - pos["entry_price"]) * pos["quantity"]
                else:
                    unrealized_pnl = (pos["entry_price"] - current_prices.get(pos["symbol"], pos["entry_price"])) * pos["quantity"]
                total += pos["margin"] + unrealized_pnl

        return total

    def get_performance_metrics(self) -> Dict:
        """获取绩效指标"""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_percent": 0.0
            }

        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t["pnl"] > 0]
        losing_trades = [t for t in self.trades if t["pnl"] < 0]

        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t["pnl"] for t in self.trades)
        total_pnl_percent = (total_pnl / self.initial_capital) * 100

        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        profit_factor = abs(sum(t["pnl"] for t in winning_trades) / sum(t["pnl"] for t in losing_trades)) if losing_trades else float('inf')

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "current_cash": round(self.cash, 2),
            "open_positions": len(self.positions)
        }


# 全局实例
_trader = SimulationTrader()


@tool
def record_simulation_trade(
    symbol: str,
    side: str,
    entry_price: float,
    quantity: float,
    action: str = "open",  # "open" or "close"
    position_id: Optional[str] = None,
    exit_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    confidence: Optional[float] = None,
    signal_source: Optional[str] = None
) -> str:
    """
    记录模拟盘交易

    Args:
        symbol: 交易对
        side: 方向 (long 或 short)
        entry_price: 入场价格
        quantity: 数量
        action: 操作类型 (open 开仓 / close 平仓)
        position_id: 持仓ID（平仓时必需）
        exit_price: 出场价格（平仓时必需）
        stop_loss: 止损价格
        take_profit: 止盈价格
        confidence: 信号置信度 (0-1)
        signal_source: 信号来源

    Returns:
        交易结果
    """
    ctx = request_context.get() or new_context(method="record_simulation_trade")

    try:
        if action == "open":
            result = _trader.open_position(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=confidence,
                signal_source=signal_source
            )
        elif action == "close":
            if not position_id or exit_price is None:
                return json.dumps({
                    "error": "position_id and exit_price are required for close action"
                }, ensure_ascii=False, indent=2)

            result = _trader.close_position(
                position_id=position_id,
                exit_price=exit_price,
                reason="signal"
            )
        else:
            return json.dumps({
                "error": f"Invalid action: {action}. Must be 'open' or 'close'"
            }, ensure_ascii=False, indent=2)

        # 保存交易记录到文件
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        sim_dir = os.path.join(workspace_path, "simulation/trades")
        os.makedirs(sim_dir, exist_ok=True)

        trades_file = os.path.join(sim_dir, "trades.json")
        with open(trades_file, 'w', encoding='utf-8') as f:
            json.dump(_trader.trades, f, ensure_ascii=False, indent=2)

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_simulation_performance() -> str:
    """
    获取模拟盘绩效统计

    Returns:
        绩效报告
    """
    ctx = request_context.get() or new_context(method="get_simulation_performance")

    try:
        metrics = _trader.get_performance_metrics()

        # 获取最近的交易记录
        recent_trades = _trader.trades[-10:] if len(_trader.trades) > 10 else _trader.trades

        report = {
            "performance": metrics,
            "recent_trades": recent_trades,
            "open_positions": list(_trader.positions.values()),
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_open_positions() -> str:
    """
    获取当前持仓列表

    Returns:
        持仓列表
    """
    ctx = request_context.get() or new_context(method="get_open_positions")

    try:
        positions = list(_trader.positions.values())

        return json.dumps({
            "count": len(positions),
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def reset_simulation() -> str:
    """
    重置模拟盘（清空所有持仓和交易记录）

    Returns:
        操作结果
    """
    ctx = request_context.get() or new_context(method="reset_simulation")

    try:
        _trader.__init__()  # 重新初始化

        return json.dumps({
            "success": True,
            "message": "Simulation reset successfully",
            "initial_capital": _trader.initial_capital,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
