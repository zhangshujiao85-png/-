"""
Stock Selector Module
Selects representative stocks from sectors based on sentiment and fundamental factors
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import settings


class StockSelector:
    """Stock selector for sector representatives"""

    def __init__(self, data_fetcher=None):
        """
        Initialize stock selector

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.data_fetcher = data_fetcher
        if self.data_fetcher is None:
            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

    def select_representative_stocks(self, sector_name: str, top_n: int = 5) -> List[Dict]:
        """
        Select top N representative stocks from a sector

        Scoring formula:
        Score = Sentiment × 0.30 + Money Flow × 0.30 + Market Cap × 0.20 + Activity × 0.20

        Args:
            sector_name: Sector name
            top_n: Number of top stocks to return

        Returns:
            List of selected stocks with details
        """
        try:
            # Get sector constituents
            constituents = self.data_fetcher.get_sector_constituents(sector_name)

            if constituents.empty:
                return []

            # Calculate scores for each stock
            scored_stocks = []

            for _, stock in constituents.iterrows():
                try:
                    score_data = self._calculate_stock_score(stock, constituents)
                    scored_stocks.append(score_data)
                except Exception as e:
                    print(f"Failed to score {stock.get('code', 'N/A')}: {e}")
                    continue

            # Sort by score
            scored_stocks.sort(key=lambda x: x['score'], reverse=True)

            # Return top N
            return scored_stocks[:top_n]

        except Exception as e:
            print(f"Failed to select stocks for {sector_name}: {e}")
            return []

    def _calculate_stock_score(self, stock: pd.Series, all_stocks: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive score for a stock

        Args:
            stock: Stock data series
            all_stocks: All stocks in sector (for relative comparison)

        Returns:
            Dictionary with stock info and score
        """
        code = stock.get('code', '')
        name = stock.get('name', '')
        price = stock.get('price', 0)
        change_pct = stock.get('change_pct', 0)
        volume = stock.get('volume', 0)
        amount = stock.get('amount', 0)
        turnover = stock.get('turnover', 0)
        market_cap = stock.get('market_cap', 0)

        # 1. Sentiment score (based on price change)
        sentiment_score = self._calculate_sentiment_score(change_pct)

        # 2. Money flow score (based on turnover and volume)
        flow_score = self._calculate_money_flow_score(turnover, amount)

        # 3. Market cap score (prefer large caps for stability)
        cap_score = self._calculate_cap_score(market_cap, all_stocks)

        # 4. Activity score (based on turnover rate)
        activity_score = self._calculate_activity_score(turnover)

        # Comprehensive score
        total_score = (
            sentiment_score * settings.SELECTION_WEIGHT_SENTIMENT +
            flow_score * settings.SELECTION_WEIGHT_MONEY_FLOW +
            cap_score * settings.SELECTION_WEIGHT_MARKET_CAP +
            activity_score * settings.SELECTION_WEIGHT_ACTIVITY
        )

        # Determine stock type
        stock_type = self._classify_stock_type(market_cap, turnover)

        return {
            'code': code,
            'name': name,
            'price': price,
            'change_pct': change_pct,
            'score': round(total_score, 2),
            'sentiment_score': round(sentiment_score, 2),
            'flow_score': round(flow_score, 2),
            'cap_score': round(cap_score, 2),
            'activity_score': round(activity_score, 2),
            'market_cap': market_cap / 100000000 if market_cap > 0 else 0,  # Convert to 亿元
            'turnover': turnover,
            'type': stock_type
        }

    def _calculate_sentiment_score(self, change_pct: float) -> float:
        """
        Calculate sentiment score based on price change

        Args:
            change_pct: Price change percentage

        Returns:
            Sentiment score (0-100)
        """
        if change_pct >= 5:
            return 100.0
        elif change_pct >= 3:
            return 85.0
        elif change_pct >= 1:
            return 70.0
        elif change_pct >= 0:
            return 55.0
        elif change_pct >= -1:
            return 45.0
        elif change_pct >= -3:
            return 30.0
        else:
            return 15.0

    def _calculate_money_flow_score(self, turnover: float, amount: float) -> float:
        """
        Calculate money flow score based on turnover and amount

        Args:
            turnover: Turnover rate
            amount: Trading amount

        Returns:
            Money flow score (0-100)
        """
        # High turnover with positive price change = strong inflow
        # This is a simplified version - actual implementation would analyze
        # the relationship between price change and turnover

        if turnover >= 10:
            return 100.0
        elif turnover >= 5:
            return 80.0
        elif turnover >= 3:
            return 65.0
        elif turnover >= 1:
            return 50.0
        elif turnover >= 0.5:
            return 35.0
        else:
            return 20.0

    def _calculate_cap_score(self, market_cap: float, all_stocks: pd.DataFrame) -> float:
        """
        Calculate market cap score

        Args:
            market_cap: Market capitalization
            all_stocks: All stocks in sector

        Returns:
            Market cap score (0-100)
        """
        if market_cap <= 0:
            return 50.0

        # Calculate cap percentile within sector
        all_caps = all_stocks['market_cap'].values
        percentile = (all_caps < market_cap).sum() / len(all_caps) * 100

        # Higher cap = higher score (prefer large caps)
        return percentile

    def _calculate_activity_score(self, turnover: float) -> float:
        """
        Calculate activity score based on turnover rate

        Args:
            turnover: Turnover rate

        Returns:
            Activity score (0-100)
        """
        # Prefer stocks with moderate to high activity
        if turnover >= 8:
            return 90.0  # Very active
        elif turnover >= 5:
            return 100.0  # Ideal activity
        elif turnover >= 3:
            return 85.0
        elif turnover >= 1:
            return 70.0
        elif turnover >= 0.5:
            return 50.0
        else:
            return 30.0  # Low activity

    def _classify_stock_type(self, market_cap: float, turnover: float) -> str:
        """
        Classify stock type

        Args:
            market_cap: Market capitalization (in yuan)
            turnover: Turnover rate

        Returns:
            Stock type: stable/sensitive/active
        """
        cap_yi = market_cap / 100000000  # Convert to 亿元

        if cap_yi >= settings.STABLE_CAP_THRESHOLD:
            # Large cap
            if turnover >= 3:
                return '敏感型'  # Sensitive (large cap but high activity)
            else:
                return '稳定型'  # Stable (large cap, low activity)
        elif cap_yi >= settings.ACTIVE_CAP_THRESHOLD:
            # Mid cap
            if turnover >= 5:
                return '活跃型'  # Active
            else:
                return '敏感型'
        else:
            # Small cap
            return '活跃型'  # Most small caps are active

    def filter_stocks_by_criteria(self, stocks: List[Dict],
                                   min_score: float = 60,
                                   max_stocks: int = 10) -> List[Dict]:
        """
        Filter stocks by criteria

        Args:
            stocks: List of scored stocks
            min_score: Minimum score threshold
            max_stocks: Maximum number of stocks to return

        Returns:
            Filtered list of stocks
        """
        # Filter by score
        filtered = [s for s in stocks if s['score'] >= min_score]

        # Sort by score
        filtered.sort(key=lambda x: x['score'], reverse=True)

        # Limit number
        return filtered[:max_stocks]

    def get_stock_summary(self, stocks: List[Dict]) -> str:
        """
        Generate summary text for selected stocks

        Args:
            stocks: List of selected stocks

        Returns:
            Summary text
        """
        if not stocks:
            return "未找到符合条件的股票"

        lines = [f"共 {len(stocks)} 只股票:\n"]

        for i, stock in enumerate(stocks, 1):
            lines.append(
                f"{i}. {stock['code']} {stock['name']} ({stock['score']:.0f}分) - {stock['type']}\n"
                f"   价格: {stock['price']:.2f} ({stock['change_pct']:+.2f}%) "
                f"市值: {stock['market_cap']:.1f}亿 换手: {stock['turnover']:.2f}%"
            )

        return "\n".join(lines)

    def batch_select_stocks(self, sectors: List[str], top_n: int = 5) -> Dict[str, List[Dict]]:
        """
        Batch select stocks from multiple sectors

        Args:
            sectors: List of sector names
            top_n: Number of top stocks per sector

        Returns:
            Dictionary mapping sector names to selected stocks
        """
        results = {}

        for sector in sectors:
            try:
                stocks = self.select_representative_stocks(sector, top_n)
                if stocks:
                    results[sector] = stocks
            except Exception as e:
                print(f"Failed to select stocks for {sector}: {e}")

        return results


# Test code
if __name__ == "__main__":
    selector = StockSelector()

    print("=== Stock Selector Test ===\n")

    # Test selecting stocks from a sector
    print("Selecting top 5 stocks from '半导体' sector:\n")
    stocks = selector.select_representative_stocks('半导体', top_n=5)

    if stocks:
        print(selector.get_stock_summary(stocks))

        # Print scoring details
        print("\n=== Scoring Details ===\n")
        for stock in stocks:
            print(f"{stock['code']} {stock['name']}:")
            print(f"  总分: {stock['score']:.1f}")
            print(f"  情绪: {stock['sentiment_score']:.1f}, "
                  f"资金: {stock['flow_score']:.1f}, "
                  f"市值: {stock['cap_score']:.1f}, "
                  f"活跃: {stock['activity_score']:.1f}")
            print(f"  类型: {stock['type']}")
            print()
    else:
        print("No stocks found. Please check if the data fetcher is working correctly.")

    # Test batch selection
    print("\n=== Batch Selection ===\n")
    sectors = ['军工', '半导体', '新能源']
    batch_results = selector.batch_select_stocks(sectors, top_n=3)

    for sector, stocks in batch_results.items():
        print(f"\n{sector} - Top 3:")
        for stock in stocks:
            print(f"  {stock['code']} {stock['name']}: {stock['score']:.0f}分 ({stock['type']})")
