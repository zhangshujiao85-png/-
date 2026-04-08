"""
Event Analyzer Module
Analyzes market events and their impact on sectors
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from news.news_fetcher import NewsFetcher
from news.sector_mapper import SectorMapper
from sentiment.sector_sentiment import SectorSentimentAnalyzer


@dataclass
class EventAnalysis:
    """Event analysis result"""
    event_keyword: str
    event_type: str
    sentiment: str  # positive/negative/neutral
    affected_sectors: Dict[str, str]  # sector -> sentiment
    news_count: int
    latest_news: List[Dict]
    current_sentiment_scores: Dict[str, float]
    timestamp: str
    recommendation: str


class EventAnalyzer:
    """Event analyzer"""

    def __init__(self, data_fetcher=None):
        """
        Initialize event analyzer

        Args:
            data_fetcher: Market data fetcher instance
        """
        self.news_fetcher = NewsFetcher()
        self.sector_mapper = SectorMapper()
        self.sector_analyzer = SectorSentimentAnalyzer(data_fetcher)

    def analyze_event(self, event_keyword: str, days: int = 7) -> EventAnalysis:
        """
        Analyze a market event

        Args:
            event_keyword: Event keyword (e.g., '美以冲突', '降息')
            days: Number of days to look back for news

        Returns:
            EventAnalysis object
        """
        # Get affected sectors
        affected_sectors = self.sector_mapper.get_affected_sectors(event_keyword)
        event_type = self.sector_mapper.get_event_type(event_keyword)

        # Fetch related news
        news_list = self.news_fetcher.search_news(event_keyword, days=days, max_results=20)

        # Get current sentiment scores for affected sectors
        current_sentiment = {}
        for sector in affected_sectors.keys():
            try:
                sentiment = self.sector_analyzer.calculate_sector_sentiment(sector)
                current_sentiment[sector] = sentiment['sentiment_score']
            except Exception as e:
                print(f"Failed to get sentiment for {sector}: {e}")
                current_sentiment[sector] = 50.0

        # Determine overall sentiment
        overall_sentiment = self._determine_overall_sentiment(affected_sectors, current_sentiment)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            event_keyword, event_type, affected_sectors, current_sentiment, len(news_list)
        )

        return EventAnalysis(
            event_keyword=event_keyword,
            event_type=event_type,
            sentiment=overall_sentiment,
            affected_sectors=affected_sectors,
            news_count=len(news_list),
            latest_news=news_list[:5],  # Keep top 5 news
            current_sentiment_scores=current_sentiment,
            timestamp=datetime.now().isoformat(),
            recommendation=recommendation
        )

    def _determine_overall_sentiment(self, affected_sectors: Dict[str, str],
                                     current_scores: Dict[str, float]) -> str:
        """
        Determine overall event sentiment

        Args:
            affected_sectors: Affected sectors and their sentiment
            current_scores: Current sentiment scores

        Returns:
            Overall sentiment (positive/negative/neutral)
        """
        if not affected_sectors:
            return 'neutral'

        # Count bullish and bearish sectors
        bullish_count = sum(1 for s in affected_sectors.values() if s == '利好')
        bearish_count = sum(1 for s in affected_sectors.values() if s == '利空')

        # Determine based on count
        if bullish_count > bearish_count * 1.5:
            return 'positive'
        elif bearish_count > bullish_count * 1.5:
            return 'negative'
        else:
            return 'neutral'

    def _generate_recommendation(self, event_keyword: str, event_type: str,
                                 affected_sectors: Dict[str, str],
                                 current_scores: Dict[str, float],
                                 news_count: int) -> str:
        """
        Generate trading recommendation

        Args:
            event_keyword: Event keyword
            event_type: Event type
            affected_sectors: Affected sectors
            current_scores: Current sentiment scores
            news_count: Number of related news

        Returns:
            Recommendation string
        """
        lines = []

        # Event heat assessment
        heat = self._assess_event_heat(news_count, event_type)
        lines.append(f"【事件热度】{heat}")

        # Affected sectors analysis
        bullish_sectors = [s for s, sentiment in affected_sectors.items() if sentiment == '利好']
        bearish_sectors = [s for s, sentiment in affected_sectors.items() if sentiment == '利空']

        if bullish_sectors:
            lines.append(f"\n利好板块: {', '.join(bullish_sectors[:5])}")
            high_sentiment_bullish = [s for s in bullish_sectors if current_scores.get(s, 50) > 60]
            if high_sentiment_bullish:
                lines.append(f"  → 当前情绪高涨({', '.join(high_sentiment_bullish[:3])}): 可关注")

        if bearish_sectors:
            lines.append(f"\n利空板块: {', '.join(bearish_sectors[:5])}")
            lines.append(f"  → 建议规避或做空")

        # Trading suggestion
        lines.append("\n【操作建议】")

        if event_type == '地缘':
            lines.append("地缘政治事件，建议:")
            lines.append("• 关注军工、黄金、石油等防御性板块")
            lines.append("• 避免受影响较大的航空、航运等板块")
            lines.append("• 控制仓位，等待局势明朗")

        elif event_type == '宏观':
            if '降息' in event_keyword or '降准' in event_keyword:
                lines.append("货币宽松信号，建议:")
                lines.append("• 关注券商、地产等受益板块")
                lines.append("• 可适当提高仓位")
            else:
                lines.append("宏观政策变化，建议:")
                lines.append("• 密切关注政策落地情况")
                lines.append("• 控制仓位，灵活应对")

        elif event_type == '行业':
            lines.append("行业事件，建议:")
            lines.append("• 重点关注相关龙头股")
            lines.append("• 注意事件持续性，避免追高")

        elif event_type == '监管':
            lines.append("监管事件，建议:")
            lines.append("• 严格遵守监管要求")
            lines.append("• 避免受监管负面影响的板块")

        else:
            lines.append("其他事件，建议:")
            lines.append("• 综合评估事件影响")
            lines.append("• 理性分析，避免情绪化交易")

        # Risk warning
        lines.append("\n【风险提示】")
        lines.append("• 事件影响存在不确定性")
        lines.append("• 建议分批建仓，控制风险")
        lines.append("• 及时止损，保护本金")

        return "\n".join(lines)

    def _assess_event_heat(self, news_count: int, event_type: str) -> str:
        """
        Assess event heat (how hot the event is)

        Args:
            news_count: Number of related news
            event_type: Event type

        Returns:
            Heat description
        """
        if news_count >= 50:
            return "🔥 爆发 - 极高关注度"
        elif news_count >= 20:
            return "🌡️ 升温 - 高关注度"
        elif news_count >= 10:
            return "✋ 平稳 - 中等关注度"
        else:
            return "❄️ 冷却 - 低关注度"

    def monitor_event(self, event_keyword: str, check_interval_hours: int = 24) -> Dict:
        """
        Monitor event for sentiment changes

        Args:
            event_keyword: Event keyword
            check_interval_hours: Check interval in hours

        Returns:
            Monitoring status
        """
        analysis = self.analyze_event(event_keyword)

        # Check if bullish sectors have high sentiment
        bullish_sectors = [s for s, sentiment in analysis.affected_sectors.items() if sentiment == '利好']

        trading_signals = []

        for sector in bullish_sectors:
            score = analysis.current_sentiment_scores.get(sector, 50)

            if score >= 70:
                trading_signals.append({
                    'sector': sector,
                    'action': '强烈关注',
                    'reason': f'事件利好 + 板块情绪高涨({score:.0f}分)',
                    'sentiment_score': score
                })
            elif score >= 60:
                trading_signals.append({
                    'sector': sector,
                    'action': '关注',
                    'reason': f'事件利好 + 板块情绪良好({score:.0f}分)',
                    'sentiment_score': score
                })
            else:
                trading_signals.append({
                    'sector': sector,
                    'action': '观望',
                    'reason': f'事件利好但板块情绪一般({score:.0f}分)',
                    'sentiment_score': score
                })

        return {
            'event': event_keyword,
            'news_count': analysis.news_count,
            'event_heat': self._assess_event_heat(analysis.news_count, analysis.event_type),
            'trading_signals': trading_signals,
            'recommendation': analysis.recommendation
        }

    def get_active_events(self, min_news_count: int = 10) -> List[Dict]:
        """
        Get currently active events

        Args:
            min_news_count: Minimum news count to consider active

        Returns:
            List of active events
        """
        # This would typically query a database of tracked events
        # For now, return a mock list
        common_events = ['降息', '地缘冲突', 'AI突破', '新能源政策', '中美关系']

        active_events = []

        for event in common_events:
            try:
                news = self.news_fetcher.search_news(event, days=3, max_results=30)
                if len(news) >= min_news_count:
                    analysis = self.analyze_event(event, days=3)

                    active_events.append({
                        'keyword': event,
                        'type': analysis.event_type,
                        'news_count': len(news),
                        'heat': self._assess_event_heat(len(news), analysis.event_type),
                        'sentiment': analysis.sentiment
                    })
            except Exception as e:
                print(f"Failed to analyze event {event}: {e}")

        # Sort by news count
        active_events.sort(key=lambda x: x['news_count'], reverse=True)

        return active_events


# Test code
if __name__ == "__main__":
    analyzer = EventAnalyzer()

    print("=== Event Analyzer Test ===\n")

    # Test single event analysis
    print("Analyzing event: '降息'\n")
    analysis = analyzer.analyze_event('降息', days=7)

    print(f"Event: {analysis.event_keyword}")
    print(f"Type: {analysis.event_type}")
    print(f"Sentiment: {analysis.sentiment}")
    print(f"News Count: {analysis.news_count}")
    print(f"\nAffected Sectors: {analysis.affected_sectors}")
    print(f"\nCurrent Sentiment Scores:")
    for sector, score in analysis.current_sentiment_scores.items():
        print(f"  {sector}: {score:.1f}")

    print(f"\nRecommendation:\n{analysis.recommendation}")

    # Test monitor
    print("\n=== Event Monitor ===\n")
    status = analyzer.monitor_event('降息')
    print(f"Event: {status['event']}")
    print(f"Heat: {status['event_heat']}")
    print("\nTrading Signals:")
    for signal in status['trading_signals']:
        print(f"  {signal['sector']}: {signal['action']} - {signal['reason']}")

    # Test active events
    print("\n=== Active Events ===\n")
    active = analyzer.get_active_events(min_news_count=5)
    for event in active[:5]:
        print(f"{event['keyword']}: {event['heat']} ({event['news_count']} news)")
