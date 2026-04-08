# -*- coding: utf-8 -*-
"""
实时监控引擎
负责盘中实时监控，5分钟更新一次情绪数据
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time as dt_time
import threading
import time as tm
from typing import Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class MonitorConfig:
    """监控配置"""
    # 更新频率（秒）
    update_interval: int = 300  # 5分钟

    # 交易时间
    market_open: dt_time = dt_time(9, 30)
    market_close: dt_time = dt_time(15, 0)
    pre_market_start: dt_time = dt_time(9, 0)

    # 是否启用盘前监控
    enable_pre_market: bool = True

    # 是否启用盘后监控
    enable_after_market: bool = False


class RealtimeMonitor:
    """实时监控引擎

    功能：
    1. 5分钟定时更新情绪数据
    2. 盘前分析（9:00）
    3. 盘中监控（9:30-15:00）
    4. 回调通知机制
    """

    def __init__(self, config: MonitorConfig = None):
        """
        初始化实时监控引擎

        Args:
            config: 监控配置
        """
        self.config = config or MonitorConfig()

        # 调度器
        self.scheduler = BackgroundScheduler()

        # 回调函数
        self.callbacks = {
            'pre_market': [],  # 盘前分析回调
            'market_open': [],  # 开盘回调
            'update': [],  # 数据更新回调
            'market_close': [],  # 收盘回调
            'alert': []  # 预警回调
        }

        # 运行状态
        self.is_running = False
        self.is_market_time = False

        # 最新数据缓存
        self.latest_sentiment = None
        self.latest_market_status = None

        print("[实时监控] 监控引擎初始化完成")

    def add_callback(self, event: str, callback: Callable):
        """
        添加回调函数

        Args:
            event: 事件类型（pre_market/market_open/update/market_close/alert）
            callback: 回调函数
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            print(f"[实时监控] 已添加 {event} 回调")
        else:
            print(f"[实时监控] 未知事件类型: {event}")

    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """触发回调函数"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[实时监控] 回调执行失败 ({event}): {e}")

    def _is_trading_time(self) -> bool:
        """判断是否是交易时间"""
        now = datetime.now()
        current_time = now.time()

        # 判断是否是工作日（周一到周五）
        if now.weekday() >= 5:  # 5=周六, 6=周日
            return False

        # 判断是否在交易时间段
        is_pre_market = (self.config.pre_market_start <= current_time < self.config.market_open)
        is_market_hours = (self.config.market_open <= current_time < self.config.market_close)

        return is_pre_market or is_market_hours

    def _update_sentiment_data(self):
        """更新情绪数据"""
        try:
            from sentiment.sentiment_scorer import SentimentScorer

            scorer = SentimentScorer()
            sentiment = scorer.calculate_overall_sentiment()

            self.latest_sentiment = sentiment

            # 触发更新回调
            self._trigger_callbacks('update', sentiment)

            print(f"[实时监控] 情绪数据已更新: {sentiment.sentiment_score:.0f}分 "
                  f"({sentiment.market_state})")

        except Exception as e:
            print(f"[实时监控] 更新情绪数据失败: {e}")

    def _pre_market_analysis(self):
        """盘前分析（9:00）"""
        now = datetime.now()
        print(f"[实时监控] 执行盘前分析 - {now.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 触发盘前分析回调
            self._trigger_callbacks('pre_market', now)

            # 更新情绪数据
            self._update_sentiment_data()

            print("[实时监控] 盘前分析完成")

        except Exception as e:
            print(f"[实时监控] 盘前分析失败: {e}")

    def _market_open_routine(self):
        """开盘例行任务"""
        now = datetime.now()
        print(f"[实时监控] 市场开盘 - {now.strftime('%Y-%m-%d %H:%M:%S')}")

        self.is_market_time = True

        # 触发开盘回调
        self._trigger_callbacks('market_open', now)

        # 立即更新一次数据
        self._update_sentiment_data()

    def _market_close_routine(self):
        """收盘例行任务"""
        now = datetime.now()
        print(f"[实时监控] 市场收盘 - {now.strftime('%Y-%m-%d %H:%M:%S')}")

        self.is_market_time = False

        # 触发收盘回调
        self._trigger_callbacks('market_close', now)

        # 最后更新一次数据
        self._update_sentiment_data()

    def _periodic_update(self):
        """定时更新任务（每5分钟）"""
        # 只在交易时间更新
        if not self._is_trading_time():
            return

        self._update_sentiment_data()

    def _check_market_status(self):
        """检查市场状态"""
        was_market_time = self.is_market_time
        self.is_market_time = self._is_trading_time()

        now = datetime.now()
        current_time = now.time()

        # 检测开盘
        if not was_market_time and self.is_market_time:
            if current_time >= self.config.market_open:
                self._market_open_routine()

        # 检测收盘
        elif was_market_time and not self.is_market_time:
            if current_time >= self.config.market_close:
                self._market_close_routine()

    def start(self):
        """启动监控"""
        if self.is_running:
            print("[实时监控] 监控已在运行中")
            return

        print("[实时监控] 启动监控引擎...")

        # 添加定时任务

        # 1. 盘前分析（每个交易日 9:00）
        if self.config.enable_pre_market:
            self.scheduler.add_job(
                self._pre_market_analysis,
                CronTrigger(hour=9, minute=0, second=0,
                           day_of_week='mon-fri'),
                id='pre_market_analysis',
                name='盘前分析'
            )
            print("[实时监控] 已添加盘前分析任务 (09:00)")

        # 2. 开盘检测（每个交易日 9:30）
        self.scheduler.add_job(
            self._check_market_status,
            CronTrigger(hour=9, minute=30, second=0,
                       day_of_week='mon-fri'),
            id='market_open_check',
            name='开盘检测'
        )
        print("[实时监控] 已添加开盘检测任务 (09:30)")

        # 3. 收盘检测（每个交易日 15:00）
        self.scheduler.add_job(
            self._check_market_status,
            CronTrigger(hour=15, minute=0, second=0,
                       day_of_week='mon-fri'),
            id='market_close_check',
            name='收盘检测'
        )
        print("[实时监控] 已添加收盘检测任务 (15:00)")

        # 4. 定时更新（每5分钟，仅在交易时间）
        self.scheduler.add_job(
            self._periodic_update,
            'interval',
            seconds=self.config.update_interval,
            id='periodic_update',
            name='定时更新'
        )
        print(f"[实时监控] 已添加定时更新任务 (每{self.config.update_interval}秒)")

        # 5. 市场状态检测（每分钟）
        self.scheduler.add_job(
            self._check_market_status,
            'interval',
            seconds=60,
            id='market_status_check',
            name='市场状态检测'
        )
        print("[实时监控] 已添加市场状态检测任务 (每60秒)")

        # 启动调度器
        self.scheduler.start()
        self.is_running = True

        print(f"[实时监控] ✅ 监控引擎已启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 立即检查一次市场状态
        self._check_market_status()

        # 如果当前是交易时间，立即更新数据
        if self.is_market_time:
            print("[实时监控] 当前为交易时间，立即更新数据...")
            self._update_sentiment_data()

    def stop(self):
        """停止监控"""
        if not self.is_running:
            print("[实时监控] 监控未在运行")
            return

        print("[实时监控] 停止监控引擎...")
        self.scheduler.shutdown()
        self.is_running = False
        print("[实时监控] ✅ 监控引擎已停止")

    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'is_market_time': self.is_market_time,
            'is_trading_day': datetime.now().weekday() < 5,
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'latest_sentiment': self.latest_sentiment.__dict__ if self.latest_sentiment else None,
            'config': {
                'update_interval': self.config.update_interval,
                'market_open': self.config.market_open.strftime('%H:%M:%S'),
                'market_close': self.config.market_close.strftime('%H:%M:%S'),
                'pre_market_start': self.config.pre_market_start.strftime('%H:%M:%S')
            }
        }

    def manual_update(self):
        """手动触发更新"""
        print("[实时监控] 手动触发更新...")
        self._update_sentiment_data()


# 创建全局实例
_global_monitor: Optional[RealtimeMonitor] = None


def get_global_monitor() -> RealtimeMonitor:
    """获取全局监控实例（单例模式）"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = RealtimeMonitor()
    return _global_monitor


# 测试代码
if __name__ == '__main__':
    # 创建监控实例
    monitor = RealtimeMonitor()

    # 添加回调函数
    def on_update(sentiment):
        print(f"📊 情绪更新回调: {sentiment.sentiment_score:.0f}分")

    def on_pre_market(now):
        print(f"🌅 盘前分析回调: {now}")

    def on_market_open(now):
        print(f"🔔 开盘回调: {now}")

    def on_market_close(now):
        print(f"🔔 收盘回调: {now}")

    monitor.add_callback('update', on_update)
    monitor.add_callback('pre_market', on_pre_market)
    monitor.add_callback('market_open', on_market_open)
    monitor.add_callback('market_close', on_market_close)

    # 启动监控
    monitor.start()

    # 打印状态
    status = monitor.get_status()
    print("\n监控状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # 手动触发一次更新
    print("\n手动触发更新:")
    monitor.manual_update()

    # 保持运行（用于测试）
    print("\n监控运行中... (按Ctrl+C停止)")
    try:
        while True:
            tm.sleep(60)
            status = monitor.get_status()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                  f"运行中: {status['is_running']}, "
                  f"交易时间: {status['is_market_time']}")
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        monitor.stop()
        print("已退出")
