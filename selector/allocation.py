"""
Position Allocation Generator Module
Generates personalized position allocation based on capital and risk preference
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

from config.settings import settings


class AllocationGenerator:
    """Position allocation generator"""

    def __init__(self, data_fetcher=None):
        """
        Initialize allocation generator

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.data_fetcher = data_fetcher
        if self.data_fetcher is None:
            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def generate_allocation(self, total_capital: float, risk_preference: str,
                           stocks: List[Dict]) -> Dict:
        """
        Generate position allocation plan

        Args:
            total_capital: Total investment capital (yuan)
            risk_preference: Risk preference (保守/稳健/激进)
            stocks: List of selected stocks with details

        Returns:
            Allocation plan with positions
        """
        if not stocks:
            return {
                'error': 'No stocks provided for allocation'
            }

        # Validate risk preference
        if risk_preference not in settings.RISK_PREFERENCES:
            risk_preference = '稳健'

        # Get allocation weights for risk preference
        weights = settings.RISK_PREFERENCES[risk_preference]

        # Group stocks by type
        stock_groups = self._group_stocks_by_type(stocks)

        # Calculate allocation for each type
        allocation = []

        # Stable type allocation
        if '稳定型' in stock_groups and stock_groups['稳定型']:
            stable_capital = total_capital * weights['stable']
            stable_positions = self._allocate_capital_to_stocks(
                stock_groups['稳定型'], stable_capital
            )
            allocation.extend(stable_positions)

        # Sensitive type allocation
        if '敏感型' in stock_groups and stock_groups['敏感型']:
            sensitive_capital = total_capital * weights['sensitive']
            sensitive_positions = self._allocate_capital_to_stocks(
                stock_groups['敏感型'], sensitive_capital
            )
            allocation.extend(sensitive_positions)

        # Active type allocation
        if '活跃型' in stock_groups and stock_groups['活跃型']:
            active_capital = total_capital * weights['active']
            active_positions = self._allocate_capital_to_stocks(
                stock_groups['活跃型'], active_capital
            )
            allocation.extend(active_positions)

        return {
            'total_capital': total_capital,
            'risk_preference': risk_preference,
            'weights': weights,
            'positions': allocation,
            'summary': self._generate_allocation_summary(allocation, weights),
            'timestamp': datetime.now().isoformat()
        }

    def _group_stocks_by_type(self, stocks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group stocks by type

        Args:
            stocks: List of stocks

        Returns:
            Dictionary mapping types to stock lists
        """
        groups = {
            '稳定型': [],
            '敏感型': [],
            '活跃型': []
        }

        for stock in stocks:
            stock_type = stock.get('type', '活跃型')
            groups[stock_type].append(stock)

        return groups

    def _allocate_capital_to_stocks(self, stocks: List[Dict], capital: float) -> List[Dict]:
        """
        Allocate capital to a group of stocks

        Args:
            stocks: List of stocks
            capital: Total capital to allocate

        Returns:
            List of position allocations
        """
        if not stocks:
            return []

        # Calculate allocation weights based on scores
        total_score = sum(s['score'] for s in stocks)

        positions = []

        for stock in stocks:
            # Calculate weight based on score
            weight = stock['score'] / total_score if total_score > 0 else 1 / len(stocks)

            # Calculate capital for this stock
            stock_capital = capital * weight

            # Calculate number of shares
            price = stock.get('price', 10)
            if price > 0:
                shares = int(stock_capital / price / 100) * 100  # Round to lots (100 shares)
                actual_capital = shares * price
            else:
                shares = 0
                actual_capital = 0

            positions.append({
                'code': stock['code'],
                'name': stock['name'],
                'type': stock.get('type', '活跃型'),
                'price': price,
                'shares': shares,
                'capital': actual_capital,
                'weight': weight,
                'reason': self._generate_stock_reason(stock)
            })

        return positions

    def _generate_stock_reason(self, stock: Dict) -> str:
        """
        Generate reason for selecting a stock

        Args:
            stock: Stock data

        Returns:
            Reason string
        """
        stock_type = stock.get('type', '活跃型')
        score = stock.get('score', 0)
        market_cap = stock.get('market_cap', 0)

        reasons = []

        if stock_type == '稳定型':
            reasons.append(f"大市值龙头({market_cap:.0f}亿)")
            reasons.append("防守型配置")
        elif stock_type == '敏感型':
            reasons.append(f"中等市值({market_cap:.0f}亿)")
            reasons.append("对市场情绪敏感，弹性大")
        else:  # 活跃型
            reasons.append(f"小盘活跃股({market_cap:.0f}亿)")
            reasons.append("进攻型配置")

        reasons.append(f"综合得分{score:.0f}分")

        return "，".join(reasons)

    def _generate_allocation_summary(self, positions: List[Dict], weights: Dict[str, float]) -> str:
        """
        Generate allocation summary

        Args:
            positions: List of positions
            weights: Weight configuration

        Returns:
            Summary string
        """
        total_capital = sum(p['capital'] for p in positions)
        actual_capital = sum(p['capital'] for p in positions)

        lines = [
            f"总资金: {actual_capital:.0f} 元 (实际使用)",
            f"配置方案: 保守{weights['stable']*100:.0f}% + "
            f"敏感{weights['sensitive']*100:.0f}% + "
            f"活跃{weights['active']*100:.0f}%",
            "",
            f"持仓明细 ({len(positions)}只):"
        ]

        for i, pos in enumerate(positions, 1):
            lines.append(
                f"{i}. {pos['code']} {pos['name']} - {pos['shares']}股 ({pos['capital']:.0f}元)"
                f" [{pos['type']}]"
            )

        return "\n".join(lines)

    def format_allocation_plan(self, allocation: Dict) -> str:
        """
        Format allocation plan as readable text

        Args:
            allocation: Allocation dictionary

        Returns:
            Formatted text
        """
        lines = [
            "=" * 60,
            "【持仓配置方案】",
            "=" * 60,
            "",
            f"总资金: {allocation['total_capital']:,.0f} 元",
            f"风险偏好: {allocation['risk_preference']}",
            "",
            "【配置比例】",
        ]

        weights = allocation['weights']
        for type_name, weight in weights.items():
            type_cn = {
                'stable': '稳定型',
                'sensitive': '敏感型',
                'active': '活跃型'
            }.get(type_name, type_name)
            capital = allocation['total_capital'] * weight
            lines.append(f"  {type_cn}: {weight*100:.0f}% ({capital:,.0f}元)")

        lines.extend([
            "",
            "【持仓明细】",
            ""
        ])

        positions = allocation['positions']
        for i, pos in enumerate(positions, 1):
            lines.extend([
                f"{i}. {pos['code']} {pos['name']} ({pos['type']})",
                f"   数量: {pos['shares']}股",
                f"   金额: {pos['capital']:,.0f}元",
                f"   理由: {pos['reason']}",
                ""
            ])

        total_allocated = sum(p['capital'] for p in positions)
        lines.extend([
            "【汇总】",
            f"  计划投入: {allocation['total_capital']:,.0f}元",
            f"  实际配置: {total_allocated:,.0f}元",
            f"  剩余现金: {allocation['total_capital'] - total_allocated:,.0f}元",
            "",
            "=" * 60
        ])

        return "\n".join(lines)

    def suggest_stocks_for_allocation(self, sector: str, total_capital: float,
                                      risk_preference: str, top_n: int = 5) -> Dict:
        """
        One-step function: select stocks and generate allocation

        Args:
            sector: Sector name
            total_capital: Total investment capital
            risk_preference: Risk preference
            top_n: Number of top stocks to select

        Returns:
            Complete allocation plan
        """
        from selector.stock_selector import StockSelector

        # Select stocks
        selector = StockSelector(self.data_fetcher)
        stocks = selector.select_representative_stocks(sector, top_n=top_n)

        if not stocks:
            return {
                'error': f'Failed to select stocks from sector {sector}'
            }

        # Generate allocation
        allocation = self.generate_allocation(total_capital, risk_preference, stocks)

        # Add sector info
        allocation['sector'] = sector
        allocation['selected_stocks'] = stocks

        return allocation


# Test code
if __name__ == "__main__":
    generator = AllocationGenerator()

    print("=== Allocation Generator Test ===\n")

    # Mock stocks for testing
    mock_stocks = [
        {
            'code': '600460',
            'name': '土兰微',
            'price': 25.50,
            'change_pct': 3.2,
            'score': 78.5,
            'market_cap': 50000000000,  # 500亿
            'turnover': 8.5,
            'type': '活跃型'
        },
        {
            'code': '603986',
            'name': '兆易创新',
            'price': 120.30,
            'change_pct': 2.8,
            'score': 75.2,
            'market_cap': 80000000000,  # 800亿
            'turnover': 6.2,
            'type': '敏感型'
        },
        {
            'code': '688981',
            'name': '中芯国际',
            'price': 55.80,
            'change_pct': 1.5,
            'score': 72.0,
            'market_cap': 200000000000,  # 2000亿
            'turnover': 3.5,
            'type': '稳定型'
        },
        {
            'code': '002049',
            'name': '紫光国微',
            'price': 85.60,
            'change_pct': 4.1,
            'score': 70.5,
            'market_cap': 60000000000,  # 600亿
            'turnover': 7.8,
            'type': '敏感型'
        },
        {
            'code': '300343',
            'name': '联创股份',
            'price': 15.20,
            'change_pct': 5.3,
            'score': 68.0,
            'market_cap': 8000000000,  # 80亿
            'turnover': 12.5,
            'type': '活跃型'
        }
    ]

    # Test different risk preferences
    for risk_pref in ['保守', '稳健', '激进']:
        print(f"\n{'='*60}")
        print(f"风险偏好: {risk_pref}")
        print('='*60)

        allocation = generator.generate_allocation(100000, risk_pref, mock_stocks)

        print(generator.format_allocation_plan(allocation))
        print("\n")
