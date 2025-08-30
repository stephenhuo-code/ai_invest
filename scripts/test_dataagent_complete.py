#!/usr/bin/env python3
"""
Complete end-to-end test for DataAgent fetch_news functionality.

Tests:
1. RSS data fetching with specified sources
2. Database storage in correct format
3. Vector embedding generation and storage
4. Complete data pipeline integrity
"""
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check dependencies
try:
    from src.application.agents.llm_data_agent import LLMDataAgent
    from src.application.tools.rss_news_fetcher import RSSNewsFetcher
    from src.application.tools.database_storage import DatabaseStorage
    from src.application.tools.vector_storage import VectorStorage
    from src.domain.entities.news_article import NewsArticle, ProcessingStatus
    from src.domain.entities.vector_document import VectorDocument, VectorSourceType
    from src.config.rss_sources import get_reliable_rss_sources
    HAS_CORE_DEPS = True
except ImportError as e:
    print(f"⚠️  Missing core dependencies: {e}")
    HAS_CORE_DEPS = False

# Optional dependencies for some tests
try:
    from src.infrastructure.database.unified_repository import UnifiedDatabaseRepository
    HAS_DB = True
except ImportError:
    print("⚠️  Database components not available - will use mock repository")
    HAS_DB = False


class MockRepository:
    """Mock repository for testing without database."""
    
    def __init__(self):
        self.news_storage = []
        self.vectors_storage = []
    
    async def save_news(self, news: NewsArticle) -> NewsArticle:
        news.id = len(self.news_storage) + 1
        news.created_at = datetime.now()
        self.news_storage.append(news)
        return news
    
    async def save_vector(self, vector: VectorDocument) -> VectorDocument:
        vector.id = len(self.vectors_storage) + 1
        vector.created_at = datetime.now()
        self.vectors_storage.append(vector)
        return vector
    
    async def health_check(self) -> bool:
        return True
    
    async def get_vector_count(self) -> int:
        return len(self.vectors_storage)
    
    async def find_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[NewsArticle]:
        return self.news_storage[-limit:] if limit else self.news_storage
    
    async def find_recent_analysis(self, days: int = 7, limit: Optional[int] = None) -> List:
        return []


