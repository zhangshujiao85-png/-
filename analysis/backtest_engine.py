"""
真实胜率回测引擎
用真实历史数据计算止盈止损方案的历史胜率

使用方法：
    from analysis.backtest_engine import BacktestEngine

    engine = BacktestEngine()
    result = engine.backtest_stop_loss_plan('000001.SZ', '保守型')
    print(result)

作者：Claude
日期：2025-04-08
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果"""
    stock_code: str  # 股票代码
    plan_name: str  # 方案名称
    total_trades: int  # 总交易次数
    winning_trades: int  # 盈利次数
    losing_trades: int  # 亏损次数
    win_rate: float  # 胜率（%）
    avg_profit: float  # 平均盈利（%）
    avg_loss: float  # 平均亏损（%）
    profit_loss_ratio: float  # 盈亏比
    max_profit: float  # 最大盈利（%）
    max_loss: float  # 最大亏损（%）
    avg_holding_days: float  # 平均持仓天数
    total_return: float  # 总收益率（%）
    sharpe_ratio: float  # 夏普比率


class BacktestEngine:
    """回测引擎"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化回测引擎

        Args:
            db_path: 本地数据库路径
        """
        self.db_path = Path(db_path)

    def get_stock_history(self, stock_code: str) -> pd.DataFrame:
        """
        从本地数据库获取股票历史数据

        Args:
            stock_code: 股票代码

        Returns:
            DataFrame包含历史数据
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = '''
                SELECT
                    trade_date as date,
                    open,
                    close,
                    high,
                    low,
                    volume
                FROM stock_daily
                WHERE stock_code = ?
                ORDER BY trade_date ASC
            '''

            df = pd.read_sql(query, conn, params=(stock_code,))
            conn.close()

            if df.empty:
                logger.warning(f"未找到 {stock_code} 的历史数据")
                return pd.DataFrame()

            df['date'] = pd.to_datetime(df['date'])
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败 {stock_code}: {e}")
            return pd.DataFrame()

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算ATR（真实波动率）

        Args:
            df: 包含OHLC数据的DataFrame
            period: ATR周期

        Returns:
            ATR序列
        """
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def backtest_stop_loss_plan(self, stock_code: str, plan_config: Dict) -> BacktestResult:
        """
        回测单个止盈止损方案

        Args:
            stock_code: 股票代码
            plan_config: 方案配置
                {
                    'name': '保守型',
                    'stop_loss_atr_multiple': 1.0,
                    'take_profit_pct': 0.08,  # 8%
                    'max_holding_days': 3
                }

        Returns:
            BacktestResult对象
        """
        # 获取历史数据
        df = self.get_stock_history(stock_code)

        if df.empty or len(df) < 50:
            logger.warning(f"数据不足，无法回测 {stock_code}")
            return None

        # 计算ATR
        df['atr'] = self.calculate_atr(df, period=14)

        # 生成交易信号（简化版：随机买入点用于演示）
        # 实际应该基于策略信号（如突破、金叉等）
        trades = self._generate_trades(df, plan_config)

        if not trades:
            logger.warning(f"未生成交易信号 {stock_code}")
            return None

        # 统计结果
        winning_trades = [t for t in trades if t['pnl_pct'] > 0]
        losing_trades = [t for t in trades if t['pnl_pct'] <= 0]

        total_trades = len(trades)
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0

        avg_profit = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0

        profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

        max_profit = max([t['pnl_pct'] for t in trades]) if trades else 0
        max_loss = min([t['pnl_pct'] for t in trades]) if trades else 0

        avg_holding_days = np.mean([t['holding_days'] for t in trades]) if trades else 0

        total_return = sum([t['pnl_pct'] for t in trades])

        # 计算夏普比率（简化版）
        returns = [t['pnl_pct'] for t in trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0

        result = BacktestResult(
            stock_code=stock_code,
            plan_name=plan_config['name'],
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=round(win_rate, 2),
            avg_profit=round(avg_profit, 2),
            avg_loss=round(avg_loss, 2),
            profit_loss_ratio=round(profit_loss_ratio, 2),
            max_profit=round(max_profit, 2),
            max_loss=round(max_loss, 2),
            avg_holding_days=round(avg_holding_days, 1),
            total_return=round(total_return, 2),
            sharpe_ratio=round(sharpe_ratio, 2)
        )

        return result

    def _generate_trades(self, df: pd.DataFrame, plan_config: Dict) -> List[Dict]:
        """
        生成交易信号并应用止盈止损规则

        Args:
            df: 历史数据
            plan_config: 方案配置

        Returns:
            交易列表
        """
        trades = []

        stop_loss_atr_multiple = plan_config['stop_loss_atr_multiple']
        take_profit_pct = plan_config['take_profit_pct']
        max_holding_days = plan_config['max_holding_days']

        # 简化的买入信号：每隔20天买入一次（实际应该用策略信号）
        # 这里只是为了演示回测逻辑
        buy_signals = range(20, len(df) - 20, 20)

        for buy_idx in buy_signals:
            buy_price = df.iloc[buy_idx]['close']
            buy_date = df.iloc[buy_idx]['date']
            atr = df.iloc[buy_idx]['atr']

            if pd.isna(atr) or atr == 0:
                continue

            # 计算止盈止损价
            stop_loss_price = buy_price - (atr * stop_loss_atr_multiple)
            take_profit_price = buy_price * (1 + take_profit_pct)

            # 模拟持仓过程
            for hold_days in range(1, max_holding_days + 1):
                sell_idx = buy_idx + hold_days

                if sell_idx >= len(df):
                    break

                current_price = df.iloc[sell_idx]['close']
                current_high = df.iloc[sell_idx]['high']
                current_low = df.iloc[sell_idx]['low']

                # 检查止损
                if current_low <= stop_loss_price:
                    pnl_price = stop_loss_price
                    pnl_pct = (pnl_price - buy_price) / buy_price * 100
                    exit_reason = '止损'
                    break

                # 检查止盈
                if current_high >= take_profit_price:
                    pnl_price = take_profit_price
                    pnl_pct = (pnl_price - buy_price) / buy_price * 100
                    exit_reason = '止盈'
                    break

                # 到期平仓
                if hold_days == max_holding_days:
                    pnl_price = current_price
                    pnl_pct = (pnl_price - buy_price) / buy_price * 100
                    exit_reason = '到期'
                    break

            # 记录交易
            trades.append({
                'buy_date': buy_date,
                'buy_price': buy_price,
                'sell_date': df.iloc[sell_idx]['date'],
                'sell_price': pnl_price,
                'pnl_pct': pnl_pct,
                'holding_days': hold_days,
                'exit_reason': exit_reason,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price
            })

        return trades

    def backtest_all_plans(self, stock_code: str) -> Dict[str, BacktestResult]:
        """
        回测所有止盈止损方案

        Args:
            stock_code: 股票代码

        Returns:
            字典，键为方案名称，值为BacktestResult
        """
        # 定义3套方案
        plans = [
            {
                'name': '保守型',
                'stop_loss_atr_multiple': 1.0,
                'take_profit_pct': 0.08,  # 8%
                'max_holding_days': 3
            },
            {
                'name': '稳健型',
                'stop_loss_atr_multiple': 1.5,
                'take_profit_pct': 0.15,  # 15%
                'max_holding_days': 7
            },
            {
                'name': '激进型',
                'stop_loss_atr_multiple': 2.0,
                'take_profit_pct': 0.25,  # 25%
                'max_holding_days': 10
            }
        ]

        results = {}

        for plan in plans:
            try:
                result = self.backtest_stop_loss_plan(stock_code, plan)
                if result:
                    results[plan['name']] = result
                    logger.info(f"✓ {stock_code} {plan['name']} 回测完成: "
                              f"胜率{result.win_rate}%, 盈亏比{result.profit_loss_ratio}")
            except Exception as e:
                logger.error(f"回测失败 {stock_code} {plan['name']}: {e}")

        return results

    def batch_backtest(self, stock_codes: List[str]) -> Dict[str, Dict[str, BacktestResult]]:
        """
        批量回测多只股票

        Args:
            stock_codes: 股票代码列表

        Returns:
            字典，键为股票代码，值为方案结果字典
        """
        all_results = {}

        for i, stock_code in enumerate(stock_codes, 1):
            logger.info(f"[{i}/{len(stock_codes)}] 回测 {stock_code}...")

            try:
                results = self.backtest_all_plans(stock_code)
                if results:
                    all_results[stock_code] = results

                # 每10只股票显示一次进度
                if i % 10 == 0:
                    logger.info(f"进度: {i}/{len(stock_codes)} ({i/len(stock_codes)*100:.1f}%)")

            except Exception as e:
                logger.error(f"回测失败 {stock_code}: {e}")

        return all_results

    def generate_report(self, results: Dict[str, Dict[str, BacktestResult]]) -> str:
        """
        生成回测报告

        Args:
            results: 回测结果

        Returns:
            报告文本
        """
        report = []
        report.append("=" * 80)
        report.append("止盈止损方案回测报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"回测股票数: {len(results)}")
        report.append("")

        # 按方案汇总
        plan_names = ['保守型', '稳健型', '激进型']

        for plan_name in plan_names:
            report.append("-" * 80)
            report.append(f"方案: {plan_name}")
            report.append("-" * 80)

            plan_results = []
            for stock_code, stock_results in results.items():
                if plan_name in stock_results:
                    plan_results.append(stock_results[plan_name])

            if not plan_results:
                report.append("  无数据\n")
                continue

            # 汇总统计
            total_trades = sum([r.total_trades for r in plan_results])
            total_winning = sum([r.winning_trades for r in plan_results])
            avg_win_rate = np.mean([r.win_rate for r in plan_results])
            avg_profit = np.mean([r.avg_profit for r in plan_results])
            avg_loss = np.mean([r.avg_loss for r in plan_results])
            avg_profit_loss_ratio = np.mean([r.profit_loss_ratio for r in plan_results])

            report.append(f"  总交易次数: {total_trades}")
            report.append(f"  总盈利次数: {total_winning}")
            report.append(f"  平均胜率: {avg_win_rate:.2f}%")
            report.append(f"  平均盈利: {avg_profit:.2f}%")
            report.append(f"  平均亏损: {avg_loss:.2f}%")
            report.append(f"  平均盈亏比: {avg_profit_loss_ratio:.2f}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# 测试代码
if __name__ == "__main__":
    # 测试回测引擎
    print("=" * 60)
    print("测试回测引擎")
    print("=" * 60)

    engine = BacktestEngine()

    # 测试单只股票
    print("\n测试单只股票回测:")
    results = engine.backtest_all_plans('000001.SZ')

    for plan_name, result in results.items():
        print(f"\n{plan_name}:")
        print(f"  交易次数: {result.total_trades}")
        print(f"  胜率: {result.win_rate}%")
        print(f"  平均盈利: {result.avg_profit}%")
        print(f"  平均亏损: {result.avg_loss}%")
        print(f"  盈亏比: {result.profit_loss_ratio}")
        print(f"  夏普比率: {result.sharpe_ratio}")

    print("\n" + "=" * 60)
