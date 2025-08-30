#!/usr/bin/env python3
"""
Test individual tool files.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


async def test_market_data_only():
    """Test only market data fetcher."""
    print("🔄 Testing Market Data Fetcher...")
    
    try:
        # Import only what we need
        from src.application.tools.market_data import MarketDataFetcher
        
        fetcher = MarketDataFetcher()
        
        # Test current prices
        result = await fetcher.execute(operation="get_prices", symbols=["AAPL"])
        
        if result.is_success:
            data = result.data
            market_data = data.get('market_data', {})
            print(f"  ✅ Market data tool working! Fetched {len(market_data)} symbols")
            
            for symbol, stock_data in market_data.items():
                if 'error' not in stock_data:
                    price = stock_data.get('price', 'N/A')
                    print(f"  📊 {symbol}: ${price}")
                else:
                    print(f"  ⚠️  {symbol}: {stock_data.get('error')}")
            
            return True
        else:
            print(f"  ❌ Failed: {result.error_message}")
            return False
            
    except ImportError as e:
        print(f"  ❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"  ❌ Test failed: {str(e)}")
        return False


async def test_rss_basic():
    """Test RSS fetcher basic functionality."""
    print("🔄 Testing RSS News Fetcher Basic...")
    
    try:
        # Test just the RSS parsing without database dependencies
        import feedparser
        import requests
        
        # Test RSS feed parsing directly
        rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline"
        response = requests.get(rss_url, timeout=10)
        feed = feedparser.parse(response.content)
        
        if feed.entries:
            print(f"  ✅ RSS feed accessible! Found {len(feed.entries)} entries")
            first_entry = feed.entries[0]
            print(f"  📰 Sample: {first_entry.get('title', 'No title')[:60]}...")
            return True
        else:
            print("  ❌ No entries found in RSS feed")
            return False
            
    except ImportError as e:
        print(f"  ⚠️  Missing dependency: {str(e)}")
        print("  💡 Run: pip install feedparser requests")
        return False
    except Exception as e:
        print(f"  ❌ RSS test failed: {str(e)}")
        return False


async def main():
    """Run simple tests."""
    print("🚀 Simple Tools Test")
    print("=" * 40)
    
    tests = [
        ("Market Data", test_market_data_only),
        ("RSS Basic", test_rss_basic)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            await test_func()
        except Exception as e:
            print(f"💥 {test_name} crashed: {str(e)}")
    
    print(f"\n⏰ Completed at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())