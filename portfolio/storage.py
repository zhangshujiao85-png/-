# -*- coding: utf-8 -*-
"""
数据存储模块
提供JSON持久化、数据导入/导出、备份恢复功能
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd


class DataStorage:
    """数据存储管理器

    功能：
    1. JSON持久化
    2. 数据导入/导出
    3. 历史记录保存
    4. 数据备份恢复
    """

    def __init__(self, data_dir: str = "data"):
        """
        初始化数据存储管理器

        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.positions_dir = self.data_dir / "positions"
        self.alerts_dir = self.data_dir / "alerts"
        self.backups_dir = self.data_dir / "backups"

        for dir_path in [self.positions_dir, self.alerts_dir, self.backups_dir]:
            dir_path.mkdir(exist_ok=True)

        print("[数据存储] 初始化完成")

    def save_json(self, data: Dict, filename: str, subdir: str = "") -> bool:
        """
        保存数据为JSON文件

        Args:
            data: 数据字典
            filename: 文件名
            subdir: 子目录

        Returns:
            是否成功
        """
        try:
            if subdir:
                file_path = self.data_dir / subdir / filename
            else:
                file_path = self.data_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"[数据存储] 保存JSON失败: {e}")
            return False

    def load_json(self, filename: str, subdir: str = "") -> Optional[Dict]:
        """
        加载JSON文件

        Args:
            filename: 文件名
            subdir: 子目录

        Returns:
            数据字典
        """
        try:
            if subdir:
                file_path = self.data_dir / subdir / filename
            else:
                file_path = self.data_dir / filename

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data

        except Exception as e:
            print(f"[数据存储] 加载JSON失败: {e}")
            return None

    def export_to_csv(self, data: List[Dict], filename: str, subdir: str = "") -> bool:
        """
        导出数据为CSV文件

        Args:
            data: 数据列表
            filename: 文件名
            subdir: 子目录

        Returns:
            是否成功
        """
        try:
            if subdir:
                file_path = self.data_dir / subdir / filename
            else:
                file_path = self.data_dir / filename

            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')

            return True

        except Exception as e:
            print(f"[数据存储] 导出CSV失败: {e}")
            return False

    def import_from_csv(self, filename: str, subdir: str = "") -> Optional[List[Dict]]:
        """
        从CSV文件导入数据

        Args:
            filename: 文件名
            subdir: 子目录

        Returns:
            数据列表
        """
        try:
            if subdir:
                file_path = self.data_dir / subdir / filename
            else:
                file_path = self.data_dir / filename

            if not file_path.exists():
                return None

            df = pd.read_csv(file_path, encoding='utf-8-sig')
            return df.to_dict('records')

        except Exception as e:
            print(f"[数据存储] 导入CSV失败: {e}")
            return None

    def create_backup(self, backup_name: str = None) -> bool:
        """
        创建数据备份

        Args:
            backup_name: 备份名称（默认使用时间戳）

        Returns:
            是否成功
        """
        try:
            if backup_name is None:
                backup_name = datetime.now().strftime('%Y%m%d_%H%M%S')

            backup_dir = self.backups_dir / backup_name
            backup_dir.mkdir(exist_ok=True)

            # 备份所有JSON文件
            for file_path in self.data_dir.glob('*.json'):
                if file_path.parent != self.backups_dir:
                    shutil.copy2(file_path, backup_dir / file_path.name)

            print(f"[数据存储] 已创建备份: {backup_name}")
            return True

        except Exception as e:
            print(f"[数据存储] 创建备份失败: {e}")
            return False

    def restore_backup(self, backup_name: str) -> bool:
        """
        恢复数据备份

        Args:
            backup_name: 备份名称

        Returns:
            是否成功
        """
        try:
            backup_dir = self.backups_dir / backup_name

            if not backup_dir.exists():
                print(f"[数据存储] 备份不存在: {backup_name}")
                return False

            # 恢复所有JSON文件
            for file_path in backup_dir.glob('*.json'):
                shutil.copy2(file_path, self.data_dir / file_path.name)

            print(f"[数据存储] 已恢复备份: {backup_name}")
            return True

        except Exception as e:
            print(f"[数据存储] 恢复备份失败: {e}")
            return False

    def list_backups(self) -> List[str]:
        """
        列出所有备份

        Returns:
            备份名称列表
        """
        try:
            if not self.backups_dir.exists():
                return []

            backups = []
            for item in self.backups_dir.iterdir():
                if item.is_dir():
                    backups.append(item.name)

            return sorted(backups, reverse=True)

        except Exception as e:
            print(f"[数据存储] 列出备份失败: {e}")
            return []

    def delete_backup(self, backup_name: str) -> bool:
        """
        删除备份

        Args:
            backup_name: 备份名称

        Returns:
            是否成功
        """
        try:
            backup_dir = self.backups_dir / backup_name

            if backup_dir.exists():
                shutil.rmtree(backup_dir)
                print(f"[数据存储] 已删除备份: {backup_name}")
                return True

            return False

        except Exception as e:
            print(f"[数据存储] 删除备份失败: {e}")
            return False

    def export_positions(self, positions: List[Any], filename: str = None) -> str:
        """
        导出持仓数据

        Args:
            positions: 持仓列表
            filename: 文件名（默认使用时间戳）

        Returns:
            导出文件的路径
        """
        try:
            if filename is None:
                filename = f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # 转换为字典
            data = {
                'export_time': datetime.now().isoformat(),
                'positions': [
                    {
                        'id': pos.id,
                        'code': pos.code,
                        'name': pos.name,
                        'shares': pos.shares,
                        'buy_price': pos.buy_price,
                        'current_price': pos.current_price,
                        'market_value': pos.market_value,
                        'cost_value': pos.cost_value,
                        'profit_loss': pos.profit_loss,
                        'profit_loss_pct': pos.profit_loss_pct,
                        'stop_loss_price': pos.stop_loss_price,
                        'take_profit_price': pos.take_profit_price,
                        'buy_date': pos.buy_date,
                        'note': pos.note,
                        'tags': pos.tags
                    }
                    for pos in positions
                ]
            }

            file_path = self.positions_dir / filename
            self.save_json(data, filename, "positions")

            return str(file_path)

        except Exception as e:
            print(f"[数据存储] 导出持仓失败: {e}")
            return ""

    def import_positions(self, filename: str) -> Optional[List[Dict]]:
        """
        导入持仓数据

        Args:
            filename: 文件名

        Returns:
            持仓数据列表
        """
        try:
            data = self.load_json(filename, "positions")

            if data and 'positions' in data:
                return data['positions']

            return None

        except Exception as e:
            print(f"[数据存储] 导入持仓失败: {e}")
            return None

    def save_alert_history(self, alerts: List[Any]) -> bool:
        """
        保存预警历史

        Args:
            alerts: 预警列表

        Returns:
            是否成功
        """
        try:
            filename = f"alerts_{datetime.now().strftime('%Y%m%d')}.json"

            # 转换为字典
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'alerts': [
                    {
                        'id': alert.id,
                        'level': alert.level.value,
                        'category': alert.category.value,
                        'title': alert.title,
                        'message': alert.message,
                        'suggestion': alert.suggestion,
                        'timestamp': alert.timestamp,
                        'metadata': alert.metadata
                    }
                    for alert in alerts
                ]
            }

            return self.save_json(data, filename, "alerts")

        except Exception as e:
            print(f"[数据存储] 保存预警历史失败: {e}")
            return False

    def get_storage_info(self) -> Dict:
        """
        获取存储信息

        Returns:
            存储信息字典
        """
        try:
            # 计算目录大小
            total_size = sum(
                f.stat().st_size
                for f in self.data_dir.rglob('*')
                if f.is_file()
            )

            # 统计文件数量
            json_files = len(list(self.data_dir.glob('*.json')))

            # 统计备份数量
            backup_count = len(self.list_backups())

            return {
                'data_dir': str(self.data_dir),
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'json_files': json_files,
                'backup_count': backup_count
            }

        except Exception as e:
            print(f"[数据存储] 获取存储信息失败: {e}")
            return {}


