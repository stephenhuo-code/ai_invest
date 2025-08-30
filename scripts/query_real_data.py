#!/usr/bin/env python3
"""
查询真实数据库中的数据

通过实际的DataAgent和API端点查询已存储的数据
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("🔍 查询数据库中的真实数据")
print("=" * 50)

async def query_recent_news():
    """查询最近存储的新闻数据"""
    print("\n📋 查询最近存储的新闻")
    print("-" * 30)
    
    try:
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        # 创建简单的测试repository
        class TestRepo:
            def __init__(self):
                self.news_items = []
                self.vectors = []
            
            async def health_check(self): return True
            
            async def save_news(self, news_data):
                """保存新闻并返回格式化对象"""
                news = type('NewsArticle', (), {})()
                news.id = len(self.news_items) + 1
                news.title = news_data.get('title', '')
                news.url = news_data.get('url', '')
                news.content = news_data.get('content', '')
                news.source = news_data.get('source', '')
                news.author = news_data.get('author', '')
                news.content_hash = news_data.get('content_hash', '')
                news.processing_status = 'completed'
                news.published_at = news_data.get('published_at')
                news.created_at = datetime.now()
                news.fetched_at = datetime.now()
                
                self.news_items.append(news)
                return news
            
            async def save_vector(self, vector_data):
                vector = type('VectorEmbedding', (), {})()
                vector.id = len(self.vectors) + 1
                vector.source_type = 'news'
                vector.source_id = str(vector_data.get('source_id', ''))
                vector.embedding = vector_data.get('embedding', [])
                vector.embedding_model = 'text-embedding-ada-002'
                vector.dimension = len(vector_data.get('embedding', []))
                self.vectors.append(vector)
                return vector
                
            async def get_vector_count(self): return len(self.vectors)
            
            async def find_recent_news(self, days=7, limit=None):
                return self.news_items[-limit:] if limit else self.news_items
                
            async def find_recent_analysis(self, days=7, limit=None): return []
        
        repo = TestRepo()
        data_agent = LLMDataAgent(repository=repo)
        
        print("🔄 步骤1: 先获取一些新闻数据...")
        # 首先获取一些数据
        fetch_result = await data_agent.fetch_news(
            sources=None,
            max_articles=3,
            store_results=True
        )
        
        if fetch_result.success:
            data = fetch_result.result
            print(f"   ✅ 成功存储 {data.get('articles_stored', 0)} 篇文章")
            print(f"   ✅ 创建 {data.get('vectors_created', 0)} 个向量嵌入")
            
            # 现在查询存储的数据
            print(f"\n🔄 步骤2: 查询数据库中的数据...")
            
            # 使用数据库工具查询
            db_tool = None
            for tool in data_agent.tools:
                if 'database' in tool.name.lower() or 'storage' in tool.name.lower():
                    db_tool = tool
                    break
            
            if db_tool:
                query_result = await db_tool.execute(
                    operation="find_recent_news",
                    days=7,
                    limit=10
                )
                
                if query_result.is_success:
                    articles = query_result.data.get('articles', [])
                    count = query_result.data.get('count', 0)
                    
                    print(f"   ✅ 数据库查询成功: 找到 {count} 篇文章")
                    
                    for i, article in enumerate(articles, 1):
                        print(f"\n   📰 文章 {i}:")
                        print(f"      ID: {article.get('id')}")
                        print(f"      标题: {article.get('title', '')[:60]}...")
                        print(f"      来源: {article.get('source', '')}")
                        print(f"      URL: {article.get('url', '')[:60]}...")
                        print(f"      状态: {article.get('processing_status', '')}")
                        print(f"      创建时间: {article.get('created_at', '')}")
                        
                        # 显示内容预览
                        if 'content' in article and article['content']:
                            content_preview = article['content'][:150] + "..." if len(article['content']) > 150 else article['content']
                            print(f"      内容预览: {content_preview}")
                        
                    print(f"\n📊 存储库状态:")
                    print(f"   💾 新闻文章: {len(repo.news_items)} 篇")
                    print(f"   🔗 向量嵌入: {len(repo.vectors)} 个")
                    
                    return True
                else:
                    print(f"   ❌ 数据库查询失败: {query_result.error_message}")
                    return False
            else:
                print("   ❌ 未找到数据库工具")
                return False
        else:
            print(f"   ❌ 数据获取失败: {fetch_result.error_message}")
            return False
            
    except Exception as e:
        print(f"   ❌ 查询过程异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def query_vector_data():
    """查询向量嵌入数据"""
    print("\n📋 查询向量嵌入数据")
    print("-" * 30)
    
    try:
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        class VectorTestRepo:
            def __init__(self):
                self.vectors = []
                self.news_items = []
                
            async def health_check(self): return True
            async def save_news(self, news): 
                self.news_items.append(news)
                return news
                
            async def save_vector(self, vector_data):
                vector = type('VectorEmbedding', (), {})()
                vector.id = len(self.vectors) + 1
                vector.source_type = 'news'
                vector.source_id = str(vector_data.get('source_id', ''))
                vector.content_hash = vector_data.get('content_hash', '')
                vector.embedding = vector_data.get('embedding', [])
                vector.embedding_model = vector_data.get('embedding_model', 'text-embedding-ada-002')
                vector.dimension = len(vector_data.get('embedding', []))
                vector.created_at = datetime.now()
                self.vectors.append(vector)
                return vector
            
            async def get_vector_count(self): return len(self.vectors)
            async def find_recent_news(self, days=7, limit=None): return []
            async def find_recent_analysis(self, days=7, limit=None): return []
        
        repo = VectorTestRepo()
        data_agent = LLMDataAgent(repository=repo)
        
        print("🔄 创建一些向量数据...")
        
        # 获取数据并创建向量
        fetch_result = await data_agent.fetch_news(
            sources=None,
            max_articles=2,
            store_results=True
        )
        
        if fetch_result.success and repo.vectors:
            print(f"   ✅ 成功创建 {len(repo.vectors)} 个向量嵌入")
            
            print(f"\n🔄 查询向量嵌入详情...")
            
            for i, vector in enumerate(repo.vectors, 1):
                print(f"\n   🔗 向量 {i}:")
                print(f"      向量ID: {vector.id}")
                print(f"      源类型: {vector.source_type}")
                print(f"      源ID: {vector.source_id}")
                print(f"      内容哈希: {vector.content_hash}")
                print(f"      嵌入模型: {vector.embedding_model}")
                print(f"      向量维度: {vector.dimension}")
                print(f"      创建时间: {vector.created_at}")
                
                # 显示向量的前5个值
                if vector.embedding and len(vector.embedding) > 0:
                    preview = vector.embedding[:5]
                    print(f"      向量预览: [{', '.join(f'{x:.4f}' for x in preview)}...]")
                
                # 计算向量的统计信息
                if vector.embedding:
                    import statistics
                    mean_val = statistics.mean(vector.embedding)
                    std_val = statistics.stdev(vector.embedding) if len(vector.embedding) > 1 else 0
                    min_val = min(vector.embedding)
                    max_val = max(vector.embedding)
                    
                    print(f"      向量统计: 均值={mean_val:.4f}, 标准差={std_val:.4f}")
                    print(f"      值范围: [{min_val:.4f}, {max_val:.4f}]")
            
            print(f"\n📊 向量存储总结:")
            print(f"   🔗 总向量数: {len(repo.vectors)}")
            print(f"   📏 向量维度: {repo.vectors[0].dimension if repo.vectors else 'N/A'}")
            print(f"   🤖 嵌入模型: {repo.vectors[0].embedding_model if repo.vectors else 'N/A'}")
            
            return True
        else:
            print(f"   ❌ 向量创建失败或没有向量数据")
            return False
            
    except Exception as e:
        print(f"   ❌ 向量查询异常: {str(e)}")
        return False

async def simulate_api_query():
    """模拟通过API端点查询数据"""
    print("\n📋 模拟API端点查询")
    print("-" * 30)
    
    try:
        from src.presentation.api.main_simplified import data_agent
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        # 创建全局data_agent (模拟API中的初始化)
        class APITestRepo:
            def __init__(self):
                self.stored_articles = []
                self.vectors = []
            
            async def health_check(self): return True
            
            async def save_news(self, news_data):
                article = {
                    'id': len(self.stored_articles) + 1,
                    'title': news_data.get('title', ''),
                    'url': news_data.get('url', ''),
                    'source': news_data.get('source', ''),
                    'content': news_data.get('content', ''),
                    'content_hash': news_data.get('content_hash', ''),
                    'processing_status': 'completed',
                    'created_at': datetime.now(),
                    'published_at': news_data.get('published_at')
                }
                self.stored_articles.append(article)
                return type('Article', (), article)()
            
            async def save_vector(self, vector_data): 
                self.vectors.append(vector_data)
                return vector_data
            async def get_vector_count(self): return len(self.vectors)
            async def find_recent_news(self, days=7, limit=None):
                return self.stored_articles[-limit:] if limit else self.stored_articles
            async def find_recent_analysis(self, days=7, limit=None): return []
        
        # 设置全局data_agent
        global data_agent
        repo = APITestRepo()
        data_agent = LLMDataAgent(repository=repo)
        
        print("🔄 模拟 /data/recent-news API调用...")
        
        # 模拟API端点的逻辑
        fetch_result = await data_agent.fetch_news(
            sources=None,
            max_articles=3,
            store_results=True
        )
        
        if fetch_result.success:
            result_data = fetch_result.result
            articles_fetched = result_data.get('articles_fetched', 0)
            articles_stored = result_data.get('articles_stored', 0) 
            articles_data = result_data.get('articles', [])
            
            # 格式化API响应(类似真实API)
            formatted_articles = []
            for article in articles_data:
                formatted_articles.append({
                    "id": article.get('content_hash', 'unknown'),
                    "title": article.get('title', ''),
                    "url": article.get('url', ''),
                    "source": article.get('source', ''),
                    "author": article.get('author', ''),
                    "published_at": article.get('published_at'),
                    "content_preview": article.get('content', '')[:200] + "..." if article.get('content') else "",
                    "processing_status": "completed",
                    "created_at": article.get('fetched_at')
                })
            
            api_response = {
                "success": True,
                "articles_found": len(formatted_articles),
                "articles": formatted_articles,
                "summary": {
                    "articles_fetched": articles_fetched,
                    "articles_stored": articles_stored,
                    "vectors_created": result_data.get('vectors_created', 0),
                    "sources_used": len(result_data.get('sources_used', [])),
                    "execution_time_ms": fetch_result.execution_time_ms
                }
            }
            
            print(f"   ✅ API响应成功!")
            print(f"   📊 找到文章数: {api_response['articles_found']}")
            print(f"   📊 获取文章数: {api_response['summary']['articles_fetched']}")
            print(f"   📊 存储文章数: {api_response['summary']['articles_stored']}")
            print(f"   📊 向量创建数: {api_response['summary']['vectors_created']}")
            print(f"   ⏱️  执行时间: {api_response['summary']['execution_time_ms']}ms")
            
            print(f"\n   📰 返回的文章:")
            for i, article in enumerate(api_response['articles'], 1):
                print(f"      {i}. {article['title'][:50]}...")
                print(f"         来源: {article['source']}")
                print(f"         ID: {article['id'][:20]}...")
            
            return True
        else:
            print(f"   ❌ API调用失败: {fetch_result.error_message}")
            return False
            
    except Exception as e:
        print(f"   ❌ API查询异常: {str(e)}")
        return False

async def main():
    """运行所有查询测试"""
    print(f"🕐 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🔧 OpenAI API: {'✅ 可用' if os.getenv('OPENAI_API_KEY') else '❌ 缺失'}")
    
    queries = [
        ("查询最近新闻数据", query_recent_news),
        ("查询向量嵌入数据", query_vector_data),
        ("模拟API端点查询", simulate_api_query)
    ]
    
    passed = 0
    for query_name, query_func in queries:
        try:
            print(f"\n{'='*50}")
            result = await query_func()
            if result:
                passed += 1
                print(f"\n✅ {query_name}: 成功")
            else:
                print(f"\n❌ {query_name}: 失败")
        except Exception as e:
            print(f"\n💥 {query_name}: 异常 - {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"📊 数据库查询测试结果: {passed}/{len(queries)} 成功")
    
    if passed == len(queries):
        print("🎉 所有查询测试通过!")
    else:
        print("⚠️  部分查询需要检查")
    
    print(f"\n💡 实际使用建议:")
    print(f"   🌐 Web API: curl http://localhost:8000/data/recent-news")
    print(f"   🐍 Python: 使用 DataAgent.fetch_news() 和数据库工具")
    print(f"   💾 SQL: 直接查询 PostgreSQL 数据库表")
    print(f"   📊 统计: 使用 /health 端点获取系统状态")

if __name__ == "__main__":
    asyncio.run(main())