"""
Sector Sentiment Analysis Module
Analyzes sentiment for specific sectors/industries
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class SectorSentimentAnalyzer:
    """Sector sentiment analyzer"""

    def __init__(self, data_fetcher=None, use_cmes=True):
        """
        Initialize sector sentiment analyzer

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
                except Exception as e:
                    print(f"[板块情绪] CMES初始化失败，使用传统数据源: {e}")
                    from data.market_data import MarketDataFetcher
                    self.data_fetcher = MarketDataFetcher()
        else:
            self.cmes_fetcher = None

        # Sector list
        self.sectors = [
            '军工', '半导体', '新能源', '医药', '消费', '银行',
            '地产', '煤炭', '石油', '黄金', 'AI', '软件',
            '传媒', '通信', '电力', '汽车', '化工'
        ]

    def calculate_sector_sentiment(self, sector_name: str) -> Dict:
        """
        Calculate sentiment score for a specific sector

        Args:
            sector_name: Sector/industry name

        Returns:
            Dictionary with sector sentiment metrics and score
        """
        try:
            # 优先使用CMES数据源
            if self.use_cmes and hasattr(self, 'cmes_fetcher'):
                sector_data = self.cmes_fetcher.get_sector_data(sector_name)
                constituents = self.cmes_fetcher.get_sector_constituents(sector_name)
            else:
                # 降级到传统数据源
                sector_data = self.data_fetcher.get_sector_data(sector_name)
                constituents = self.data_fetcher.get_sector_constituents(sector_name)

            if constituents.empty:
                return self._generate_mock_sector_sentiment(sector_name)

            # Calculate component scores
            price_score = self._calculate_price_momentum_score(constituents)
            breadth_score = self._calculate_sector_breadth_score(constituents)
            volume_score = self._calculate_volume_score(constituents)
            strength_score = self._calculate_strength_score(sector_data)

            # Comprehensive sector sentiment score
            sentiment_score = (
                price_score * 0.30 +
                breadth_score * 0.30 +
                volume_score * 0.20 +
                strength_score * 0.20
            )

            return {
                'sector': sector_name,
                'timestamp': datetime.now().isoformat(),
                'sentiment_score': round(sentiment_score, 2),
                'price_score': round(price_score, 2),
                'breadth_score': round(breadth_score, 2),
                'volume_score': round(volume_score, 2),
                'strength_score': round(strength_score, 2),
                'metrics': {
                    'change_pct': sector_data.get('change_pct', 0),
                    'total_stocks': len(constituents),
                    'rising_stocks': len(constituents[constituents['change_pct'] > 0]),
                    'avg_change': round(constituents['change_pct'].mean(), 2),
                    'total_volume': constituents['volume'].sum() if 'volume' in constituents.columns else 0
                }
            }

        except Exception as e:
            print(f"Failed to calculate sector sentiment: {e}")
            return self._generate_mock_sector_sentiment(sector_name)

    def _calculate_price_momentum_score(self, constituents: pd.DataFrame) -> float:
        """
        Calculate price momentum score

        Based on average change percentage
        """
        if 'change_pct' not in constituents.columns:
            return 50.0

        avg_change = constituents['change_pct'].mean()

        # Map average change to 0-100 score
        if avg_change >= 5:
            return 100.0
        elif avg_change >= 3:
            return 85.0
        elif avg_change >= 1:
            return 70.0
        elif avg_change >= 0:
            return 55.0
        elif avg_change >= -1:
            return 40.0
        elif avg_change >= -3:
            return 25.0
        else:
            return 10.0

    def _calculate_sector_breadth_score(self, constituents: pd.DataFrame) -> float:
        """
        Calculate sector breadth score

        Based on ratio of rising to falling stocks
        """
        if 'change_pct' not in constituents.columns:
            return 50.0

        total = len(constituents)
        rising = len(constituents[constituents['change_pct'] > 0])
        falling = len(constituents[constituents['change_pct'] < 0])

        if total == 0:
            return 50.0

        rising_ratio = rising / total

        # Map rising ratio to 0-100
        if rising_ratio >= 0.8:
            return 100.0
        elif rising_ratio >= 0.6:
            return 80.0
        elif rising_ratio >= 0.5:
            return 65.0
        elif rising_ratio >= 0.4:
            return 50.0
        elif rising_ratio >= 0.2:
            return 30.0
        else:
            return 10.0

    def _calculate_volume_score(self, constituents: pd.DataFrame) -> float:
        """
        Calculate volume score

        Based on trading activity
        """
        if 'turnover' not in constituents.columns or 'volume' not in constituents.columns:
            return 50.0

        # Calculate average turnover
        avg_turnover = constituents['turnover'].mean()

        # Typical turnover: 2-5%
        if avg_turnover >= 8:
            return 100.0  # Very active
        elif avg_turnover >= 5:
            return 85.0
        elif avg_turnover >= 3:
            return 70.0
        elif avg_turnover >= 1:
            return 55.0
        else:
            return 40.0  # Low activity

    def _calculate_strength_score(self, sector_data: Dict) -> float:
        """
        Calculate sector strength score

        Based on sector performance
        """
        change_pct = sector_data.get('change_pct', 0)

        # Map change to 0-100 score
        if change_pct >= 3:
            return 100.0
        elif change_pct >= 2:
            return 90.0
        elif change_pct >= 1:
            return 75.0
        elif change_pct >= 0:
            return 60.0
        elif change_pct >= -1:
            return 45.0
        elif change_pct >= -2:
            return 30.0
        else:
            return 15.0

    def get_all_sectors_sentiment(self) -> pd.DataFrame:
        """
        Get sentiment scores for all sectors

        Returns:
            DataFrame with all sectors sorted by sentiment score
        """
        results = []

        for sector in self.sectors:
            try:
                sentiment = self.calculate_sector_sentiment(sector)
                results.append({
                    'sector': sector,
                    'sentiment_score': sentiment['sentiment_score'],
                    'price_score': sentiment['price_score'],
                    'breadth_score': sentiment['breadth_score'],
                    'volume_score': sentiment['volume_score'],
                    'strength_score': sentiment['strength_score'],
                    'change_pct': sentiment['metrics'].get('change_pct', 0),
                    'rising_ratio': sentiment['metrics'].get('rising_stocks', 0) / max(sentiment['metrics'].get('total_stocks', 1), 1)
                })
            except Exception as e:
                print(f"Failed to analyze {sector}: {e}")

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('sentiment_score', ascending=False).reset_index(drop=True)

        return df

    def get_hot_sectors(self, top_n: int = 5) -> List[Dict]:
        """
        Get top N hot sectors

        Args:
            top_n: Number of top sectors to return

        Returns:
            List of top sectors with details
        """
        df = self.get_all_sectors_sentiment()

        if df.empty:
            return []

        result = []
        for _, row in df.head(top_n).iterrows():
            result.append({
                'name': row['sector'],
                'score': round(row['sentiment_score'], 1),
                'change_pct': round(row['change_pct'], 2),
                'rising_ratio': round(row['rising_ratio'] * 100, 1)
            })

        return result

    def detect_sector_rotation(self, threshold: float = 15.0) -> List[Dict]:
        """
        Detect sector rotation (sudden sentiment changes)

        Args:
            threshold: Minimum score change to consider as rotation

        Returns:
            List of rotating sectors
        """
        # This would require historical sentiment data
        # For now, return sectors with high sentiment scores
        df = self.get_all_sectors_sentiment()

        if df.empty:
            return []

        # Find sectors with very high scores (potential rotation in)
        rotating_in = df[df['sentiment_score'] >= 70]['sector'].tolist()

        # Find sectors with very low scores (potential rotation out)
        rotating_out = df[df['sentiment_score'] <= 30]['sector'].tolist()

        result = []

        if rotating_in:
            result.append({
                'type': 'rotation_in',
                'sectors': rotating_in[:3],
                'description': '资金流入，情绪升温'
            })

        if rotating_out:
            result.append({
                'type': 'rotation_out',
                'sectors': rotating_out[:3],
                'description': '资金流出，情绪降温'
            })

        return result

    def _generate_mock_sector_sentiment(self, sector_name: str) -> Dict:
        """Generate mock sector sentiment for testing"""
        np.random.seed(hash(sector_name) % 2**32)

        base_score = np.random.uniform(30, 80)

        return {
            'sector': sector_name,
            'timestamp': datetime.now().isoformat(),
            'sentiment_score': round(base_score, 2),
            'price_score': round(base_score + np.random.uniform(-10, 10), 2),
            'breadth_score': round(base_score + np.random.uniform(-10, 10), 2),
            'volume_score': round(base_score + np.random.uniform(-10, 10), 2),
            'strength_score': round(base_score + np.random.uniform(-10, 10), 2),
            'metrics': {
                'change_pct': round(np.random.uniform(-5, 5), 2),
                'total_stocks': np.random.randint(20, 100),
                'rising_stocks': np.random.randint(5, 50),
                'avg_change': round(np.random.uniform(-3, 3), 2),
                'total_volume': np.random.randint(1000000, 50000000)
            }
        }


# Test code
if __name__ == "__main__":
    analyzer = SectorSentimentAnalyzer()

    # Test single sector
    print("=== Sector Sentiment Analysis ===")
    result = analyzer.calculate_sector_sentiment('军工')
    print(f"Sector: {result['sector']}")
    print(f"Sentiment Score: {result['sentiment_score']:.1f}")
    print(f"Metrics: {result['metrics']}")

    # Test all sectors
    print("\n=== All Sectors Sentiment ===")
    all_sectors = analyzer.get_all_sectors_sentiment()
    print(all_sectors.head(10))

    # Test hot sectors
    print("\n=== Hot Sectors ===")
    hot = analyzer.get_hot_sectors(top_n=3)
    for sector in hot:
        print(f"{sector['name']}: {sector['score']:.1f}分 ({sector['change_pct']:+.1f}%)")
