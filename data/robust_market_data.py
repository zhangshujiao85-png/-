# -*- coding: utf-8 -*-
"""
增强版市场数据获取器
支持多数据源自动切换，确保短线交易的实时性
"""
import akshare as ak
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class RobustMarketDataFetcher:
    """增强版市场数据获取器 - 多数据源自动切换"""

    def __init__(self):
        """初始化数据获取器"""
        self.data_sources = ['akshare', 'sina', 'eastmoney']
        self.current_source = None
        self.request_timeout = 5  # 5秒超时

    def get_realtime_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取实时行情（多数据源自动切换）

        Args:
            symbols: 股票代码列表

        Returns:
            股票实时行情字典
        """
        # 数据源1: AkShare (最全面)
        try:
            print(f"[数据源] 尝试 AkShare...")
            data = self._fetch_from_akshare(symbols)
            if data:
                self.current_source = 'akshare'
                print(f"[数据源] [OK] AkShare 成功")
                return data
        except Exception as e:
            print(f"[数据源] [FAIL] AkShare 失败: {str(e)[:50]}")

        # 数据源2: 新浪财经API (实时性最好)
        try:
            print(f"[数据源] 尝试新浪财经...")
            data = self._fetch_from_sina(symbols)
            if data:
                self.current_source = 'sina'
                print(f"[数据源] [OK] 新浪财经 成功")
                return data
        except Exception as e:
            print(f"[数据源] [FAIL] 新浪财经 失败: {str(e)[:50]}")

        # 数据源3: 东方财富API (备用)
        try:
            print(f"[数据源] 尝试东方财富...")
            data = self._fetch_from_eastmoney(symbols)
            if data:
                self.current_source = 'eastmoney'
                print(f"[数据源] [OK] 东方财富 成功")
                return data
        except Exception as e:
            print(f"[数据源] [FAIL] 东方财富 失败: {str(e)[:50]}")

        # 全部失败，返回模拟数据
        print(f"[数据源] WARNING: All sources failed, using mock data")
        return self._generate_mock_quotes(symbols)

    def _fetch_from_akshare(self, symbols: List[str]) -> Optional[Dict]:
        """从AkShare获取数据"""
        try:
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                return None

            result = {}
            for symbol in symbols:
                matching = df[df['代码'] == symbol]
                if not matching.empty:
                    row = matching.iloc[0]
                    result[symbol] = {
                        'code': symbol,
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'open': float(row.get('今开', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'volume': float(row.get('成交量', 0)),
                        'amount': float(row.get('成交额', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'turnover': float(row.get('换手率', 0)),
                        'market_cap': float(row.get('总市值', 0)),
                        'timestamp': datetime.now().isoformat()
                    }

            return result if result else None

        except Exception as e:
            return None

    def _fetch_from_sina(self, symbols: List[str]) -> Optional[Dict]:
        """从新浪财经获取数据（实时性最好）"""
        try:
            # 新浪财经API
            url = "http://hq.sinajs.cn/list=" + ",".join([f"sh{sym}" if sym.startswith('6')
                                                             else f"sz{sym}" for sym in symbols])

            response = requests.get(url, timeout=self.request_timeout)
            if response.status_code != 200:
                return None

            result = {}
            for i, symbol in enumerate(symbols):
                try:
                    data_str = response.text.split('\n')[i]
                    if not data_str or '"' not in data_str:
                        continue

                    # 解析新浪数据格式
                    parts = data_str.split('"')[1].split(',')

                    if len(parts) >= 32:
                        result[symbol] = {
                            'code': symbol,
                            'name': parts[0],
                            'price': float(parts[3]) if parts[3] else 0,
                            'open': float(parts[1]) if len(parts) > 1 and parts[1] else 0,
                            'high': float(parts[4]) if len(parts) > 4 and parts[4] else 0,
                            'low': float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                            'volume': float(parts[8]) if len(parts) > 8 and parts[8] else 0,
                            'amount': float(parts[9]) if len(parts) > 9 and parts[9] else 0,
                            'change_pct': ((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100)
                                          if len(parts) > 2 and parts[2] and parts[3] else 0,
                            'timestamp': datetime.now().isoformat()
                        }
                except:
                    continue

            return result if result else None

        except Exception as e:
            return None

    def _fetch_from_eastmoney(self, symbols: List[str]) -> Optional[Dict]:
        """从东方财富获取数据"""
        try:
            # 东方财富API
            url = "http://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1,
                'pz': len(symbols),
                'po': 1,
                'np': 1,
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25'
            }

            response = requests.get(url, params=params, timeout=self.request_timeout)

            if response.status_code != 200:
                return None

            data = response.json()

            if data.get('rc') != 0:
                return None

            result = {}
            for item in data.get('data', {}).get('diff', []):
                code = item.get('f12', '')
                if code in symbols:
                    result[code] = {
                        'code': code,
                        'name': item.get('f14', ''),
                        'price': item.get('f2', 0) / 100 if item.get('f2') else 0,
                        'open': item.get('f17', 0) / 100 if item.get('f17') else 0,
                        'high': item.get('f15', 0) / 100 if item.get('f15') else 0,
                        'low': item.get('f16', 0) / 100 if item.get('f16') else 0,
                        'volume': item.get('f5', 0),
                        'amount': item.get('f6', 0),
                        'change_pct': item.get('f3', 0),
                        'timestamp': datetime.now().isoformat()
                    }

            return result if result else None

        except Exception as e:
            return None

    def _generate_mock_quotes(self, symbols: List[str]) -> Dict:
        """生成模拟数据（降级方案）"""
        result = {}
        np.random.seed(int(datetime.now().timestamp()))

        for symbol in symbols:
            base_price = np.random.uniform(10, 100)
            change_pct = np.random.uniform(-5, 5)

            result[symbol] = {
                'code': symbol,
                'name': f'测试股票{symbol}',
                'price': round(base_price, 2),
                'open': round(base_price * (1 + np.random.uniform(-0.02, 0.02)), 2),
                'high': round(base_price * (1 + np.random.uniform(0, 0.03)), 2),
                'low': round(base_price * (1 - np.random.uniform(0, 0.03)), 2),
                'volume': np.random.randint(1000000, 50000000),
                'amount': np.random.randint(100000000, 500000000),
                'change_pct': round(change_pct, 2),
                'timestamp': datetime.now().isoformat(),
                'is_mock': True
            }

        return result

    def get_market_overview(self) -> Dict:
        """
        获取市场概览（涨跌家数、涨跌停等）

        Returns:
            市场概览数据
        """
        # 优先使用AkShare
        try:
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
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'akshare'
                }
        except:
            pass

        # 降级到模拟数据
        np.random.seed(int(datetime.now().timestamp()))
        total = 5000
        rising_ratio = np.random.uniform(0.3, 0.7)

        return {
            'total_stocks': total,
            'rising_stocks': int(total * rising_ratio),
            'falling_stocks': int(total * (1 - rising_ratio)),
            'limit_up': np.random.randint(5, 50),
            'limit_down': np.random.randint(5, 50),
            'rising_ratio': round(rising_ratio * 100, 2),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'mock'
        }

    def get_sector_data(self, sector_name: str) -> Dict:
        """获取板块数据"""
        # 优先使用AkShare
        try:
            sector_df = ak.stock_board_industry_name_em()

            if not sector_df.empty:
                matching = sector_df[sector_df['板块名称'].str.contains(sector_name, na=False)]

                if not matching.empty:
                    row = matching.iloc[0]
                    return {
                        'name': sector_name,
                        'change_pct': float(row.get('涨跌幅', 0)) if '涨跌幅' in row else 0,
                        'leading_stock': row.get('领涨股票', '') if '领涨股票' in row else '',
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'akshare'
                    }
        except:
            pass

        # 降级到模拟数据
        np.random.seed(hash(sector_name) % 2**32)

        return {
            'name': sector_name,
            'change_pct': round(np.random.uniform(-5, 5), 2),
            'leading_stock': f'测试龙头{np.random.randint(1, 100)}',
            'timestamp': datetime.now().isoformat(),
            'data_source': 'mock'
        }


# 单例模式
_fetcher_instance = None

def get_robust_fetcher() -> RobustMarketDataFetcher:
    """获取增强版数据获取器实例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = RobustMarketDataFetcher()
    return _fetcher_instance


