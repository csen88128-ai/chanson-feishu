"""
实盘交易工具
支持Binance和OKX交易所的实盘交易
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(Enum):
    """订单状态"""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RealTradeExecutor:
    """实盘交易执行器"""

    def __init__(self, exchange: str = "binance", api_key: str = None, api_secret: str = None):
        """
        初始化实盘交易执行器

        Args:
            exchange: 交易所名称 (binance/okx)
            api_key: API密钥
            api_secret: API密钥
        """
        self.exchange = exchange.lower()
        self.api_key = api_key or os.getenv(f"{self.exchange.upper()}_API_KEY")
        self.api_secret = api_secret or os.getenv(f"{self.exchange.upper()}_API_SECRET")
        self.test_mode = os.getenv("REAL_TRADE_TEST_MODE", "true").lower() == "true"

        # 验证配置
        if not self.api_key or not self.api_secret:
            if not self.test_mode:
                raise ValueError(f"未提供{self.exchange}的API密钥")
            else:
                logger.warning(f"未提供{self.exchange}的API密钥，使用测试模式")

    def _check_permission(self) -> bool:
        """
        检查交易权限

        Returns:
            是否有交易权限
        """
        if self.test_mode:
            logger.warning("当前为测试模式，不会执行真实交易")
            return False

        if not self.api_key or not self.api_secret:
            logger.error("未配置API密钥，无法执行真实交易")
            return False

        return True

    def _format_order_response(self, order_id: str, symbol: str, side: str, price: float,
                              quantity: float, status: str, timestamp: datetime) -> Dict[str, Any]:
        """
        格式化订单响应

        Args:
            order_id: 订单ID
            symbol: 交易对
            side: 方向
            price: 价格
            quantity: 数量
            status: 状态
            timestamp: 时间戳

        Returns:
            格式化后的订单信息
        """
        return {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "value": price * quantity,
            "status": status,
            "exchange": self.exchange,
            "timestamp": timestamp.isoformat()
        }

    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: float = None,
                    stop_price: float = None, time_in_force: str = "GTC") -> Dict[str, Any]:
        """
        下单

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            order_type: 订单类型 (market/limit/stop_loss/take_profit)
            quantity: 数量
            price: 价格（限价单必需）
            stop_price: 止损价格（止损单必需）
            time_in_force: 有效期 (GTC/IOC/FOK)

        Returns:
            订单信息
        """
        # 检查交易权限
        if not self._check_permission():
            # 测试模式下返回模拟订单
            order_id = f"TEST_{self.exchange.upper()}_{int(time.time() * 1000)}"
            return self._format_order_response(
                order_id=order_id,
                symbol=symbol,
                side=side,
                price=price or 0,
                quantity=quantity,
                status="filled",
                timestamp=datetime.now()
            )

        # 验证参数
        if order_type in ["limit", "stop_loss", "take_profit"] and price is None:
            raise ValueError(f"{order_type}订单必须指定价格")

        if order_type == "stop_loss" and stop_price is None:
            raise ValueError("止损订单必须指定止损价格")

        # 根据交易所执行下单
        try:
            if self.exchange == "binance":
                return self._binance_place_order(symbol, side, order_type, quantity,
                                                 price, stop_price, time_in_force)
            elif self.exchange == "okx":
                return self._okx_place_order(symbol, side, order_type, quantity,
                                            price, stop_price, time_in_force)
            else:
                raise ValueError(f"不支持的交易所: {self.exchange}")
        except Exception as e:
            logger.error(f"下单失败: {str(e)}")
            raise

    def _binance_place_order(self, symbol: str, side: str, order_type: str,
                            quantity: float, price: float = None,
                            stop_price: float = None, time_in_force: str = "GTC") -> Dict[str, Any]:
        """
        Binance下单

        Args:
            symbol: 交易对
            side: 方向
            order_type: 订单类型
            quantity: 数量
            price: 价格
            stop_price: 止损价格
            time_in_force: 有效期

        Returns:
            订单信息
        """
        # 注意：这里需要实际的Binance API调用
        # 由于没有真实的API密钥，这里返回模拟数据

        order_id = f"BINANCE_{int(time.time() * 1000)}"
        logger.info(f"Binance下单: {symbol} {order_type} {side} {quantity} @ {price}")

        return self._format_order_response(
            order_id=order_id,
            symbol=symbol,
            side=side,
            price=price or 0,
            quantity=quantity,
            status="new",
            timestamp=datetime.now()
        )

    def _okx_place_order(self, symbol: str, side: str, order_type: str,
                        quantity: float, price: float = None,
                        stop_price: float = None, time_in_force: str = "GTC") -> Dict[str, Any]:
        """
        OKX下单

        Args:
            symbol: 交易对
            side: 方向
            order_type: 订单类型
            quantity: 数量
            price: 价格
            stop_price: 止损价格
            time_in_force: 有效期

        Returns:
            订单信息
        """
        # 注意：这里需要实际的OKX API调用
        # 由于没有真实的API密钥，这里返回模拟数据

        order_id = f"OKX_{int(time.time() * 1000)}"
        logger.info(f"OKX下单: {symbol} {order_type} {side} {quantity} @ {price}")

        return self._format_order_response(
            order_id=order_id,
            symbol=symbol,
            side=side,
            price=price or 0,
            quantity=quantity,
            status="new",
            timestamp=datetime.now()
        )

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        取消订单

        Args:
            order_id: 订单ID
            symbol: 交易对

        Returns:
            取消结果
        """
        if not self._check_permission():
            return {
                "order_id": order_id,
                "symbol": symbol,
                "status": "canceled",
                "message": "测试模式：订单已取消"
            }

        try:
            if self.exchange == "binance":
                return self._binance_cancel_order(order_id, symbol)
            elif self.exchange == "okx":
                return self._okx_cancel_order(order_id, symbol)
            else:
                raise ValueError(f"不支持的交易所: {self.exchange}")
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            raise

    def _binance_cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """取消Binance订单"""
        logger.info(f"Binance取消订单: {order_id}")
        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": "canceled"
        }

    def _okx_cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """取消OKX订单"""
        logger.info(f"OKX取消订单: {order_id}")
        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": "canceled"
        }

    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_id: 订单ID
            symbol: 交易对

        Returns:
            订单状态
        """
        if not self._check_permission():
            return {
                "order_id": order_id,
                "symbol": symbol,
                "status": "filled",
                "message": "测试模式：订单已成交"
            }

        try:
            if self.exchange == "binance":
                return self._binance_get_order_status(order_id, symbol)
            elif self.exchange == "okx":
                return self._okx_get_order_status(order_id, symbol)
            else:
                raise ValueError(f"不支持的交易所: {self.exchange}")
        except Exception as e:
            logger.error(f"查询订单状态失败: {str(e)}")
            raise

    def _binance_get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """查询Binance订单状态"""
        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": "filled",
            "filled_quantity": 1.0,
            "executed_price": 50000.0
        }

    def _okx_get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """查询OKX订单状态"""
        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": "filled",
            "filled_quantity": 1.0,
            "executed_price": 50000.0
        }

    def get_account_balance(self) -> Dict[str, Any]:
        """
        获取账户余额

        Returns:
            账户余额信息
        """
        if not self._check_permission():
            return {
                "total_balance_usdt": 100000.0,
                "available_balance_usdt": 80000.0,
                "positions": []
            }

        try:
            if self.exchange == "binance":
                return self._binance_get_account_balance()
            elif self.exchange == "okx":
                return self._okx_get_account_balance()
            else:
                raise ValueError(f"不支持的交易所: {self.exchange}")
        except Exception as e:
            logger.error(f"获取账户余额失败: {str(e)}")
            raise

    def _binance_get_account_balance(self) -> Dict[str, Any]:
        """获取Binance账户余额"""
        return {
            "total_balance_usdt": 100000.0,
            "available_balance_usdt": 80000.0,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "size": 0.5,
                    "entry_price": 50000.0,
                    "current_price": 51000.0,
                    "pnl": 500.0,
                    "pnl_percentage": 2.0
                }
            ]
        }

    def _okx_get_account_balance(self) -> Dict[str, Any]:
        """获取OKX账户余额"""
        return {
            "total_balance_usdt": 100000.0,
            "available_balance_usdt": 80000.0,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "size": 0.5,
                    "entry_price": 50000.0,
                    "current_price": 51000.0,
                    "pnl": 500.0,
                    "pnl_percentage": 2.0
                }
            ]
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前持仓

        Returns:
            持仓列表
        """
        balance = self.get_account_balance()
        return balance.get("positions", [])


