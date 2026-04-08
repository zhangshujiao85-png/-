# -*- coding: utf-8 -*-
"""
异常熔断引擎
检测极端市场情况触发熔断预警
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import numpy as np


class CircuitBreakerLevel(Enum):
    """熔断级别"""
    CRITICAL = "CRITICAL"  # 严重市场崩盘
    SEVERE = "SEVERE"  # 严重大幅下跌
    MODERATE = "MODERATE"  # 中度下跌
    MILD = "MILD"  # 轻度波动


@dataclass
class CircuitBreakerAlert:
    """熔断预警"""
    level: CircuitBreakerLevel
    type: str  # market_crash/plunge/surge/limit_down/limit_up
    message: str
    current_value: float
    threshold: float
    timestamp: str
    suggestion: str


@dataclass
class PositionAlert:
    """持仓预警"""
    code: str
    name: str
    alert_type: str  # stop_loss/take_profit/limit_down/limit_up
    current_price: float
    target_price: float
    suggestion: str
    timestamp: str


class CircuitBreakerEngine:
    """异常熔断引擎

    功能
    1. 极端砸盘检测单日跌幅>7%
    2. 止损/止盈检测
    3. 涨停/跌停检测
    4. 异常波动告警
    """

    def __init__(self):
        """初始化"""
        # 市场熔断阈值
        self.market_crash_threshold = -7.0  # 市场崩盘阈值
        self.market_plunge_threshold = -5.0  # 大幅下跌阈值
        self.market_surge_threshold = 5.0  # 大幅上涨阈值

        # 个股熔断阈值
        self.stock_plunge_threshold = -7.0  # 个股大跌阈值
        self.stock_surge_threshold = 7.0  # 个股大涨阈值

        # 回调函数
        self.alert_callbacks = []

        print("[CircuitBreaker] Initialized")

    def add_alert_callback(self, callback: Callable):
        """添加预警回调函数"""
        self.alert_callbacks.append(callback)

    def _trigger_alert(self, alert: CircuitBreakerAlert):
        """触发预警"""
        print(f"[CircuitBreaker] {alert.level.value} - {alert.message}")

        # 调用所有回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"[CircuitBreaker] Callback failed: {e}")

    def check_market_crash(self, market_change_pct: float) -> Optional[CircuitBreakerAlert]:
        """
        检测市场崩盘

        Args:
            market_change_pct: 市场涨跌幅%

        Returns:
            熔断预警对象
        """
        if market_change_pct <= self.market_crash_threshold:
            alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.CRITICAL,
                type='market_crash',
                message=f"[CRITICAL] Market crash: down {market_change_pct:.2f}%",
                current_value=market_change_pct,
                threshold=self.market_crash_threshold,
                timestamp=datetime.now().isoformat(),
                suggestion=(
                    "Action required:\n"
                    "1. Stop trading immediately\n"
                    "2. Evaluate position risk\n"
                    "3. Consider stop loss\n"
                    "4. Wait for market stabilization"
                )
            )
            self._trigger_alert(alert)
            return alert

        return None

    def check_market_plunge(self, market_change_pct: float) -> Optional[CircuitBreakerAlert]:
        """
        检测市场大幅下跌

        Args:
            market_change_pct: 市场涨跌幅%

        Returns:
            熔断预警对象
        """
        if (market_change_pct <= self.market_plunge_threshold and
            market_change_pct > self.market_crash_threshold):

            alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.SEVERE,
                type='plunge',
                message=f" 大幅下跌预警大盘下跌 {market_change_pct:.2f}%",
                current_value=market_change_pct,
                threshold=self.market_plunge_threshold,
                timestamp=datetime.now().isoformat(),
                suggestion=(
                    "建议操作\n"
                    "1. 控制仓位谨慎交易\n"
                    "2. 关注抗跌板块\n"
                    "3. 准备止损计划"
                )
            )
            self._trigger_alert(alert)
            return alert

        return None

    def check_market_surge(self, market_change_pct: float) -> Optional[CircuitBreakerAlert]:
        """
        检测市场大幅上涨

        Args:
            market_change_pct: 市场涨跌幅%

        Returns:
            熔断预警对象
        """
        if market_change_pct >= self.market_surge_threshold:
            alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.MODERATE,
                type='surge',
                message=f" 大幅上涨提示大盘上涨 {market_change_pct:.2f}%",
                current_value=market_change_pct,
                threshold=self.market_surge_threshold,
                timestamp=datetime.now().isoformat(),
                suggestion=(
                    "建议操作\n"
                    "1. 理性看待大涨\n"
                    "2. 注意回调风险\n"
                    "3. 及时止盈"
                )
            )
            self._trigger_alert(alert)
            return alert

        return None

    def check_stock_plunge(self, stock_data: Dict) -> Optional[PositionAlert]:
        """
        检测个股大跌

        Args:
            stock_data: 股票数据字典
                {
                    'code': '600519',
                    'name': '贵州茅台',
                    'price': 1700.0,
                    'change_pct': -8.5
                }

        Returns:
            持仓预警对象
        """
        change_pct = stock_data.get('change_pct', 0)

        if change_pct <= self.stock_plunge_threshold:
            alert = PositionAlert(
                code=stock_data.get('code', ''),
                name=stock_data.get('name', ''),
                alert_type='plunge',
                current_price=stock_data.get('price', 0),
                target_price=self.stock_plunge_threshold,
                suggestion=f"个股大跌 {change_pct:.2f}%注意风险",
                timestamp=datetime.now().isoformat()
            )

            # 转换为CircuitBreakerAlert
            cb_alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.SEVERE,
                type='plunge',
                message=f" {alert.name} 大跌 {change_pct:.2f}%",
                current_value=change_pct,
                threshold=self.stock_plunge_threshold,
                timestamp=alert.timestamp,
                suggestion=alert.suggestion
            )
            self._trigger_alert(cb_alert)

            return alert

        return None

    def check_stop_loss(self, position: Dict) -> Optional[PositionAlert]:
        """
        检测止损

        Args:
            position: 持仓数据字典
                {
                    'code': '600519',
                    'name': '贵州茅台',
                    'buy_price': 1750.0,
                    'current_price': 1660.0,
                    'stop_loss_price': 1675.0  # 止损价
                }

        Returns:
            持仓预警对象
        """
        current_price = position.get('current_price', 0)
        stop_loss_price = position.get('stop_loss_price', 0)

        if stop_loss_price > 0 and current_price <= stop_loss_price:
            loss_pct = (current_price - position.get('buy_price', 0)) / position.get('buy_price', 1) * 100

            alert = PositionAlert(
                code=position.get('code', ''),
                name=position.get('name', ''),
                alert_type='stop_loss',
                current_price=current_price,
                target_price=stop_loss_price,
                suggestion=f" 止损预警触及止损价 {stop_loss_price:.2f}亏损 {loss_pct:.2f}%",
                timestamp=datetime.now().isoformat()
            )

            # 转换为CircuitBreakerAlert
            cb_alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.SEVERE,
                type='stop_loss',
                message=alert.suggestion,
                current_value=current_price,
                threshold=stop_loss_price,
                timestamp=alert.timestamp,
                suggestion="建议立即止损控制风险"
            )
            self._trigger_alert(cb_alert)

            return alert

        return None

    def check_take_profit(self, position: Dict) -> Optional[PositionAlert]:
        """
        检测止盈

        Args:
            position: 持仓数据字典
                {
                    'code': '600519',
                    'name': '贵州茅台',
                    'buy_price': 1750.0,
                    'current_price': 1850.0,
                    'take_profit_price': 1840.0  # 止盈价
                }

        Returns:
            持仓预警对象
        """
        current_price = position.get('current_price', 0)
        take_profit_price = position.get('take_profit_price', 0)

        if take_profit_price > 0 and current_price >= take_profit_price:
            profit_pct = (current_price - position.get('buy_price', 0)) / position.get('buy_price', 1) * 100

            alert = PositionAlert(
                code=position.get('code', ''),
                name=position.get('name', ''),
                alert_type='take_profit',
                current_price=current_price,
                target_price=take_profit_price,
                suggestion=f" 止盈提醒触及止盈价 {take_profit_price:.2f}盈利 {profit_pct:.2f}%",
                timestamp=datetime.now().isoformat()
            )

            # 转换为CircuitBreakerAlert
            cb_alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.MILD,
                type='take_profit',
                message=alert.suggestion,
                current_value=current_price,
                threshold=take_profit_price,
                timestamp=alert.timestamp,
                suggestion="建议考虑止盈落袋为安"
            )
            self._trigger_alert(cb_alert)

            return alert

        return None

    def check_limit_down(self, stock_data: Dict) -> Optional[PositionAlert]:
        """
        检测跌停

        Args:
            stock_data: 股票数据字典

        Returns:
            持仓预警对象
        """
        change_pct = stock_data.get('change_pct', 0)

        # A股跌停约为-10%ST股-5%
        if change_pct <= -9.5:
            alert = PositionAlert(
                code=stock_data.get('code', ''),
                name=stock_data.get('name', ''),
                alert_type='limit_down',
                current_price=stock_data.get('price', 0),
                target_price=-10.0,
                suggestion=f" 跌停预警{stock_data.get('name', '')} 跌停",
                timestamp=datetime.now().isoformat()
            )

            # 转换为CircuitBreakerAlert
            cb_alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.SEVERE,
                type='limit_down',
                message=alert.suggestion,
                current_value=change_pct,
                threshold=-9.5,
                timestamp=alert.timestamp,
                suggestion="注意风险考虑止损"
            )
            self._trigger_alert(cb_alert)

            return alert

        return None

    def check_limit_up(self, stock_data: Dict) -> Optional[PositionAlert]:
        """
        检测涨停

        Args:
            stock_data: 股票数据字典

        Returns:
            持仓预警对象
        """
        change_pct = stock_data.get('change_pct', 0)

        # A股涨停约为+10%ST股+5%
        if change_pct >= 9.5:
            alert = PositionAlert(
                code=stock_data.get('code', ''),
                name=stock_data.get('name', ''),
                alert_type='limit_up',
                current_price=stock_data.get('price', 0),
                target_price=10.0,
                suggestion=f" 涨停提示{stock_data.get('name', '')} 涨停",
                timestamp=datetime.now().isoformat()
            )

            # 转换为CircuitBreakerAlert
            cb_alert = CircuitBreakerAlert(
                level=CircuitBreakerLevel.MILD,
                type='limit_up',
                message=alert.suggestion,
                current_value=change_pct,
                threshold=9.5,
                timestamp=alert.timestamp,
                suggestion="可考虑止盈不要追高"
            )
            self._trigger_alert(cb_alert)

            return alert

        return None


# 测试代码
if __name__ == '__main__':
    engine = CircuitBreakerEngine()

    # 添加回调函数
    def on_alert(alert):
        print(f"\n收到预警:")
        print(f"  级别: {alert.level.value}")
        print(f"  类型: {alert.type}")
        print(f"  消息: {alert.message}")
        print(f"  建议: {alert.suggestion}")

    engine.add_alert_callback(on_alert)

    # 测试市场崩盘
    print("测试1: 市场崩盘检测")
    engine.check_market_crash(-8.5)

    # 测试大幅下跌
    print("\n测试2: 大幅下跌检测")
    engine.check_market_plunge(-5.5)

    # 测试大幅上涨
    print("\n测试3: 大幅上涨检测")
    engine.check_market_surge(5.8)

    # 测试个股大跌
    print("\n测试4: 个股大跌检测")
    stock_data = {
        'code': '600519',
        'name': '贵州茅台',
        'price': 1700.0,
        'change_pct': -8.2
    }
    engine.check_stock_plunge(stock_data)

    # 测试止损
    print("\n测试5: 止损检测")
    position = {
        'code': '600519',
        'name': '贵州茅台',
        'buy_price': 1750.0,
        'current_price': 1660.0,
        'stop_loss_price': 1675.0
    }
    engine.check_stop_loss(position)

    # 测试止盈
    print("\n测试6: 止盈检测")
    position = {
        'code': '600519',
        'name': '贵州茅台',
        'buy_price': 1750.0,
        'current_price': 1850.0,
        'take_profit_price': 1840.0
    }
    engine.check_take_profit(position)

    # 测试跌停
    print("\n测试7: 跌停检测")
    stock_data = {
        'code': '600519',
        'name': '贵州茅台',
        'price': 1700.0,
        'change_pct': -10.0
    }
    engine.check_limit_down(stock_data)

    # 测试涨停
    print("\n测试8: 涨停检测")
    stock_data = {
        'code': '600519',
        'name': '贵州茅台',
        'price': 1700.0,
        'change_pct': 10.0
    }
    engine.check_limit_up(stock_data)
