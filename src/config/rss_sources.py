"""
RSS Sources Configuration for AI Invest platform.

Based on testing results and optimization recommendations.
"""
import random
from typing import List, Dict, Any
from enum import Enum


class SourceReliability(Enum):
    """RSS source reliability levels based on testing."""
    HIGH = "high"           # >90% success rate
    MEDIUM = "medium"       # 60-90% success rate  
    LOW = "low"            # <60% success rate
    UNTESTED = "untested"   # Not yet tested


class RSSSourceConfig:
    """Configuration for RSS news sources."""
    
    # Primary sources - tested and working reliably
    PRIMARY_SOURCES = [
        {
            "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "name": "CNBC Business",
            "reliability": SourceReliability.HIGH,
            "avg_response_time": 2.6,
            "content_quality": "excellent",
            "notes": "High quality financial news, good full-text extraction"
        },
        {
            "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
            "name": "MarketWatch Top Stories", 
            "reliability": SourceReliability.HIGH,
            "avg_response_time": 1.9,
            "content_quality": "excellent",
            "notes": "Reliable source with good market coverage"
        },
        {
            "url": "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
            "name": "NASDAQ Stocks",
            "reliability": SourceReliability.HIGH,
            "avg_response_time": 1.0,
            "content_quality": "good",
            "notes": "Fast response, focused on stock market news"
        }
    ]
    
    # Secondary sources - alternatives and backups
    SECONDARY_SOURCES = [
        {
            "url": "https://www.marketwatch.com/rss/realtimeheadlines",
            "name": "MarketWatch Real-time",
            "reliability": SourceReliability.UNTESTED,
            "notes": "Alternative MarketWatch feed"
        },
        {
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "name": "Wall Street Journal Markets",
            "reliability": SourceReliability.UNTESTED,
            "notes": "WSJ market news"
        },
        {
            "url": "https://feeds.feedburner.com/zerohedge/feed",
            "name": "ZeroHedge",
            "reliability": SourceReliability.UNTESTED,
            "notes": "Alternative financial perspective"
        },
        {
            "url": "https://rss.cbc.ca/lineup/business.xml",
            "name": "CBC Business",
            "reliability": SourceReliability.UNTESTED,
            "notes": "Canadian business news"
        },
        {
            "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
            "name": "BBC Business",
            "reliability": SourceReliability.UNTESTED,
            "notes": "UK/global business news"
        }
    ]
    
    # Problematic sources - known issues from testing
    PROBLEMATIC_SOURCES = [
        {
            "url": "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "name": "Yahoo Finance Headlines",
            "reliability": SourceReliability.LOW,
            "issue": "HTTP 429 - Rate limiting",
            "solution": "Needs User-Agent rotation and delays"
        },
        {
            "url": "https://www.reuters.com/business/finance/rss", 
            "name": "Reuters Finance",
            "reliability": SourceReliability.LOW,
            "issue": "HTTP 401 - Authentication required",
            "solution": "May need subscription or different endpoint"
        },
        {
            "url": "https://rss.cnn.com/rss/money_latest.rss",
            "name": "CNN Money",
            "reliability": SourceReliability.LOW,
            "issue": "SSL connection errors",
            "solution": "SSL configuration or alternative endpoint needed"
        },
        {
            "url": "https://feeds.bloomberg.com/markets/news.rss",
            "name": "Bloomberg Markets",
            "reliability": SourceReliability.LOW,
            "issue": "Connection reset by peer",
            "solution": "May require special headers or proxy"
        }
    ]
    
    @classmethod
    def get_active_sources(cls, reliability_threshold: SourceReliability = SourceReliability.MEDIUM) -> List[str]:
        """Get list of active RSS source URLs based on reliability."""
        active_sources = []
        
        # Always include primary sources
        for source in cls.PRIMARY_SOURCES:
            active_sources.append(source["url"])
        
        # Include secondary sources if threshold allows
        if reliability_threshold in [SourceReliability.LOW, SourceReliability.UNTESTED]:
            for source in cls.SECONDARY_SOURCES:
                active_sources.append(source["url"])
        
        return active_sources
    
    @classmethod
    def get_source_info(cls, url: str) -> Dict[str, Any]:
        """Get detailed information about a specific RSS source."""
        all_sources = cls.PRIMARY_SOURCES + cls.SECONDARY_SOURCES + cls.PROBLEMATIC_SOURCES
        
        for source in all_sources:
            if source["url"] == url:
                return source
        
        return {"url": url, "name": "Unknown Source", "reliability": SourceReliability.UNTESTED}
    
    @classmethod
    def get_optimized_user_agents(cls) -> List[str]:
        """Get list of user agents for rotation."""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    @classmethod
    def get_optimized_headers(cls) -> Dict[str, str]:
        """Get optimized headers for RSS requests."""
        return {
            'User-Agent': random.choice(cls.get_optimized_user_agents()),
            'Accept': 'application/rss+xml, application/xml, text/xml, application/atom+xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        }
    
    @classmethod
    def get_retry_config(cls) -> Dict[str, Any]:
        """Get retry configuration for failed requests."""
        return {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_on_status': [429, 500, 502, 503, 504],
            'delay_between_sources': 1.5,  # seconds
            'timeout': 20,  # seconds
            'ssl_verify': True,
            'allow_redirects': True,
            'max_redirects': 3
        }


# Convenience functions
def get_default_rss_sources() -> List[str]:
    """Get the default list of RSS sources for production use."""
    return RSSSourceConfig.get_active_sources(SourceReliability.MEDIUM)


def get_all_rss_sources() -> List[str]:
    """Get all RSS sources including experimental ones.""" 
    return RSSSourceConfig.get_active_sources(SourceReliability.UNTESTED)


def get_reliable_rss_sources() -> List[str]:
    """Get only the most reliable RSS sources."""
    return RSSSourceConfig.get_active_sources(SourceReliability.HIGH)


# Export configuration for easy import
__all__ = [
    'RSSSourceConfig',
    'SourceReliability', 
    'get_default_rss_sources',
    'get_all_rss_sources',
    'get_reliable_rss_sources'
]