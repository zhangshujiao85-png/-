# -*- coding: utf-8 -*-
"""
混合数据获取器
CMES(实时行情) + AkShare(市场宽度/资金流向/板块)
"""
from data.cmes_fetcher import CMESDataFetcher
from data.market_data import MarketDataFetcher
from typing import Dict, List
import pandas as pd


class HybridDataFetcher:
    """混合数据获取器 - 结合CMES和AkShare优势"""

    def __init__(self, cmes_token: str = None):
        """
        初始化混合数据获取器

        Args:
            cmes_token: CMES API Token
        """
        self.cmes_fetcher = CMESDataFetcher(cmes_token)
        self.akshare_fetcher = MarketDataFetcher()
        self.cmes_available = False

        # 尝试登录CMES
        try:
            self.cmes_available = self.cmes_fetcher.login()
            if self.cmes_available:
                print("[混合数据源] CMES已启用 - 实时行情使用CMES")
        except Exception as e:
            print(f"[混合数据源] CMES登录失败: {e}，仅使用AkShare")
            self.cmes_available = False

    def get_realtime_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取实时行情（优先CMES，降级AkShare）

        Args:
            symbols: 股票代码列表

        Returns:
            股票实时行情字典
        """
        # 方案1: 优先使用CMES（实时性最好）
        if self.cmes_available:
            try:
                data = self.cmes_fetcher.get_realtime_quotes(symbols)
                if data and len(data) > 0:
                    print(f"[混合数据源] CMES成功 - 获取{len(data)}只股票")
                    return data
            except Exception as e:
                print(f"[混合数据源] CMES失败: {e}，降级到AkShare")

        # 方案2: 降级到AkShare
        try:
            print(f"[混合数据源] 使用AkShare获取{len(symbols)}只股票")
            result = {}
            for symbol in symbols:
                quote = self.akshare_fetcher.get_realtime_quote(symbol)
                if quote:
                    result[symbol] = {
                        'code': symbol,
                        'name': quote.get('name', ''),
                        'price': quote.get('price', 0),
                        'open': quote.get('open', 0),
                        'high': quote.get('high', 0),
                        'low': quote.get('low', 0),
                        'volume': quote.get('volume', 0),
                        'amount': quote.get('amount', 0),
                        'change_pct': quote.get('change_pct', 0),
                        'turnover': quote.get('turnover', 0),
                        'timestamp': quote.get('timestamp', ''),
                        'data_source': 'AkShare'
                    }
            return result
        except Exception as e:
            print(f"[混合数据源] AkShare也失败: {e}")
            return {}

    def get_market_overview(self) -> Dict:
        """
        获取市场概览（使用AkShare）

        Returns:
            市场概览数据（涨跌家数、涨跌停等）
        """
        try:
            # AkShare提供市场宽度数据
            import akshare as ak
            df = ak.stock_zh_a_spot_em()

            if not df.empty:
                total = len(df)
                rising = len(df[df['涨跌幅'] > 0])
                falling = len(df[df['涨跌幅'] < 0])

                return {
                    'total_stocks': total,
                    'rising_stocks': rising,
                    'falling_stocks': falling,
                    'limit_up': len(df[df['涨跌幅'] >= 9.9]),
                    'limit_down': len(df[df['涨跌幅'] <= -9.9]),
                    'rising_ratio': round(rising / total * 100, 2) if total > 0 else 0,
                    'timestamp': pd.Timestamp.now().isoformat(),
                    'data_source': 'AkShare'
                }
        except Exception as e:
            print(f"[混合数据源] 获取市场概览失败: {e}")

        # 降级到模拟数据
        import numpy as np
        total = 5000
        np.random.seed(int(pd.Timestamp.now().timestamp()))
        rising_ratio = np.random.uniform(0.3, 0.7)

        return {
            'total_stocks': total,
            'rising_stocks': int(total * rising_ratio),
            'falling_stocks': int(total * (1 - rising_ratio)),
            'limit_up': np.random.randint(5, 50),
            'limit_down': np.random.randint(5, 50),
            'rising_ratio': round(rising_ratio * 100, 2),
            'timestamp': pd.Timestamp.now().isoformat(),
            'data_source': 'Mock'
        }

    def get_sector_data(self, sector_name: str) -> Dict:
        """
        获取板块数据（使用AkShare）

        Args:
            sector_name: 板块名称

        Returns:
            板块数据
        """
        try:
            return self.akshare_fetcher.get_sector_data(sector_name)
        except Exception as e:
            print(f"[混合数据源] 获取板块数据失败: {e}")
            return self.akshare_fetcher._generate_mock_sector_data(sector_name)

    def get_sector_constituents(self, sector_name: str) -> pd.DataFrame:
        """
        获取板块成分股（使用AkShare）

        Args:
            sector_name: 板块名称

        Returns:
            成分股DataFrame
        """
        try:
            return self.akshare_fetcher.get_sector_constituents(sector_name)
        except Exception as e:
            print(f"[混合数据源] 获取成分股失败: {e}")
            return self.akshare_fetcher._generate_mock_constituents(sector_name)

    def get_status(self) -> Dict:
        """
        获取数据源状态

        Returns:
            数据源状态信息
        """
        status = {
            'cmes_available': self.cmes_available,
            'cmes_status': '未登录' if not self.cmes_available else '已登录',
            'akshare_available': True,
            'primary_source': 'CMES' if self.cmes_available else 'AkShare',
            'recommendation': ''
        }

        if self.cmes_available:
            status['recommendation'] = '✅ 最佳状态：CMES实时行情 + AkShare补充数据'
        else:
            status['recommendation'] = '⚠️ 仅AkShare可用（建议检查CMES token或网络）'

        return status


# 创建全局实例
_hybrid_fetcher = None


def get_hybrid_fetcher(token: str = None) -> HybridDataFetcher:
    """
    获取混合数据获取器实例（单例模式）

    Args:
        token: CMES API Token

    Returns:
        HybridDataFetcher实例
    """
    global _hybrid_fetcher
    if _hybrid_fetcher is None:
        _hybrid_fetcher = HybridDataFetcher(token)
    return _hybrid_fetcher
