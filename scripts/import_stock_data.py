"""
股票历史数据导入脚本
从下载的stk_factor数据包中提取日K线数据并导入到SQLite数据库

数据源：D:\BaiduNetdiskDownload\stk_factor\
目标：data\stock_data.db

使用方法：
    python scripts/import_stock_data.py

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
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockDataImporter:
    """股票数据导入器"""

    # 导入所有股票（充分利用4GB数据）
    HS300_STOCKS = None

    def __init__(self, source_dir: str, target_db: str = "data/stock_data.db"):
        """
        初始化导入器

        Args:
            source_dir: 源数据目录（stk_factor文件夹）
            target_db: 目标SQLite数据库路径
        """
        self.source_dir = Path(source_dir)
        self.target_db = Path(target_db)
        self.target_db.parent.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            'total_files': 0,
            'imported_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'imported_records': 0,
            'start_time': None,
            'end_time': None
        }

        logger.info("=" * 70)
        logger.info("股票历史数据导入工具")
        logger.info("=" * 70)
        logger.info(f"源目录: {self.source_dir}")
        logger.info(f"目标数据库: {self.target_db.absolute()}")
        logger.info(f"股票过滤: {'沪深300' if self.HS300_STOCKS else '全市场'}")

    def scan_data_files(self) -> list:
        """
        扫描源数据目录，找到所有CSV文件

        Returns:
            数据文件路径列表
        """
        logger.info(f"\n扫描数据目录: {self.source_dir}")

        data_files = list(self.source_dir.glob('*.csv'))
        data_files.sort()

        self.stats['total_files'] = len(data_files)
        logger.info(f"找到 {len(data_files)} 个CSV文件")

        return data_files

    def extract_stock_code(self, file_path: Path) -> str:
        """
        从文件路径提取股票代码

        Args:
            file_path: 文件路径（如 000001.SZ.csv）

        Returns:
            股票代码（如 '000001.SZ'）
        """
        return file_path.stem  # 去掉.csv扩展名

    def is_stock_needed(self, stock_code: str) -> bool:
        """
        判断是否需要导入该股票数据

        Args:
            stock_code: 股票代码

        Returns:
            是否需要导入
        """
        if not stock_code:
            return False

        # 如果设置了股票白名单，只导入白名单中的股票
        if self.HS300_STOCKS:
            return stock_code in self.HS300_STOCKS

        # 否则导入所有股票
        return True

    def read_stock_file(self, file_path: Path) -> pd.DataFrame:
        """
        读取股票数据文件

        Args:
            file_path: 文件路径

        Returns:
            DataFrame
        """
        try:
            # 尝试多种编码
            for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']:
                try:
                    # 只读取最近2年数据（约500行）
                    df = pd.read_csv(file_path, encoding=encoding)
                    if len(df) > 0:
                        logger.debug(f"成功读取: {file_path.name} (编码: {encoding})")
                        return df
                except Exception as e:
                    continue

            logger.error(f"读取文件失败: {file_path.name}")
            return None

        except Exception as e:
            logger.error(f"读取文件异常: {file_path.name}, 错误: {e}")
            return None

    def parse_and_clean_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        解析和清洗数据

        Args:
            df: 原始DataFrame
            stock_code: 股票代码

        Returns:
            清洗后的DataFrame
        """
        if df is None or df.empty:
            return None

        try:
            # 获取前10列数据（核心OHLCV数据）
            # 根据实际数据结构，前10列通常包含：
            # 股票代码, 日期, 开盘, 收盘, 最高, 最低, 成交量等
            df_core = df.iloc[:, :15].copy()  # 取前15列，包含基本数据和技术指标

            # 重命名列（根据实际列索引）
            # 列名映射需要根据实际文件调整
            new_columns = {
                df_core.columns[0]: 'stock_code',
                df_core.columns[1]: 'trade_date',
                df_core.columns[2]: 'open',
                df_core.columns[3]: 'close',
                df_core.columns[4]: 'high',
                df_core.columns[5]: 'low',
                df_core.columns[6]: 'volume',
                df_core.columns[7]: 'amount',
            }

            # 只重命名存在的列
            for old_col, new_col in new_columns.items():
                if old_col in df_core.columns:
                    df_core = df_core.rename(columns={old_col: new_col})

            # 确保有必要的列
            required_cols = ['trade_date', 'close']
            missing_cols = [col for col in required_cols if col not in df_core.columns]

            if missing_cols:
                logger.warning(f"{stock_code} 缺少必要列: {missing_cols}")
                return None

            # 转换日期格式
            df_core['trade_date'] = pd.to_datetime(df_core['trade_date'], errors='coerce')

            # 删除日期为空的行
            df_core = df_core.dropna(subset=['trade_date'])

            # 只保留最近2年数据
            two_years_ago = datetime.now() - timedelta(days=365*2)
            df_core = df_core[df_core['trade_date'] >= two_years_ago]

            # 按日期排序
            df_core = df_core.sort_values('trade_date').reset_index(drop=True)

            # 删除重复数据
            df_core = df_core.drop_duplicates(subset=['trade_date'], keep='last')

            # 确保价格数据为正数
            price_cols = ['open', 'close', 'high', 'low']
            for col in price_cols:
                if col in df_core.columns:
                    df_core[col] = pd.to_numeric(df_core[col], errors='coerce')
                    df_core = df_core[df_core[col] > 0]

            # 确保成交量为正数
            if 'volume' in df_core.columns:
                df_core['volume'] = pd.to_numeric(df_core['volume'], errors='coerce')
                df_core = df_core[df_core['volume'] > 0]

            # 删除异常值
            if all(col in df_core.columns for col in ['high', 'low', 'close']):
                df_core = df_core[df_core['high'] >= df_core['low']]
                df_core = df_core[df_core['close'] <= df_core['high']]
                df_core = df_core[df_core['close'] >= df_core['low']]

            # 填充缺失值
            df_core = df_core.fillna(method='ffill').fillna(method='bfill')

            return df_core

        except Exception as e:
            logger.error(f"清洗数据失败 {stock_code}: {e}")
            return None

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.target_db)
        cursor = conn.cursor()

        # 创建股票日K线表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL,
                close REAL,
                high REAL,
                low REAL,
                volume REAL,
                amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, trade_date)
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_date
            ON stock_daily (stock_code, trade_date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trade_date
            ON stock_daily (trade_date)
        ''')

        # 创建导入日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT,
                file_name TEXT,
                records_imported INTEGER,
                status TEXT,
                error_message TEXT,
                import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("数据库初始化完成")

    def save_to_database(self, df: pd.DataFrame, stock_code: str, file_name: str):
        """
        保存数据到数据库

        Args:
            df: DataFrame
            stock_code: 股票代码
            file_name: 文件名
        """
        if df is None or df.empty:
            return

        try:
            conn = sqlite3.connect(self.target_db)

            # 准备数据
            df_to_save = df[['trade_date', 'open', 'close', 'high', 'low', 'volume', 'amount']].copy()
            df_to_save.insert(0, 'stock_code', stock_code)

            # 转换日期为字符串
            df_to_save['trade_date'] = df_to_save['trade_date'].dt.strftime('%Y-%m-%d')

            # 保存数据（忽略重复数据）
            df_to_save.to_sql('stock_daily', conn, if_exists='append', index=False)

            conn.close()

            self.stats['imported_records'] += len(df)
            self.log_import(stock_code, file_name, len(df), 'success')

        except Exception as e:
            logger.error(f"保存数据失败 {stock_code}: {e}")
            self.log_import(stock_code, file_name, 0, 'failed', str(e))

    def log_import(self, stock_code: str, file_name: str,
                   records_imported: int, status: str, error: str = None):
        """记录导入日志"""
        try:
            conn = sqlite3.connect(self.target_db)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO import_log (stock_code, file_name, records_imported, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (stock_code, file_name, records_imported, status, error))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"记录日志失败: {e}")

    def process_file(self, file_path: Path) -> bool:
        """
        处理单个数据文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功处理
        """
        # 提取股票代码
        stock_code = self.extract_stock_code(file_path)

        # 判断是否需要导入
        if not self.is_stock_needed(stock_code):
            self.stats['skipped_files'] += 1
            return False

        # 读取文件
        df = self.read_stock_file(file_path)
        if df is None:
            self.stats['failed_files'] += 1
            return False

        # 解析和清洗数据
        df = self.parse_and_clean_data(df, stock_code)
        if df is None or df.empty:
            self.stats['failed_files'] += 1
            return False

        # 保存到数据库
        self.save_to_database(df, stock_code, file_path.name)
        self.stats['imported_files'] += 1

        return True

    def import_all(self, max_files: int = None):
        """
        导入所有数据

        Args:
            max_files: 最大导入文件数（用于测试），None表示全部导入
        """
        self.stats['start_time'] = datetime.now()

        # 初始化数据库
        self.init_database()

        # 扫描文件
        files = self.scan_data_files()
        if not files:
            logger.error("未找到数据文件！")
            return

        # 限制导入数量（测试用）
        if max_files:
            files = files[:max_files]
            logger.info(f"测试模式：只导入前 {max_files} 个文件")

        # 处理每个文件
        logger.info(f"\n开始导入数据...")
        logger.info("-" * 70)

        for file_path in tqdm(files, desc="导入进度"):
            try:
                self.process_file(file_path)
            except Exception as e:
                logger.error(f"处理文件失败 {file_path.name}: {e}")
                self.stats['failed_files'] += 1

        self.stats['end_time'] = datetime.now()
        self.print_summary()

    def print_summary(self):
        """打印导入摘要"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("导入完成！")
        logger.info("=" * 70)
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"成功导入: {self.stats['imported_files']}")
        logger.info(f"跳过文件: {self.stats['skipped_files']}")
        logger.info(f"失败文件: {self.stats['failed_files']}")
        logger.info(f"总记录数: {self.stats['imported_records']:,}")
        logger.info(f"耗时: {duration:.2f}秒 ({duration/60:.1f}分钟)")
        logger.info(f"数据库路径: {self.target_db.absolute()}")

        # 计算数据库大小
        if self.target_db.exists():
            db_size = self.target_db.stat().st_size / 1024 / 1024
            logger.info(f"数据库大小: {db_size:.2f} MB")

        logger.info("=" * 70)


def main():
    """主函数"""
    # 配置
    SOURCE_DIR = r"D:\BaiduNetdiskDownload\stk_factor"
    TARGET_DB = "data/stock_data.db"

    # 创建导入器
    importer = StockDataImporter(SOURCE_DIR, TARGET_DB)

    # 测试模式：先导入10个文件测试
    print("\n是否测试模式？")
    print("1. 测试模式（导入10个文件）")
    print("2. 完整模式（导入所有文件）")

    choice = input("请选择 (1/2): ").strip()

    if choice == '1':
        print("\n测试模式：导入前10个文件...")
        importer.import_all(max_files=10)
    else:
        print("\n完整模式：导入所有文件...")
        print(f"这将导入 {len(importer.HS300_STOCKS) if importer.HS300_STOCKS else '全部'} 只股票的数据")
        confirm = input("确认继续？(y/n): ").strip().lower()
        if confirm == 'y':
            importer.import_all()
        else:
            print("已取消导入")


if __name__ == '__main__':
    main()
