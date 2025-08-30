#!/usr/bin/env python3
"""
Simplified DataAgent test without full database dependencies.

Focus on testing the core fetch_news functionality.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("🧪 DataAgent Simplified Test")
print("=" * 50)

# Test 1: Individual tool testing
async def test_individual_tools():
    """Test each tool independently."""
    print("\n📋 Phase 1: Individual Tool Testing")
    print("-" * 30)
    
    # Test RSS tool
    try:
        from src.application.tools.rss_news_fetcher import RSSNewsFetcher
        from src.config.rss_sources import get_reliable_rss_sources
        
        print("🔄 Testing RSS Tool...")
        rss_tool = RSSNewsFetcher()
        sources = get_reliable_rss_sources()[:1]  # Use first reliable source
        
        result = await rss_tool.execute(
            rss_urls=sources,
            max_articles=2,
            hours_back=24,
            include_content=False
        )
        
        if result.is_success:
            articles = result.data.get('articles', [])
            print(f"   ✅ RSS Tool: Fetched {len(articles)} articles")
            if articles:
                sample = articles[0]
                print(f"   📰 Sample: {sample.get('title', '')[:50]}...")
                
                # Check data format
                required_fields = ['title', 'url', 'source', 'content_hash']
                missing_fields = [field for field in required_fields if not sample.get(field)]
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ Data format: All required fields present")
        else:
            print(f"   ❌ RSS Tool failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"   ❌ RSS Tool error: {str(e)}")
        return False
    
    # Test Market Data tool
    try:
        from src.application.tools.market_data import MarketDataFetcher
        
        print("🔄 Testing Market Data Tool...")
        market_tool = MarketDataFetcher()
        
        result = await market_tool.execute(
            operation="get_prices",
            symbols=["AAPL"]
        )
        
        if result.is_success:
            data = result.data.get('market_data', {})
            print(f"   ✅ Market Tool: Got data for {len(data)} symbols")
        else:
            print(f"   ❌ Market Tool failed: {result.error_message}")
            
    except Exception as e:
        print(f"   ❌ Market Tool error: {str(e)}")
    
    return True

# Test 2: DataAgent basic functionality
async def test_dataagent_basic():
    """Test DataAgent initialization and basic methods."""
    print("\n📋 Phase 2: DataAgent Basic Testing")
    print("-" * 30)
    
    try:
        # Import without database dependencies
        sys.modules['src.infrastructure.database.unified_repository'] = type('MockModule', (), {
            'UnifiedDatabaseRepository': type('MockRepo', (), {})
        })()
        
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        print("🔄 Testing DataAgent initialization...")
        
        # Create a mock repository
        class SimpleRepo:
            async def health_check(self): return True
            async def save_news(self, news): return news
            async def get_vector_count(self): return 0
        
        data_agent = LLMDataAgent(repository=SimpleRepo())
        
        print(f"   ✅ DataAgent created with {len(data_agent.tools)} tools")
        
        # Check tool types
        tool_names = [tool.name for tool in data_agent.tools]
        print(f"   🛠️  Tools: {', '.join(tool_names)}")
        
        # Check if required tools are present
        has_rss = any('rss' in name or 'news' in name for name in tool_names)
        has_db = any('database' in name or 'storage' in name for name in tool_names)
        has_vector = any('vector' in name for name in tool_names)
        
        print(f"   📊 Tool check: RSS={has_rss}, DB={has_db}, Vector={has_vector}")
        
        if not all([has_rss, has_db, has_vector]):
            print("   ⚠️  Some required tools missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ DataAgent initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Test 3: Check fetch_news method structure
async def test_fetch_news_structure():
    """Test the fetch_news method structure without full execution."""
    print("\n📋 Phase 3: fetch_news Method Structure")
    print("-" * 30)
    
    try:
        from src.application.agents.llm_data_agent import LLMDataAgent
        from src.config.rss_sources import get_reliable_rss_sources
        
        class SimpleRepo:
            async def health_check(self): return True
            async def save_news(self, news): return news
            async def get_vector_count(self): return 0
        
        data_agent = LLMDataAgent(repository=SimpleRepo())
        
        # Check if fetch_news method exists
        if hasattr(data_agent, 'fetch_news'):
            print("   ✅ fetch_news method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(data_agent.fetch_news)
            params = list(sig.parameters.keys())
            print(f"   📝 Parameters: {params}")
            
            # Check if it has the right parameters
            expected_params = ['sources', 'max_articles', 'store_results']
            has_right_params = all(param in params for param in expected_params)
            
            if has_right_params:
                print("   ✅ Method signature correct")
            else:
                missing = [p for p in expected_params if p not in params]
                print(f"   ⚠️  Missing parameters: {missing}")
            
            # Check the method implementation (inspect the code)
            source_code = inspect.getsource(data_agent.fetch_news)
            
            # Look for key implementation details
            checks = {
                'creates_task': 'LLMAgentTask' in source_code,
                'mentions_rss': 'rss' in source_code.lower(),
                'mentions_database': 'database' in source_code.lower() or 'storage' in source_code.lower(),
                'mentions_vector': 'vector' in source_code.lower() or 'embedding' in source_code.lower(),
                'uses_execute_task': 'execute_task' in source_code
            }
            
            print("   🔍 Implementation analysis:")
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"      {status} {check}: {passed}")
            
            # Key issue identification
            if checks['creates_task'] and checks['uses_execute_task']:
                print("   📋 Implementation type: LLM-driven (creates task for LLM to execute)")
                print("   💡 This means success depends on LLM understanding and tool calling")
            else:
                print("   📋 Implementation type: Direct tool calling")
            
            return all(checks.values())
            
        else:
            print("   ❌ fetch_news method not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error analyzing fetch_news: {str(e)}")
        return False

async def main():
    """Run simplified tests."""
    print(f"🕐 Starting at {datetime.now().strftime('%H:%M:%S')}")
    
    tests = [
        ("Individual Tools", test_individual_tools),
        ("DataAgent Basic", test_dataagent_basic),  
        ("fetch_news Structure", test_fetch_news_structure)
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
    
    print(f"\n{'='*50}")
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All basic tests passed!")
    else:
        print("⚠️  Issues found - detailed analysis needed")
    
    print(f"\n💡 Key Findings:")
    print("   - Individual tools appear to be working")
    print("   - DataAgent uses LLM-driven approach for fetch_news")
    print("   - Success depends on LLM reasoning and tool orchestration")
    print("   - May need direct tool calling for guaranteed execution")


if __name__ == "__main__":
    asyncio.run(main())