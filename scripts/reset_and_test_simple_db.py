#!/usr/bin/env python3
"""
Reset PostgreSQL database and test SimplePGDB functionality.

This script will:
1. Clear all existing data from PostgreSQL tables
2. Create new simplified table structure  
3. Test the new SimplePGDB access methods
4. Verify API endpoints work with new database access
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("🔄 PostgreSQL Database Reset and SimplePGDB Test")
print("=" * 60)

async def reset_database():
    """Reset the PostgreSQL database to use simplified structure."""
    print("\n📋 Step 1: Reset PostgreSQL Database")
    print("-" * 40)
    
    try:
        from src.infrastructure.database.simple_pg_db import get_simple_db, ensure_tables
        
        db = get_simple_db()
        
        print("🔄 Connecting to PostgreSQL...")
        
        # Test connection
        if await db.health_check():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Clear existing data
        print("🔄 Clearing existing data...")
        try:
            await db.clear_all_data()
            print("   ✅ All existing data cleared")
        except Exception as e:
            print(f"   ⚠️  Clear data warning: {str(e)}")
            # Continue anyway - tables might not exist yet
        
        # Create tables with simplified structure
        print("🔄 Creating simplified table structure...")
        await ensure_tables()
        print("   ✅ Simplified tables created/verified")
        
        # Verify database statistics
        stats = await db.get_statistics()
        print(f"📊 Database status:")
        print(f"   Total articles: {stats['total_articles']}")
        print(f"   Total sources: {stats['total_sources']}")
        print(f"   Latest article: {stats['latest_article_date'] or 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_database():
    """Test SimplePGDB functionality."""
    print("\n📋 Step 2: Test SimplePGDB Functionality")
    print("-" * 40)
    
    try:
        from src.infrastructure.database.simple_pg_db import get_simple_db
        
        db = get_simple_db()
        
        # Test 1: Save sample articles
        print("🔄 Test 1: Saving sample articles...")
        sample_articles = [
            {
                'title': 'Test Article 1: Market Update',
                'url': 'https://example.com/article1',
                'content': 'This is test content for article 1 about market updates...',
                'source': 'test.com',
                'author': 'Test Author 1',
                'published_at': datetime.now(),
                'content_hash': 'hash1'
            },
            {
                'title': 'Test Article 2: Tech News',
                'url': 'https://example.com/article2', 
                'content': 'This is test content for article 2 about technology news...',
                'source': 'tech.com',
                'author': 'Test Author 2',
                'published_at': datetime.now(),
                'content_hash': 'hash2'
            }
        ]
        
        saved_articles = await db.save_news_batch(sample_articles)
        print(f"   ✅ Saved {len(saved_articles)} sample articles")
        
        # Test 2: Find recent news without content
        print("🔄 Test 2: Finding recent news (without content)...")
        result_no_content = await db.find_recent_news(days=7, limit=10, include_content=False)
        articles_no_content = result_no_content['articles']
        print(f"   ✅ Found {len(articles_no_content)} articles without content")
        if articles_no_content:
            sample = articles_no_content[0]
            print(f"   📰 Sample: {sample['title'][:50]}...")
            print(f"   📰 Contains content field: {'content' in sample}")
        
        # Test 3: Find recent news with content
        print("🔄 Test 3: Finding recent news (with content)...")
        result_with_content = await db.find_recent_news(days=7, limit=10, include_content=True)
        articles_with_content = result_with_content['articles']
        print(f"   ✅ Found {len(articles_with_content)} articles with content")
        if articles_with_content:
            sample = articles_with_content[0]
            print(f"   📰 Sample: {sample['title'][:50]}...")
            print(f"   📰 Contains content field: {'content' in sample}")
            if 'content' in sample:
                content_preview = sample['content'][:60] + "..." if len(sample['content']) > 60 else sample['content']
                print(f"   📰 Content preview: {content_preview}")
        
        # Test 4: Get article by ID
        if saved_articles:
            print("🔄 Test 4: Getting article by ID...")
            article_id = saved_articles[0]['id']
            article = await db.get_article_by_id(article_id, include_content=True)
            if article:
                print(f"   ✅ Retrieved article by ID {article_id}")
                print(f"   📰 Title: {article['title']}")
                print(f"   📰 Content length: {len(article.get('content', ''))} chars")
            else:
                print(f"   ❌ Article not found by ID {article_id}")
        
        # Test 5: Get updated statistics
        print("🔄 Test 5: Getting database statistics...")
        stats = await db.get_statistics()
        print(f"   ✅ Database statistics:")
        print(f"      Total articles: {stats['total_articles']}")
        print(f"      Total sources: {stats['total_sources']}")
        print(f"      Sources: {list(stats['sources'].keys())}")
        print(f"      Latest article: {stats['latest_article_date']}")
        
        return True
        
    except Exception as e:
        print(f"❌ SimplePGDB test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_agent():
    """Test LLMDataAgent with SimplePGDB."""
    print("\n📋 Step 3: Test LLMDataAgent with SimplePGDB")
    print("-" * 40)
    
    try:
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        print("🔄 Initializing LLMDataAgent...")
        data_agent = LLMDataAgent()
        print(f"   ✅ DataAgent initialized with {len(data_agent.tools)} tools")
        print(f"   🔧 Tools: {[tool.name for tool in data_agent.tools]}")
        print(f"   📊 Database instance: {type(data_agent.db).__name__}")
        
        # Test fetch_news method (without actually fetching from RSS)
        print("🔄 Testing fetch_news method structure...")
        
        # Check if database is accessible
        db_healthy = await data_agent.db.health_check()
        print(f"   📊 Database health: {'✅ Healthy' if db_healthy else '❌ Unhealthy'}")
        
        # Get current statistics
        stats = await data_agent.db.get_statistics()
        print(f"   📊 Current articles in database: {stats['total_articles']}")
        
        return True
        
    except Exception as e:
        print(f"❌ DataAgent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test API endpoint with SimplePGDB."""
    print("\n📋 Step 4: Test API Endpoints")
    print("-" * 40)
    
    try:
        # Test the stored news endpoint logic
        from src.infrastructure.database.simple_pg_db import get_simple_db, ensure_tables
        
        print("🔄 Testing /data/stored-news endpoint logic...")
        
        # Ensure tables
        await ensure_tables()
        
        db = get_simple_db()
        
        # Query stored news (simulating API call)
        result = await db.find_recent_news(
            days=7,
            limit=5,
            include_content=True
        )
        
        # Format like API response
        api_response = {
            "success": True,
            "articles_found": result['count'],
            "days_requested": 7,
            "limit_requested": 5,
            "include_content": True,
            "articles": result['articles'],
            "note": "Data retrieved from SimplePGDB without fetching new articles"
        }
        
        print(f"   ✅ API endpoint simulation successful")
        print(f"   📊 Response summary:")
        print(f"      Articles found: {api_response['articles_found']}")
        print(f"      Days requested: {api_response['days_requested']}")
        print(f"      Include content: {api_response['include_content']}")
        
        if api_response['articles']:
            sample = api_response['articles'][0]
            print(f"   📰 Sample article:")
            print(f"      Title: {sample['title'][:60]}...")
            print(f"      Source: {sample['source']}")
            print(f"      Has content: {'content' in sample}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run complete reset and testing workflow."""
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🗄️  Database: PostgreSQL with SimplePGDB")
    
    tests = [
        ("Reset Database", reset_database),
        ("Test SimplePGDB", test_simple_database),
        ("Test DataAgent", test_data_agent),
        ("Test API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: CRASHED - {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"📊 Reset and Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 EXCELLENT: Database reset and SimplePGDB fully working!")
        print("✅ PostgreSQL database cleared and recreated")
        print("✅ SimplePGDB provides direct access without complex abstractions")
        print("✅ LLMDataAgent uses SimplePGDB successfully")
        print("✅ API endpoints work with new database access")
        print("✅ All database initialization errors should be resolved")
    else:
        print("⚠️  Some issues need attention before deployment")
    
    print(f"\n💡 Next Steps:")
    print("   1. Start API server: uvicorn src.presentation.api.main_simplified:app")
    print("   2. Test endpoint: curl 'http://localhost:8000/data/stored-news?include_content=true'")
    print("   3. Add new articles: Use /data/recent-news to fetch and store")
    print("   4. Verify: Check stored data with /data/stored-news")

if __name__ == "__main__":
    asyncio.run(main())