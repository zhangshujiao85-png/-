"""
Tushare Data Fetcher - 真实市场数据获取模块
使用 Tushare API 获取 A股市场数据
"""
import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import os


class TushareDataFetcher:
    """Tushare 数据获取器"""

    def __init__(self, token: str = None):
        """
        初始化 Tushare 数据获取器

        Args:
            token: Tushare Token，如果为 None 则从环境变量读取
        """
        self.token = token or os.getenv("TUSHARE_TOKEN")
        if not self.token:
            raise ValueError("请设置 TUSHARE_TOKEN 环境变量或传入 token 参数")

        # 设置 token
        ts.set_token(self.token)
        self.pro = ts.pro_api()

    def get_index_data(self, index_code: str, period: int = 250) -> pd.DataFrame:
        """
        获取指数历史数据

        Args:
            index_code: 指数代码（如 '000001'）
            period: 获取天数

        Returns:
            包含日期、开盘、最高、最低、收盘、成交量的DataFrame
        """
        try:
            # 转换代码格式
            if index_code.startswith('00'):
                ts_code = f"{index_code}.SH"  # 上证
            elif index_code.startswith('399'):
                ts_code = f"{index_code}.SZ"  # 深证
            else:
                ts_code = f"{index_code}.SH"

            # 计算起始日期
            start_date = (datetime.now() - timedelta(days=period+365)).strftime("%Y%m%d")

            # 获取指数日线数据
            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date
            )

            if df.empty:
                print(f"未获取到数据: {index_code}")
                return pd.DataFrame()

            # 转换列名
            df = df.rename(columns={
                'ts_code': 'code',
                'trade_date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount'
            })

            # 选择需要的列
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            # 排序并取最近的数据
            df = df.sort_values('date', ascending=True).tail(period).reset_index(drop=True)

            return df

        except Exception as e:
            print(f"获取指数数据失败 {index_code}: {e}")
            return pd.DataFrame()

    def get_stock_quote(self, symbol: str) -> Dict:
        """
        获取个股实时行情

        Args:
            symbol: 股票代码（如 '600519'）

        Returns:
            包含价格、成交量、涨跌幅等信息的字典
        """
        try:
            # 转换代码格式
            if symbol.startswith('6'):
                ts_code = f"{symbol}.SH"
            else:
                ts_code = f"{symbol}.SZ"

            # 获取实时行情
            df = self.pro.daily(
                ts_code=ts_code,
                trade_date=datetime.now().strftime("%Y%m%d")
            )

            if df.empty:
                # 尝试获取最近一天的数据
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
                )
                df = df.tail(1)

            if df.empty:
                return {}

            result = {
                'code': symbol,
                'name': f"股票{symbol}",  # Tushare 需要另外获取名称
                'price': float(df['close'].iloc[0]),
                'open': float(df['open'].iloc[0]),
                'high': float(df['high'].iloc[0]),
                'low': float(df['low'].iloc[0]),
                'volume': float(df['vol'].iloc[0]),
                'change_pct': round((float(df['close'].iloc[0]) - float(df['pre_close'].iloc[0])) / float(df['pre_close'].iloc[0]) * 100, 2),
            }

            return result

        except Exception as e:
            print(f"获取股票行情失败 {symbol}: {e}")
            return {}

    def get_stock_history(self, symbol: str, period: int = 250) -> pd.DataFrame:
        """
        获取个股历史数据

        Args:
            symbol: 股票代码
            period: 获取天数

        Returns:
            包含历史行情的DataFrame
        """
        try:
            # 转换代码格式
            if symbol.startswith('6'):
                ts_code = f"{symbol}.SH"
            else:
                ts_code = f"{symbol}.SZ"

            # 计算起始日期
            start_date = (datetime.now() - timedelta(days=period+365)).strftime("%Y%m%d")

            # 获取日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date
            )

            if df.empty:
                print(f"未获取到历史数据: {symbol}")
                return pd.DataFrame()

            # 转换列名
            df = df.rename(columns={
                'ts_code': 'code',
                'trade_date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount',
                'pct_chg': 'change_pct'
            })

            # 选择需要的列
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']]

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            # 排序并取最近的数据
            df = df.sort_values('date', ascending=True).tail(period).reset_index(drop=True)

            return df

        except Exception as e:
            print(f"获取股票历史数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_name(self, symbol: str) -> str:
        """
        获取股票名称

        Args:
            symbol: 股票代码

        Returns:
            股票名称
        """
        try:
            # 转换代码格式
            if symbol.startswith('6'):
                ts_code = f"{symbol}.SH"
            else:
                ts_code = f"{symbol}.SZ"

            # 获取股票基本信息
            df = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,name'
            )

            if not df.empty:
                return df['name'].iloc[0]

            return f"股票{symbol}"

        except Exception as e:
            print(f"获取股票名称失败 {symbol}: {e}")
            return f"股票{symbol}"


# 测试代码
if __name__ == "__main__":
    # 测试时需要设置 token
    print("请先设置 TUSHARE_TOKEN 环境变量")
    print("export TUSHARE_TOKEN=your_token")
    print("或者在代码中直接传入 token")
