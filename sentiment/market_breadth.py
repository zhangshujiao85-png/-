"""
Market Breadth Analysis Module
Analyzes market breadth indicators: advance/decline ratio, limit up/down stocks, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class MarketBreadthAnalyzer:
    """Market breadth analyzer"""

    def __init__(self, data_fetcher=None, use_cmes=True):
        """
        Initialize market breadth analyzer

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
                    print(f"[市场宽度] CMES初始化失败，使用传统数据源: {e}")

            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def calculate_breadth_score(self, index_code: str = '000001') -> Dict:
        """
        Calculate market breadth score (0-100)

        Args:
            index_code: Market index code

        Returns:
            Dictionary with breadth metrics and score
        """
        try:
            # Get market overview data
            breadth_data = self._get_market_breadth_data()

            # Calculate component scores
            advance_decline_score = self._calculate_advance_decline_score(breadth_data)
            limit_up_down_score = self._calculate_limit_up_down_score(breadth_data)
            breadth_ratio_score = self._calculate_breadth_ratio_score(breadth_data)

            # Comprehensive breadth score
            breadth_score = (
                advance_decline_score * 0.4 +
                limit_up_down_score * 0.3 +
                breadth_ratio_score * 0.3
            )

            return {
                'timestamp': datetime.now().isoformat(),
                'breadth_score': round(breadth_score, 2),
                'advance_decline_score': round(advance_decline_score, 2),
                'limit_up_down_score': round(limit_up_down_score, 2),
                'breadth_ratio_score': round(breadth_ratio_score, 2),
                'metrics': breadth_data
            }

        except Exception as e:
            print(f"Failed to calculate breadth score: {e}")
            # Return default values on error
            return {
                'timestamp': datetime.now().isoformat(),
                'breadth_score': 50.0,
                'advance_decline_score': 50.0,
                'limit_up_down_score': 50.0,
                'breadth_ratio_score': 50.0,
                'metrics': {}
            }

    def _get_market_breadth_data(self) -> Dict:
        """
        Get market breadth data

        Returns:
            Dictionary with breadth metrics
        """
        # 优先使用CMES数据源
        if self.use_cmes and hasattr(self, 'cmes_fetcher'):
            try:
                return self.cmes_fetcher.get_market_breadth()
            except Exception as e:
                print(f"[市场宽度] CMES数据获取失败: {e}")

        # 降级到传统数据源
        try:
            # Get real-time market data from AkShare
            import akshare as ak

            # Get market overview
            market_data = ak.stock_zh_a_spot_em()

            if market_data.empty:
                return self._generate_mock_breadth_data()

            # Calculate breadth metrics
            total_stocks = len(market_data)

            # Count rising/falling stocks
            rising_stocks = len(market_data[market_data['涨跌幅'] > 0])
            falling_stocks = len(market_data[market_data['涨跌幅'] < 0])
            flat_stocks = total_stocks - rising_stocks - falling_stocks

            # Count limit up/down stocks (±10%)
            limit_up_stocks = len(market_data[market_data['涨跌幅'] >= 9.9])
            limit_down_stocks = len(market_data[market_data['涨跌幅'] <= -9.9])

            # Strong rising/falling (>5%)
            strong_rising = len(market_data[market_data['涨跌幅'] >= 5])
            strong_falling = len(market_data[market_data['涨跌幅'] <= -5])

            return {
                'total_stocks': total_stocks,
                'rising_stocks': rising_stocks,
                'falling_stocks': falling_stocks,
                'flat_stocks': flat_stocks,
                'limit_up_stocks': limit_up_stocks,
                'limit_down_stocks': limit_down_stocks,
                'strong_rising': strong_rising,
                'strong_falling': strong_falling,
                'rising_ratio': round(rising_stocks / total_stocks * 100, 2) if total_stocks > 0 else 0,
                'advance_decline_ratio': round(rising_stocks / falling_stocks, 2) if falling_stocks > 0 else rising_stocks
            }

        except Exception as e:
            print(f"Failed to get market breadth data: {e}")
            return self._generate_mock_breadth_data()

    def _calculate_advance_decline_score(self, breadth_data: Dict) -> float:
        """
        Calculate advance/decline score

        Score based on rising ratio
        - >70% rising: 100 points
        - 50-70% rising: 70-100 points
        - 30-50% rising: 30-70 points
        - <30% rising: 0-30 points
        """
        rising_ratio = breadth_data.get('rising_ratio', 50)

        if rising_ratio >= 70:
            return 100.0
        elif rising_ratio >= 50:
            # 50-70 maps to 70-100
            return 70 + (rising_ratio - 50) * 1.5
        elif rising_ratio >= 30:
            # 30-50 maps to 30-70
            return 30 + (rising_ratio - 30) * 2
        else:
            # 0-30 maps to 0-30
            return rising_ratio

    def _calculate_limit_up_down_score(self, breadth_data: Dict) -> float:
        """
        Calculate limit up/down score

        Score based on limit up vs limit down ratio
        """
        limit_up = breadth_data.get('limit_up_stocks', 0)
        limit_down = breadth_data.get('limit_down_stocks', 0)

        if limit_up + limit_down == 0:
            return 50.0  # Neutral when no limit moves

        limit_up_ratio = limit_up / (limit_up + limit_down)

        # Convert ratio to 0-100 score
        return limit_up_ratio * 100

    def _calculate_breadth_ratio_score(self, breadth_data: Dict) -> float:
        """
        Calculate breadth ratio score

        Based on advance/decline ratio
        - A/D ratio > 2: Strong bullish (100 points)
        - A/D ratio 1.5-2: Bullish (80 points)
        - A/D ratio 1-1.5: Mild bullish (60 points)
        - A/D ratio 0.8-1: Neutral (50 points)
        - A/D ratio 0.5-0.8: Mild bearish (40 points)
        - A/D ratio < 0.5: Bearish (20 points)
        """
        ad_ratio = breadth_data.get('advance_decline_ratio', 1)

        if ad_ratio >= 2:
            return 100.0
        elif ad_ratio >= 1.5:
            return 80.0
        elif ad_ratio >= 1:
            return 60.0
        elif ad_ratio >= 0.8:
            return 50.0
        elif ad_ratio >= 0.5:
            return 40.0
        else:
            return 20.0

    def _generate_mock_breadth_data(self) -> Dict:
        """Generate mock market breadth data for testing"""
        np.random.seed(int(datetime.now().timestamp()))

        total_stocks = 5000
        base_ratio = np.random.uniform(0.3, 0.7)  # Random rising ratio

        rising_stocks = int(total_stocks * base_ratio)
        falling_stocks = int(total_stocks * (1 - base_ratio) * 0.95)
        flat_stocks = total_stocks - rising_stocks - falling_stocks

        # Generate limit moves
        limit_up_stocks = int(rising_stocks * np.random.uniform(0.01, 0.05))
        limit_down_stocks = int(falling_stocks * np.random.uniform(0.01, 0.05))

        # Strong moves
        strong_rising = int(rising_stocks * np.random.uniform(0.1, 0.3))
        strong_falling = int(falling_stocks * np.random.uniform(0.1, 0.3))

        return {
            'total_stocks': total_stocks,
            'rising_stocks': rising_stocks,
            'falling_stocks': falling_stocks,
            'flat_stocks': flat_stocks,
            'limit_up_stocks': limit_up_stocks,
            'limit_down_stocks': limit_down_stocks,
            'strong_rising': strong_rising,
            'strong_falling': strong_falling,
            'rising_ratio': round(rising_stocks / total_stocks * 100, 2),
            'advance_decline_ratio': round(rising_stocks / falling_stocks, 2) if falling_stocks > 0 else rising_stocks
        }

    def get_breadth_trend(self, days: int = 5) -> pd.DataFrame:
        """
        Get breadth trend over past days

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with breadth history
        """
        try:
            # Get historical market data
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

            # For now, generate mock historical data
            # In production, this would query historical breadth data
            data = []
            for i, date in enumerate(dates):
                np.random.seed(i)
                breadth = self._generate_mock_breadth_data()
                data.append({
                    'date': date,
                    'breadth_score': self._calculate_advance_decline_score(breadth),
                    'rising_ratio': breadth['rising_ratio'],
                    'limit_up': breadth['limit_up_stocks'],
                    'limit_down': breadth['limit_down_stocks']
                })

            return pd.DataFrame(data)

        except Exception as e:
            print(f"Failed to get breadth trend: {e}")
            return pd.DataFrame()


# Test code
if __name__ == "__main__":
    analyzer = MarketBreadthAnalyzer()

    print("=== Market Breadth Analysis ===")
    result = analyzer.calculate_breadth_score()

    print(f"Breadth Score: {result['breadth_score']:.1f}")
    print(f"Advance/Decline Score: {result['advance_decline_score']:.1f}")
    print(f"Limit Up/Down Score: {result['limit_up_down_score']:.1f}")
    print(f"Breadth Ratio Score: {result['breadth_ratio_score']:.1f}")
    print(f"\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")
