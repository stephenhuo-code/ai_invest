#!/usr/bin/env python3
"""
查询数据库中已存储的数据

演示如何通过不同方式查询NewsArticle、AnalysisResult和VectorEmbedding数据
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("🔍 数据库数据查询工具")
print("=" * 50)

async def query_via_dataagent():
    """方式1: 通过DataAgent的数据库工具查询"""
    print("\n📋 方式1: 通过DataAgent查询")
    print("-" * 30)
    
    try:
        from src.application.agents.llm_data_agent import LLMDataAgent
        
        # Mock repository for testing
        class SimpleRepo:
            def __init__(self):
                self.news_items = []
                self.vectors = []
                # 添加一些示例数据
                for i in range(3):
                    article = type('Article', (), {})()
                    article.id = i + 1
                    article.title = f"Sample Article {i+1}"
                    article.url = f"https://example.com/article{i+1}"
                    article.source = "example.com"
                    article.content_hash = f"hash{i+1}"
                    article.processing_status = "completed"
                    article.created_at = datetime.utcnow()
                    article.published_at = datetime.utcnow() - timedelta(hours=i)
                    self.news_items.append(article)
                    
            async def health_check(self): return True
            async def save_news(self, news): return news
            async def get_vector_count(self): return len(self.vectors)
            async def find_recent_news(self, days=7, limit=None):
                return self.news_items[-limit:] if limit else self.news_items
            async def find_recent_analysis(self, days=7, limit=None): return []
        
        data_agent = LLMDataAgent(repository=SimpleRepo())
        
        # 使用数据库工具查询最近的新闻
        db_tool = None
        for tool in data_agent.tools:
            if 'database' in tool.name.lower() or 'storage' in tool.name.lower():
                db_tool = tool
                break
        
        if db_tool:
            # 查询最近7天的新闻
            result = await db_tool.execute(
                operation="find_recent_news",
                days=7,
                limit=10
            )
            
            if result.is_success:
                articles = result.data.get('articles', [])
                count = result.data.get('count', 0)
                
                print(f"   ✅ 查询成功: 找到 {count} 篇文章")
                print(f"   📊 查询条件: 最近7天,限制10篇")
                
                for i, article in enumerate(articles, 1):
                    print(f"\n   📰 文章 {i}:")
                    print(f"      ID: {article.get('id')}")
                    print(f"      标题: {article.get('title', '')[:50]}...")
                    print(f"      来源: {article.get('source', '')}")
                    print(f"      状态: {article.get('processing_status', '')}")
                    print(f"      创建时间: {article.get('created_at', '')}")
            else:
                print(f"   ❌ 查询失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ DataAgent查询失败: {str(e)}")
        return False

async def query_via_repository_direct():
    """方式2: 直接使用Repository查询"""
    print("\n📋 方式2: 直接使用Repository查询")
    print("-" * 30)
    
    try:
        # 创建模拟的repository来演示查询方法
        class MockRepository:
            def __init__(self):
                # 模拟数据库中的数据
                self.news_data = [
                    {
                        'id': 1,
                        'title': 'Apple Reports Strong Quarterly Earnings',
                        'url': 'https://cnbc.com/apple-earnings',
                        'source': 'cnbc.com',
                        'content': 'Apple Inc. reported better than expected...',
                        'content_hash': 'abc123',
                        'processing_status': 'completed',
                        'created_at': datetime.utcnow(),
                        'published_at': datetime.utcnow() - timedelta(hours=2)
                    },
                    {
                        'id': 2,
                        'title': 'Tesla Stock Surges on New Model Announcement',
                        'url': 'https://marketwatch.com/tesla-surge',
                        'source': 'marketwatch.com',
                        'content': 'Tesla shares jumped 8% after...',
                        'content_hash': 'def456',
                        'processing_status': 'completed',
                        'created_at': datetime.utcnow(),
                        'published_at': datetime.utcnow() - timedelta(hours=4)
                    }
                ]
                
                self.vector_data = [
                    {
                        'id': 1,
                        'source_type': 'news',
                        'source_id': '1',
                        'embedding': [0.1] * 1536,  # 模拟OpenAI嵌入
                        'embedding_model': 'text-embedding-ada-002',
                        'dimension': 1536,
                        'created_at': datetime.utcnow()
                    }
                ]
            
            async def find_recent_news(self, days=7, limit=10):
                """查询最近的新闻"""
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                recent_news = [
                    article for article in self.news_data 
                    if article['created_at'] >= cutoff_date
                ]
                return recent_news[:limit] if limit else recent_news
            
            async def find_news_by_id(self, news_id):
                """根据ID查询新闻"""
                for article in self.news_data:
                    if article['id'] == news_id:
                        return article
                return None
            
            async def find_news_by_source(self, source, limit=10):
                """根据来源查询新闻"""
                source_news = [
                    article for article in self.news_data 
                    if source.lower() in article['source'].lower()
                ]
                return source_news[:limit] if limit else source_news
            
            async def find_vectors_by_source_id(self, source_id):
                """查询特定文章的向量嵌入"""
                return [
                    vector for vector in self.vector_data 
                    if vector['source_id'] == str(source_id)
                ]
            
            async def get_statistics(self):
                """获取数据库统计信息"""
                return {
                    'total_news': len(self.news_data),
                    'total_vectors': len(self.vector_data),
                    'latest_article_time': max(a['created_at'] for a in self.news_data) if self.news_data else None,
                    'sources_count': len(set(a['source'] for a in self.news_data))
                }
        
        repo = MockRepository()
        
        # 1. 查询最近新闻
        print("🔄 查询最近7天的新闻...")
        recent_news = await repo.find_recent_news(days=7, limit=5)
        print(f"   ✅ 找到 {len(recent_news)} 篇最近文章")
        
        for article in recent_news:
            print(f"   📰 {article['title'][:40]}... (来源: {article['source']})")
        
        # 2. 根据ID查询特定文章
        print(f"\n🔄 根据ID查询文章...")
        article = await repo.find_news_by_id(1)
        if article:
            print(f"   ✅ 找到文章:")
            print(f"      标题: {article['title']}")
            print(f"      URL: {article['url']}")
            print(f"      内容预览: {article['content'][:100]}...")
        
        # 3. 根据来源查询
        print(f"\n🔄 查询CNBC来源的文章...")
        cnbc_articles = await repo.find_news_by_source('cnbc', limit=3)
        print(f"   ✅ 找到 {len(cnbc_articles)} 篇CNBC文章")
        
        # 4. 查询向量嵌入
        print(f"\n🔄 查询文章ID=1的向量嵌入...")
        vectors = await repo.find_vectors_by_source_id('1')
        if vectors:
            vector = vectors[0]
            print(f"   ✅ 找到向量嵌入:")
            print(f"      向量ID: {vector['id']}")
            print(f"      嵌入模型: {vector['embedding_model']}")
            print(f"      向量维度: {vector['dimension']}")
            print(f"      嵌入预览: [{vector['embedding'][:3]}...] (前3个值)")
        
        # 5. 获取统计信息
        print(f"\n🔄 获取数据库统计信息...")
        stats = await repo.get_statistics()
        print(f"   ✅ 数据库统计:")
        print(f"      总文章数: {stats['total_news']}")
        print(f"      总向量数: {stats['total_vectors']}")
        print(f"      数据源数: {stats['sources_count']}")
        print(f"      最新文章时间: {stats['latest_article_time']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Repository查询失败: {str(e)}")
        return False

async def query_via_api_endpoints():
    """方式3: 通过API端点查询"""
    print("\n📋 方式3: 通过API端点查询")
    print("-" * 30)
    
    try:
        print("🔄 模拟API端点查询...")
        
        # 模拟 /data/recent-news API调用
        print("\n   📡 GET /data/recent-news?days=7&limit=5")
        print("   ✅ 模拟响应:")
        mock_response = {
            "success": True,
            "articles_found": 2,
            "days_requested": 7,
            "limit_requested": 5,
            "articles": [
                {
                    "id": "abc123",
                    "title": "Market Update: Tech Stocks Rally",
                    "url": "https://example.com/tech-rally",
                    "source": "cnbc.com",
                    "processing_status": "completed",
                    "created_at": "2025-08-30T12:00:00Z"
                },
                {
                    "id": "def456",
                    "title": "Federal Reserve Meeting Results",
                    "url": "https://example.com/fed-meeting",
                    "source": "marketwatch.com", 
                    "processing_status": "completed",
                    "created_at": "2025-08-30T11:30:00Z"
                }
            ],
            "summary": {
                "articles_fetched": 2,
                "articles_stored": 2,
                "sources_used": 2
            }
        }
        
        for i, article in enumerate(mock_response["articles"], 1):
            print(f"      📰 文章 {i}: {article['title']}")
            print(f"         来源: {article['source']}")
            print(f"         状态: {article['processing_status']}")
        
        # 模拟 /data/recent-analysis API调用
        print(f"\n   📡 GET /data/recent-analysis?days=7&limit=3")
        print("   ✅ 模拟响应:")
        mock_analysis = {
            "analyses_found": 2,
            "analyses": [
                {
                    "id": "analysis_1",
                    "article_id": "abc123",
                    "analysis_type": "sentiment",
                    "result": {"sentiment": "positive", "confidence": 0.87},
                    "model_name": "gpt-4o",
                    "created_at": "2025-08-30T12:05:00Z"
                },
                {
                    "id": "analysis_2", 
                    "article_id": "def456",
                    "analysis_type": "topics",
                    "result": {"topics": ["federal_reserve", "interest_rates", "monetary_policy"]},
                    "model_name": "gpt-4o",
                    "created_at": "2025-08-30T11:35:00Z"
                }
            ]
        }
        
        for i, analysis in enumerate(mock_analysis["analyses"], 1):
            print(f"      🧠 分析 {i}: {analysis['analysis_type']} (文章ID: {analysis['article_id']})")
            print(f"         结果: {analysis['result']}")
            print(f"         模型: {analysis['model_name']}")
        
        print(f"\n   💡 实际使用方法:")
        print(f"      curl http://localhost:8000/data/recent-news?days=7&limit=10")
        print(f"      curl http://localhost:8000/data/recent-analysis?days=3&limit=5")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API查询演示失败: {str(e)}")
        return False

async def query_with_sql_examples():
    """方式4: SQL查询示例(仅展示查询语句)"""
    print("\n📋 方式4: 直接SQL查询示例")
    print("-" * 30)
    
    print("🔄 PostgreSQL查询示例...")
    
    sql_examples = [
        {
            "purpose": "查询最近7天的新闻",
            "sql": """
