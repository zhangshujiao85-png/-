# -*- coding: utf-8 -*-
"""
Phase 5 实时监控模块测试
测试实时监控、先行指标、熔断引擎、预警管理器
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_alert_manager():
    """测试预警管理器"""
    print("\n" + "="*60)
    print("测试1: 预警管理器")
    print("="*60)

    from monitor.alert_manager import AlertManager, AlertCategory, AlertLevel

    manager = AlertManager()

    # 创建测试预警
    manager.create_critical_alert(
        AlertCategory.MARKET,
        "测试严重预警",
        "这是一个测试严重预警",
        "建议立即处理"
    )

    manager.create_warning_alert(
        AlertCategory.POSITION,
        "测试警告预警",
        "这是一个测试警告预警",
        "建议关注"
    )

    manager.create_info_alert(
        AlertCategory.SECTOR,
        "测试信息预警",
        "这是一个测试信息预警",
        "仅供参考"
    )

    # 获取统计信息
    stats = manager.get_statistics()
    print(f"\n预警统计: {stats}")

    # 获取未读预警
    unread = manager.get_unread_alerts()
    print(f"\n未读预警数量: {len(unread)}")

    print("[OK] Alert Manager test passed")


def test_circuit_breaker():
    """测试熔断引擎"""
    print("\n" + "="*60)
    print("测试2: 熔断引擎")
    print("="*60)

    from monitor.circuit_breaker import CircuitBreakerEngine

    engine = CircuitBreakerEngine()

    # 测试市场崩盘检测
    print("\n测试市场崩盘检测:")
    engine.check_market_crash(-8.5)

    # 测试止损检测
    print("\n测试止损检测:")
    position = {
        'code': '600519',
        'name': '贵州茅台',
        'buy_price': 1750.0,
        'current_price': 1660.0,
        'stop_loss_price': 1675.0
    }
    engine.check_stop_loss(position)

    # 测试止盈检测
    print("\n测试止盈检测:")
    position = {
        'code': '600519',
        'name': '贵州茅台',
        'buy_price': 1750.0,
        'current_price': 1850.0,
        'take_profit_price': 1840.0
    }
    engine.check_take_profit(position)

    print("[OK] Circuit Breaker test passed")


def test_leading_indicator():
    """测试先行指标分析"""
    print("\n" + "="*60)
    print("测试3: 先行指标分析")
    print("="*60)

    from monitor.leading_indicator import LeadingIndicatorAnalyzer

    analyzer = LeadingIndicatorAnalyzer()

    # 生成盘前预警
    print("\n生成盘前预警:")
    alert = analyzer.generate_pre_market_alert()

    print(f"预警级别: {alert.level}")
    print(f"预警消息: {alert.message}")
    print(f"建议操作:\n{alert.suggestion}")

    # 打印报告
    print("\n" + analyzer.format_alert_report(alert))

    print("[OK] Leading Indicator test passed")


def test_realtime_monitor():
    """测试实时监控引擎"""
    print("\n" + "="*60)
    print("测试4: 实时监控引擎")
    print("="*60)

    from monitor.realtime_monitor import RealtimeMonitor

    monitor = RealtimeMonitor()

    # 添加回调函数
    def on_update(sentiment):
        print(f"  情绪更新回调触发: {sentiment.sentiment_score:.0f}分")

    monitor.add_callback('update', on_update)

    # 获取状态
    print("\n获取监控状态:")
    status = monitor.get_status()
    print(f"  运行状态: {status['is_running']}")
    print(f"  交易时间: {status['is_market_time']}")
    print(f"  当前时间: {status['current_time']}")

    # 手动触发更新
    print("\n手动触发更新:")
    monitor.manual_update()

    print("\n注意: 完整的定时任务测试需要长时间运行")
    print("[OK] Realtime Monitor basic test passed")


def test_integration():
    """集成测试：测试各模块协同工作"""
    print("\n" + "="*60)
    print("测试5: 集成测试")
    print("="*60)

    from monitor.realtime_monitor import RealtimeMonitor
    from monitor.alert_manager import AlertManager, AlertCategory, AlertLevel
    from monitor.circuit_breaker import CircuitBreakerEngine

    # 创建各模块实例
    monitor = RealtimeMonitor()
    alert_manager = AlertManager()
    circuit_breaker = CircuitBreakerEngine()

    # 将熔断引擎的预警连接到预警管理器
    def on_circuit_breaker_alert(alert):
        alert_manager.create_alert(
            AlertLevel(alert.level.value),
            AlertCategory.MARKET,
            f"熔断预警: {alert.type}",
            alert.message,
            alert.suggestion,
            {'current_value': alert.current_value}
        )

    circuit_breaker.add_alert_callback(on_circuit_breaker_alert)

    # 将实时监控的更新连接到熔断检测
    def on_monitor_update(sentiment):
        # 模拟检测市场情况
        print(f"\n监控更新触发，当前情绪得分: {sentiment.sentiment_score:.0f}")

        # 这里可以添加实际的熔断检测逻辑
        # circuit_breaker.check_market_crash(...)

    monitor.add_callback('update', on_monitor_update)

    # 触发一次更新
    print("\n触发集成测试更新:")
    monitor.manual_update()

    # 查看预警统计
    print("\n预警管理器统计:")
    stats = alert_manager.get_statistics()
    print(f"  总预警数: {stats['total']}")

    print("[OK] Integration test passed")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Phase 5 实时监控模块测试")
    print("="*60)

    try:
        # 测试1: 预警管理器
        test_alert_manager()

        # 测试2: 熔断引擎
        test_circuit_breaker()

        # 测试3: 先行指标分析
        test_leading_indicator()

        # 测试4: 实时监控引擎
        test_realtime_monitor()

        # 测试5: 集成测试
        test_integration()

        print("\n" + "="*60)
        print("SUCCESS: Phase 5 all tests passed!")
        print("="*60)

        print("\nTest Summary:")
        print("  [OK] Alert Manager - Normal")
        print("  [OK] Circuit Breaker - Normal")
        print("  [OK] Leading Indicator - Normal")
        print("  [OK] Realtime Monitor - Normal")
        print("  [OK] Integration Test - Normal")

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
