# -*- coding: utf-8 -*-
"""
持仓监控器
全天候监控持仓，实时盈亏计算，检查预警条件
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import threading
import time as tm


class AlertType(Enum):
    """预警类型"""
    STOP_LOSS = "stop_loss"  # 止损
    TAKE_PROFIT = "take_profit"  # 止盈
    PLUNGE = "plunge"  # 大跌
    SURGE = "surge"  # 大涨
    LIMIT_DOWN = "limit_down"  # 跌停
    LIMIT_UP = "limit_up"  # 涨停


@dataclass
class PositionAlert:
    """持仓预警"""
    position_id: str
    code: str
    name: str
    alert_type: AlertType
    current_price: float
    target_price: float
    message: str
    suggestion: str
    timestamp: str


class PositionMonitor:
    """持仓监控器

    功能：
    1. 全天候监控持仓
    2. 实时盈亏计算
    3. 检查止损条件
    4. 检查止盈条件
    """

    def __init__(self, position_manager=None, alert_manager=None):
        """
        初始化持仓监控器

        Args:
            position_manager: 持仓管理器
            alert_manager: 预警管理器
        """
        # 延迟导入避免循环依赖
        if position_manager is None:
            from portfolio.position_manager import get_position_manager
            position_manager = get_position_manager()

        if alert_manager is None:
            from monitor.alert_manager import get_alert_manager, AlertCategory
            alert_manager = get_alert_manager()

        self.position_manager = position_manager
        self.alert_manager = alert_manager

        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None

        # 预警阈值
        self.plunge_threshold = -5.0  # 大跌阈值（%）
        self.surge_threshold = 5.0  # 大涨阈值（%）

        # 回调函数
        self.alert_callbacks = []

        print("[持仓监控器] 初始化完成")

    def add_alert_callback(self, callback: Callable):
        """添加预警回调函数"""
        self.alert_callbacks.append(callback)

    def _trigger_alert(self, alert: PositionAlert):
        """触发预警"""
        print(f"[持仓监控器] {alert.alert_type.value} - {alert.message}")

        # 保存到预警管理器
        from monitor.alert_manager import AlertLevel, AlertCategory

        level_map = {
            AlertType.STOP_LOSS: AlertLevel.CRITICAL,
            AlertType.TAKE_PROFIT: AlertLevel.INFO,
            AlertType.PLUNGE: AlertLevel.WARNING,
            AlertType.SURGE: AlertLevel.INFO,
            AlertType.LIMIT_DOWN: AlertLevel.CRITICAL,
            AlertType.LIMIT_UP: AlertLevel.INFO
        }

        level = level_map.get(alert.alert_type, AlertLevel.INFO)

        self.alert_manager.create_alert(
            level=level,
            category=AlertCategory.POSITION,
            title=f"{alert.name} {alert.alert_type.value}",
            message=alert.message,
            suggestion=alert.suggestion,
            metadata={
                'position_id': alert.position_id,
                'code': alert.code,
                'alert_type': alert.alert_type.value
            }
        )

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"[持仓监控器] 回调执行失败: {e}")

    def update_prices(self, prices: Dict[str, float]):
        """
        更新持仓价格

        Args:
            prices: 价格字典 {code: current_price}
        """
        positions = self.position_manager.get_all_positions()

        for position in positions:
            if position.code in prices:
                new_price = prices[position.code]
                old_price = position.current_price

                # 更新价格
                self.position_manager.update_position_price(position.id, new_price)

                # 检查预警条件
                self._check_position_alerts(position, old_price, new_price)

    def _check_position_alerts(self, position, old_price: float, new_price: float):
        """
        检查持仓预警条件

        Args:
            position: 持仓对象
            old_price: 旧价格
            new_price: 新价格
        """
        # 1. 检查止损
        if position.stop_loss_price and new_price <= position.stop_loss_price:
            loss_pct = (new_price - position.buy_price) / position.buy_price * 100

            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.STOP_LOSS,
                current_price=new_price,
                target_price=position.stop_loss_price,
                message=f"Stop loss triggered for {position.name}",
                suggestion=f"Current price {new_price:.2f} reached stop loss {position.stop_loss_price:.2f}. Loss: {loss_pct:.2f}%",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

        # 2. 检查止盈
        elif position.take_profit_price and new_price >= position.take_profit_price:
            profit_pct = (new_price - position.buy_price) / position.buy_price * 100

            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.TAKE_PROFIT,
                current_price=new_price,
                target_price=position.take_profit_price,
                message=f"Take profit triggered for {position.name}",
                suggestion=f"Current price {new_price:.2f} reached take profit {position.take_profit_price:.2f}. Profit: {profit_pct:.2f}%",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

        # 3. 检查大跌
        change_pct = (new_price - old_price) / old_price * 100 if old_price > 0 else 0
        if change_pct <= self.plunge_threshold:
            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.PLUNGE,
                current_price=new_price,
                target_price=0,
                message=f"{position.name} plunged {change_pct:.2f}%",
                suggestion=f"Price dropped from {old_price:.2f} to {new_price:.2f}. Consider stop loss.",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

        # 4. 检查大涨
        elif change_pct >= self.surge_threshold:
            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.SURGE,
                current_price=new_price,
                target_price=0,
                message=f"{position.name} surged {change_pct:.2f}%",
                suggestion=f"Price increased from {old_price:.2f} to {new_price:.2f}. Consider taking profit.",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

        # 5. 检查跌停
        if change_pct <= -9.5:
            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.LIMIT_DOWN,
                current_price=new_price,
                target_price=-10.0,
                message=f"{position.name} hit limit down",
                suggestion="Stock hit limit down. High risk advised.",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

        # 6. 检查涨停
        elif change_pct >= 9.5:
            alert = PositionAlert(
                position_id=position.id,
                code=position.code,
                name=position.name,
                alert_type=AlertType.LIMIT_UP,
                current_price=new_price,
                target_price=10.0,
                message=f"{position.name} hit limit up",
                suggestion="Stock hit limit up. Consider taking profit.",
                timestamp=datetime.now().isoformat()
            )
            self._trigger_alert(alert)

    def monitor_all_positions(self):
        """监控所有持仓（手动触发）"""
        from data.cmes_market_data import get_cmes_market_data

        positions = self.position_manager.get_all_positions()

        if not positions:
            print("[PositionMonitor] No positions to monitor")
            return

        # 获取实时价格
        codes = [pos.code for pos in positions]
        cmes_fetcher = get_cmes_market_data()

        try:
            quotes = cmes_fetcher.cmes.get_realtime_quotes(codes)

            # 更新价格并检查预警
            prices = {code: data['price'] for code, data in quotes.items() if 'price' in data}
            self.update_prices(prices)

            print(f"[PositionMonitor] Updated {len(prices)} position prices")

        except Exception as e:
            print(f"[PositionMonitor] Failed to update prices: {e}")

    def start_monitoring(self, interval: int = 60):
        """
        开始监控（后台线程）

        Args:
            interval: 更新间隔（秒）
        """
        if self.is_monitoring:
            print("[持仓监控器] 监控已在运行中")
            return

        print(f"[持仓监控器] 启动监控，更新间隔 {interval}秒")

        self.is_monitoring = True

        def monitor_loop():
            while self.is_monitoring:
                try:
                    self.monitor_all_positions()
                except Exception as e:
                    print(f"[持仓监控器] 监控循环错误: {e}")

                tm.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        print("[持仓监控器] 监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            print("[持仓监控器] 监控未在运行")
            return

        print("[持仓监控器] 停止监控...")
        self.is_monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        print("[持仓监控器] 监控已停止")

    def get_monitoring_status(self) -> Dict:
        """
        获取监控状态

        Returns:
            状态信息字典
        """
        positions = self.position_manager.get_all_positions()

        return {
            'is_monitoring': self.is_monitoring,
            'total_positions': len(positions),
            'last_update': datetime.now().isoformat(),
            'thresholds': {
                'plunge': self.plunge_threshold,
                'surge': self.surge_threshold
            }
        }


# 创建全局实例
_global_position_monitor: Optional[PositionMonitor] = None


def get_position_monitor() -> PositionMonitor:
    """获取全局持仓监控器实例（单例模式）"""
    global _global_position_monitor
    if _global_position_monitor is None:
        _global_position_monitor = PositionMonitor()
    return _global_position_monitor


# 测试代码
if __name__ == '__main__':
    from portfolio.position_manager import PositionManager

    # 创建持仓管理器并添加测试持仓
    pos_manager = PositionManager()
    pos_manager.add_position(
        code='600519',
        name='贵州茅台',
        shares=100,
        buy_price=1750.0,
        stop_loss_price=1675.0,
        take_profit_price=1840.0
    )

    # 创建持仓监控器
    monitor = PositionMonitor(pos_manager)

    # 添加回调函数
    def on_alert(alert):
        print(f"\n收到预警:")
        print(f"  类型: {alert.alert_type.value}")
        print(f"  消息: {alert.message}")
        print(f"  建议: {alert.suggestion}")

    monitor.add_alert_callback(on_alert)

    # 手动监控一次
    print("\n手动监控:")
    monitor.monitor_all_positions()

    # 获取状态
    print("\n监控状态:")
    status = monitor.get_monitoring_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # 模拟价格更新测试预警
    print("\n模拟止损预警:")
    monitor.update_prices({'600519': 1660.0})

    print("\n模拟止盈预警:")
    monitor.update_prices({'600519': 1850.0})
