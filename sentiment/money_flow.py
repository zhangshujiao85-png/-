"""
Money Flow Analysis Module
Analyzes capital flow: northbound funds, main funds, large orders
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class MoneyFlowAnalyzer:
    """Money flow analyzer"""

    def __init__(self, data_fetcher=None, use_cmes=True):
        """
        Initialize money flow analyzer

        Args:
            data_fetcher: Market data fetcher instance
            use_cmes: 是否优先使用CMES数据源
        """
        self.data_fetcher = data_fetcher
        self.use_cmes = use_cmes

        if self.data_fetcher is None:
            if use_cmes:
                try:
                    from data.cmes_market_data import get_cmes_market_data
                    self.cmes_fetcher = get_cmes_market_data()
                    self.data_fetcher = None
                    return
                except Exception as e:
                    print(f"[资金流向] CMES初始化失败，使用传统数据源: {e}")

            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def calculate_money_flow_score(self, index_code: str = '000001') -> Dict:
        """
        Calculate money flow score (0-100)

        Args:
            index_code: Market index code

        Returns:
            Dictionary with money flow metrics and score
        """
        try:
            # Get money flow data
            flow_data = self._get_money_flow_data()

            # Calculate component scores
            northbound_score = self._calculate_northbound_score(flow_data)
            main_fund_score = self._calculate_main_fund_score(flow_data)
            large_order_score = self._calculate_large_order_score(flow_data)

            # Comprehensive money flow score
            flow_score = (
                northbound_score * 0.35 +
                main_fund_score * 0.40 +
                large_order_score * 0.25
            )

            return {
                'timestamp': datetime.now().isoformat(),
                'flow_score': round(flow_score, 2),
                'northbound_score': round(northbound_score, 2),
                'main_fund_score': round(main_fund_score, 2),
                'large_order_score': round(large_order_score, 2),
                'metrics': flow_data
            }

        except Exception as e:
            print(f"Failed to calculate money flow score: {e}")
            # Return default values on error
            return {
                'timestamp': datetime.now().isoformat(),
                'flow_score': 50.0,
                'northbound_score': 50.0,
                'main_fund_score': 50.0,
                'large_order_score': 50.0,
                'metrics': {}
            }

    def _get_money_flow_data(self) -> Dict:
        """
        Get money flow data

        Returns:
            Dictionary with money flow metrics
        """
        # 优先使用CMES数据源
        if self.use_cmes and hasattr(self, 'cmes_fetcher'):
            try:
                return self.cmes_fetcher.get_money_flow()
            except Exception as e:
                print(f"[资金流向] CMES数据获取失败: {e}")

        # 降级到传统数据源
        try:
            import akshare as ak

            # Get capital flow data
            try:
                # Try to get northbound funds data
                northbound = ak.stock_em_hsgt_hist_em(symbol="北向资金")

                if not northbound.empty:
                    latest = northbound.iloc[-1]
                    northbound_flow = float(latest.get('北向资金', latest.get('flow', 0)))
                else:
                    northbound_flow = 0
            except:
                northbound_flow = 0

            # Get main fund flow
            try:
                # Get individual stock flow data and aggregate
                market_data = ak.stock_zh_a_spot_em()

                if not market_data.empty and '成交额' in market_data.columns:
                    # Estimate main fund flow from turnover and price change
                    total_amount = market_data['成交额'].sum()

                    # Calculate net flow based on price action
                    rising_amount = market_data[market_data['涨跌幅'] > 0]['成交额'].sum()
                    falling_amount = market_data[market_data['涨跌幅'] < 0]['成交额'].sum()

                    main_net_flow = (rising_amount - falling_amount) / total_amount * 100 if total_amount > 0 else 0
                else:
                    main_net_flow = 0
            except:
                main_net_flow = 0

            # Get large order data
            try:
                # Get large order statistics
                flow_stats = self._get_large_order_stats()
                super_large_inflow = flow_stats.get('super_large_inflow', 0)
                large_inflow = flow_stats.get('large_inflow', 0)
            except:
                super_large_inflow = 0
                large_inflow = 0

            return {
                'northbound_net_inflow': round(northbound_flow, 2),  # 亿元
                'main_net_inflow': round(main_net_flow, 2),  # %
                'super_large_inflow': round(super_large_inflow, 2),  # 亿元
                'large_inflow': round(large_inflow, 2),  # 亿元
            }

        except Exception as e:
            print(f"Failed to get money flow data: {e}")
            return self._generate_mock_flow_data()

    def _get_large_order_stats(self) -> Dict:
        """Get large order flow statistics"""
        try:
            import akshare as ak

            # Get individual stock capital flow
            # Using stock_zh_a_spot_em to get aggregate data
            market_data = ak.stock_zh_a_spot_em()

            if not market_data.empty:
                # Estimate large order flow from market data
                # Large orders typically correlate with high turnover stocks

                # Get top 100 stocks by turnover
                if '换手率' in market_data.columns and '成交额' in market_data.columns:
                    top_stocks = market_data.nlargest(100, '换手率')

                    # Estimate large order flow
                    total_large_amount = top_stocks['成交额'].sum()

                    # Super large orders (>1亿)
                    super_large = top_stocks[top_stocks['成交额'] > 100000000]
                    super_large_inflow = super_large['成交额'].sum() / 100000000  # Convert to 亿元

                    # Large orders (>5000万)
                    large = top_stocks[top_stocks['成交额'] > 50000000]
                    large_inflow = large['成交额'].sum() / 100000000

                    return {
                        'super_large_inflow': super_large_inflow,
                        'large_inflow': large_inflow
                    }

        except Exception as e:
            print(f"Failed to get large order stats: {e}")

        return {
            'super_large_inflow': 0,
            'large_inflow': 0
        }

    def _calculate_northbound_score(self, flow_data: Dict) -> float:
        """
        Calculate northbound funds score

        Score based on net inflow amount
        - >50亿: 100 points
        - 20-50亿: 80 points
        - 0-20亿: 60 points
        - -20-0亿: 40 points
        - <-50亿: 0 points
        """
        inflow = flow_data.get('northbound_net_inflow', 0)

        if inflow >= 50:
            return 100.0
        elif inflow >= 20:
            return 80.0 + (inflow - 20) * 1  # 80-100
        elif inflow >= 0:
            return 60.0 + inflow * 2  # 60-80
        elif inflow >= -20:
            return 40.0 + inflow * 1.5  # 20-40
        elif inflow >= -50:
            return 20.0 + (inflow + 50) * 0.67  # 0-20
        else:
            return 0.0

    def _calculate_main_fund_score(self, flow_data: Dict) -> float:
        """
        Calculate main fund flow score

        Score based on main fund net inflow percentage
        """
        inflow = flow_data.get('main_net_inflow', 0)

        # Normalize -10% to +10% range to 0-100 score
        # 0% = 50 points
        if inflow >= 10:
            return 100.0
        elif inflow >= 0:
            return 50.0 + inflow * 5  # 50-100
        elif inflow >= -10:
            return 50.0 + inflow * 5  # 0-50
        else:
            return 0.0

    def _calculate_large_order_score(self, flow_data: Dict) -> float:
        """
        Calculate large order score

        Score based on large order inflow
        """
        super_large = flow_data.get('super_large_inflow', 0)
        large = flow_data.get('large_inflow', 0)

        # Total large order inflow
        total_large = super_large + large

        if total_large >= 100:  # >100亿
            return 100.0
        elif total_large >= 50:
            return 80.0 + (total_large - 50) * 0.4
        elif total_large >= 0:
            return 50.0 + total_large
        elif total_large >= -50:
            return 50.0 + total_large
        else:
            return 0.0

    def _generate_mock_flow_data(self) -> Dict:
        """Generate mock money flow data for testing"""
        np.random.seed(int(datetime.now().timestamp()))

        # Generate random but reasonable flow data
        northbound = np.random.uniform(-100, 100)  # -100 to 100亿
        main_inflow = np.random.uniform(-5, 5)  # -5% to 5%
        super_large = np.random.uniform(-50, 200)  # -50 to 200亿
        large = np.random.uniform(-30, 150)  # -30 to 150亿

        return {
            'northbound_net_inflow': round(northbound, 2),
            'main_net_inflow': round(main_inflow, 2),
            'super_large_inflow': round(super_large, 2),
            'large_inflow': round(large, 2),
        }

    def get_flow_trend(self, days: int = 5) -> pd.DataFrame:
        """
        Get money flow trend over past days

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with flow history
        """
        try:
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

            # For now, generate mock historical data
            data = []
            for i, date in enumerate(dates):
                np.random.seed(i)
                flow = self._generate_mock_flow_data()
                data.append({
                    'date': date,
                    'flow_score': self._calculate_main_fund_score(flow),
                    'northbound': flow['northbound_net_inflow'],
                    'main_inflow': flow['main_net_inflow']
                })

            return pd.DataFrame(data)

        except Exception as e:
            print(f"Failed to get flow trend: {e}")
            return pd.DataFrame()


# Test code
if __name__ == "__main__":
    analyzer = MoneyFlowAnalyzer()

    print("=== Money Flow Analysis ===")
    result = analyzer.calculate_money_flow_score()

    print(f"Flow Score: {result['flow_score']:.1f}")
    print(f"Northbound Score: {result['northbound_score']:.1f}")
    print(f"Main Fund Score: {result['main_fund_score']:.1f}")
    print(f"Large Order Score: {result['large_order_score']:.1f}")
    print(f"\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")
