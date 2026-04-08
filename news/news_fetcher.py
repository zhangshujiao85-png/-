"""
News Fetcher Module
Fetches news related to market events
"""
import requests
from typing import List, Dict
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re


class NewsFetcher:
    """News fetcher for market events"""

    def __init__(self):
        """Initialize news fetcher"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def search_news(self, keyword: str, days: int = 7, max_results: int = 20) -> List[Dict]:
        """
        Search news by keyword

        Args:
            keyword: Search keyword
            days: Number of days to look back
            max_results: Maximum number of results

        Returns:
            List of news articles
        """
        all_news = []

        # Try multiple sources
        try:
            # Source 1: Eastmoney
            eastmoney_news = self._search_eastmoney(keyword, days, max_results)
            all_news.extend(eastmoney_news)
        except Exception as e:
            print(f"Eastmoney search failed: {e}")

        try:
            # Source 2: Sina Finance
            sina_news = self._search_sina(keyword, days, max_results)
            all_news.extend(sina_news)
        except Exception as e:
            print(f"Sina search failed: {e}")

        # Sort by date and deduplicate
        all_news = sorted(all_news, key=lambda x: x['date'], reverse=True)

        # Remove duplicates based on title
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
                if len(unique_news) >= max_results:
                    break

        return unique_news

    def _search_eastmoney(self, keyword: str, days: int, max_results: int) -> List[Dict]:
        """Search news from Eastmoney"""
        try:
            url = "http://search-api.eastmoney.com/search/xmlp"

            params = {
                'param': keyword,
                'type': 'cmsArticleWebOld',
                'page': '1',
                'per_page': str(max_results)
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                news_list = []
                if 'data' in data and 'list' in data['data']:
                    for item in data['data']['list'][:max_results]:
                        try:
                            # Parse date
                            date_str = item.get('artTime', item.get('date', ''))
                            date = self._parse_date(date_str)

                            # Filter by days
                            if date and date < datetime.now() - timedelta(days=days):
                                continue

                            news_list.append({
                                'title': item.get('title', item.get('artTitle', '')),
                                'url': item.get('url', item.get('artUrl', '')),
                                'date': date.isoformat() if date else datetime.now().isoformat(),
                                'source': '东方财富',
                                'summary': item.get('digest', item.get('content', ''))[:200]
                            })
                        except Exception as e:
                            print(f"Failed to parse news item: {e}")
                            continue

                return news_list

        except Exception as e:
            print(f"Eastmoney API error: {e}")

        return []

    def _search_sina(self, keyword: str, days: int, max_results: int) -> List[Dict]:
        """Search news from Sina Finance"""
        try:
            url = "https://search.sina.com.cn/"

            params = {
                'q': keyword,
                'range': 'all',
                'c': 'news'
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                news_list = []

                # Parse search results (this is a simplified example)
                # Actual implementation would need to handle the specific HTML structure
                for item in soup.find_all('div', class_='news-item')[:max_results]:
                    try:
                        title_elem = item.find('a')
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')

                        date_elem = item.find('span', class_='date')
                        date_str = date_elem.get_text(strip=True) if date_elem else ''
                        date = self._parse_date(date_str)

                        # Filter by days
                        if date and date < datetime.now() - timedelta(days=days):
                            continue

                        news_list.append({
                            'title': title,
                            'url': url,
                            'date': date.isoformat() if date else datetime.now().isoformat(),
                            'source': '新浪财经',
                            'summary': item.get_text(strip=True)[:200]
                        })
                    except Exception as e:
                        print(f"Failed to parse Sina news item: {e}")
                        continue

                return news_list

        except Exception as e:
            print(f"Sina search error: {e}")

        return []

    def get_hot_news(self, category: str = 'market', max_results: int = 20) -> List[Dict]:
        """
        Get hot news by category

        Args:
            category: News category (market/sector/global)
            max_results: Maximum number of results

        Returns:
            List of hot news articles
        """
        try:
            if category == 'market':
                return self._get_market_hot_news(max_results)
            elif category == 'sector':
                return self._get_sector_hot_news(max_results)
            elif category == 'global':
                return self._get_global_hot_news(max_results)
            else:
                return []
        except Exception as e:
            print(f"Failed to get hot news: {e}")
            return []

    def _get_market_hot_news(self, max_results: int) -> List[Dict]:
        """Get hot market news"""
        try:
            import akshare as ak

            # Get flash news from Eastmoney
            news_df = ak.stock_news_em(symbol="市场突发")

            if news_df.empty:
                return []

            news_list = []
            for _, row in news_df.head(max_results).iterrows():
                try:
                    # Parse date
                    date_str = row.get('发布时间', row.get('时间', ''))
                    date = self._parse_date(date_str)

                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'url': row.get('新闻链接', ''),
                        'date': date.isoformat() if date else datetime.now().isoformat(),
                        'source': '东方财富',
                        'summary': ''
                    })
                except Exception as e:
                    continue

            return news_list

        except Exception as e:
            print(f"Failed to get market hot news: {e}")
            return []

    def _get_sector_hot_news(self, max_results: int) -> List[Dict]:
        """Get hot sector news"""
        try:
            import akshare as ak

            # Get sector news
            news_df = ak.stock_news_em(symbol="行业新闻")

            if news_df.empty:
                return []

            news_list = []
            for _, row in news_df.head(max_results).iterrows():
                try:
                    date_str = row.get('发布时间', '')
                    date = self._parse_date(date_str)

                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'url': row.get('新闻链接', ''),
                        'date': date.isoformat() if date else datetime.now().isoformat(),
                        'source': '东方财富',
                        'summary': ''
                    })
                except Exception as e:
                    continue

            return news_list

        except Exception as e:
            print(f"Failed to get sector hot news: {e}")
            return []

    def _get_global_hot_news(self, max_results: int) -> List[Dict]:
        """Get global hot news"""
        try:
            import akshare as ak

            # Get global news
            news_df = ak.stock_news_em(symbol="国际市场")

            if news_df.empty:
                return []

            news_list = []
            for _, row in news_df.head(max_results).iterrows():
                try:
                    date_str = row.get('发布时间', '')
                    date = self._parse_date(date_str)

                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'url': row.get('新闻链接', ''),
                        'date': date.isoformat() if date else datetime.now().isoformat(),
                        'source': '东方财富',
                        'summary': ''
                    })
                except Exception as e:
                    continue

            return news_list

        except Exception as e:
            print(f"Failed to get global hot news: {e}")
            return []

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object

        Args:
            date_str: Date string

        Returns:
            Datetime object
        """
        if not date_str:
            return datetime.now()

        # Common date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y年%m月%d日',
            '%Y/%m/%d',
            '%m-%d %H:%M',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        # If parsing fails, return current time
        return datetime.now()


# Test code
if __name__ == "__main__":
    fetcher = NewsFetcher()

    print("=== News Fetcher Test ===\n")

    # Test search news
    print("Searching news for '降息'...")
    news = fetcher.search_news('降息', days=7, max_results=5)

    print(f"Found {len(news)} articles:\n")
    for i, article in enumerate(news, 1):
        print(f"{i}. {article['title']}")
        print(f"   Date: {article['date']}")
        print(f"   Source: {article['source']}")
        if article['summary']:
            print(f"   Summary: {article['summary'][:100]}...")
        print()

    # Test hot news
    print("\n=== Hot Market News ===\n")
    hot_news = fetcher.get_hot_news(category='market', max_results=5)

    for i, article in enumerate(hot_news, 1):
        print(f"{i}. {article['title']}")
        print(f"   Date: {article['date']}")
        print()
