"""
股票数据自动更新脚本
每天自动从AkShare获取最新行情，增量更新到本地数据库

使用方法：
    python scripts/auto_update_data.py

作者：Claude
日期：2025-04-08
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockDataAutoUpdater:
    """股票数据自动更新器"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化更新器

        Args:
            db_path: 数据库路径
        """
        self.db_path = Path(db_path)

        # 统计信息
        self.stats = {
            'stocks_to_update': 0,
            'stocks_updated': 0,
            'stocks_failed': 0,
            'records_added': 0,
            'start_time': None,
            'end_time': None
        }

    def get_db_latest_date(self, stock_code: str) -> Optional[str]:
        """
        获取数据库中某股票的最新日期

        Args:
            stock_code: 股票代码

        Returns:
            最新日期字符串 (YYYY-MM-DD)，如果没有数据返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT MAX(trade_date) FROM stock_daily WHERE stock_code = ?
            ''', (stock_code,))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return result[0]
            return None

        except Exception as e:
            logger.error(f"获取最新日期失败 {stock_code}: {e}")
            return None

    def get_all_stock_codes(self) -> List[str]:
        """
        获取数据库中所有股票代码

        Returns:
            股票代码列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT stock_code FROM stock_daily')
            codes = [row[0] for row in cursor.fetchall()]
            conn.close()

            return codes

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def fetch_latest_data_akshare(self, stock_code: str,
                                   start_date: str) -> Optional[pd.DataFrame]:
        """
        从AkShare获取最新数据

        Args:
            stock_code: 股票代码（如 000001.SZ）
            start_date: 开始日期

        Returns:
            DataFrame包含最新数据
        """
        try:
            import akshare as ak

            # 提取数字代码（000001.SZ -> 000001）
            code = stock_code.split('.')[0]

            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace('-', ''),
                adjust="qfq"  # 前复权
            )

            if df.empty:
                return None

            # 重命名列
            df = df.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # 选择需要的列
            df = df[['trade_date', 'open', 'close', 'high', 'low', 'volume', 'amount']]

            # 添加股票代码
            df['stock_code'] = stock_code

            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

            # 排除已存在的最后一天（避免重复）
            df = df[df['trade_date'] > start_date]

            return df

        except Exception as e:
            logger.debug(f"AkShare获取失败 {stock_code}: {e}")
            return None

    def fetch_latest_data_cmes(self, stock_code: str,
                               start_date: str) -> Optional[pd.DataFrame]:
        """
        从CMES获取最新数据（备用）

        Args:
            stock_code: 股票代码
            start_date: 开始日期

        Returns:
            DataFrame包含最新数据
        """
        try:
            # CMES数据获取逻辑
            # 如果安装了CMES，可以在这里实现
            logger.debug(f"CMES获取 {stock_code} (未实现)")
            return None

        except Exception as e:
            logger.debug(f"CMES获取失败 {stock_code}: {e}")
            return None

    def update_stock_data(self, stock_code: str) -> bool:
        """
        更新单只股票的数据

        Args:
            stock_code: 股票代码

        Returns:
            是否成功更新
        """
        # 获取数据库最新日期
        latest_date = self.get_db_latest_date(stock_code)

        if not latest_date:
            logger.warning(f"{stock_code} 没有历史数据，跳过")
            return False

        # 如果最新数据是今天，不需要更新
        today = datetime.now().strftime('%Y-%m-%d')
        if latest_date >= today:
            logger.debug(f"{stock_code} 数据已是最新 ({latest_date})")
            return False

        # 获取增量数据
        df = self.fetch_latest_data_akshare(stock_code, latest_date)

        if df is None or df.empty:
            logger.debug(f"{stock_code} 没有新数据")
            return False

        # 保存到数据库
        try:
            conn = sqlite3.connect(self.db_path)

            # 转换DataFrame为列表
            data_to_insert = [
                (
                    row['stock_code'],
                    row['trade_date'],
                    float(row['open']) if pd.notna(row['open']) else None,
                    float(row['close']) if pd.notna(row['close']) else None,
                    float(row['high']) if pd.notna(row['high']) else None,
                    float(row['low']) if pd.notna(row['low']) else None,
                    float(row['volume']) if pd.notna(row['volume']) else None,
                    float(row['amount']) if pd.notna(row['amount']) else None
                )
                for _, row in df.iterrows()
            ]

            # 批量插入
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT OR IGNORE INTO stock_daily
                (stock_code, trade_date, open, close, high, low, volume, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', data_to_insert)

            conn.commit()
            conn.close()

            self.stats['records_added'] += len(df)
            logger.info(f"✓ {stock_code} 新增 {len(df)} 条数据 ({latest_date} → {df.iloc[-1]['trade_date']})")

            return True

        except Exception as e:
            logger.error(f"保存数据失败 {stock_code}: {e}")
            return False

    def update_all(self, max_stocks: int = None):
        """
        更新所有股票数据

        Args:
            max_stocks: 最大更新股票数（用于测试），None表示全部更新
        """
        self.stats['start_time'] = datetime.now()

        logger.info("=" * 70)
        logger.info("股票数据自动更新")
        logger.info("=" * 70)
        logger.info(f"数据库: {self.db_path.absolute()}")
        logger.info(f"开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        # 获取所有股票代码
        stock_codes = self.get_all_stock_codes()

        if not stock_codes:
            logger.error("未找到股票数据！")
            return

        self.stats['stocks_to_update'] = len(stock_codes)

        # 限制更新数量（测试用）
        if max_stocks:
            stock_codes = stock_codes[:max_stocks]
            logger.info(f"测试模式：只更新前 {max_stocks} 只股票")

        logger.info(f"需要更新: {len(stock_codes)} 只股票")
        logger.info("-" * 70)

        # 更新每只股票
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                success = self.update_stock_data(stock_code)

                if success:
                    self.stats['stocks_updated'] += 1
                else:
                    self.stats['stocks_failed'] += 1

                # 每100只股票显示一次进度
                if i % 100 == 0:
                    logger.info(f"进度: {i}/{len(stock_codes)} ({i/len(stock_codes)*100:.1f}%)")

            except Exception as e:
                logger.error(f"更新失败 {stock_code}: {e}")
                self.stats['stocks_failed'] += 1

        self.stats['end_time'] = datetime.now()
        self.print_summary()

    def print_summary(self):
        """打印更新摘要"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("更新完成！")
        logger.info("=" * 70)
        logger.info(f"需要更新: {self.stats['stocks_to_update']} 只")
        logger.info(f"成功更新: {self.stats['stocks_updated']} 只")
        logger.info(f"跳过/失败: {self.stats['stocks_failed']} 只")
        logger.info(f"新增记录: {self.stats['records_added']:,} 条")
        logger.info(f"耗时: {duration:.2f}秒 ({duration/60:.1f}分钟)")

        # 检查数据库大小
        if self.db_path.exists():
            db_size = self.db_path.stat().st_size / 1024 / 1024
            logger.info(f"数据库大小: {db_size:.2f} MB")

        logger.info("=" * 70)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='自动更新股票数据')
    parser.add_argument('--test', action='store_true', help='测试模式（只更新10只股票）')
    parser.add_argument('--db', default='data/stock_data.db', help='数据库路径')

    args = parser.parse_args()

    # 创建更新器
    updater = StockDataAutoUpdater(args.db)

    # 执行更新
    max_stocks = 10 if args.test else None
    updater.update_all(max_stocks=max_stocks)


if __name__ == '__main__':
    main()
