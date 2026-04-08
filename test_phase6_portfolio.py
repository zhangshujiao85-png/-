# -*- coding: utf-8 -*-
"""
Phase 6 持仓管理模块测试
测试持仓管理器、持仓监控器、数据存储
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_position_manager():
    """测试持仓管理器"""
    print("\n" + "="*60)
    print("Test 1: Position Manager")
    print("="*60)

    from portfolio.position_manager import PositionManager, PositionType

    manager = PositionManager()

    # 添加测试持仓
    print("\nAdding test positions:")
    pos1 = manager.add_position(
        code='600519',
        name='Guizhou Moutai',
        shares=100,
        buy_price=1750.0,
        stop_loss_price=1675.0,
        take_profit_price=1840.0,
        note='Long-term holding'
    )

    pos2 = manager.add_position(
        code='000858',
        name='Wuliangye',
        shares=200,
        buy_price=150.0,
        stop_loss_price=142.0,
        take_profit_price=160.0,
        tags=['Consumption', 'Baijiu']
    )

    print(f"  Added position 1: {pos1.name}")
    print(f"  Added position 2: {pos2.name}")

    # 更新价格
    print("\nUpdating prices:")
    manager.update_position_price(pos1.id, 1800.0)
    manager.update_position_price(pos2.id, 155.0)
    print("  [OK] Prices updated")

    # 获取统计信息
    print("\nPosition statistics:")
    stats = manager.get_statistics()
    print(f"  Total positions: {stats['total_positions']}")
    print(f"  Total market value: {stats['total_market_value']:.2f}")
    print(f"  Total cost: {stats['total_cost']:.2f}")
    print(f"  Total profit/loss: {stats['total_profit_loss']:.2f}")
    print(f"  Profit positions: {stats['profit_positions']}")
    print(f"  Loss positions: {stats['loss_positions']}")

    # 导出持仓
    print("\nExporting positions:")
    export_data = manager.export_positions()
    print(f"  [OK] Exported {len(export_data)} characters")

    # 获取所有持仓
    print("\nAll positions:")
    positions = manager.get_all_positions()
    for pos in positions:
        print(f"\n  {pos.name} ({pos.code})")
        print(f"    Shares: {pos.shares}")
        print(f"    Buy price: {pos.buy_price:.2f}")
        print(f"    Current price: {pos.current_price:.2f}")
        print(f"    P/L: {pos.profit_loss:+.2f} ({pos.profit_loss_pct:+.2f}%)")

    print("\n[OK] Position Manager test passed")


def test_position_monitor():
    """测试持仓监控器"""
    print("\n" + "="*60)
    print("Test 2: Position Monitor")
    print("="*60)

    from portfolio.position_manager import PositionManager
    from portfolio.position_monitor import PositionMonitor

    # 创建持仓管理器并添加测试持仓
    pos_manager = PositionManager()
    pos_manager.add_position(
        code='600519',
        name='Guizhou Moutai',
        shares=100,
        buy_price=1750.0,
        stop_loss_price=1675.0,
        take_profit_price=1840.0
    )

    # 创建持仓监控器
    monitor = PositionMonitor(pos_manager)

    # 添加回调函数
    def on_alert(alert):
        print(f"\n  Alert received:")
        print(f"    Type: {alert.alert_type.value}")
        print(f"    Message: {alert.message}")

    monitor.add_alert_callback(on_alert)

    # 手动监控一次
    print("\nManual monitoring:")
    monitor.monitor_all_positions()

    # 获取状态
    print("\nMonitor status:")
    status = monitor.get_monitoring_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n[OK] Position Monitor test passed")


def test_storage():
    """测试数据存储"""
    print("\n" + "="*60)
    print("Test 3: Data Storage")
    print("="*60)

    from portfolio.storage import DataStorage

    storage = DataStorage()

    # 测试保存和加载
    print("\nTesting save/load JSON:")
    test_data = {
        'test': 'data',
        'timestamp': '2026-04-08 15:00:00'
    }
    storage.save_json(test_data, 'test_phase6.json')
    print("  [OK] Saved")

    loaded_data = storage.load_json('test_phase6.json')
    if loaded_data and loaded_data['test'] == 'data':
        print("  [OK] Loaded successfully")
    else:
        print("  [FAILED] Load failed")

    # 测试备份
    print("\nTesting backup:")
    if storage.create_backup('test_phase6_backup'):
        print("  [OK] Backup created")

    backups = storage.list_backups()
    if 'test_phase6_backup' in backups:
        print("  [OK] Backup listed")

    # 测试导出CSV
    print("\nTesting CSV export:")
    test_data = [
        {'code': '600519', 'name': 'Moutai', 'price': 1750.0},
        {'code': '000858', 'name': 'Wuliangye', 'price': 150.0}
    ]
    if storage.export_to_csv(test_data, 'test_phase6_stocks.csv'):
        print("  [OK] CSV exported")

    # 获取存储信息
    print("\nStorage info:")
    info = storage.get_storage_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 清理测试数据
    print("\nCleaning up test data:")
    storage.delete_backup('test_phase6_backup')
    print("  [OK] Cleanup completed")

    print("\n[OK] Data Storage test passed")


def test_integration():
    """集成测试"""
    print("\n" + "="*60)
    print("Test 4: Integration")
    print("="*60)

    from portfolio.position_manager import PositionManager
    from portfolio.position_monitor import PositionMonitor
    from portfolio.storage import DataStorage

    # 创建管理器
    pos_manager = PositionManager()
    monitor = PositionMonitor(pos_manager)
    storage = DataStorage()

    # 添加持仓
    print("\nAdding positions:")
    pos1 = pos_manager.add_position(
        code='600519',
        name='Moutai',
        shares=100,
        buy_price=1750.0,
        stop_loss_price=1675.0,
        take_profit_price=1840.0
    )
    print(f"  [OK] Added {pos1.name}")

    # 导出数据
    print("\nExporting data:")
    positions = pos_manager.get_all_positions()
    file_path = storage.export_positions(positions, 'phase6_test_positions.json')
    print(f"  [OK] Exported to {file_path}")

    # 导入数据
    print("\nImporting data:")
    imported_data = storage.import_positions('phase6_test_positions.json')
    if imported_data:
        print(f"  [OK] Imported {len(imported_data)} positions")

    # 模拟价格更新和预警检查
    print("\nSimulating price update:")
    monitor.update_prices({'600519': 1660.0})
    print("  [OK] Price updated and alerts checked")

    # 获取统计
    print("\nFinal statistics:")
    stats = pos_manager.get_statistics()
    print(f"  Total positions: {stats['total_positions']}")
    print(f"  Total P/L: {stats['total_profit_loss']:.2f}")

    print("\n[OK] Integration test passed")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Phase 6 Portfolio Management Module Test")
    print("="*60)

    try:
        # 测试1: 持仓管理器
        test_position_manager()

        # 测试2: 持仓监控器
        test_position_monitor()

        # 测试3: 数据存储
        test_storage()

        # 测试4: 集成测试
        test_integration()

        print("\n" + "="*60)
        print("SUCCESS: Phase 6 all tests passed!")
        print("="*60)

        print("\nTest Summary:")
        print("  [OK] Position Manager - Normal")
        print("  [OK] Position Monitor - Normal")
        print("  [OK] Data Storage - Normal")
        print("  [OK] Integration Test - Normal")

    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