# 测试代码
if __name__ == "__main__":
    print("=== 增强版数据获取器测试 ===\n")

    fetcher = RobustMarketDataFetcher()

    # 测试获取实时行情
    print("1. 测试获取实时行情...")
    symbols = ['600519', '000858', '600036']
    quotes = fetcher.get_realtime_quotes(symbols)

    print(f"当前数据源: {fetcher.current_source}")
    for symbol, data in quotes.items():
        mock_flag = " [模拟]" if data.get('is_mock') else ""
        print(f"  {symbol} {data['name']}: {data['price']:.2f} ({data['change_pct']:+.2f}%){mock_flag}")

    # 测试市场概览
    print("\n2. 测试获取市场概览...")
    overview = fetcher.get_market_overview()
    print(f"数据源: {overview['data_source']}")
    print(f"  总数: {overview['total_stocks']}")
    print(f"  上涨: {overview['rising_stocks']} ({overview['rising_ratio']:.1f}%)")
    print(f"  涨停: {overview['limit_up']}")
    print(f"  跌停: {overview['limit_down']}")

    # 测试板块数据
    print("\n3. 测试获取板块数据...")
    sector_data = fetcher.get_sector_data('半导体')
    print(f"数据源: {sector_data['data_source']}")
    print(f"  {sector_data['name']}: {sector_data['change_pct']:+.2f}%")
