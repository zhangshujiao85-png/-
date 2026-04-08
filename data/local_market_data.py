"""
本地市场数据获取器
优先从本地SQLite数据库获取历史数据，失败时使用远程数据源

使用方法：
    from data.local_market_data import LocalMarketData

    fetcher = LocalMarketData()
    df = fetcher.get_stock_history('000001.SZ', period=250)

作者：Claude
日期：2025-04-08
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LocalMarketData:
    """本地市场数据获取器"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化本地数据获取器

        Args:
            db_path: 本地数据库路径
        """
        self.db_path = Path(db_path)

        # 检查数据库是否存在
        if not self.db_path.exists():
            logger.warning(f"本地数据库不存在: {self.db_path}")
            self.db_available = False
        else:
            self.db_available = True
            logger.info(f"使用本地数据库: {self.db_path}")

    def get_stock_history(self, stock_code: str, period: int = 250) -> pd.DataFrame:
        """
        获取股票历史数据（优先从本地数据库）

        Args:
            stock_code: 股票代码（如 000001.SZ）
            period: 获取最近N天的数据

        Returns:
            DataFrame包含历史数据
        """
        if not self.db_available:
            logger.warning(f"本地数据库不可用，无法获取 {stock_code} 数据")
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)

            # 查询最近N天的数据
            query = f'''
                SELECT
                    trade_date as date,
                    open,
                    close,
                    high,
                    low,
                    volume,
                    amount
                FROM stock_daily
                WHERE stock_code = ?
                ORDER BY trade_date DESC
                LIMIT {period}
            '''

            df = pd.read_sql(query, conn, params=(stock_code,))
            conn.close()

            if df.empty:
                logger.warning(f"本地数据库中没有 {stock_code} 的数据")
                return pd.DataFrame()

            # 按日期升序排序
            df = df.sort_values('date').reset_index(drop=True)

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            logger.info(f"从本地数据库获取 {stock_code} 数据: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"从本地数据库获取数据失败 {stock_code}: {e}")
            return pd.DataFrame()

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取本地数据库中的所有股票列表

        Returns:
            DataFrame包含股票代码和数据量
        """
        if not self.db_available:
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)

            query = '''
                SELECT
                    stock_code,
                    COUNT(*) as records,
                    MIN(trade_date) as first_date,
                    MAX(trade_date) as last_date
                FROM stock_daily
                GROUP BY stock_code
                ORDER BY stock_code
            '''

            df = pd.read_sql(query, conn)
            conn.close()

            logger.info(f"本地数据库共有 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_quote(self, stock_code: str) -> Dict:
        """
        获取股票最新报价（从本地数据库）

        Args:
            stock_code: 股票代码

        Returns:
            包含最新报价的字典
        """
        if not self.db_available:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)

            query = '''
                SELECT
                    trade_date,
                    open,
                    close,
                    high,
                    low,
                    volume,
                    amount
                FROM stock_daily
                WHERE stock_code = ?
                ORDER BY trade_date DESC
                LIMIT 1
            '''

            df = pd.read_sql(query, conn, params=(stock_code,))
            conn.close()

            if df.empty:
                return {}

            row = df.iloc[0]

            return {
                'code': stock_code,
                'date': row['trade_date'],
                'price': float(row['close']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['volume']),
                'amount': float(row['amount']) if row['amount'] else 0,
                'change': 0,  # 本地数据无法计算涨跌幅
                'change_pct': 0
            }

        except Exception as e:
            logger.error(f"获取股票报价失败 {stock_code}: {e}")
            return {}

    def batch_get_stock_history(self, stock_codes: List[str],
                                period: int = 250) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的历史数据

        Args:
            stock_codes: 股票代码列表
            period: 获取最近N天的数据

        Returns:
            字典，键为股票代码，值为DataFrame
        """
        result = {}

        for stock_code in stock_codes:
            df = self.get_stock_history(stock_code, period)
            if not df.empty:
                result[stock_code] = df

        logger.info(f"批量获取 {len(result)}/{len(stock_codes)} 只股票数据")
        return result

    def get_index_data(self, index_code: str = '000001.SH',
                      period: int = 250) -> pd.DataFrame:
        """
        获取指数历史数据（注意：本地数据库可能没有指数数据）

        Args:
            index_code: 指数代码
            period: 获取最近N天的数据

        Returns:
            DataFrame包含指数数据
        """
        # 本地数据库目前只有股票数据，没有指数数据
        # 这里返回空DataFrame，调用者会自动使用远程数据源
        logger.warning(f"本地数据库暂不支持指数数据，请使用远程数据源")
        return pd.DataFrame()

    def check_data_freshness(self, stock_code: str,
                             max_days_old: int = 1) -> bool:
        """
        检查数据是否新鲜

        Args:
            stock_code: 股票代码
            max_days_old: 最大允许的数据陈旧天数

        Returns:
            数据是否新鲜
        """
        if not self.db_available:
            return False

        try:
            conn = sqlite3.connect(self.db_path)

            query = '''
                SELECT MAX(trade_date) as latest_date
                FROM stock_daily
                WHERE stock_code = ?
            '''

            df = pd.read_sql(query, conn, params=(stock_code,))
            conn.close()

            if df.empty or df.iloc[0]['latest_date'] is None:
                return False

            latest_date = pd.to_datetime(df.iloc[0]['latest_date'])
            days_old = (datetime.now() - latest_date).days

            return days_old <= max_days_old

        except Exception as e:
            logger.error(f"检查数据新鲜度失败 {stock_code}: {e}")
            return False

    def get_data_summary(self) -> Dict:
        """
        获取数据库数据摘要

        Returns:
            数据摘要字典
        """
        if not self.db_available:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)

            # 统计信息
            stats = {}

            # 总记录数
            df = pd.read_sql('SELECT COUNT(*) as total FROM stock_daily', conn)
            stats['total_records'] = int(df.iloc[0]['total'])

            # 股票数量
            df = pd.read_sql('SELECT COUNT(DISTINCT stock_code) as total FROM stock_daily', conn)
            stats['stock_count'] = int(df.iloc[0]['total'])

            # 日期范围
            df = pd.read_sql('''
                SELECT
                    MIN(trade_date) as min_date,
                    MAX(trade_date) as max_date
                FROM stock_daily
            ''', conn)
            stats['date_range'] = {
                'start': df.iloc[0]['min_date'],
                'end': df.iloc[0]['max_date']
            }

            # 数据库大小
            stats['db_size_mb'] = self.db_path.stat().st_size / 1024 / 1024

            conn.close()

            return stats

        except Exception as e:
            logger.error(f"获取数据摘要失败: {e}")
            return {}


class HybridMarketData:
    """
    混合市场数据获取器
    优先使用本地数据库，失败时使用远程数据源
    """

    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化混合数据获取器

        Args:
            db_path: 本地数据库路径
        """
        self.local = LocalMarketData(db_path)

        # 延迟导入远程数据源
        self.remote = None

    def _get_remote(self):
        """延迟初始化远程数据源"""
        if self.remote is None:
            try:
                from data.market_data import MarketDataFetcher
                self.remote = MarketDataFetcher()
                logger.info("远程数据源初始化成功")
            except Exception as e:
                logger.error(f"远程数据源初始化失败: {e}")
                self.remote = False  # 标记为失败
        return self.remote

    def get_stock_history(self, stock_code: str, period: int = 250,
                          use_remote_fallback: bool = True) -> pd.DataFrame:
        """
        获取股票历史数据（优先本地，失败时远程）

        Args:
            stock_code: 股票代码
            period: 获取最近N天的数据
            use_remote_fallback: 本地失败时是否使用远程数据源

        Returns:
            DataFrame包含历史数据
        """
        # 优先从本地获取
        df = self.local.get_stock_history(stock_code, period)

        if not df.empty and len(df) >= period * 0.9:  # 至少90%的数据
            return df

        # 本地数据不足或失败，尝试远程
        if use_remote_fallback:
            logger.info(f"本地数据不足，尝试远程获取 {stock_code}")
            remote = self._get_remote()

            if remote:
                try:
                    df_remote = remote.get_stock_history(
                        stock_code.replace('.SZ', '').replace('.SH', ''),
                        period=period
                    )
                    if not df_remote.empty:
                        logger.info(f"从远程获取 {stock_code} 数据成功")
                        return df_remote
                except Exception as e:
                    logger.error(f"远程获取失败: {e}")

        return df  # 返回本地数据（可能为空或不完整）

    def get_stock_quote(self, stock_code: str,
                        use_remote_fallback: bool = True) -> Dict:
        """
        获取股票最新报价（优先本地，失败时远程）

        Args:
            stock_code: 股票代码
            use_remote_fallback: 本地失败时是否使用远程数据源

        Returns:
            包含最新报价的字典
        """
        # 优先从本地获取
        quote = self.local.get_stock_quote(stock_code)

        if quote:
            return quote

        # 本地失败，尝试远程
        if use_remote_fallback:
            remote = self._get_remote()
            if remote:
                try:
                    code = stock_code.replace('.SZ', '').replace('.SH', '')
                    quote_remote = remote.get_stock_quote(code)
                    if quote_remote:
                        return quote_remote
                except Exception as e:
                    logger.error(f"远程获取报价失败: {e}")

        return {}

    def get_data_summary(self) -> Dict:
        """获取数据摘要"""
        return self.local.get_data_summary()


# 测试代码
if __name__ == "__main__":
    # 测试本地数据获取
    print("=" * 60)
    print("测试本地数据获取器")
    print("=" * 60)

    local = LocalMarketData()

    # 获取数据摘要
    summary = local.get_data_summary()
    print(f"\n数据摘要:")
    print(f"  总记录数: {summary.get('total_records', 0):,}")
    print(f"  股票数量: {summary.get('stock_count', 0):,}")
    print(f"  日期范围: {summary.get('date_range', {}).get('start')} 至 {summary.get('date_range', {}).get('end')}")
    print(f"  数据库大小: {summary.get('db_size_mb', 0):.2f} MB")

    # 测试获取单只股票数据
    print(f"\n测试获取股票数据:")
    df = local.get_stock_history('000001.SZ', period=10)
    if not df.empty:
        print(f"  股票: 000001.SZ")
        print(f"  记录数: {len(df)}")
        print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"  最新收盘价: {df['close'].iloc[-1]:.2f}")
    else:
        print("  获取失败")

    print("\n" + "=" * 60)