SELECT id, title, source, url, processing_status, created_at
FROM news_articles 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 10;
"""
        },
        {
            "purpose": "根据来源查询文章",
            "sql": """
SELECT id, title, url, published_at
FROM news_articles 
WHERE source LIKE '%cnbc%'
ORDER BY published_at DESC;
"""
        },
        {
            "purpose": "查询处理状态统计",
            "sql": """
SELECT processing_status, COUNT(*) as count
FROM news_articles 
GROUP BY processing_status;
"""
        },
        {
            "purpose": "查询文章和对应的分析结果",
            "sql": """
SELECT 
    n.id,
    n.title,
    n.source,
    a.analysis_type,
    a.confidence_score,
    a.created_at as analysis_time
FROM news_articles n
LEFT JOIN analysis_results a ON n.id = a.article_id
WHERE n.created_at >= NOW() - INTERVAL '3 days'
ORDER BY n.created_at DESC;
"""
        },
        {
            "purpose": "查询向量嵌入信息",
            "sql": """
SELECT 
    v.id,
    v.source_type,
    v.source_id,
    v.embedding_model,
    v.dimension,
    v.created_at
FROM vector_embeddings v
WHERE v.source_type = 'news'
ORDER BY v.created_at DESC
LIMIT 5;
"""
        },
        {
            "purpose": "查询数据库统计",
            "sql": """
