"""
Volatility Analysis Module
Analyzes market volatility: historical volatility, volatility percentile, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


class VolatilityAnalyzer:
    """Volatility analyzer"""

    def __init__(self, data_fetcher=None):
        """
        Initialize volatility analyzer

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.data_fetcher = data_fetcher
        if self.data_fetcher is None:
            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def calculate_volatility_score(self, index_code: str = '000001', period: int = 20) -> Dict:
        """
        Calculate volatility score (0-100)

        Args:
            index_code: Market index code
            period: Lookback period in days

        Returns:
            Dictionary with volatility metrics and score
        """
        try:
            # Get volatility data
            vol_data = self._get_volatility_data(index_code, period)

            # Calculate component scores
            hist_vol_score = self._calculate_hist_vol_score(vol_data)
            vol_percentile_score = self._calculate_vol_percentile_score(vol_data)
            vol_state_score = self._calculate_vol_state_score(vol_data)

            # Comprehensive volatility score
            vol_score = (
                hist_vol_score * 0.35 +
                vol_percentile_score * 0.40 +
                vol_state_score * 0.25
            )

            return {
                'timestamp': datetime.now().isoformat(),
                'volatility_score': round(vol_score, 2),
                'hist_vol_score': round(hist_vol_score, 2),
                'vol_percentile_score': round(vol_percentile_score, 2),
                'vol_state_score': round(vol_state_score, 2),
                'metrics': vol_data
            }

        except Exception as e:
            print(f"Failed to calculate volatility score: {e}")
            # Return default values on error
            return {
                'timestamp': datetime.now().isoformat(),
                'volatility_score': 50.0,
                'hist_vol_score': 50.0,
                'vol_percentile_score': 50.0,
                'vol_state_score': 50.0,
                'metrics': {}
            }

    def _get_volatility_data(self, index_code: str, period: int) -> Dict:
        """
        Get volatility data

        Args:
            index_code: Index code
            period: Lookback period

        Returns:
            Dictionary with volatility metrics
        """
        try:
            # Get historical index data
            index_data = self.data_fetcher.get_index_data(index_code, period=period * 2)

            if index_data is None or index_data.empty:
                return self._generate_mock_volatility_data()

            # Calculate daily returns
            index_data = index_data.sort_values('date').reset_index(drop=True)
            index_data['return'] = index_data['close'].pct_change() * 100

            # Use last 'period' days
            recent_data = index_data.tail(period).copy()

            # Calculate historical volatility (annualized)
            hist_vol = recent_data['return'].std() * np.sqrt(252)  # Annualized

            # Calculate volatility percentile (compared to past 252 days)
            all_data = index_data.tail(252).copy() if len(index_data) >= 252 else index_data
            rolling_vol = all_data['return'].rolling(window=period).std() * np.sqrt(252)

            if not rolling_vol.empty:
                vol_percentile = (rolling_vol < hist_vol).sum() / len(rolling_vol) * 100
            else:
                vol_percentile = 50

            # Determine volatility state
            current_vol = hist_vol
            long_term_vol = all_data['return'].std() * np.sqrt(252)

            if current_vol > long_term_vol * 1.5:
                vol_state = 'extreme'  # 极端波动
            elif current_vol > long_term_vol * 1.2:
                vol_state = 'high'  # 高波动
            elif current_vol > long_term_vol * 0.8:
                vol_state = 'normal'  # 正常波动
            else:
                vol_state = 'low'  # 低波动

            # ATR (Average True Range)
            if len(recent_data) >= 14:
                recent_data['high_low'] = recent_data['high'] - recent_data['low']
                recent_data['high_close'] = abs(recent_data['high'] - recent_data['close'].shift(1))
                recent_data['low_close'] = abs(recent_data['low'] - recent_data['close'].shift(1))
                recent_data['tr'] = recent_data[['high_low', 'high_close', 'low_close']].max(axis=1)
                atr = recent_data['tr'].tail(14).mean()
                atr_pct = atr / recent_data['close'].iloc[-1] * 100
            else:
                atr = 0
                atr_pct = 0

            return {
                'historical_volatility': round(hist_vol, 2),  # Annualized %
                'volatility_percentile': round(vol_percentile, 2),  # 0-100
                'volatility_state': vol_state,  # extreme/high/normal/low
                'atr': round(atr, 2),
                'atr_pct': round(atr_pct, 2),
                'current_vol': round(current_vol, 2),
                'long_term_vol': round(long_term_vol, 2)
            }

        except Exception as e:
            print(f"Failed to get volatility data: {e}")
            return self._generate_mock_volatility_data()

    def _calculate_hist_vol_score(self, vol_data: Dict) -> float:
        """
        Calculate historical volatility score

        Lower volatility = higher score (market is stable)
        Very high volatility = panic = lower score
        """
        hist_vol = vol_data.get('historical_volatility', 20)

        # Typical A-share volatility: 15-25%
        if hist_vol <= 15:
            return 90.0  # Very stable
        elif hist_vol <= 20:
            return 75.0  # Normal stable
        elif hist_vol <= 25:
            return 60.0  # Normal
        elif hist_vol <= 35:
            return 40.0  # Elevated
        else:
            return 20.0  # Extreme volatility

    def _calculate_vol_percentile_score(self, vol_data: Dict) -> float:
        """
        Calculate volatility percentile score

        Moderate volatility (40-60 percentile) = highest score
        Very low or very high = lower score
        """
        percentile = vol_data.get('volatility_percentile', 50)

        # Ideal range: 30-70 percentile
        if 30 <= percentile <= 70:
            # Map 30-70 to 80-100
            return 80 + (1 - abs(percentile - 50) / 20) * 20
        elif percentile < 30:
            # Very low volatility - might be complacency
            return percentile * 2  # 0-60
        else:
            # Very high volatility - panic
            return 100 - percentile  # 0-30

    def _calculate_vol_state_score(self, vol_data: Dict) -> float:
        """
        Calculate volatility state score
        """
        state = vol_data.get('volatility_state', 'normal')

        state_scores = {
            'low': 60.0,      # Low volatility - some complacency
            'normal': 80.0,   # Normal - ideal
            'high': 50.0,     # High - some concern
            'extreme': 20.0   # Extreme - panic
        }

        return state_scores.get(state, 50.0)

    def _generate_mock_volatility_data(self) -> Dict:
        """Generate mock volatility data for testing"""
        np.random.seed(int(datetime.now().timestamp()))

        hist_vol = np.random.uniform(15, 35)  # 15-35%
        percentile = np.random.uniform(20, 80)  # 20-80 percentile

        # Determine state based on vol
        if hist_vol > 30:
            state = 'extreme'
        elif hist_vol > 25:
            state = 'high'
        elif hist_vol > 18:
            state = 'normal'
        else:
            state = 'low'

        atr_pct = hist_vol / np.sqrt(252) * 2  # Approximate ATR as daily vol * 2

        return {
            'historical_volatility': round(hist_vol, 2),
            'volatility_percentile': round(percentile, 2),
            'volatility_state': state,
            'atr': round(atr_pct * 3000 / 100, 2),  # Mock ATR value
            'atr_pct': round(atr_pct, 2),
            'current_vol': round(hist_vol, 2),
            'long_term_vol': round(22.0, 2)
        }

    def get_volatility_trend(self, index_code: str = '000001', days: int = 20) -> pd.DataFrame:
        """
        Get volatility trend over past days

        Args:
            index_code: Index code
            days: Number of days to look back

        Returns:
            DataFrame with volatility history
        """
        try:
            index_data = self.data_fetcher.get_index_data(index_code, period=days)

            if index_data is None or index_data.empty:
                return pd.DataFrame()

            index_data = index_data.sort_values('date').reset_index(drop=True)
            index_data['return'] = index_data['close'].pct_change() * 100

            # Calculate rolling volatility
            index_data['volatility'] = index_data['return'].rolling(window=5).std() * np.sqrt(252)

            return index_data[['date', 'volatility']].dropna()

        except Exception as e:
            print(f"Failed to get volatility trend: {e}")
            return pd.DataFrame()


# Test code
if __name__ == "__main__":
    analyzer = VolatilityAnalyzer()

    print("=== Volatility Analysis ===")
    result = analyzer.calculate_volatility_score()

    print(f"Volatility Score: {result['volatility_score']:.1f}")
    print(f"Historical Vol Score: {result['hist_vol_score']:.1f}")
    print(f"Percentile Score: {result['vol_percentile_score']:.1f}")
    print(f"State Score: {result['vol_state_score']:.1f}")
    print(f"\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")
