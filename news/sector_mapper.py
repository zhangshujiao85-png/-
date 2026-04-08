"""
Event-Sector Mapping Module
Defines mapping between events and affected sectors
"""
from typing import Dict, List


# Event to sector mapping
# Defines which sectors are affected by different types of events
EVENT_SECTOR_MAPPING = {
    # Geopolitical events
    '地缘冲突': {
        '军工': '利好',
        '石油': '利好',
        '黄金': '利好',
        '航运': '利空',
        '航空': '利空',
        '旅游': '利空',
        '半导体': '中性',
        '新能源': '中性'
    },
    '战争': {
        '军工': '利好',
        '石油': '利好',
        '黄金': '利好',
        '农业': '利好',
        '医药': '利好'
    },
    '制裁': {
        '半导体': '利空',
        '软件': '利空',
        '科技': '利空',
        '军工': '利好',
        '国产替代': '利好'
    },

    # Macro policy events
    '降息': {
        '银行': '中性',
        '地产': '利好',
        '券商': '利好',
        '成长股': '利好',
        '高股息': '中性'
    },
    '加息': {
        '银行': '利好',
        '地产': '利空',
        '券商': '利空',
        '成长股': '利空',
        '高股息': '利好'
    },
    '降准': {
        '银行': '利好',
        '地产': '利好',
        '券商': '利好',
        '基建': '利好'
    },
    '财政刺激': {
        '基建': '利好',
        '建材': '利好',
        '工程机械': '利好',
        '地产': '利好'
    },

    # Industry events
    'AI突破': {
        '半导体': '利好',
        '软件': '利好',
        '传媒': '利好',
        '通信': '利好',
        '算力': '利好'
    },
    '新能源政策': {
        '新能源': '利好',
        '光伏': '利好',
        '风电': '利好',
        '储能': '利好',
        '电动车': '利好'
    },
    '医药创新': {
        '医药': '利好',
        '生物制药': '利好',
        '医疗器械': '利好'
    },
    '消费刺激': {
        '消费': '利好',
        '食品饮料': '利好',
        '汽车': '利好',
        '家电': '利好',
        '旅游': '利好'
    },

    # Regulatory events
    'IPO重启': {
        '券商': '利好',
        '次新股': '利空',
        '市场整体': '利空'
    },
    '再融资收紧': {
        '券商': '利空',
        '市场整体': '利好'
    },
    '退市加速': {
        'ST股票': '利空',
        '垃圾股': '利空',
        '优质股': '利好'
    },

    # International events
    '中美关系': {
        '半导体': '利空',
        '科技': '利空',
        '军工': '利好',
        '国产替代': '利好'
    },
    '美联储加息': {
        '成长股': '利空',
        '高股息': '利好',
        '出口': '利空'
    },
    '全球通胀': {
        '资源': '利好',
        '黄金': '利好',
        '消费': '利空'
    },

    # Market events
    '牛市': {
        '券商': '利好',
        '成长股': '利好',
        '高贝塔': '利好'
    },
    '熊市': {
        '高股息': '利好',
        '黄金': '利好',
        '消费': '利好',
        '医药': '利好'
    },

    # Weather/Natural disaster
    '极端天气': {
        '农业': '利空',
        '保险': '利空',
        '建材': '利好',
        '电力': '利好'
    },
    '疫情': {
        '医药': '利好',
        '在线教育': '利好',
        '远程办公': '利好',
        '旅游': '利空',
        '航空': '利空',
        '餐饮': '利空'
    }
}


# Event type classification
EVENT_TYPES = {
    '地缘': ['地缘冲突', '战争', '制裁', '贸易战', '外交摩擦'],
    '宏观': ['降息', '加息', '降准', '财政刺激', '货币宽松', '紧缩'],
    '行业': ['AI突破', '新能源政策', '医药创新', '消费刺激', '国产替代'],
    '监管': ['IPO重启', '再融资收紧', '退市加速', '监管政策'],
    '国际': ['中美关系', '美联储加息', '全球通胀', '国际局势'],
    '市场': ['牛市', '熊市', '震荡', '大涨', '大跌'],
    '灾害': ['极端天气', '疫情', '自然灾害']
}


