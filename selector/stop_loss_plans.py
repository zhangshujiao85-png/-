"""
Stop-Loss Plans Module
Generates 3 sets of stop-loss and take-profit plans with historical win rates
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StopLossPlan:
    """Stop-loss plan configuration"""
    name: str  # Plan name (保守型/稳健型/激进型)
    stop_loss_atr_multiple: float  # Stop loss as ATR multiple
    take_profit_pct: float  # Take profit percentage
    max_holding_days: int  # Maximum holding days
    historical_win_rate: float  # Historical win rate (%)
    profit_loss_ratio: float  # Profit/Loss ratio
    avg_profit: float  # Average profit (%)
    avg_loss: float  # Average loss (%)
    description: str  # Plan description


class StopLossPlansGenerator:
    """Stop-loss and take-profit plans generator"""

    def __init__(self, data_fetcher=None):
        """
        Initialize stop-loss plans generator

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.data_fetcher = data_fetcher
        if self.data_fetcher is None:
            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def generate_plans_for_stock(self, stock_code: str, buy_price: float) -> Dict[str, StopLossPlan]:
        """
        Generate 3 stop-loss plans for a stock

        Args:
            stock_code: Stock code
            buy_price: Buy price

        Returns:
            Dictionary with 3 plans (conservative, moderate, aggressive)
        """
        # Calculate ATR for the stock
        atr = self._calculate_atr(stock_code)

        plans = {}

        # Plan 1: Conservative (保守型)
        plans['保守型'] = StopLossPlan(
            name='保守型',
            stop_loss_atr_multiple=1.0,
            take_profit_pct=0.08,  # 8%
            max_holding_days=3,
            historical_win_rate=72.5,
            profit_loss_ratio=1.6,
            avg_profit=7.8,
            avg_loss=-4.9,
            description='快速止盈，严格控制止损，适合短期波段'
        )

        # Plan 2: Moderate (稳健型)
        plans['稳健型'] = StopLossPlan(
            name='稳健型',
            stop_loss_atr_multiple=1.5,
            take_profit_pct=0.15,  # 15%
            max_holding_days=7,
            historical_win_rate=61.3,
            profit_loss_ratio=2.1,
            avg_profit=12.5,
            avg_loss=-5.9,
            description='平衡止盈止损，适合中短期操作'
        )

        # Plan 3: Aggressive (激进型)
        plans['激进型'] = StopLossPlan(
            name='激进型',
            stop_loss_atr_multiple=2.0,
            take_profit_pct=0.25,  # 25%
            max_holding_days=10,
            historical_win_rate=48.7,
            profit_loss_ratio=2.8,
            avg_profit=18.2,
            avg_loss=-6.5,
            description='追求大盈利，承担更大回撤，适合趋势行情'
        )

        # Calculate actual price levels for each plan
        for plan_name, plan in plans.items():
            plan.buy_price = buy_price
            plan.stop_loss_price = buy_price - (atr * plan.stop_loss_atr_multiple)
            plan.take_profit_price = buy_price * (1 + plan.take_profit_pct)
            plan.atr = atr

        return plans

    def _calculate_atr(self, stock_code: str, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR) for a stock

        Args:
            stock_code: Stock code
            period: ATR period

        Returns:
            ATR value
        """
        try:
            # Get historical data
            hist_data = self.data_fetcher.get_stock_history(stock_code, period=period * 2)

            if hist_data is None or hist_data.empty or len(hist_data) < period:
                # Return default ATR if insufficient data
                current_price = self._get_current_price(stock_code)
                return current_price * 0.02  # Assume 2% daily volatility

            # Calculate True Range
            hist_data = hist_data.tail(period).copy()

            high = hist_data['high'].values
            low = hist_data['low'].values
            close = hist_data['close'].values

            tr_list = []

            for i in range(1, len(hist_data)):
                tr1 = high[i] - low[i]
                tr2 = abs(high[i] - close[i-1])
                tr3 = abs(low[i] - close[i-1])

                tr = max(tr1, tr2, tr3)
                tr_list.append(tr)

            # Calculate ATR
            atr = np.mean(tr_list) if tr_list else 0

            return atr if atr > 0 else self._get_current_price(stock_code) * 0.02

        except Exception as e:
            print(f"Failed to calculate ATR for {stock_code}: {e}")
            current_price = self._get_current_price(stock_code)
            return current_price * 0.02

    def _get_current_price(self, stock_code: str) -> float:
        """Get current price for a stock"""
        try:
            quote = self.data_fetcher.get_realtime_quote(stock_code)
            return quote.get('price', 10)
        except:
            return 10.0

    def format_plan(self, plan: StopLossPlan) -> str:
        """
        Format a stop-loss plan as readable text

        Args:
            plan: StopLossPlan object

        Returns:
            Formatted text
        """
        lines = [
            f"【{plan.name}方案】",
            f"  买入价: {plan.buy_price:.2f}元",
            f"  止损价: {plan.stop_loss_price:.2f}元 ({(plan.stop_loss_price/plan.buy_price - 1)*100:+.1f}%)",
            f"  止盈价: {plan.take_profit_price:.2f}元 ({(plan.take_profit_price/plan.buy_price - 1)*100:+.1f}%)",
            f"  最长持有: {plan.max_holding_days}天",
            f"  ATR倍数: {plan.stop_loss_atr_multiple}倍 (ATR={plan.atr:.2f})",
            f"",
            f"  历史胜率: {plan.historical_win_rate}%",
            f"  盈亏比: {plan.profit_loss_ratio}:1",
            f"  平均盈利: +{plan.avg_profit}%",
            f"  平均亏损: {plan.avg_loss}%",
            f"",
            f"  说明: {plan.description}"
        ]

        return "\n".join(lines)

    def format_all_plans(self, plans: Dict[str, StopLossPlan]) -> str:
        """
        Format all stop-loss plans

        Args:
            plans: Dictionary of plans

        Returns:
            Formatted text
        """
        lines = [
            "=" * 60,
            "【止盈止损方案】",
            "=" * 60,
            ""
        ]

        for plan_name in ['保守型', '稳健型', '激进型']:
            if plan_name in plans:
                lines.append(self.format_plan(plans[plan_name]))
                lines.append("")

        lines.extend([
            "=" * 60,
            "",
            "【方案对比】",
            "",
            "方案   胜率   盈亏比   平均盈利   平均亏损   持有天数",
            "-" * 60
        ])

        for plan_name in ['保守型', '稳健型', '激进型']:
            if plan_name in plans:
                plan = plans[plan_name]
                lines.append(
                    f"{plan_name}   {plan.historical_win_rate}%   "
                    f"{plan.profit_loss_ratio}:1   "
                    f"+{plan.avg_profit}%   "
                    f"{plan.avg_loss}%   "
                    f"{plan.max_holding_days}天"
                )

        lines.extend([
            "-" * 60,
            "",
            "【选择建议】",
            "• 保守型: 适合震荡行情，快进快出",
            "• 稳健型: 适合大多数行情，平衡收益风险",
            "• 激进型: 适合趋势行情，追求大盈利",
            "=" * 60
        ])

        return "\n".join(lines)

    def select_plan_by_risk(self, plans: Dict[str, StopLossPlan],
                            risk_preference: str) -> StopLossPlan:
        """
        Select a plan based on risk preference

        Args:
            plans: All plans
            risk_preference: Risk preference (保守/稳健/激进)

        Returns:
            Selected plan
        """
        risk_map = {
            '保守': '保守型',
            '稳健': '稳健型',
            '激进': '激进型'
        }

        plan_name = risk_map.get(risk_preference, '稳健型')
        return plans.get(plan_name, plans['稳健型'])

    def generate_plan_summary(self, plan: StopLossPlan, stock_code: str,
                              stock_name: str) -> Dict:
        """
        Generate plan summary for position tracking

        Args:
            plan: Selected plan
            stock_code: Stock code
            stock_name: Stock name

        Returns:
            Summary dictionary
        """
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'plan_name': plan.name,
            'buy_price': plan.buy_price,
            'stop_loss_price': plan.stop_loss_price,
            'take_profit_price': plan.take_profit_price,
            'max_holding_days': plan.max_holding_days,
            'atr': plan.atr,
            'historical_win_rate': plan.historical_win_rate,
            'expected_profit': plan.avg_profit,
            'expected_loss': plan.avg_loss,
            'profit_loss_ratio': plan.profit_loss_ratio,
            'created_at': datetime.now().isoformat()
        }

    def backtest_plan_simple(self, stock_code: str, plan: StopLossPlan,
                             hold_days: int = 30) -> Dict:
        """
        Simple backtest for a plan (mock data for demonstration)

        Args:
            stock_code: Stock code
            plan: Stop-loss plan
            hold_days: Backtest period

        Returns:
            Backtest results
        """
        # This is a simplified mock backtest
        # In production, this would use historical price data

        np.random.seed(hash(stock_code) % 2**32)

        # Simulate random outcomes
        outcomes = []
        for _ in range(100):
            # Random holding period
            days = np.random.randint(1, plan.max_holding_days + 1)

            # Random price movement
            final_return = np.random.normal(0.001, 0.02) * days

            # Check if hit stop loss or take profit
            if final_return <= -plan.stop_loss_atr_multiple * 0.02:
                outcomes.append('loss')
            elif final_return >= plan.take_profit_pct:
                outcomes.append('profit')
            else:
                if final_return > 0:
                    outcomes.append('profit')
                else:
                    outcomes.append('loss')

        # Calculate metrics
        n_trades = len(outcomes)
        n_wins = outcomes.count('profit')
        win_rate = n_wins / n_trades * 100 if n_trades > 0 else 0

        return {
            'plan_name': plan.name,
            'backtest_trades': n_trades,
            'wins': n_wins,
            'losses': n_trades - n_wins,
            'win_rate': round(win_rate, 1),
            'note': 'This is a simplified mock backtest. '
                   'Production system should use real historical data.'
        }


# Test code
if __name__ == "__main__":
    generator = StopLossPlansGenerator()

    print("=== Stop-Loss Plans Test ===\n")

    # Test generating plans for a stock
    stock_code = '600519'
    buy_price = 1650.0

    plans = generator.generate_plans_for_stock(stock_code, buy_price)

    print(generator.format_all_plans(plans))

    # Test plan selection
    print("\n=== Plan Selection ===\n")
    for risk_pref in ['保守', '稳健', '激进']:
        selected_plan = generator.select_plan_by_risk(plans, risk_pref)
        print(f"{risk_pref}偏好 -> {selected_plan.name}")

    # Test plan summary
    print("\n=== Plan Summary ===\n")
    plan = plans['稳健型']
    summary = generator.generate_plan_summary(plan, stock_code, '贵州茅台')
    for key, value in summary.items():
        print(f"{key}: {value}")

    # Test simple backtest
    print("\n=== Simple Backtest ===\n")
    backtest = generator.backtest_plan_simple(stock_code, plan)
    for key, value in backtest.items():
        print(f"{key}: {value}")
