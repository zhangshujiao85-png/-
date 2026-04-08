# -*- coding: utf-8 -*-
"""
预警管理器
统一管理所有预警信息，提供预警分级、历史记录、通知功能
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path


class AlertLevel(Enum):
    """预警级别"""
    CRITICAL = "CRITICAL"  # 严重（红色）
    WARNING = "WARNING"  # 警告（黄色）
    INFO = "INFO"  # 信息（蓝色）
    SUCCESS = "SUCCESS"  # 成功（绿色）


class AlertCategory(Enum):
    """预警类别"""
    MARKET = "market"  # 市场预警
    POSITION = "position"  # 持仓预警
    SECTOR = "sector"  # 板块预警
    SYSTEM = "system"  # 系统预警


@dataclass
class Alert:
    """预警对象"""
    id: str  # 预警ID
    level: AlertLevel  # 预警级别
    category: AlertCategory  # 预警类别
    title: str  # 预警标题
    message: str  # 预警消息
    suggestion: str  # 操作建议
    timestamp: str  # 时间戳
    is_read: bool = False  # 是否已读
    is_dismissed: bool = False  # 是否已忽略
    metadata: Dict = field(default_factory=dict)  # 附加数据


class AlertManager:
    """预警管理器

    功能：
    1. 预警分级管理
    2. 预警历史记录
    3. 预警通知
    4. 预警查询
    """

    def __init__(self, storage_path: str = None):
        """
        初始化预警管理器

        Args:
            storage_path: 存储路径（默认为data/alerts.json）
        """
        self.storage_path = storage_path or "data/alerts.json"
        self.alerts: List[Alert] = []
        self.alert_counter = 0

        # 确保存储目录存在
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        # 加载历史预警
        self._load_alerts()

        print("[预警管理器] 初始化完成")

    def _load_alerts(self):
        """加载历史预警"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.alert_counter = data.get('counter', 0)
                for alert_data in data.get('alerts', []):
                    alert = Alert(
                        id=alert_data['id'],
                        level=AlertLevel(alert_data['level']),
                        category=AlertCategory(alert_data['category']),
                        title=alert_data['title'],
                        message=alert_data['message'],
                        suggestion=alert_data['suggestion'],
                        timestamp=alert_data['timestamp'],
                        is_read=alert_data.get('is_read', False),
                        is_dismissed=alert_data.get('is_dismissed', False),
                        metadata=alert_data.get('metadata', {})
                    )
                    self.alerts.append(alert)

                print(f"[预警管理器] 已加载 {len(self.alerts)} 条历史预警")

        except Exception as e:
            print(f"[预警管理器] 加载历史预警失败: {e}")

    def _save_alerts(self):
        """保存预警到文件"""
        try:
            data = {
                'counter': self.alert_counter,
                'alerts': [
                    {
                        'id': alert.id,
                        'level': alert.level.value,
                        'category': alert.category.value,
                        'title': alert.title,
                        'message': alert.message,
                        'suggestion': alert.suggestion,
                        'timestamp': alert.timestamp,
                        'is_read': alert.is_read,
                        'is_dismissed': alert.is_dismissed,
                        'metadata': alert.metadata
                    }
                    for alert in self.alerts
                ]
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[预警管理器] 保存预警失败: {e}")

    def _generate_alert_id(self) -> str:
        """生成预警ID"""
        self.alert_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"ALERT_{timestamp}_{self.alert_counter:04d}"

    def create_alert(
        self,
        level: AlertLevel,
        category: AlertCategory,
        title: str,
        message: str,
        suggestion: str = "",
        metadata: Dict = None
    ) -> Alert:
        """
        创建新预警

        Args:
            level: 预警级别
            category: 预警类别
            title: 预警标题
            message: 预警消息
            suggestion: 操作建议
            metadata: 附加数据

        Returns:
            预警对象
        """
        alert = Alert(
            id=self._generate_alert_id(),
            level=level,
            category=category,
            title=title,
            message=message,
            suggestion=suggestion,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )

        # 添加到列表
        self.alerts.insert(0, alert)  # 最新的在前面

        # 保存到文件
        self._save_alerts()

        # 打印预警信息
        self._print_alert(alert)

        return alert

    def _print_alert(self, alert: Alert):
        """打印预警信息"""
        level_symbol = {
            AlertLevel.CRITICAL: "[RED]",
            AlertLevel.WARNING: "[YELLOW]",
            AlertLevel.INFO: "[BLUE]",
            AlertLevel.SUCCESS: "[GREEN]"
        }

        symbol = level_symbol.get(alert.level, "[INFO]")
        print(f"\n{symbol} [{alert.level.value}] {alert.title}")
        print(f"   {alert.message}")
        if alert.suggestion:
            print(f"   Suggestion: {alert.suggestion}")

    def create_critical_alert(
        self,
        category: AlertCategory,
        title: str,
        message: str,
        suggestion: str = "",
        metadata: Dict = None
    ) -> Alert:
        """创建严重预警"""
        return self.create_alert(
            AlertLevel.CRITICAL,
            category,
            title,
            message,
            suggestion,
            metadata
        )

    def create_warning_alert(
        self,
        category: AlertCategory,
        title: str,
        message: str,
        suggestion: str = "",
        metadata: Dict = None
    ) -> Alert:
        """创建警告预警"""
        return self.create_alert(
            AlertLevel.WARNING,
            category,
            title,
            message,
            suggestion,
            metadata
        )

    def create_info_alert(
        self,
        category: AlertCategory,
        title: str,
        message: str,
        suggestion: str = "",
        metadata: Dict = None
    ) -> Alert:
        """创建信息预警"""
        return self.create_alert(
            AlertLevel.INFO,
            category,
            title,
            message,
            suggestion,
            metadata
        )

    def mark_as_read(self, alert_id: str) -> bool:
        """
        标记预警为已读

        Args:
            alert_id: 预警ID

        Returns:
            是否成功
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.is_read = True
                self._save_alerts()
                return True
        return False

    def mark_all_as_read(self):
        """标记所有预警为已读"""
        for alert in self.alerts:
            alert.is_read = True
        self._save_alerts()

    def dismiss_alert(self, alert_id: str) -> bool:
        """
        忽略预警

        Args:
            alert_id: 预警ID

        Returns:
            是否成功
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.is_dismissed = True
                self._save_alerts()
                return True
        return False

    def get_unread_alerts(self) -> List[Alert]:
        """获取未读预警"""
        return [alert for alert in self.alerts if not alert.is_read]

    def get_recent_alerts(self, limit: int = 10) -> List[Alert]:
        """
        获取最近的预警

        Args:
            limit: 数量限制

        Returns:
            预警列表
        """
        return self.alerts[:limit]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """
        按级别获取预警

        Args:
            level: 预警级别

        Returns:
            预警列表
        """
        return [alert for alert in self.alerts if alert.level == level]

    def get_alerts_by_category(self, category: AlertCategory) -> List[Alert]:
        """
        按类别获取预警

        Args:
            category: 预警类别

        Returns:
            预警列表
        """
        return [alert for alert in self.alerts if alert.category == category]

    def get_alerts_today(self) -> List[Alert]:
        """获取今天的预警"""
        today = datetime.now().date()
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert.timestamp).date() == today
        ]

    def get_critical_alerts(self) -> List[Alert]:
        """获取所有严重预警"""
        return self.get_alerts_by_level(AlertLevel.CRITICAL)

    def clear_old_alerts(self, days: int = 7):
        """
        清除旧预警

        Args:
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert.timestamp) > cutoff_date
        ]
        self._save_alerts()
        print(f"[预警管理器] 已清除 {days} 天前的预警")

    def get_statistics(self) -> Dict:
        """
        获取预警统计

        Returns:
            统计信息字典
        """
        total = len(self.alerts)
        unread = len(self.get_unread_alerts())
        critical = len(self.get_alerts_by_level(AlertLevel.CRITICAL))
        warning = len(self.get_alerts_by_level(AlertLevel.WARNING))
        info = len(self.get_alerts_by_level(AlertLevel.INFO))

        return {
            'total': total,
            'unread': unread,
            'critical': critical,
            'warning': warning,
            'info': info,
            'today': len(self.get_alerts_today())
        }

    def format_alert_text(self, alert: Alert) -> str:
        """
        格式化预警为文本

        Args:
            alert: 预警对象

        Returns:
            格式化的文本
        """
        level_emoji = {
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.WARNING: "🟡",
            AlertLevel.INFO: "🔵",
            AlertLevel.SUCCESS: "🟢"
        }

        emoji = level_emoji.get(alert.level, "⚪")
        timestamp = datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')

        text = f"""
{emoji} [{alert.level.value}] {alert.title}
时间: {timestamp}
消息: {alert.message}
"""
        if alert.suggestion:
            text += f"建议: {alert.suggestion}\n"

        return text


# 创建全局实例
_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取全局预警管理器实例（单例模式）"""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager


# 测试代码
if __name__ == '__main__':
    manager = AlertManager()

    # 创建不同级别的预警
    print("创建预警测试:")

    manager.create_critical_alert(
        AlertCategory.MARKET,
        "市场崩盘",
        "大盘下跌超过7%",
        "建议立即止损，控制风险",
        {'change_pct': -8.5}
    )

    manager.create_warning_alert(
        AlertCategory.POSITION,
        "止损提醒",
        "贵州茅台触及止损价",
        "建议考虑止损",
        {'code': '600519', 'price': 1670.0}
    )

    manager.create_info_alert(
        AlertCategory.SECTOR,
        "板块轮动",
        "半导体板块情绪升温",
        "可适当关注",
        {'sector': '半导体', 'score': 75}
    )

    # 获取统计信息
    print("\n预警统计:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 获取未读预警
    print("\n未读预警:")
    unread = manager.get_unread_alerts()
    for alert in unread:
        print(manager.format_alert_text(alert))

    # 获取严重预警
    print("\n严重预警:")
    critical = manager.get_critical_alerts()
    for alert in critical:
        print(manager.format_alert_text(alert))
