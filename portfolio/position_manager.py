# -*- coding: utf-8 -*-
"""
持仓管理器
管理用户持仓：添加、删除、更新持仓
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path


class PositionType(Enum):
    """持仓类型"""
    LONG = "long"  # 多头
    SHORT = "short"  # 空头（A股不支持）


@dataclass
class Position:
    """持仓对象"""
    id: str  # 持仓ID
    code: str  # 股票代码
    name: str  # 股票名称
    position_type: PositionType  # 持仓类型
    shares: int  # 持股数量
    buy_price: float  # 买入价格
    current_price: float  # 当前价格
    stop_loss_price: Optional[float] = None  # 止损价
    take_profit_price: Optional[float] = None  # 止盈价
    buy_date: str = field(default_factory=lambda: datetime.now().isoformat())  # 买入日期
    note: str = ""  # 备注
    tags: List[str] = field(default_factory=list)  # 标签

    def __post_init__(self):
        """初始化后计算"""
        if isinstance(self.position_type, str):
            self.position_type = PositionType(self.position_type)

    @property
    def market_value(self) -> float:
        """市值"""
        return self.shares * self.current_price

    @property
    def cost_value(self) -> float:
        """成本"""
        return self.shares * self.buy_price

    @property
    def profit_loss(self) -> float:
        """盈亏金额"""
        return (self.current_price - self.buy_price) * self.shares

    @property
    def profit_loss_pct(self) -> float:
        """盈亏百分比"""
        if self.buy_price == 0:
            return 0.0
        return (self.current_price - self.buy_price) / self.buy_price * 100


class PositionManager:
    """持仓管理器

    功能：
    1. 添加持仓
    2. 删除持仓
    3. 更新持仓
    4. 查询持仓
    """

    def __init__(self, storage_path: str = None):
        """
        初始化持仓管理器

        Args:
            storage_path: 存储路径（默认为data/positions.json）
        """
        self.storage_path = storage_path or "data/positions.json"
        self.positions: Dict[str, Position] = {}
        self.position_counter = 0

        # 确保存储目录存在
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        # 加载持仓数据
        self._load_positions()

        print("[持仓管理器] 初始化完成")

    def _load_positions(self):
        """加载持仓数据"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.position_counter = data.get('counter', 0)
                for pos_data in data.get('positions', []):
                    position = Position(
                        id=pos_data['id'],
                        code=pos_data['code'],
                        name=pos_data['name'],
                        position_type=PositionType(pos_data['position_type']),
                        shares=pos_data['shares'],
                        buy_price=pos_data['buy_price'],
                        current_price=pos_data.get('current_price', pos_data['buy_price']),
                        stop_loss_price=pos_data.get('stop_loss_price'),
                        take_profit_price=pos_data.get('take_profit_price'),
                        buy_date=pos_data.get('buy_date', datetime.now().isoformat()),
                        note=pos_data.get('note', ''),
                        tags=pos_data.get('tags', [])
                    )
                    self.positions[position.id] = position

                print(f"[持仓管理器] 已加载 {len(self.positions)} 个持仓")

        except Exception as e:
            print(f"[持仓管理器] 加载持仓失败: {e}")

    def _save_positions(self):
        """保存持仓到文件"""
        try:
            data = {
                'counter': self.position_counter,
                'positions': [
                    {
                        'id': pos.id,
                        'code': pos.code,
                        'name': pos.name,
                        'position_type': pos.position_type.value,
                        'shares': pos.shares,
                        'buy_price': pos.buy_price,
                        'current_price': pos.current_price,
                        'stop_loss_price': pos.stop_loss_price,
                        'take_profit_price': pos.take_profit_price,
                        'buy_date': pos.buy_date,
                        'note': pos.note,
                        'tags': pos.tags
                    }
                    for pos in self.positions.values()
                ]
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[持仓管理器] 保存持仓失败: {e}")

    def _generate_position_id(self) -> str:
        """生成持仓ID"""
        self.position_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"POS_{timestamp}_{self.position_counter:04d}"

    def add_position(
        self,
        code: str,
        name: str,
        shares: int,
        buy_price: float,
        position_type: PositionType = PositionType.LONG,
        stop_loss_price: float = None,
        take_profit_price: float = None,
        note: str = "",
        tags: List[str] = None
    ) -> Position:
        """
        添加持仓

        Args:
            code: 股票代码
            name: 股票名称
            shares: 持股数量
            buy_price: 买入价格
            position_type: 持仓类型
            stop_loss_price: 止损价
            take_profit_price: 止盈价
            note: 备注
            tags: 标签

        Returns:
            持仓对象
        """
        position = Position(
            id=self._generate_position_id(),
            code=code,
            name=name,
            position_type=position_type,
            shares=shares,
            buy_price=buy_price,
            current_price=buy_price,  # 初始当前价格等于买入价格
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            note=note,
            tags=tags or []
        )

        self.positions[position.id] = position
        self._save_positions()

        print(f"[持仓管理器] 已添加持仓: {name} ({code})")
        return position

    def remove_position(self, position_id: str) -> bool:
        """
        删除持仓

        Args:
            position_id: 持仓ID

        Returns:
            是否成功
        """
        if position_id in self.positions:
            position = self.positions[position_id]
            del self.positions[position_id]
            self._save_positions()

            print(f"[持仓管理器] 已删除持仓: {position.name} ({position.code})")
            return True
        return False

    def update_position_price(self, position_id: str, current_price: float) -> bool:
        """
        更新持仓当前价格

        Args:
            position_id: 持仓ID
            current_price: 当前价格

        Returns:
            是否成功
        """
        if position_id in self.positions:
            self.positions[position_id].current_price = current_price
            self._save_positions()
            return True
        return False

    def update_position_stop_loss(self, position_id: str, stop_loss_price: float) -> bool:
        """
        更新止损价

        Args:
            position_id: 持仓ID
            stop_loss_price: 止损价

        Returns:
            是否成功
        """
        if position_id in self.positions:
            self.positions[position_id].stop_loss_price = stop_loss_price
            self._save_positions()
            return True
        return False

    def update_position_take_profit(self, position_id: str, take_profit_price: float) -> bool:
        """
        更新止盈价

        Args:
            position_id: 持仓ID
            take_profit_price: 止盈价

        Returns:
            是否成功
        """
        if position_id in self.positions:
            self.positions[position_id].take_profit_price = take_profit_price
            self._save_positions()
            return True
        return False

    def get_position(self, position_id: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            position_id: 持仓ID

        Returns:
            持仓对象
        """
        return self.positions.get(position_id)

    def get_all_positions(self) -> List[Position]:
        """
        获取所有持仓

        Returns:
            持仓列表
        """
        return list(self.positions.values())

    def get_positions_by_code(self, code: str) -> List[Position]:
        """
        按股票代码获取持仓

        Args:
            code: 股票代码

        Returns:
            持仓列表
        """
        return [pos for pos in self.positions.values() if pos.code == code]

    def get_positions_by_tag(self, tag: str) -> List[Position]:
        """
        按标签获取持仓

        Args:
            tag: 标签

        Returns:
            持仓列表
        """
        return [pos for pos in self.positions.values() if tag in pos.tags]

    def get_total_market_value(self) -> float:
        """
        获取总市值

        Returns:
            总市值
        """
        return sum(pos.market_value for pos in self.positions.values())

    def get_total_cost(self) -> float:
        """
        获取总成本

        Returns:
            总成本
        """
        return sum(pos.cost_value for pos in self.positions.values())

    def get_total_profit_loss(self) -> float:
        """
        获取总盈亏

        Returns:
            总盈亏
        """
        return sum(pos.profit_loss for pos in self.positions.values())

    def get_statistics(self) -> Dict:
        """
        获取持仓统计

        Returns:
            统计信息字典
        """
        total_positions = len(self.positions)
        total_market_value = self.get_total_market_value()
        total_cost = self.get_total_cost()
        total_profit_loss = self.get_total_profit_loss()

        profit_positions = sum(1 for pos in self.positions.values() if pos.profit_loss > 0)
        loss_positions = sum(1 for pos in self.positions.values() if pos.profit_loss < 0)

        return {
            'total_positions': total_positions,
            'total_market_value': round(total_market_value, 2),
            'total_cost': round(total_cost, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'profit_positions': profit_positions,
            'loss_positions': loss_positions,
            'profit_loss_pct': round(total_profit_loss / total_cost * 100, 2) if total_cost > 0 else 0
        }

    def export_positions(self) -> str:
        """
        导出持仓为JSON字符串

        Returns:
            JSON字符串
        """
        data = {
            'export_time': datetime.now().isoformat(),
            'positions': [
                {
                    'code': pos.code,
                    'name': pos.name,
                    'shares': pos.shares,
                    'buy_price': pos.buy_price,
                    'current_price': pos.current_price,
                    'market_value': pos.market_value,
                    'profit_loss': pos.profit_loss,
                    'profit_loss_pct': pos.profit_loss_pct
                }
                for pos in self.positions.values()
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


# 创建全局实例
_global_position_manager: Optional[PositionManager] = None


def get_position_manager() -> PositionManager:
    """获取全局持仓管理器实例（单例模式）"""
    global _global_position_manager
    if _global_position_manager is None:
        _global_position_manager = PositionManager()
    return _global_position_manager


# 测试代码
if __name__ == '__main__':
    manager = PositionManager()

    # 添加测试持仓
    print("\n添加测试持仓:")
    manager.add_position(
        code='600519',
        name='贵州茅台',
        shares=100,
        buy_price=1750.0,
        stop_loss_price=1675.0,
        take_profit_price=1840.0,
        note='长期持有'
    )

    manager.add_position(
        code='000858',
        name='五粮液',
        shares=200,
        buy_price=150.0,
        stop_loss_price=142.0,
        take_profit_price=160.0,
        tags=['消费', '白酒']
    )

    # 更新价格
    print("\n更新价格:")
    manager.update_position_price('POS_20260408150411_0001', 1800.0)

    # 获取统计信息
    print("\n持仓统计:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 获取所有持仓
    print("\n所有持仓:")
    positions = manager.get_all_positions()
    for pos in positions:
        print(f"\n  {pos.name} ({pos.code})")
        print(f"    持股: {pos.shares}股")
        print(f"    成本: {pos.buy_price:.2f}元")
        print(f"    现价: {pos.current_price:.2f}元")
        print(f"    盈亏: {pos.profit_loss:+.2f}元 ({pos.profit_loss_pct:+.2f}%)")

    # 导出持仓
    print("\n导出持仓:")
    print(manager.export_positions())
