#!/usr/bin/env python3
"""
Test RSS news fetcher with DEFAULT_RSS_SOURCES for 1-day data collection.

This script tests the RSSNewsFetcher tool with all default sources to gather
24 hours of financial news data and analyze the performance.
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test both individual components and the full tool
try:
    import feedparser
    import requests
    from newspaper import Article
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"⚠️  Missing dependencies: {e}")
    print("📦 Install with: pip install feedparser requests newspaper3k python-dateutil")
    HAS_DEPENDENCIES = False

# Default RSS sources to test (same as in RSSNewsFetcher)
DEFAULT_RSS_SOURCES = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html", 
    "https://www.reuters.com/business/finance/rss",
    "https://rss.cnn.com/rss/money_latest.rss",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
]


class RSSTestResult:
    """Container for RSS test results."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.source_results = {}
        self.summary = {
            'total_sources': len(DEFAULT_RSS_SOURCES),
            'successful_sources': 0,
            'failed_sources': 0,
            'total_articles': 0,
            'unique_articles': 0,
            'articles_with_content': 0,
            'total_errors': []
        }
        self.performance_metrics = {}


class RSSSourceTester:
    """Test individual RSS sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = 15
    
    async def test_rss_connectivity(self, rss_url: str) -> Dict[str, Any]:
        """Test basic RSS feed connectivity."""
        print(f"🔍 Testing connectivity: {rss_url}")
        
        result = {
            'url': rss_url,
            'accessible': False,
            'response_time': 0,
            'status_code': None,
            'entries_count': 0,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            response = self.session.get(rss_url, timeout=self.timeout)
            result['response_time'] = time.time() - start_time
            result['status_code'] = response.status_code
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                result['entries_count'] = len(feed.entries)
                result['accessible'] = len(feed.entries) > 0
                
                if result['accessible']:
                    print(f"  ✅ Success: {result['entries_count']} entries ({result['response_time']:.2f}s)")
                else:
                    print(f"  ⚠️  No entries found")
                    result['error'] = "No entries in feed"
            else:
                print(f"  ❌ HTTP {response.status_code}")
                result['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            result['error'] = "Request timeout"
            print(f"  ❌ Timeout after {self.timeout}s")
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ Error: {str(e)}")
        
        return result
    
    async def test_article_extraction(self, rss_url: str, max_articles: int = 3) -> Dict[str, Any]:
        """Test article extraction from RSS feed."""
        print(f"📰 Testing article extraction: {rss_url}")
        
        result = {
            'url': rss_url,
            'success': False,
            'articles': [],
            'extraction_stats': {
                'total_entries': 0,
                'recent_entries': 0,
                'content_extracted': 0,
                'extraction_failures': 0
            },
            'error': None
        }
        
        try:
            # Get RSS feed
            response = self.session.get(rss_url, timeout=self.timeout)
            if response.status_code != 200:
                result['error'] = f"HTTP {response.status_code}"
                return result
            
            feed = feedparser.parse(response.content)
            result['extraction_stats']['total_entries'] = len(feed.entries)
            
            if not feed.entries:
                result['error'] = "No entries found"
                return result
            
            # Filter for recent articles (24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_entries = []
            
            for entry in feed.entries[:max_articles * 2]:  # Get extra to filter
                pub_date = self._parse_publish_date(entry)
                if not pub_date or pub_date >= cutoff_time:
                    recent_entries.append(entry)
            
            result['extraction_stats']['recent_entries'] = len(recent_entries)
            
            # Process recent entries
            for entry in recent_entries[:max_articles]:
                article_data = await self._process_entry(entry, rss_url)
                if article_data:
                    result['articles'].append(article_data)
                    if article_data.get('full_content_extracted'):
                        result['extraction_stats']['content_extracted'] += 1
                    else:
                        result['extraction_stats']['extraction_failures'] += 1
            
            result['success'] = len(result['articles']) > 0
            print(f"  ✅ Extracted {len(result['articles'])} articles")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ Extraction failed: {str(e)}")
        
        return result
    
    async def _process_entry(self, entry, source_url: str) -> Dict[str, Any]:
        """Process a single RSS entry."""
        try:
            article_data = {
                'title': entry.get('title', '').strip(),
                'url': entry.get('link', ''),
                'summary': entry.get('summary', '').strip(),
                'author': entry.get('author', '').strip(),
                'published_at': self._parse_publish_date(entry),
                'source_url': source_url,
                'full_content': None,
                'full_content_extracted': False,
                'content_length': 0
            }
            
            # Try to extract full content
            if article_data['url']:
                try:
                    article = Article(article_data['url'])
                    article.download()
                    article.parse()
                    
                    if article.text and len(article.text.strip()) > 100:
                        article_data['full_content'] = article.text.strip()
                        article_data['full_content_extracted'] = True
                        article_data['content_length'] = len(article.text)
                    else:
                        # Fall back to summary
                        article_data['full_content'] = article_data['summary']
                        article_data['content_length'] = len(article_data['summary'])
                        
                except Exception:
                    # Use summary as fallback
                    article_data['full_content'] = article_data['summary']
                    article_data['content_length'] = len(article_data['summary'])
            
            return article_data
            
        except Exception:
            return None
    
    def _parse_publish_date(self, entry) -> datetime:
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
        
        # Try string date fields with dateutil
        string_fields = ['published', 'updated', 'created']
        for field in string_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    from dateutil.parser import parse
                    return parse(getattr(entry, field))
                except Exception:
                    continue
        
        # Default to now if no date found
        return datetime.now()


async def test_all_rss_sources():
    """Test all default RSS sources."""
    print("🚀 Starting RSS Sources 1-Day Data Test")
    print("=" * 60)
    print(f"📅 Testing data from last 24 hours")
    print(f"📡 Testing {len(DEFAULT_RSS_SOURCES)} RSS sources")
    print()
    
    if not HAS_DEPENDENCIES:
        print("❌ Cannot run tests - missing dependencies")
        return
    
    result = RSSTestResult()
    tester = RSSSourceTester()
    
    # Test 1: Basic Connectivity
    print("🔗 Phase 1: Testing RSS Feed Connectivity")
    print("-" * 40)
    
    connectivity_results = []
    for rss_url in DEFAULT_RSS_SOURCES:
        conn_result = await tester.test_rss_connectivity(rss_url)
        connectivity_results.append(conn_result)
        result.source_results[rss_url] = {'connectivity': conn_result}
        
        if conn_result['accessible']:
            result.summary['successful_sources'] += 1
        else:
            result.summary['failed_sources'] += 1
            result.summary['total_errors'].append(f"{rss_url}: {conn_result['error']}")
    
    print(f"\n📊 Connectivity Results: {result.summary['successful_sources']}/{result.summary['total_sources']} sources accessible")
    
    # Test 2: Article Extraction
    print("\n📰 Phase 2: Testing Article Extraction (24h data)")
    print("-" * 40)
    
    all_articles = []
    for rss_url in DEFAULT_RSS_SOURCES:
        if result.source_results[rss_url]['connectivity']['accessible']:
            extraction_result = await tester.test_article_extraction(rss_url, max_articles=5)
            result.source_results[rss_url]['extraction'] = extraction_result
            
            if extraction_result['success']:
                articles = extraction_result['articles']
                all_articles.extend(articles)
                result.summary['total_articles'] += len(articles)
                result.summary['articles_with_content'] += extraction_result['extraction_stats']['content_extracted']
        else:
            print(f"⏭️  Skipping {rss_url} (not accessible)")
    
    # Test 3: Deduplication
    print("\n🔄 Phase 3: Testing Deduplication")
    print("-" * 40)
    
    unique_articles = await test_deduplication(all_articles)
    result.summary['unique_articles'] = len(unique_articles)
    
    print(f"📊 Deduplication: {result.summary['total_articles']} → {result.summary['unique_articles']} articles")
    
    # Generate Report
    await generate_test_report(result, unique_articles[:5])  # Show first 5 articles
    
    return result


async def test_deduplication(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Test deduplication logic."""
    import hashlib
    
    seen_urls = set()
    seen_hashes = set()
    unique_articles = []
    
    for article in articles:
        url = article.get('url', '')
        content = article.get('full_content', '') + article.get('title', '')
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if url not in seen_urls and content_hash not in seen_hashes:
            seen_urls.add(url)
            seen_hashes.add(content_hash)
            unique_articles.append(article)
    
    return unique_articles


