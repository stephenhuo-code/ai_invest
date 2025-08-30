"""
RSS News Fetcher Tool for AI Invest platform.

Fetches financial news from RSS feeds using feedparser and newspaper3k.
"""
import os
import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import feedparser
import requests
from newspaper import Article
import logging

from .base_tool import BaseTool, ToolResult, ToolStatus


class RSSNewsFetcher(BaseTool):
    """Real RSS news fetcher for financial news sources."""
    
    # Default financial RSS sources
    DEFAULT_RSS_SOURCES = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.reuters.com/business/finance/rss",
        "https://rss.cnn.com/rss/money_latest.rss",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
    ]
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        super().__init__(
            name="rss_news_fetcher", 
            description="Fetch financial news from RSS feeds and extract full content"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute RSS news fetching."""
        try:
            rss_urls = kwargs.get("rss_urls", self.DEFAULT_RSS_SOURCES)
            max_articles = kwargs.get("max_articles", 10)
            hours_back = kwargs.get("hours_back", 24)
            include_content = kwargs.get("include_content", True)
            
            # Convert to list if single URL provided
            if isinstance(rss_urls, str):
                rss_urls = [rss_urls]
            
            self.logger.info(f"Fetching from {len(rss_urls)} RSS sources, max {max_articles} articles")
            
            # Fetch articles from all sources
            all_articles = []
            errors = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for url in rss_urls:
                try:
                    articles = await self._fetch_from_rss(
                        url, max_articles, cutoff_time, include_content
                    )
                    all_articles.extend(articles)
                    self.logger.info(f"Fetched {len(articles)} articles from {url}")
                except Exception as e:
                    error_msg = f"Failed to fetch from {url}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Remove duplicates based on URL and content hash
            unique_articles = self._remove_duplicates(all_articles)
            
            # Sort by publish date and limit results
            unique_articles.sort(key=lambda x: x.get('published_at', datetime.min), reverse=True)
            final_articles = unique_articles[:max_articles]
            
            self.logger.info(f"Final result: {len(final_articles)} unique articles after deduplication")
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "articles": final_articles,
                    "total_fetched": len(all_articles),
                    "unique_articles": len(unique_articles),
                    "final_count": len(final_articles),
                    "sources_processed": len(rss_urls),
                    "errors": errors
                }
            )
            
        except Exception as e:
            self.logger.error(f"RSS fetching failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"RSS fetching failed: {str(e)}"
            )
    
    async def _fetch_from_rss(
        self, 
        rss_url: str, 
        max_articles: int, 
        cutoff_time: datetime,
        include_content: bool
    ) -> List[Dict[str, Any]]:
        """Fetch articles from a single RSS source."""
        articles = []
        
        # Parse RSS feed
        try:
            response = self.session.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            raise Exception(f"Failed to parse RSS feed: {str(e)}")
        
        if not feed.entries:
            self.logger.warning(f"No entries found in RSS feed: {rss_url}")
            return articles
        
        source_domain = urlparse(rss_url).netloc
        
        # Process each entry
        for entry in feed.entries[:max_articles * 2]:  # Fetch extra in case some are filtered
            try:
                # Parse publish date
                published_at = self._parse_publish_date(entry)
                if published_at and published_at < cutoff_time:
                    continue  # Skip old articles
                
                # Extract basic info
                url = entry.get('link', '')
                if not url:
                    continue
                
                title = entry.get('title', '').strip()
                summary = entry.get('summary', '').strip()
                author = entry.get('author', '').strip()
                
                # Create base article data
                article_data = {
                    "url": url,
                    "title": title,
                    "summary": summary,
                    "author": author,
                    "source": source_domain,
                    "published_at": published_at or datetime.now(),
                    "fetched_at": datetime.now(),
                    "content": summary,  # Default to summary
                    "content_hash": "",
                    "metadata": {
                        "rss_source": rss_url,
                        "entry_id": entry.get('id', ''),
                        "tags": [tag.term for tag in entry.get('tags', [])] if 'tags' in entry else []
                    }
                }
                
                # Extract full content if requested
                if include_content and url:
                    full_content = await self._extract_full_content(url)
                    if full_content:
                        article_data["content"] = full_content
                
                # Generate content hash
                content_for_hash = article_data["content"] + title
                article_data["content_hash"] = hashlib.md5(content_for_hash.encode()).hexdigest()
                
                articles.append(article_data)
                
                if len(articles) >= max_articles:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Failed to process RSS entry: {str(e)}")
                continue
        
        return articles
    
    async def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full article content using newspaper3k."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Return content if successfully extracted
            if article.text and len(article.text.strip()) > 100:  # Minimum content length
                return article.text.strip()
            
        except Exception as e:
            self.logger.debug(f"Failed to extract content from {url}: {str(e)}")
        
        return None
    
    def _parse_publish_date(self, entry) -> Optional[datetime]:
        """Parse publish date from RSS entry."""
        # Try different date fields
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_struct = getattr(entry, field)
                    return datetime(*time_struct[:6])
                except (ValueError, TypeError):
                    continue
        
        # Try string date fields
        string_fields = ['published', 'updated', 'created']
        for field in string_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    from dateutil.parser import parse
                    return parse(getattr(entry, field))
                except Exception:
                    continue
        
        return None
    
    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL and content hash."""
        seen_urls = set()
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            content_hash = article.get('content_hash', '')
            
            # Skip if we've seen this URL or content hash
            if url in seen_urls or content_hash in seen_hashes:
                continue
            
            seen_urls.add(url)
            seen_hashes.add(content_hash)
            unique_articles.append(article)
        
        return unique_articles
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        return {
            "parameters": {
                "rss_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of RSS feed URLs to fetch from",
                    "default": self.DEFAULT_RSS_SOURCES
                },
                "max_articles": {
                    "type": "integer", 
                    "description": "Maximum number of articles to fetch",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                },
                "hours_back": {
                    "type": "integer",
                    "description": "Only fetch articles from the last N hours",
                    "default": 24,
                    "minimum": 1
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to extract full article content",
                    "default": True
                }
            }
        }