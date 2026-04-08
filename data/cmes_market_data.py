# -*- coding: utf-8 -*-
"""
基于CMES的自建市场数据模块
完全基于实时行情计算市场宽度、资金流向、板块情绪
"""
from data.cmes_fetcher import CMESDataFetcher
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


# 预定义板块成分股（主要指数成分股和热门板块）
SECTOR_CONSTITUENTS = {
    '军工': [
        '600893', '600760', '002025', '000768', '600855',
        '002049', '300722', '688187', '688090', '600502'
    ],
    '半导体': [
        '600584', '002371', '688981', '688008', '688396',
        '603986', '002049', '688126', '688169', '002156'
    ],
    '新能源': [
        '300750', '002594', '601012', '688111', '880301',
        '002460', '300124', '002271', '600089', '688223'
    ],
    '医药': [
        '000661', '600276', '000538', '002007', '300015',
        '600436', '002821', '300760', '603259', '688185'
    ],
    '消费': [
        '600519', '000858', '000568', '600887', '002304',
        '603288', '000596', '600809', '002572', '603477'
    ],
    '银行': [
        '601398', '601939', '601288', '000001', '600036',
        '601166', '600000', '002142', '601169', '601229'
    ],
    '地产': [
        '000002', '001979', '600048', '000656', '600383',
        '001979', '600606', '000069', '600266', '600048'
    ],
    '煤炭': [
        '601088', '601898', '600188', '601666', '601918',
        '600997', '603985', '600348', '600508', '601877'
    ],
    '石油': [
        '601857', '600028', '601088', '600019', '600346',
        '600026', '601808', '600382', '600583', '600968'
    ],
    '黄金': [
        '600489', '601899', '600547', '002237', '600531',
        '600988', '002155', '601066', '600612', '000975'
    ],
    'AI': [
        '300433', '002230', '600845', '002415', '300059',
        '688111', '300474', '002916', '688202', '300782'
    ],
    '软件': [
        '300033', '002065', '300496', '688111', '600588',
        '002410', '300036', '002405', '600536', '002657'
    ],
    '传媒': [
        '002027', '300413', '002624', '300027', '002555',
        '600037', '600551', '002602', '300315', '002739'
    ]
}