class SectorMapper:
    """Event-sector mapper"""

    @staticmethod
    def get_affected_sectors(event_keyword: str) -> Dict[str, str]:
        """
        Get sectors affected by an event

        Args:
            event_keyword: Event keyword

        Returns:
            Dictionary mapping sector names to sentiment (利好/利空/中性)
        """
        # Direct match
        if event_keyword in EVENT_SECTOR_MAPPING:
            return EVENT_SECTOR_MAPPING[event_keyword]

        # Fuzzy match
        for key, sectors in EVENT_SECTOR_MAPPING.items():
            if event_keyword in key or key in event_keyword:
                return sectors

        # No match found
        return {}

    @staticmethod
    def get_event_type(event_keyword: str) -> str:
        """
        Classify event type

        Args:
            event_keyword: Event keyword

        Returns:
            Event type string
        """
        for event_type, keywords in EVENT_TYPES.items():
            for keyword in keywords:
                if keyword in event_keyword or event_keyword in keyword:
                    return event_type

        # Default to '其他'
        return '其他'

    @staticmethod
    def get_all_event_types() -> Dict[str, List[str]]:
        """
        Get all event types and their keywords

        Returns:
            Dictionary mapping event types to keyword lists
        """
        return EVENT_TYPES

    @staticmethod
    def search_sectors_by_sentiment(sentiment: str) -> List[str]:
        """
        Search sectors that match a specific sentiment

        Args:
            sentiment: Sentiment type (利好/利空/中性)

        Returns:
            List of sectors
        """
        sectors = set()

        for event_sectors in EVENT_SECTOR_MAPPING.values():
            for sector, sector_sentiment in event_sectors.items():
                if sector_sentiment == sentiment:
                    sectors.add(sector)

        return sorted(list(sectors))

    @staticmethod
    def explain_event_impact(event_keyword: str) -> str:
        """
        Generate explanation of event impact

        Args:
            event_keyword: Event keyword

        Returns:
            Explanation string
        """
        affected_sectors = SectorMapper.get_affected_sectors(event_keyword)
        event_type = SectorMapper.get_event_type(event_keyword)

        if not affected_sectors:
            return f"未找到事件 '{event_keyword}' 的映射关系"

        lines = [
            f"事件: {event_keyword}",
            f"类型: {event_type}",
            "",
            "影响板块:"
        ]

        # Group by sentiment
        bullish = [s for s, sentiment in affected_sectors.items() if sentiment == '利好']
        bearish = [s for s, sentiment in affected_sectors.items() if sentiment == '利空']
        neutral = [s for s, sentiment in affected_sectors.items() if sentiment == '中性']

        if bullish:
            lines.append(f"  利好: {', '.join(bullish)}")
        if bearish:
            lines.append(f"  利空: {', '.join(bearish)}")
        if neutral:
            lines.append(f"  中性: {', '.join(neutral)}")

        return "\n".join(lines)


# Test code
if __name__ == "__main__":
    mapper = SectorMapper()

    # Test sector mapping
    print("=== Event-Sector Mapping Test ===\n")

    events = ['地缘冲突', '降息', 'AI突破', '新能源政策']

    for event in events:
        print(f"Event: {event}")
        print(mapper.explain_event_impact(event))
        print()

    # Test event type classification
    print("=== Event Type Classification ===\n")
    test_keywords = ['美联储加息', '中美贸易摩擦', '降准降息', 'AI技术突破']

    for keyword in test_keywords:
        event_type = mapper.get_event_type(keyword)
        print(f"{keyword} -> {event_type}")

    # Test search by sentiment
    print("\n=== Bullish Sectors ===")
    bullish = mapper.search_sectors_by_sentiment('利好')
    print(f"利好板块 ({len(bullish)}): {', '.join(bullish[:15])}...")
