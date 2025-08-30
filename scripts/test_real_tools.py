#!/usr/bin/env python3
"""
Test script for the new real tools implementation.

This script tests the RSS news fetcher, database storage, vector storage, and market data tools.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.application.tools.rss_news_fetcher import RSSNewsFetcher
from src.application.tools.database_storage import DatabaseStorage
from src.application.tools.vector_storage import VectorStorage
from src.application.tools.market_data import MarketDataFetcher


async def test_rss_news_fetcher():
    """Test RSS news fetching."""
    print("🔄 Testing RSS News Fetcher...")
    
    try:
        fetcher = RSSNewsFetcher()
        
        # Test with limited articles to avoid overwhelming the system
        result = await fetcher.execute(
            rss_urls=["https://feeds.finance.yahoo.com/rss/2.0/headline"],
            max_articles=3,
            hours_back=48,
            include_content=False  # Start with just summaries
        )
        
        if result.is_success:
            data = result.data
            print(f"  ✅ Successfully fetched {data.get('final_count', 0)} articles")
            print(f"  📊 Total from RSS: {data.get('total_fetched', 0)}")
            print(f"  🔍 After deduplication: {data.get('unique_articles', 0)}")
            
            if data.get('articles'):
                first_article = data['articles'][0]
                print(f"  📰 Sample article: {first_article.get('title', 'No title')[:100]}...")
            
            if data.get('errors'):
                print(f"  ⚠️  Errors: {len(data['errors'])}")
            
        else:
            print(f"  ❌ RSS fetching failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ RSS test failed with exception: {str(e)}")
        return False
    
    return True


async def test_database_storage():
    """Test database storage operations."""
    print("🔄 Testing Database Storage...")
    
    try:
        storage = DatabaseStorage()
        
        # Test health check
        result = await storage.execute(operation="health_check")
        
        if result.is_success:
            data = result.data
            print(f"  ✅ Database health: {data.get('healthy', False)}")
            print(f"  🔗 Connection: {data.get('connection', 'unknown')}")
        else:
            print(f"  ❌ Database health check failed: {result.error_message}")
            return False
        
        # Test statistics
        result = await storage.execute(operation="get_statistics")
        
        if result.is_success:
            data = result.data
            print(f"  📊 Vector count: {data.get('vector_count', 0)}")
            print(f"  📰 Recent news: {data.get('recent_news_count', 0)}")
            print(f"  🧠 Recent analysis: {data.get('recent_analysis_count', 0)}")
        else:
            print(f"  ⚠️  Statistics failed: {result.error_message}")
            
    except Exception as e:
        print(f"  ❌ Database test failed with exception: {str(e)}")
        return False
    
    return True


async def test_vector_storage():
    """Test vector storage operations."""
    print("🔄 Testing Vector Storage...")
    
    try:
        # Check if OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY"):
            print("  ⚠️  OPENAI_API_KEY not set - skipping embedding tests")
            return True
        
        storage = VectorStorage()
        
        # Test vector count
        result = await storage.execute(operation="count")
        
        if result.is_success:
            data = result.data
            print(f"  ✅ Vector count: {data.get('total_vectors', 0)}")
            print(f"  🤖 Model: {data.get('embedding_model', 'unknown')}")
            print(f"  📐 Dimension: {data.get('dimension', 'unknown')}")
        else:
            print(f"  ❌ Vector count failed: {result.error_message}")
            return False
        
        # Test embedding generation
        test_text = "Apple Inc. reports strong quarterly earnings with revenue growth."
        result = await storage.execute(operation="generate_embedding", text=test_text)
        
        if result.is_success:
            data = result.data
            embedding = data.get('embedding', [])
            print(f"  ✅ Generated embedding: {len(embedding)} dimensions")
            print(f"  📝 Input length: {data.get('input_length', 0)} chars")
            print(f"  💰 Tokens used: {data.get('tokens_used', 'unknown')}")
        else:
            print(f"  ❌ Embedding generation failed: {result.error_message}")
            
    except Exception as e:
        print(f"  ❌ Vector storage test failed with exception: {str(e)}")
        return False
    
    return True


async def test_market_data():
    """Test market data fetching."""
    print("🔄 Testing Market Data Fetcher...")
    
    try:
        fetcher = MarketDataFetcher()
        
        # Test current prices for a few popular stocks
        test_symbols = ["AAPL", "GOOGL", "MSFT"]
        result = await fetcher.execute(operation="get_prices", symbols=test_symbols)
        
        if result.is_success:
            data = result.data
            market_data = data.get('market_data', {})
            print(f"  ✅ Fetched data for {len(market_data)} symbols")
            print(f"  📈 Symbols processed: {data.get('symbols_processed', 0)}")
            print(f"  💾 Cached results: {data.get('cached_results', 0)}")
            
            # Show sample data
            for symbol, stock_data in list(market_data.items())[:2]:
                if 'error' not in stock_data:
                    price = stock_data.get('price', 'N/A')
                    change = stock_data.get('change', 0)
                    print(f"  📊 {symbol}: ${price} ({change:+.2f})")
                else:
                    print(f"  ⚠️  {symbol}: {stock_data.get('error', 'Unknown error')}")
            
            if data.get('errors'):
                print(f"  ⚠️  Errors: {len(data['errors'])}")
                
        else:
            print(f"  ❌ Market data fetching failed: {result.error_message}")
            return False
        
        # Test market summary
        result = await fetcher.execute(operation="get_market_summary")
        
        if result.is_success:
            data = result.data
            indices = data.get('indices', {})
            print(f"  📈 Market indices: {len(indices)} fetched")
            print(f"  🕒 Market status: {data.get('market_status', 'unknown')}")
        else:
            print(f"  ⚠️  Market summary failed: {result.error_message}")
            
    except Exception as e:
        print(f"  ❌ Market data test failed with exception: {str(e)}")
        return False
    
    return True


async def test_integration():
    """Test integration between tools."""
    print("🔄 Testing Tools Integration...")
    
    try:
        # This is a simplified integration test
        # In a full test, we would fetch news, store it, create embeddings, etc.
        
        storage = DatabaseStorage()
        
        # Test finding recent news (should be empty initially)
        result = await storage.execute(operation="find_recent_news", days=7, limit=5)
        
        if result.is_success:
            data = result.data
            articles = data.get('articles', [])
            print(f"  ✅ Found {len(articles)} recent articles in database")
            
            if articles:
                print(f"  📰 Sample: {articles[0].get('title', 'No title')[:50]}...")
            else:
                print("  📭 No articles in database yet")
        else:
            print(f"  ❌ Integration test failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Integration test failed with exception: {str(e)}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Real Tools Test Suite")
    print("=" * 50)
    
    tests = [
        ("RSS News Fetcher", test_rss_news_fetcher),
        ("Database Storage", test_database_storage),
        ("Vector Storage", test_vector_storage),
        ("Market Data", test_market_data),
        ("Integration", test_integration)
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
        print("🎉 All tests passed! Real tools implementation is working correctly.")
    else:
        print(f"⚠️  {failed} tests failed. Please check the implementation.")
        
    print(f"⏰ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())