SELECT 
    'news_articles' as table_name,
    COUNT(*) as total_count,
    MAX(created_at) as latest_entry
FROM news_articles
UNION ALL
SELECT 
    'vector_embeddings' as table_name,
    COUNT(*) as total_count,
    MAX(created_at) as latest_entry  
FROM vector_embeddings
UNION ALL
SELECT 
    'analysis_results' as table_name,
    COUNT(*) as total_count,
    MAX(created_at) as latest_entry
FROM analysis_results;
"""
        }
    ]
    
    for i, example in enumerate(sql_examples, 1):
        print(f"\n   📝 示例 {i}: {example['purpose']}")
        print(f"   SQL:")
        for line in example['sql'].strip().split('\n'):
            print(f"      {line}")
    
    print(f"\n   💡 使用方法:")
    print(f"      # 连接到PostgreSQL数据库")
    print(f"      psql postgresql://ai_invest:password@localhost:5432/ai_invest")
    print(f"      # 或者使用Python连接")
    print(f"      # from sqlalchemy import create_engine, text")
    print(f"      # engine = create_engine(DATABASE_URL)")
    print(f"      # result = engine.execute(text(sql_query))")
    
    return True

async def main():
    """运行所有查询示例"""
    print(f"🕐 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    
    methods = [
        ("通过DataAgent查询", query_via_dataagent),
        ("直接使用Repository", query_via_repository_direct), 
        ("通过API端点查询", query_via_api_endpoints),
        ("SQL查询示例", query_with_sql_examples)
    ]
    
    passed = 0
    for method_name, method_func in methods:
        try:
            result = await method_func()
            if result:
                passed += 1
                print(f"\n✅ {method_name}: 演示成功")
            else:
                print(f"\n❌ {method_name}: 演示失败")
        except Exception as e:
            print(f"\n💥 {method_name}: 异常 - {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"📊 查询方法演示结果: {passed}/{len(methods)} 成功")
    
    print(f"\n💡 总结 - 数据库查询的4种方式:")
    print(f"   1. 🤖 DataAgent工具: 使用data_agent的数据库工具查询")
    print(f"   2. 🔧 Repository直接: 使用repository接口的查询方法") 
    print(f"   3. 📡 API端点: 通过HTTP API获取格式化的数据")
    print(f"   4. 💾 SQL直接: 使用原生SQL查询PostgreSQL数据库")
    
    print(f"\n🎯 推荐使用方式:")
    print(f"   - 应用开发: 使用API端点 (/data/recent-news, /data/recent-analysis)")
    print(f"   - 数据分析: 使用Repository方法或SQL查询")
    print(f"   - 系统监控: 使用DataAgent工具进行健康检查和统计")

if __name__ == "__main__":
    asyncio.run(main())