#!/usr/bin/env python3
"""
Standalone test script for individual tools.

Tests tools without database dependencies.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.application.tools.rss_news_fetcher import RSSNewsFetcher
from src.application.tools.market_data import MarketDataFetcher


async def test_rss_news_fetcher():
    """Test RSS news fetching without database."""
    print("🔄 Testing RSS News Fetcher (Standalone)...")
    
    try:
        fetcher = RSSNewsFetcher()
        
        # Test with limited articles and no content extraction to avoid external dependencies
        result = await fetcher.execute(
            rss_urls=["https://feeds.finance.yahoo.com/rss/2.0/headline"],
            max_articles=2,
            hours_back=48,
            include_content=False  # Avoid newspaper3k dependency
        )
        
        if result.is_success:
            data = result.data
            print(f"  ✅ Successfully fetched {data.get('final_count', 0)} articles")
            print(f"  📊 Total from RSS: {data.get('total_fetched', 0)}")
            print(f"  🔍 After deduplication: {data.get('unique_articles', 0)}")
            
            if data.get('articles'):
                first_article = data['articles'][0]
                print(f"  📰 Sample article: {first_article.get('title', 'No title')[:80]}...")
                print(f"  🔗 URL: {first_article.get('url', 'No URL')[:50]}...")
            
            if data.get('errors'):
                print(f"  ⚠️  Errors: {len(data['errors'])}")
                for error in data['errors'][:2]:  # Show first 2 errors
                    print(f"    - {error}")
            
            return True
            
        else:
            print(f"  ❌ RSS fetching failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ RSS test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_data():
    """Test market data fetching."""
    print("🔄 Testing Market Data Fetcher (Standalone)...")
    
    try:
        fetcher = MarketDataFetcher()
        
        # Test current prices for a few popular stocks
        test_symbols = ["AAPL", "GOOGL"]  # Limit to 2 for testing
        result = await fetcher.execute(operation="get_prices", symbols=test_symbols)
        
        if result.is_success:
            data = result.data
            market_data = data.get('market_data', {})
            print(f"  ✅ Fetched data for {len(market_data)} symbols")
            print(f"  📈 Symbols processed: {data.get('symbols_processed', 0)}")
            print(f"  💾 Cached results: {data.get('cached_results', 0)}")
            
            # Show sample data
            for symbol, stock_data in market_data.items():
                if 'error' not in stock_data:
                    price = stock_data.get('price', 'N/A')
                    change = stock_data.get('change', 0)
                    company = stock_data.get('company_name', symbol)
                    print(f"  📊 {symbol} ({company}): ${price} ({change:+.2f})")
                else:
                    print(f"  ⚠️  {symbol}: {stock_data.get('error', 'Unknown error')}")
            
            if data.get('errors'):
                print(f"  ⚠️  Errors: {len(data['errors'])}")
                
            return True
                
        else:
            print(f"  ❌ Market data fetching failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Market data test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_data_operations():
    """Test various market data operations."""
    print("🔄 Testing Market Data Operations...")
    
    try:
        fetcher = MarketDataFetcher()
        
        # Test market summary
        result = await fetcher.execute(operation="get_market_summary")
        
        if result.is_success:
            data = result.data
            indices = data.get('indices', {})
            print(f"  📈 Market indices: {len(indices)} fetched")
            print(f"  🕒 Market status: {data.get('market_status', 'unknown')}")
            
            # Show a couple of indices
            for symbol, index_data in list(indices.items())[:2]:
                if 'error' not in index_data:
                    price = index_data.get('price', 'N/A')
                    change = index_data.get('change', 0)
                    print(f"  📊 {symbol}: {price} ({change:+.2f})")
        else:
            print(f"  ⚠️  Market summary failed: {result.error_message}")
        
        # Test symbol search
        result = await fetcher.execute(operation="search_symbols", query="app")
        
        if result.is_success:
            data = result.data
            matches = data.get('matches', [])
            print(f"  🔍 Symbol search for 'app': {len(matches)} matches")
            if matches:
                print(f"  🎯 Matches: {', '.join(matches[:5])}")
        else:
            print(f"  ⚠️  Symbol search failed: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Market data operations test failed: {str(e)}")
        return False


async def main():
    """Run standalone tests."""
    print("🚀 Starting Standalone Tools Test Suite")
    print("=" * 50)
    print("ℹ️  Note: Testing tools without full database integration")
    
    tests = [
        ("RSS News Fetcher", test_rss_news_fetcher),
        ("Market Data Basic", test_market_data),
        ("Market Data Operations", test_market_data_operations)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} test CRASHED: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All standalone tests passed!")
    else:
        print(f"⚠️  {failed} tests failed. Check the implementation and dependencies.")
    
    print(f"⏰ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Instructions for full integration
    print("\n📝 Next Steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Set up database connection and environment variables")
    print("3. Run full integration tests")


if __name__ == "__main__":
    asyncio.run(main())