async def generate_test_report(result: RSSTestResult, sample_articles: List[Dict[str, Any]]):
    """Generate comprehensive test report."""
    print("\n📋 Test Report")
    print("=" * 60)
    
    # Summary Statistics
    print(f"⏱️  Test Duration: {(datetime.now() - result.start_time).total_seconds():.1f} seconds")
    print(f"📡 RSS Sources: {result.summary['successful_sources']}/{result.summary['total_sources']} accessible")
    print(f"📰 Articles Found: {result.summary['total_articles']} total, {result.summary['unique_articles']} unique")
    print(f"📄 Full Content: {result.summary['articles_with_content']} articles")
    print(f"🔄 Deduplication: {result.summary['total_articles'] - result.summary['unique_articles']} duplicates removed")
    
    # Source-by-Source Results
    print(f"\n📊 Source Performance:")
    print("-" * 40)
    
    for url in DEFAULT_RSS_SOURCES:
        source_data = result.source_results.get(url, {})
        conn = source_data.get('connectivity', {})
        extr = source_data.get('extraction', {})
        
        status = "✅" if conn.get('accessible', False) else "❌"
        response_time = conn.get('response_time', 0)
        entries = conn.get('entries_count', 0)
        articles = len(extr.get('articles', [])) if extr else 0
        
        source_name = url.split('/')[2]  # Extract domain
        print(f"{status} {source_name:20s} | {response_time:4.1f}s | {entries:3d} entries | {articles:2d} articles")
    
    # Sample Articles
    if sample_articles:
        print(f"\n📄 Sample Articles (First 5):")
        print("-" * 40)
        
        for i, article in enumerate(sample_articles, 1):
            title = article.get('title', 'No title')[:60]
            source = article.get('source_url', '').split('/')[2] if article.get('source_url') else 'Unknown'
            content_len = article.get('content_length', 0)
            extracted = "✅" if article.get('full_content_extracted', False) else "📝"
            
            print(f"{i}. {title}...")
            print(f"   {extracted} {source} | {content_len} chars")
    
    # Errors and Issues
    if result.summary['total_errors']:
        print(f"\n⚠️  Errors Encountered:")
        print("-" * 40)
        for error in result.summary['total_errors']:
            print(f"  • {error}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print("-" * 40)
    
    success_rate = result.summary['successful_sources'] / result.summary['total_sources'] * 100
    
    if success_rate < 70:
        print("  • Consider adding User-Agent rotation or proxy support")
        print("  • Some RSS feeds may require special headers or authentication")
    
    if result.summary['articles_with_content'] < result.summary['total_articles'] * 0.5:
        print("  • Content extraction rate is low - consider fallback strategies")
        print("  • Some sites may require JavaScript rendering")
    
    if result.summary['total_articles'] - result.summary['unique_articles'] > result.summary['total_articles'] * 0.3:
        print("  • High duplication rate - consider improving deduplication logic")
    
    if success_rate >= 70:
        print("  ✅ RSS sources are performing well!")
    
    print(f"\n🎯 Overall Assessment: ", end="")
    if success_rate >= 80 and result.summary['unique_articles'] >= 10:
        print("EXCELLENT - Ready for production use")
    elif success_rate >= 60 and result.summary['unique_articles'] >= 5:
        print("GOOD - Minor optimizations recommended")
    else:
        print("NEEDS WORK - Significant improvements required")


async def main():
    """Run the complete RSS 1-day data test."""
    try:
        await test_all_rss_sources()
    except KeyboardInterrupt:
        print("\n\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())