# 创建全局实例
_global_storage: Optional[DataStorage] = None


def get_storage() -> DataStorage:
    """获取全局数据存储实例（单例模式）"""
    global _global_storage
    if _global_storage is None:
        _global_storage = DataStorage()
    return _global_storage


# 测试代码
if __name__ == '__main__':
    storage = DataStorage()

    # 测试保存和加载
    print("\n测试保存JSON:")
    test_data = {
        'test': 'data',
        'timestamp': datetime.now().isoformat()
    }
    storage.save_json(test_data, 'test.json')
    print("  [OK] 保存成功")

    print("\n测试加载JSON:")
    loaded_data = storage.load_json('test.json')
    print(f"  [OK] 加载成功: {loaded_data}")

    # 测试备份
    print("\n测试创建备份:")
    storage.create_backup('test_backup')
    print("  [OK] 备份创建成功")

    print("\n列出备份:")
    backups = storage.list_backups()
    for backup in backups:
        print(f"  - {backup}")

    # 测试导出CSV
    print("\n测试导出CSV:")
    test_data = [
        {'code': '600519', 'name': '贵州茅台', 'price': 1750.0},
        {'code': '000858', 'name': '五粮液', 'price': 150.0}
    ]
    storage.export_to_csv(test_data, 'test_stocks.csv')
    print("  [OK] CSV导出成功")

    # 获取存储信息
    print("\n存储信息:")
    info = storage.get_storage_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 清理测试数据
    print("\n清理测试数据:")
    storage.delete_backup('test_backup')
    print("  [OK] 清理完成")
