"""
Comprehensive Sentiment Scorer Module
Combines market breadth, money flow, and volatility into overall sentiment score
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from sentiment.market_breadth import MarketBreadthAnalyzer
from sentiment.money_flow import MoneyFlowAnalyzer
from sentiment.volatility import VolatilityAnalyzer
from sentiment.sector_sentiment import SectorSentimentAnalyzer
from config.settings import settings


@dataclass
class SentimentScore:
    """Sentiment score data structure"""
    sentiment_score: float  # Overall sentiment score (0-100)
    market_state: str  # extreme_greed/greed/neutral/fear/extreme_fear
    breadth_score: float
    money_flow_score: float
    volatility_score: float
    timestamp: str
    details: Dict


class SentimentScorer:
    """Comprehensive sentiment scorer"""

    def __init__(self, data_fetcher=None):
        """
        Initialize sentiment scorer

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.data_fetcher = data_fetcher
        if self.data_fetcher is None:
            from data.market_data import MarketDataFetcher
            self.data_fetcher = MarketDataFetcher()

        # Initialize sub-analyzers
        self.breadth_analyzer = MarketBreadthAnalyzer(data_fetcher)
        self.flow_analyzer = MoneyFlowAnalyzer(data_fetcher)
        self.volatility_analyzer = VolatilityAnalyzer(data_fetcher)
        self.sector_analyzer = SectorSentimentAnalyzer(data_fetcher)

    def calculate_overall_sentiment(self, index_code: str = '000001') -> SentimentScore:
        """
        Calculate comprehensive market sentiment score

        Formula:
        Overall Score = Breadth Score × 35% + Money Flow × 40% + Volatility × 25%

        Args:
            index_code: Market index code

        Returns:
            SentimentScore object with comprehensive sentiment data
        """
        try:
            # Get component scores
            breadth_result = self.breadth_analyzer.calculate_breadth_score(index_code)
            flow_result = self.flow_analyzer.calculate_money_flow_score(index_code)
            volatility_result = self.volatility_analyzer.calculate_volatility_score(index_code)

            # Extract scores
            breadth_score = breadth_result['breadth_score']
            flow_score = flow_result['flow_score']
            vol_score = volatility_result['volatility_score']

            # Calculate overall score using configured weights
            overall_score = (
                breadth_score * settings.SENTIMENT_WEIGHT_MARKET_BREADTH +
                flow_score * settings.SENTIMENT_WEIGHT_MONEY_FLOW +
                vol_score * settings.SENTIMENT_WEIGHT_VOLATILITY
            )

            # Determine market state
            market_state = self._determine_market_state(overall_score)

            return SentimentScore(
                sentiment_score=round(overall_score, 2),
                market_state=market_state,
                breadth_score=round(breadth_score, 2),
                money_flow_score=round(flow_score, 2),
                volatility_score=round(vol_score, 2),
                timestamp=datetime.now().isoformat(),
                details={
                    'breadth': breadth_result,
                    'money_flow': flow_result,
                    'volatility': volatility_result
                }
            )

        except Exception as e:
            print(f"Failed to calculate overall sentiment: {e}")
            # Return default values on error
            return SentimentScore(
                sentiment_score=50.0,
                market_state='neutral',
                breadth_score=50.0,
                money_flow_score=50.0,
                volatility_score=50.0,
                timestamp=datetime.now().isoformat(),
                details={}
            )

    def _determine_market_state(self, score: float) -> str:
        """
        Determine market state based on sentiment score

        Args:
            score: Sentiment score (0-100)

        Returns:
            Market state string
        """
        if score >= settings.MARKET_EXTREME_GREED:
            return 'extreme_greed'  # 极度贪婪
        elif score >= settings.MARKET_GREED:
            return 'greed'  # 贪婪
        elif score >= settings.MARKET_NEUTRAL:
            return 'neutral'  # 中性
        elif score >= settings.MARKET_FEAR:
            return 'fear'  # 恐慌
        else:
            return 'extreme_fear'  # 极度恐慌

    def get_market_state_display(self, state: str) -> Dict:
        """
        Get display information for market state

        Args:
            state: Market state string

        Returns:
            Dictionary with display info
        """
        state_info = {
            'extreme_greed': {
                'name': '极度贪婪',
                'emoji': '🤑',
                'color': 'red',
                'description': '市场过热，风险极高，建议谨慎',
                'action': '减仓或空仓'
            },
            'greed': {
                'name': '贪婪',
                'emoji': '😊',
                'color': 'orange',
                'description': '市场情绪积极，可适当参与',
                'action': '控制仓位'
            },
            'neutral': {
                'name': '中性',
                'emoji': '😐',
                'color': 'yellow',
                'description': '市场情绪平稳，观望为主',
                'action': '观望或小仓位'
            },
            'fear': {
                'name': '恐慌',
                'emoji': '😨',
                'color': 'lightgreen',
                'description': '市场情绪低迷，等待机会',
                'action': '等待机会'
            },
            'extreme_fear': {
                'name': '极度恐慌',
                'emoji': '😱',
                'color': 'green',
                'description': '市场极度恐慌，可能存在机会',
                'action': '寻找反弹机会'
            }
        }

        return state_info.get(state, state_info['neutral'])

    def get_full_sentiment_report(self, index_code: str = '000001') -> Dict:
        """
        Get comprehensive sentiment report including all components

        Args:
            index_code: Market index code

        Returns:
            Dictionary with full sentiment report
        """
        sentiment = self.calculate_overall_sentiment(index_code)
        state_display = self.get_market_state_display(sentiment.market_state)

        # Get sector sentiment
        sector_df = self.sector_analyzer.get_all_sectors_sentiment()

        return {
            'overall': {
                'score': sentiment.sentiment_score,
                'state': sentiment.market_state,
                'state_display': state_display,
                'timestamp': sentiment.timestamp
            },
            'components': {
                'breadth': {
                    'score': sentiment.breadth_score,
                    'weight': settings.SENTIMENT_WEIGHT_MARKET_BREADTH,
                    'contribution': round(sentiment.breadth_score * settings.SENTIMENT_WEIGHT_MARKET_BREADTH, 2)
                },
                'money_flow': {
                    'score': sentiment.money_flow_score,
                    'weight': settings.SENTIMENT_WEIGHT_MONEY_FLOW,
                    'contribution': round(sentiment.money_flow_score * settings.SENTIMENT_WEIGHT_MONEY_FLOW, 2)
                },
                'volatility': {
                    'score': sentiment.volatility_score,
                    'weight': settings.SENTIMENT_WEIGHT_VOLATILITY,
                    'contribution': round(sentiment.volatility_score * settings.SENTIMENT_WEIGHT_VOLATILITY, 2)
                }
            },
            'sectors': {
                'hot': self.sector_analyzer.get_hot_sectors(top_n=5),
                'rotation': self.sector_analyzer.detect_sector_rotation(),
                'all': sector_df.to_dict('records') if not sector_df.empty else []
            },
            'details': sentiment.details
        }

    def format_sentiment_report(self, report: Dict) -> str:
        """
        Format sentiment report as text

        Args:
            report: Sentiment report dictionary

        Returns:
            Formatted text report
        """
        overall = report['overall']
        state = overall['state_display']

        lines = [
            "=" * 60,
            f"市场情绪分析报告 - {overall['timestamp']}",
            "=" * 60,
            "",
            f"【总体情绪】{state['emoji']} {state['name']}",
            f"  综合得分: {overall['score']:.1f} / 100",
            f"  市场状态: {state['description']}",
            f"  操作建议: {state['action']}",
            "",
            "【情绪构成】",
        ]

        components = report['components']
        for comp_name, comp_data in components.items():
            comp_names_cn = {
                'breadth': '市场宽度',
                'money_flow': '资金流向',
                'volatility': '波动率'
            }
            lines.append(
                f"  {comp_names_cn[comp_name]}: {comp_data['score']:.1f}分 "
                f"(权重{comp_data['weight']*100:.0f}%, 贡献{comp_data['contribution']:.1f}分)"
            )

        lines.extend([
            "",
            "【热门板块】"
        ])

        hot_sectors = report['sectors']['hot']
        for i, sector in enumerate(hot_sectors, 1):
            lines.append(f"  {i}. {sector['name']}: {sector['score']:.1f}分 ({sector['change_pct']:+.1f}%)")

        rotation = report['sectors']['rotation']
        if rotation:
            lines.extend([
                "",
                "【板块轮动】"
            ])
            for rot in rotation:
                sectors_str = ', '.join(rot['sectors'][:3])
                lines.append(f"  {rot['description']}: {sectors_str}")

        lines.append("=" * 60)

        return "\n".join(lines)


# Test code
if __name__ == "__main__":
    scorer = SentimentScorer()

    print("=== Comprehensive Sentiment Analysis ===\n")

    # Calculate overall sentiment
    sentiment = scorer.calculate_overall_sentiment()

    print(f"Overall Sentiment Score: {sentiment.sentiment_score:.1f}")
    print(f"Market State: {sentiment.market_state}")
    print(f"Breadth Score: {sentiment.breadth_score:.1f}")
    print(f"Money Flow Score: {sentiment.money_flow_score:.1f}")
    print(f"Volatility Score: {sentiment.volatility_score:.1f}")

    print("\n" + "=" * 60)
    print("Full Report:")
    print("=" * 60 + "\n")

    report = scorer.get_full_sentiment_report()
    print(scorer.format_sentiment_report(report))