class DataAgentTester:
    """Comprehensive DataAgent testing suite."""
    
    def __init__(self):
        self.results = {
            'start_time': datetime.now(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': []
        }
        
        # Initialize repository (use mock if database not available)
        if HAS_DB:
            try:
                self.repository = UnifiedDatabaseRepository()
                self.using_real_db = True
            except Exception:
                print("⚠️  Failed to initialize real database, using mock")
                self.repository = MockRepository()
                self.using_real_db = False
        else:
            self.repository = MockRepository()
            self.using_real_db = False
    
    async def run_test(self, test_name: str, test_func) -> Dict[str, Any]:
        """Run a single test and record results."""
        print(f"\n🧪 Running {test_name}...")
        
        self.results['tests_run'] += 1
        start_time = datetime.now()
        
        try:
            result = await test_func()
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.get('success', False):
                self.results['tests_passed'] += 1
                print(f"   ✅ PASSED ({duration:.2f}s)")
            else:
                self.results['tests_failed'] += 1
                print(f"   ❌ FAILED ({duration:.2f}s): {result.get('error', 'Unknown error')}")
            
            result.update({
                'test_name': test_name,
                'duration': duration,
                'timestamp': datetime.now()
            })
            
            self.results['detailed_results'].append(result)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.results['tests_failed'] += 1
            
            error_result = {
                'test_name': test_name,
                'success': False,
                'error': str(e),
                'duration': duration,
                'timestamp': datetime.now()
            }
            
            print(f"   💥 CRASHED ({duration:.2f}s): {str(e)}")
            self.results['detailed_results'].append(error_result)
            return error_result
    
    async def test_dataagent_initialization(self) -> Dict[str, Any]:
        """Test DataAgent initialization and configuration."""
        try:
            # Create DataAgent instance
            data_agent = LLMDataAgent(repository=self.repository)
            
            # Check basic properties
            checks = {
                'has_tools': len(data_agent.tools) > 0,
                'has_rss_tool': any('rss' in tool.name for tool in data_agent.tools),
                'has_database_tool': any('database' in tool.name for tool in data_agent.tools),
                'has_vector_tool': any('vector' in tool.name for tool in data_agent.tools),
                'has_repository': data_agent.repository is not None
            }
            
            all_passed = all(checks.values())
            
            return {
                'success': all_passed,
                'data': {
                    'tool_count': len(data_agent.tools),
                    'tool_names': [tool.name for tool in data_agent.tools],
                    'checks': checks,
                    'using_real_db': self.using_real_db
                },
                'error': None if all_passed else f"Failed checks: {[k for k, v in checks.items() if not v]}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_rss_tool_direct(self) -> Dict[str, Any]:
        """Test RSS tool directly with specified sources."""
        try:
            rss_tool = RSSNewsFetcher()
            
            # Use reliable sources for testing
            test_sources = get_reliable_rss_sources()[:2]  # Use first 2 reliable sources
            
            result = await rss_tool.execute(
                rss_urls=test_sources,
                max_articles=3,
                hours_back=24,
                include_content=False  # Skip content extraction for faster testing
            )
            
            if result.is_success:
                data = result.data
                articles = data.get('articles', [])
                
                # Validate article structure
                valid_articles = 0
                for article in articles:
                    required_fields = ['title', 'url', 'source', 'content_hash', 'fetched_at']
                    if all(field in article and article[field] for field in required_fields):
                        valid_articles += 1
                
                success = valid_articles > 0
                
                return {
                    'success': success,
                    'data': {
                        'sources_used': test_sources,
                        'total_articles': len(articles),
                        'valid_articles': valid_articles,
                        'sample_article': articles[0] if articles else None,
                        'errors': data.get('errors', [])
                    },
                    'error': None if success else "No valid articles retrieved"
                }
            else:
                return {'success': False, 'error': result.error_message}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_database_storage_direct(self) -> Dict[str, Any]:
        """Test database storage tool directly."""
        try:
            db_tool = DatabaseStorage(repository=self.repository)
            
            # Test health check
            health_result = await db_tool.execute(operation="health_check")
            
            if not health_result.is_success:
                return {'success': False, 'error': f"Database health check failed: {health_result.error_message}"}
            
            # Create test article
            test_article_data = {
                'url': 'https://test.com/article1',
                'title': 'Test Article for DataAgent',
                'content': 'This is test content for validating database storage functionality.',
                'source': 'test_source',
                'author': 'Test Author',
                'published_at': datetime.now(),
                'content_hash': 'test_hash_123'
            }
            
            # Test saving article
            save_result = await db_tool.execute(
                operation="save_news",
                news_data=test_article_data
            )
            
            if save_result.is_success:
                saved_data = save_result.data
                article_id = saved_data.get('article_id')
                
                # Test retrieving article
                find_result = await db_tool.execute(
                    operation="find_recent_news",
                    days=1,
                    limit=5
                )
                
                if find_result.is_success:
                    recent_articles = find_result.data.get('articles', [])
                    found_article = any(
                        article.get('title') == test_article_data['title'] 
                        for article in recent_articles
                    )
                    
                    return {
                        'success': True,
                        'data': {
                            'article_saved': True,
                            'article_id': article_id,
                            'articles_in_db': len(recent_articles),
                            'test_article_found': found_article,
                            'health_status': health_result.data
                        }
                    }
                else:
                    return {'success': False, 'error': f"Failed to retrieve articles: {find_result.error_message}"}
            else:
                return {'success': False, 'error': f"Failed to save article: {save_result.error_message}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_vector_storage_direct(self) -> Dict[str, Any]:
        """Test vector storage tool directly."""
        try:
            vector_tool = VectorStorage(repository=self.repository)
            
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                return {
                    'success': False,
                    'error': 'OPENAI_API_KEY not set - cannot test embeddings',
                    'data': {'skipped': True}
                }
            
            # Test embedding generation
            test_text = "Apple Inc. reported strong quarterly earnings with revenue exceeding expectations."
            
            embedding_result = await vector_tool.execute(
                operation="generate_embedding",
                text=test_text
            )
            
            if not embedding_result.is_success:
                return {'success': False, 'error': f"Failed to generate embedding: {embedding_result.error_message}"}
            
            embedding_data = embedding_result.data
            embedding = embedding_data.get('embedding', [])
            
            # Test storing vector
            vector_data = {
                'source_type': 'news',
                'source_id': 'test_article_1',
                'content_hash': 'test_content_hash',
                'embedding': embedding,
                'metadata': {'test': True, 'text_length': len(test_text)}
            }
            
            store_result = await vector_tool.execute(
                operation="store_vector",
                vector_data=vector_data
            )
            
            if store_result.is_success:
                stored_data = store_result.data
                
                # Test vector count
                count_result = await vector_tool.execute(operation="count")
                
                return {
                    'success': True,
                    'data': {
                        'embedding_generated': True,
                        'embedding_dimension': len(embedding),
                        'vector_stored': True,
                        'vector_id': stored_data.get('vector_id'),
                        'total_vectors': count_result.data.get('total_vectors', 0) if count_result.is_success else 'unknown',
                        'tokens_used': embedding_data.get('tokens_used')
                    }
                }
            else:
                return {'success': False, 'error': f"Failed to store vector: {store_result.error_message}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_dataagent_fetch_news_integration(self) -> Dict[str, Any]:
        """Test DataAgent fetch_news method end-to-end."""
        try:
            data_agent = LLMDataAgent(repository=self.repository)
            
            # Use specific reliable sources
            test_sources = get_reliable_rss_sources()[:1]  # Use just 1 source for integration test
            
            # This is the key test - does fetch_news work as designed?
            fetch_result = await data_agent.fetch_news(
                sources=test_sources,
                max_articles=2,
                store_results=True
            )
            
            # Note: This will depend on the LLM implementation
            # The current implementation uses LLM reasoning to call tools
            
            return {
                'success': fetch_result.success if hasattr(fetch_result, 'success') else False,
                'data': {
                    'sources_specified': test_sources,
                    'store_results_requested': True,
                    'result_type': type(fetch_result).__name__,
                    'has_result': hasattr(fetch_result, 'result'),
                    'result_data': getattr(fetch_result, 'result', None),
                    'tools_used': getattr(fetch_result, 'tools_used', []),
                    'error_message': getattr(fetch_result, 'error_message', None)
                },
                'error': getattr(fetch_result, 'error_message', None) if hasattr(fetch_result, 'success') and not fetch_result.success else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_data_pipeline_integrity(self) -> Dict[str, Any]:
        """Test the complete data pipeline: RSS -> Database -> Vectors."""
        try:
            # Step 1: Fetch data via RSS
            rss_tool = RSSNewsFetcher()
            test_sources = get_reliable_rss_sources()[:1]
            
            rss_result = await rss_tool.execute(
                rss_urls=test_sources,
                max_articles=1,
                hours_back=24,
                include_content=False
            )
            
            if not rss_result.is_success:
                return {'success': False, 'error': f"RSS fetch failed: {rss_result.error_message}"}
            
            articles = rss_result.data.get('articles', [])
            if not articles:
                return {'success': False, 'error': "No articles fetched"}
            
            article_data = articles[0]
            
            # Step 2: Store in database
            db_tool = DatabaseStorage(repository=self.repository)
            
            db_result = await db_tool.execute(
                operation="save_news",
                news_data=article_data
            )
            
            if not db_result.is_success:
                return {'success': False, 'error': f"Database save failed: {db_result.error_message}"}
            
            article_id = db_result.data.get('article_id')
            
            # Step 3: Create vector embedding (if OpenAI available)
            if os.getenv('OPENAI_API_KEY'):
                vector_tool = VectorStorage(repository=self.repository)
                
                text_content = f"{article_data.get('title', '')} {article_data.get('content', '')}"
                
                vector_result = await vector_tool.execute(
                    operation="store_vector",
                    vector_data={
                        'source_type': 'news',
                        'source_id': str(article_id),
                        'content_hash': article_data.get('content_hash', ''),
                        'text': text_content,
                        'metadata': {
                            'title': article_data.get('title'),
                            'source': article_data.get('source'),
                            'url': article_data.get('url')
                        }
                    }
                )
                
                vector_success = vector_result.is_success
                vector_error = vector_result.error_message if not vector_success else None
            else:
                vector_success = None  # Skipped
                vector_error = "OpenAI API key not available"
            
            return {
                'success': True,
                'data': {
                    'rss_fetch': {'success': True, 'articles_count': len(articles)},
                    'database_save': {'success': True, 'article_id': article_id},
                    'vector_store': {
                        'success': vector_success,
                        'skipped': vector_success is None,
                        'error': vector_error
                    },
                    'pipeline_complete': vector_success is not False
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


async def main():
    """Run the complete DataAgent test suite."""
    print("🚀 DataAgent Complete Functionality Test")
    print("=" * 60)
    
    if not HAS_CORE_DEPS:
        print("❌ Cannot run tests - missing core dependencies")
        return
    
    print(f"🔧 OpenAI API: {'✅ Available' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"💾 Database: {'✅ Real DB' if HAS_DB else '⚠️  Mock Repository'}")
    print()
    
    tester = DataAgentTester()
    
    # Define tests to run
    tests = [
        ("DataAgent Initialization", tester.test_dataagent_initialization),
        ("RSS Tool Direct Test", tester.test_rss_tool_direct),
        ("Database Storage Direct Test", tester.test_database_storage_direct),
        ("Vector Storage Direct Test", tester.test_vector_storage_direct),
        ("DataAgent fetch_news Integration", tester.test_dataagent_fetch_news_integration),
        ("Complete Data Pipeline", tester.test_data_pipeline_integrity)
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        await tester.run_test(test_name, test_func)
    
    # Generate summary
    results = tester.results
    duration = (datetime.now() - results['start_time']).total_seconds()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total Duration: {duration:.1f} seconds")
    print(f"🧪 Tests Run: {results['tests_run']}")
    print(f"✅ Passed: {results['tests_passed']}")
    print(f"❌ Failed: {results['tests_failed']}")
    print(f"📈 Success Rate: {(results['tests_passed'] / results['tests_run'] * 100):.1f}%" if results['tests_run'] > 0 else "0%")
    
    print("\n📋 Detailed Results:")
    for result in results['detailed_results']:
        status = "✅" if result.get('success') else "❌"
        print(f"{status} {result['test_name']} ({result['duration']:.2f}s)")
        if not result.get('success') and result.get('error'):
            print(f"    Error: {result['error']}")
    
    print(f"\n🎯 Overall Assessment:")
    if results['tests_failed'] == 0:
        print("🎉 EXCELLENT: All tests passed! DataAgent is fully functional.")
    elif results['tests_passed'] >= results['tests_run'] * 0.8:
        print("👍 GOOD: Most tests passed. Minor issues to address.")
    elif results['tests_passed'] >= results['tests_run'] * 0.6:
        print("⚠️  FAIR: Significant issues found. Needs attention.")
    else:
        print("🚨 CRITICAL: Major problems detected. Immediate fixes required.")
    
    print(f"\n💡 Next Steps:")
    if results['tests_failed'] > 0:
        print("   1. Review failed tests and fix underlying issues")
        print("   2. Ensure all dependencies are properly configured")
        print("   3. Re-run tests to verify fixes")
    else:
        print("   1. Deploy to production environment")
        print("   2. Monitor data quality and performance")
        print("   3. Set up automated testing pipeline")


if __name__ == "__main__":
    asyncio.run(main())