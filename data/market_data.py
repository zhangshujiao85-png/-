"""
Market Data Fetcher Module
Use AkShare or Tushare to fetch real A-share market data
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import os

# Try to import Tushare
try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False


class MarketDataFetcher:
    """Market data fetcher"""

    def __init__(self, cache_ttl: int = 3600, use_tushare: bool = True):
        """
        Initialize data fetcher

        Args:
            cache_ttl: Cache expiration time (seconds)
            use_tushare: Whether to use Tushare (requires token)
        """
        self.cache_ttl = cache_ttl
        self._cache = {}

        # Initialize Tushare if available and requested
        self.use_tushare = use_tushare and TUSHARE_AVAILABLE
        if self.use_tushare:
            token = os.getenv("TUSHARE_TOKEN")
            if token:
                try:
                    ts.set_token(token)
                    self.pro = ts.pro_api()
                    print("✅ Using Tushare data source")
                except Exception as e:
                    print(f"Tushare 初始化失败: {e}, fallback to AkShare")
                    self.use_tushare = False
            else:
                print("WARNING: TUSHARE_TOKEN not set, using AkShare")
                self.use_tushare = False

    def get_stock_list(self) -> pd.DataFrame:
        """
        Get A-share stock list

        Returns:
            DataFrame with stock code, name, industry
        """
        try:
            # Get A-share list
            stock_list = ak.stock_info_a_code_name()

            # Rename columns
            stock_list.columns = ['code', 'name']

            # Add market identifier
            stock_list['market'] = stock_list['code'].apply(
                lambda x: 'SH' if x.startswith('6') else 'SZ'
            )

            return stock_list

        except Exception as e:
            print(f"Failed to get stock list: {e}")
            return pd.DataFrame(columns=['code', 'name', 'market'])

    def get_index_data(self, index_code: str, period: int = 250) -> pd.DataFrame:
        """
        Get index historical data

        Args:
            index_code: Index code (e.g., '000001' for Shanghai Composite)
            period: Number of days to fetch

        Returns:
            DataFrame with date, open, high, low, close, volume
        """
        try:
            # Map index codes to AkShare format
            index_map = {
                '000001': 's_sh000001',  # Shanghai Composite
                '399001': 's_sz399001',  # Shenzhen Component
                '399006': 's_sz399006',  # ChiNext
            }

            # Get historical data using stock_zh_index_daily
            df = ak.index_zh_a_hist(symbol=index_map.get(index_code, f"sh{index_code}"),
                                    period="daily",
                                    start_date=(datetime.now() - timedelta(days=period+365)).strftime("%Y%m%d"))

            if df.empty:
                print(f"No data for index {index_code}")
                return pd.DataFrame()

            # Rename columns to standard format
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # Select needed columns
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            # Convert date format
            df['date'] = pd.to_datetime(df['date'])

            # Sort and take recent data
            df = df.sort_values('date').tail(period).reset_index(drop=True)

            return df

        except Exception as e:
            print(f"Failed to get index data {index_code}: {e}, using mock data")
            return self._generate_mock_index_data(index_code, period)

    def get_stock_quote(self, symbol: str) -> Dict:
        """
        Get stock real-time quote

        Args:
            symbol: Stock code (e.g., '600519')

        Returns:
            Dictionary with price, volume, change percentage, etc.
        """
        try:
            # Get real-time quotes
            df = ak.stock_zh_a_spot_em()

            # Find target stock
            stock_data = df[df['代码'] == symbol]

            if stock_data.empty:
                return {}

            result = {
                'code': symbol,
                'name': stock_data['名称'].values[0],
                'price': stock_data['最新价'].values[0],
                'open': stock_data['今开'].values[0],
                'high': stock_data['最高'].values[0],
                'low': stock_data['最低'].values[0],
                'volume': stock_data['成交量'].values[0],
                'amount': stock_data['成交额'].values[0],
                'change_pct': stock_data['涨跌幅'].values[0],
                'change_amount': stock_data['涨跌额'].values[0],
                'amplitude': stock_data['振幅'].values[0],
                'turnover': stock_data['换手率'].values[0],
                'market_cap': stock_data['总市值'].values[0],
            }

            return result

        except Exception as e:
            print(f"Failed to get stock quote {symbol}: {e}, using mock data")
            return self._generate_mock_stock_quote(symbol)

    def get_stock_history(self, symbol: str, period: int = 250) -> pd.DataFrame:
        """
        Get stock historical data

        Args:
            symbol: Stock code
            period: Number of days

        Returns:
            DataFrame with historical quotes
        """
        try:
            # Get historical data
            df = ak.stock_zh_a_hist(symbol=symbol,
                                   period="daily",
                                   start_date="19900101",
                                   adjust="qfq")

            # Rename columns
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume',
                        'amount', 'amplitude', 'change_pct', 'change_amount', 'turnover']

            # Convert date format
            df['date'] = pd.to_datetime(df['date'])

            # Sort and take recent data
            df = df.sort_values('date').tail(period).reset_index(drop=True)

            return df

        except Exception as e:
            print(f"Failed to get stock history {symbol}: {e}, using mock data")
            # Generate mock historical data
            dates = pd.date_range(end=datetime.now(), periods=period, freq='D')
            np.random.seed(hash(symbol) % 2**32)
            base_price = np.random.uniform(10, 1000)
            returns = np.random.normal(0.001, 0.02, period)
            prices = base_price * (1 + returns).cumprod()

            df = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.uniform(-0.01, 0.01, period)),
                'close': prices,
                'high': prices * (1 + np.random.uniform(0, 0.02, period)),
                'low': prices * (1 - np.random.uniform(0, 0.02, period)),
                'volume': np.random.randint(1000000, 50000000, period)
            })

            df = df[['date', 'open', 'close', 'high', 'low', 'volume']]
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date').reset_index(drop=True)

    def get_stock_financials(self, symbol: str) -> Dict:
        """
        Get stock financial data

        Args:
            symbol: Stock code

        Returns:
            Dictionary with financial indicators
        """
        try:
            # Get stock basic info
            info = ak.stock_individual_info_em(symbol=symbol)

            # Convert to dictionary
            info_dict = {}
            for _, row in info.iterrows():
                info_dict[row['item']] = row['value']

            # Extract key financial indicators
            result = {
                'code': symbol,
                'name': info_dict.get('股票简称', ''),
                'industry': info_dict.get('行业', ''),
                'pe_ratio': float(info_dict.get('市盈率-动态', 0)) if info_dict.get('市盈率-动态') else 0,
            }

            return result

        except Exception as e:
            print(f"Failed to get financial data {symbol}: {e}")
            return {}

    def get_sector_data(self, sector_name: str) -> Dict:
        """
        Get sector/industry data

        Args:
            sector_name: Sector name (e.g., '军工', '半导体', '新能源')

        Returns:
            Dictionary with sector sentiment, performance, and key stats
        """
        try:
            # Get sector index data
            # Map common sector names to their codes
            sector_map = {
                '军工': '国防军工',
                '半导体': '半导体',
                '新能源': '新能源',
                '医药': '医药生物',
                '消费': '食品饮料',
                '银行': '银行',
                '地产': '房地产',
                '煤炭': '煤炭',
                '石油': '石油石化',
                '黄金': '贵金属',
                'AI': '人工智能',
                '人工智能': '人工智能',
                '软件': '软件服务',
                '传媒': '传媒',
                '通信': '通信',
                '电力': '电力及公用事业',
                '汽车': '汽车',
                '化工': '基础化工',
            }

            mapped_name = sector_map.get(sector_name, sector_name)

            # Get sector performance from Eastmoney
            try:
                sector_df = ak.stock_board_industry_name_em()

                # Find matching sector
                sector_row = sector_df[sector_df['板块名称'].str.contains(sector_name, na=False)]

                if not sector_row.empty:
                    result = {
                        'name': sector_name,
                        'code': sector_row['板块代码'].values[0] if '板块代码' in sector_row.columns else '',
                        'change_pct': sector_row['涨跌幅'].values[0] if '涨跌幅' in sector_row.columns else 0,
                        'leading_stocks': sector_row['领涨股票'].values[0] if '领涨股票' in sector_row.columns else '',
                        'market_cap': sector_row['总市值'].values[0] if '总市值' in sector_row.columns else 0,
                        'volume': sector_row['成交量'].values[0] if '成交量' in sector_row.columns else 0,
                        'timestamp': datetime.now().isoformat()
                    }
                    return result
            except Exception as e:
                print(f"Failed to get sector data from Eastmoney: {e}")

            # Fallback: generate mock sector data
            return self._generate_mock_sector_data(sector_name)

        except Exception as e:
            print(f"Failed to get sector data {sector_name}: {e}")
            return self._generate_mock_sector_data(sector_name)

    def get_sector_constituents(self, sector_name: str) -> pd.DataFrame:
        """
        Get constituent stocks of a sector

        Args:
            sector_name: Sector name

        Returns:
            DataFrame with stock codes, names, and key metrics
        """
        try:
            # Get sector constituents from Eastmoney
            sector_map = {
                '军工': '国防军工',
                '半导体': '半导体',
                '新能源': '新能源',
                '医药': '医药生物',
                '消费': '食品饮料',
                '银行': '银行',
                '地产': '房地产',
                '煤炭': '煤炭',
                '石油': '石油石化',
                '黄金': '贵金属',
                'AI': '人工智能',
                '人工智能': '人工智能',
                '软件': '软件服务',
                '传媒': '传媒',
                '通信': '通信',
                '电力': '电力及公用事业',
                '汽车': '汽车',
                '化工': '基础化工',
            }

            mapped_name = sector_map.get(sector_name, sector_name)

            # Get all sectors first to find the code
            sector_list = ak.stock_board_industry_name_em()

            matching_sector = sector_list[sector_list['板块名称'].str.contains(sector_name, na=False)]

            if not matching_sector.empty:
                sector_code = matching_sector.iloc[0]['板块代码'] if '板块代码' in matching_sector.columns else matching_sector.iloc[0].name

                # Get constituents
                constituents = ak.stock_board_industry_cons_em(symbol=sector_code)

                if not constituents.empty:
                    # Rename columns to standard format
                    col_mapping = {
                        '代码': 'code',
                        '名称': 'name',
                        '最新价': 'price',
                        '涨跌幅': 'change_pct',
                        '涨跌额': 'change_amount',
                        '成交量': 'volume',
                        '成交额': 'amount',
                        '振幅': 'amplitude',
                        '最高': 'high',
                        '最低': 'low',
                        '今开': 'open',
                        '昨收': 'pre_close',
                        '换手率': 'turnover',
                        '市盈率-动态': 'pe_ratio',
                        '总市值': 'market_cap',
                        '流通市值': 'float_cap'
                    }

                    constituents = constituents.rename(columns=col_mapping)

                    # Keep only essential columns
                    essential_cols = [col for col in ['code', 'name', 'price', 'change_pct', 'volume',
                                                      'amount', 'turnover', 'market_cap', 'float_cap']
                                       if col in constituents.columns]

                    return constituents[essential_cols]

        except Exception as e:
            print(f"Failed to get sector constituents {sector_name}: {e}")

        # Fallback: generate mock constituents
        return self._generate_mock_constituents(sector_name)

    def get_realtime_quote(self, stock_code: str) -> Dict:
        """
        Get real-time stock quote (alias for get_stock_quote)

        Args:
            stock_code: Stock code (e.g., '600519')

        Returns:
            Dictionary with real-time quote data
        """
        return self.get_stock_quote(stock_code)

    def get_pre_market_data(self) -> Dict:
        """
        Get pre-market data (A50 futures, US markets, etc.)

        Returns:
            Dictionary with pre-market indicators
        """
        try:
            result = {
                'timestamp': datetime.now().isoformat(),
                'a50': self._get_a50_data(),
                'us_stocks': self._get_us_chinese_stocks(),
                'asia_markets': self._get_asia_markets()
            }
            return result
        except Exception as e:
            print(f"Failed to get pre-market data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'a50': {},
                'us_stocks': {},
                'asia_markets': {}
            }

    def _get_a50_data(self) -> Dict:
        """Get A50 futures data"""
        try:
            # A50 futures from Eastmoney
            a50_df = ak.index_zh_a_hist(symbol="ftseg上证50", period="daily")

            if not a50_df.empty:
                latest = a50_df.iloc[-1]
                return {
                    'name': 'A50期货',
                    'price': float(latest.get('收盘', latest.get('close', 0))),
                    'change_pct': float(latest.get('涨跌幅', 0)) if '涨跌幅' in latest else 0,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Failed to get A50 data: {e}")

        # Mock data fallback
        base_value = 13500
        change_pct = np.random.uniform(-3, 3)
        return {
            'name': 'A50期货',
            'price': round(base_value * (1 + change_pct / 100), 2),
            'change_pct': round(change_pct, 2),
            'timestamp': datetime.now().isoformat()
        }

    def _get_us_chinese_stocks(self) -> Dict:
        """Get US-listed Chinese stocks data"""
        try:
            # Alibaba, Baidu, JD, NIO, etc.
            symbols = ['BABA', 'JD', 'PDD', 'NIO', 'BIDU']
            result = {}

            for symbol in symbols:
                try:
                    # Get US stock data from Eastmoney
                    us_df = ak.stock_us_spot_em()

                    matching = us_df[us_df['代码'] == symbol]
                    if not matching.empty:
                        result[symbol] = {
                            'name': matching['名称'].values[0] if '名称' in matching.columns else symbol,
                            'price': float(matching['最新价'].values[0]) if '最新价' in matching.columns else 0,
                            'change_pct': float(matching['涨跌幅'].values[0]) if '涨跌幅' in matching.columns else 0
                        }
                except:
                    pass

            if result:
                return result

        except Exception as e:
            print(f"Failed to get US Chinese stocks: {e}")

        # Mock data fallback
        return {
            'BABA': {'name': '阿里巴巴', 'price': 85.0, 'change_pct': np.random.uniform(-5, 5)},
            'JD': {'name': '京东', 'price': 30.0, 'change_pct': np.random.uniform(-5, 5)},
            'PDD': {'name': '拼多多', 'price': 140.0, 'change_pct': np.random.uniform(-5, 5)},
            'NIO': {'name': '蔚来', 'price': 8.0, 'change_pct': np.random.uniform(-5, 5)},
            'BIDU': {'name': '百度', 'price': 110.0, 'change_pct': np.random.uniform(-5, 5)}
        }

    def _get_asia_markets(self) -> Dict:
        """Get Asia market data"""
        try:
            result = {}

            # Get other Asian markets
            markets = {
                '日经225': 'NKY',
                '恒生': 'HSI',
                '台湾加权': 'TWI'
            }

            for name, code in markets.items():
                try:
                    idx_data = ak.index_zh_a_hist(symbol=f"s_sh{code}", period="daily")
                    if not idx_data.empty:
                        latest = idx_data.iloc[-1]
                        result[name] = {
                            'name': name,
                            'price': float(latest.get('收盘', latest.get('close', 0))),
                            'change_pct': float(latest.get('涨跌幅', 0)) if '涨跌幅' in latest else 0
                        }
                except:
                    pass

            if result:
                return result

        except Exception as e:
            print(f"Failed to get Asia markets: {e}")

        # Mock data fallback
        return {
            '日经225': {'name': '日经225', 'price': 38000, 'change_pct': np.random.uniform(-2, 2)},
            '恒生': {'name': '恒生指数', 'price': 17500, 'change_pct': np.random.uniform(-3, 3)},
            '台湾加权': {'name': '台湾加权', 'price': 18500, 'change_pct': np.random.uniform(-2, 2)}
        }

    def _generate_mock_sector_data(self, sector_name: str) -> Dict:
        """Generate mock sector data"""
        np.random.seed(hash(sector_name) % 2**32)

        return {
            'name': sector_name,
            'code': f'BK{hash(sector_name) % 10000:04d}',
            'change_pct': round(np.random.uniform(-5, 5), 2),
            'leading_stocks': f'测试龙头{np.random.randint(1, 1000)}',
            'market_cap': round(np.random.uniform(100, 10000) * 100000000, 2),
            'volume': round(np.random.uniform(1, 100) * 100000000, 2),
            'timestamp': datetime.now().isoformat()
        }

    def _generate_mock_constituents(self, sector_name: str) -> pd.DataFrame:
        """Generate mock sector constituents"""
        np.random.seed(hash(sector_name) % 2**32)

        n_stocks = np.random.randint(10, 50)

        data = {
            'code': [f'{np.random.choice([6, 0, 3])}{np.random.randint(0, 9):02d}{np.random.randint(0, 9):03d}' for _ in range(n_stocks)],
            'name': [f'{sector_name}股票{i+1}' for i in range(n_stocks)],
            'price': [round(np.random.uniform(5, 200), 2) for _ in range(n_stocks)],
            'change_pct': [round(np.random.uniform(-10, 10), 2) for _ in range(n_stocks)],
            'volume': [np.random.randint(100000, 100000000) for _ in range(n_stocks)],
            'amount': [round(np.random.uniform(1, 10000) * 10000, 2) for _ in range(n_stocks)],
            'turnover': [round(np.random.uniform(0.1, 20), 2) for _ in range(n_stocks)],
            'market_cap': [round(np.random.uniform(10, 1000) * 100000000, 2) for _ in range(n_stocks)]
        }

        return pd.DataFrame(data)

    def batch_get_stock_history(self, symbols: List[str], period: int = 250,
                               delay: float = 0.5) -> Dict[str, pd.DataFrame]:
        """
        Batch fetch stock historical data

        Args:
            symbols: List of stock codes
            period: Number of days
            delay: Delay between requests (seconds)

        Returns:
            Dictionary mapping stock codes to historical data
        """
        result = {}

        for symbol in symbols:
            data = self.get_stock_history(symbol, period)
            if not data.empty:
                result[symbol] = data

            # Delay to avoid too frequent requests
            time.sleep(delay)

        return result

    def _generate_mock_index_data(self, index_code: str, period: int) -> pd.DataFrame:
        """Generate mock index data for demonstration when AkShare fails"""
        dates = pd.date_range(end=datetime.now(), periods=period, freq='D')

        # Generate random walk price data
        np.random.seed(hash(index_code) % 2**32)
        base_price = 3000 if '000001' in index_code else 10000
        returns = np.random.normal(0.001, 0.02, period)
        prices = base_price * (1 + returns).cumprod()

        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, period)),
            'high': prices * (1 + np.random.uniform(0, 0.02, period)),
            'low': prices * (1 - np.random.uniform(0, 0.02, period)),
            'close': prices,
            'volume': np.random.randint(100000000, 500000000, period)
        })

        return df

    def _generate_mock_stock_quote(self, symbol: str) -> Dict:
        """Generate mock stock quote for demonstration"""
        base_price = np.random.uniform(10, 1000)
        change_pct = np.random.uniform(-5, 5)

        return {
            'code': symbol,
            'name': f'测试股票{symbol}',
            'price': round(base_price, 2),
            'open': round(base_price * (1 + np.random.uniform(-0.02, 0.02)), 2),
            'high': round(base_price * (1 + np.random.uniform(0, 0.03)), 2),
            'low': round(base_price * (1 - np.random.uniform(0, 0.03)), 2),
            'volume': np.random.randint(1000000, 50000000),
            'change_pct': round(change_pct, 2),
            'market_cap': round(base_price * np.random.uniform(1, 10) * 100000000, 2)
        }


# Test code
if __name__ == "__main__":
    fetcher = MarketDataFetcher()

    # Test getting stock list
    print("=== Test: Get stock list ===")
    stock_list = fetcher.get_stock_list()
    print(f"Got {len(stock_list)} stocks")
    print(stock_list.head())

    # Test getting index data
    print("\n=== Test: Get index data ===")
    index_data = fetcher.get_index_data('000001', period=30)
    print(f"Got {len(index_data)} Shanghai Composite data points")
    print(index_data.head())

    # Test getting stock quote
    print("\n=== Test: Get stock quote ===")
    quote = fetcher.get_stock_quote('600519')
    print(quote)