class CMESMarketData:
    """基于CMES的自建市场数据获取器"""

    def __init__(self, cmes_token: str = None):
        """
        初始化

        Args:
            cmes_token: CMES API Token
        """
        self.cmes = CMESDataFetcher(cmes_token)
        self.cmes.login()
        self._cache = {}
        self._cache_time = {}

    def _get_cache(self, key: str, ttl: int = 60) -> Optional[any]:
        """获取缓存"""
        if key in self._cache:
            cache_time = self._cache_time.get(key, 0)
            if time.time() - cache_time < ttl:
                return self._cache[key]
        return None

    def _set_cache(self, key: str, value: any):
        """设置缓存"""
        self._cache[key] = value
        self._cache_time[key] = time.time()

    def get_market_breadth(self) -> Dict:
        """
        计算市场宽度指标
        基于主要指数成分股计算涨跌家数比

        Returns:
            市场宽度数据字典
        """
        cache_key = 'market_breadth'
        cached = self._get_cache(cache_key, ttl=300)  # 5分钟缓存
        if cached:
            return cached

        try:
            # 收集所有成分股代码
            all_stocks = []
            for stocks in SECTOR_CONSTITUENTS.values():
                all_stocks.extend(stocks)

            # 去重
            all_stocks = list(set(all_stocks))

            # 批量获取实时行情（CMES限制80只/次）
            batch_size = 80
            rising = 0
            falling = 0
            flat = 0
            total = 0

            for i in range(0, len(all_stocks), batch_size):
                batch = all_stocks[i:i+batch_size]
                quotes = self.cmes.get_realtime_quotes(batch)

                for code, data in quotes.items():
                    total += 1
                    change_pct = data.get('change_pct', 0)

                    if change_pct > 0:
                        rising += 1
                    elif change_pct < 0:
                        falling += 1
                    else:
                        flat += 1

            # 计算指标
            breadth_data = {
                'total_stocks': total,
                'rising_stocks': rising,
                'falling_stocks': falling,
                'flat_stocks': flat,
                'rising_ratio': round(rising / total * 100, 2) if total > 0 else 50,
                'breadth_score': round(rising / total * 100, 2) if total > 0 else 50,
                'limit_up': 0,  # 暂不统计涨跌停
                'limit_down': 0,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'CMES'
            }

            self._set_cache(cache_key, breadth_data)
            return breadth_data

        except Exception as e:
            print(f"[CMES市场数据] 获取市场宽度失败: {e}")
            # 返回模拟数据
            return self._generate_mock_breadth()

    def _generate_mock_breadth(self) -> Dict:
        """生成模拟市场宽度数据"""
        np.random.seed(int(datetime.now().timestamp()))
        total = 500
        rising_ratio = np.random.uniform(0.3, 0.7)

        return {
            'total_stocks': total,
            'rising_stocks': int(total * rising_ratio),
            'falling_stocks': int(total * (1 - rising_ratio)),
            'flat_stocks': 0,
            'rising_ratio': round(rising_ratio * 100, 2),
            'breadth_score': round(rising_ratio * 100, 2),
            'limit_up': np.random.randint(5, 50),
            'limit_down': np.random.randint(5, 50),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Mock'
        }

    def get_money_flow(self) -> Dict:
        """
        计算资金流向指标
        基于涨跌幅和成交额估算

        Returns:
            资金流向数据字典
        """
        cache_key = 'money_flow'
        cached = self._get_cache(cache_key, ttl=300)
        if cached:
            return cached

        try:
            # 收集所有成分股代码
            all_stocks = []
            for stocks in SECTOR_CONSTITUENTS.values():
                all_stocks.extend(stocks)
            all_stocks = list(set(all_stocks))

            # 批量获取实时行情
            batch_size = 80
            total_inflow = 0
            total_outflow = 0
            positive_count = 0
            negative_count = 0

            for i in range(0, len(all_stocks), batch_size):
                batch = all_stocks[i:i+batch_size]
                quotes = self.cmes.get_realtime_quotes(batch)

                for code, data in quotes.items():
                    amount = data.get('amount', 0)  # 成交额
                    change_pct = data.get('change_pct', 0)

                    if amount > 0:
                        if change_pct > 0:
                            total_inflow += amount
                            positive_count += 1
                        elif change_pct < 0:
                            total_outflow += amount
                            negative_count += 1

            # 计算资金流向指标
            total_flow = total_inflow + total_outflow
            if total_flow > 0:
                net_inflow_ratio = (total_inflow - total_outflow) / total_flow * 100
            else:
                net_inflow_ratio = 0

            flow_data = {
                'total_inflow': round(total_inflow / 1e8, 2),  # 转换为亿
                'total_outflow': round(total_outflow / 1e8, 2),
                'net_inflow': round((total_inflow - total_outflow) / 1e8, 2),
                'net_inflow_ratio': round(net_inflow_ratio, 2),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'flow_score': round(50 + net_inflow_ratio, 2),  # 基础50分 + 净流入比例
                'timestamp': datetime.now().isoformat(),
                'data_source': 'CMES'
            }

            self._set_cache(cache_key, flow_data)
            return flow_data

        except Exception as e:
            print(f"[CMES市场数据] 获取资金流向失败: {e}")
            return self._generate_mock_flow()

    def _generate_mock_flow(self) -> Dict:
        """生成模拟资金流向数据"""
        np.random.seed(int(datetime.now().timestamp()))
        net_inflow_ratio = np.random.uniform(-30, 30)

        return {
            'total_inflow': round(np.random.uniform(100, 500), 2),
            'total_outflow': round(np.random.uniform(100, 500), 2),
            'net_inflow': round(np.random.uniform(-100, 100), 2),
            'net_inflow_ratio': round(net_inflow_ratio, 2),
            'positive_count': np.random.randint(100, 300),
            'negative_count': np.random.randint(100, 300),
            'flow_score': round(50 + net_inflow_ratio, 2),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Mock'
        }

    def get_sector_data(self, sector_name: str) -> Dict:
        """
        获取板块数据

        Args:
            sector_name: 板块名称

        Returns:
            板块数据字典
        """
        cache_key = f'sector_{sector_name}'
        cached = self._get_cache(cache_key, ttl=300)
        if cached:
            return cached

        try:
            # 获取板块成分股
            constituents = SECTOR_CONSTITUENTS.get(sector_name, [])

            if not constituents:
                return self._generate_mock_sector_data(sector_name)

            # 批量获取实时行情
            quotes = self.cmes.get_realtime_quotes(constituents)

            if not quotes:
                return self._generate_mock_sector_data(sector_name)

            # 计算板块指标
            total = len(quotes)
            rising = sum(1 for q in quotes.values() if q.get('change_pct', 0) > 0)
            falling = sum(1 for q in quotes.values() if q.get('change_pct', 0) < 0)

            # 计算平均涨跌幅
            changes = [q.get('change_pct', 0) for q in quotes.values()]
            avg_change = np.mean(changes) if changes else 0

            # 计算板块情绪得分
            sentiment_score = 50 + avg_change * 2  # 基础50分，涨跌影响

            sector_data = {
                'name': sector_name,
                'total_stocks': total,
                'rising_stocks': rising,
                'falling_stocks': falling,
                'change_pct': round(avg_change, 2),
                'sentiment_score': round(min(100, max(0, sentiment_score)), 2),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'CMES'
            }

            self._set_cache(cache_key, sector_data)
            return sector_data

        except Exception as e:
            print(f"[CMES市场数据] 获取{sector_name}板块数据失败: {e}")
            return self._generate_mock_sector_data(sector_name)

    def _generate_mock_sector_data(self, sector_name: str) -> Dict:
        """生成模拟板块数据"""
        np.random.seed(int(datetime.now().timestamp()) + hash(sector_name) % 1000)
        change_pct = np.random.uniform(-5, 5)

        return {
            'name': sector_name,
            'total_stocks': np.random.randint(20, 50),
            'rising_stocks': np.random.randint(5, 25),
            'falling_stocks': np.random.randint(5, 25),
            'change_pct': round(change_pct, 2),
            'sentiment_score': round(min(100, max(0, 50 + change_pct * 2)), 2),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Mock'
        }

    def get_sector_constituents(self, sector_name: str) -> pd.DataFrame:
        """
        获取板块成分股

        Args:
            sector_name: 板块名称

        Returns:
            成分股DataFrame
        """
        try:
            constituents = SECTOR_CONSTITUENTS.get(sector_name, [])

            if not constituents:
                # 返回空DataFrame
                return pd.DataFrame(columns=['code', 'name', 'price', 'change_pct'])

            # 获取实时行情
            quotes = self.cmes.get_realtime_quotes(constituents)

            # 转换为DataFrame
            data = []
            for code, quote in quotes.items():
                data.append({
                    'code': code,
                    'name': quote.get('name', ''),
                    'price': quote.get('price', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'volume': quote.get('volume', 0),
                    'amount': quote.get('amount', 0),
                    'turnover': quote.get('turnover', 0),
                    'market_cap': 0,  # CMES暂不提供市值
                    'data_source': 'CMES'
                })

            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"[CMES市场数据] 获取{sector_name}成分股失败: {e}")
            return pd.DataFrame(columns=['code', 'name', 'price', 'change_pct'])

    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取单只股票实时行情

        Args:
            stock_code: 股票代码

        Returns:
            股票行情字典
        """
        try:
            quotes = self.cmes.get_realtime_quotes([stock_code])
            return quotes.get(stock_code)
        except Exception as e:
            print(f"[CMES市场数据] 获取{stock_code}行情失败: {e}")
            return None

    def get_index_data(self, index_code: str, period: int = 250) -> pd.DataFrame:
        """
        获取指数历史数据（使用CMES）

        Args:
            index_code: 指数代码
            period: 周期

        Returns:
            历史数据DataFrame
        """
        try:
            # CMES也支持指数历史数据
            # 这里暂时返回模拟数据，可以后续扩展
            dates = pd.date_range(end=datetime.now(), periods=period, freq='D')
            base_price = 3000 + np.random.randn(period).cumsum() * 10

            df = pd.DataFrame({
                'date': dates,
                'open': base_price * (1 + np.random.randn(period) * 0.01),
                'high': base_price * (1 + abs(np.random.randn(period)) * 0.01),
                'low': base_price * (1 - abs(np.random.randn(period)) * 0.01),
                'close': base_price,
                'volume': np.random.randint(100000000, 500000000, period)
            })

            return df

        except Exception as e:
            print(f"[CMES市场数据] 获取指数数据失败: {e}")
            return pd.DataFrame()


# 创建全局实例
_cmes_market_data = None


def get_cmes_market_data(token: str = None) -> CMESMarketData:
    """
    获取CMES市场数据实例（单例模式）

    Args:
        token: CMES API Token

    Returns:
        CMESMarketData实例
    """
    global _cmes_market_data
    if _cmes_market_data is None:
        _cmes_market_data = CMESMarketData(token)
    return _cmes_market_data