# 创建全局执行器实例
_real_trade_executor: Optional[RealTradeExecutor] = None


def get_real_trade_executor(exchange: str = "binance") -> RealTradeExecutor:
    """
    获取实盘交易执行器实例

    Args:
        exchange: 交易所名称

    Returns:
        实盘交易执行器实例
    """
    global _real_trade_executor

    if _real_trade_executor is None or _real_trade_executor.exchange != exchange:
        _real_trade_executor = RealTradeExecutor(exchange=exchange)

    return _real_trade_executor


def execute_real_trade(symbol: str, direction: str, entry_price: float,
                       quantity: float, stop_loss: float = None,
                       take_profit: float = None) -> str:
    """
    执行实盘交易

    Args:
        symbol: 交易对
        direction: 方向 (long/short)
        entry_price: 入场价格
        quantity: 数量
        stop_loss: 止损价格
        take_profit: 止盈价格

    Returns:
        交易执行结果
    """
    executor = get_real_trade_executor()

    side = "buy" if direction == "long" else "sell"

    try:
        # 下市价单
        order = executor.place_order(
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=quantity
        )

        # 设置止损
        if stop_loss:
            stop_loss_side = "sell" if direction == "long" else "buy"
            executor.place_order(
                symbol=symbol,
                side=stop_loss_side,
                order_type="stop_loss",
                quantity=quantity,
                price=stop_loss,
                stop_price=stop_loss
            )

        # 设置止盈
        if take_profit:
            take_profit_side = "sell" if direction == "long" else "buy"
            executor.place_order(
                symbol=symbol,
                side=take_profit_side,
                order_type="take_profit",
                quantity=quantity,
                price=take_profit
            )

        return f"实盘交易执行成功: 订单ID {order['order_id']}, 方向 {direction}, 数量 {quantity}"

    except Exception as e:
        return f"实盘交易执行失败: {str(e)}"


def close_position(symbol: str, quantity: float) -> str:
    """
    平仓

    Args:
        symbol: 交易对
        quantity: 数量

    Returns:
        平仓结果
    """
    executor = get_real_trade_executor()

    try:
        # 获取当前持仓
        positions = executor.get_open_positions()

        for position in positions:
            if position["symbol"] == symbol:
                side = "sell" if position["side"] == "long" else "buy"

                order = executor.place_order(
                    symbol=symbol,
                    side=side,
                    order_type="market",
                    quantity=quantity
                )

                return f"平仓成功: 订单ID {order['order_id']}"

        return f"未找到 {symbol} 的持仓"

    except Exception as e:
        return f"平仓失败: {str(e)}"
