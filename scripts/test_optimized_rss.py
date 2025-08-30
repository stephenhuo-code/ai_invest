#!/usr/bin/env python3
"""
Test the optimized RSS configuration.

Quick validation of the improved RSS source configuration.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import requests
    import feedparser
    from src.config.rss_sources import RSSSourceConfig, get_reliable_rss_sources
    HAS_DEPS = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    HAS_DEPS = False


async def test_optimized_sources():
    """Test the optimized RSS sources configuration."""
    print("🧪 Testing Optimized RSS Configuration")
    print("=" * 50)
    
    if not HAS_DEPS:
        print("❌ Cannot run test - missing dependencies")
        return
    
    # Get reliable sources
    sources = get_reliable_rss_sources()
    print(f"📡 Testing {len(sources)} reliable sources")
    
    # Get optimized configuration
    headers = RSSSourceConfig.get_optimized_headers()
    retry_config = RSSSourceConfig.get_retry_config()
    
    print(f"🔧 User-Agent: {headers['User-Agent'][:50]}...")
    print(f"⚙️  Timeout: {retry_config['timeout']}s")
    print()
    
    success_count = 0
    total_articles = 0
    
    session = requests.Session()
    session.headers.update(headers)
    
    for i, source_url in enumerate(sources, 1):
        source_info = RSSSourceConfig.get_source_info(source_url)
        source_name = source_info.get('name', 'Unknown')
        
        print(f"{i}. Testing {source_name}...")
        
        try:
            # Test with optimized configuration
            response = session.get(
                source_url,
                timeout=retry_config['timeout'],
                verify=retry_config['ssl_verify'],
                allow_redirects=retry_config['allow_redirects']
            )
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                articles = len(feed.entries)
                total_articles += articles
                
                if articles > 0:
                    print(f"   ✅ Success: {articles} articles")
                    success_count += 1
                else:
                    print(f"   ⚠️  No articles found")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Delay between requests
        if i < len(sources):
            await asyncio.sleep(retry_config['delay_between_sources'])
    
    print()
    print("📊 Results Summary:")
    print(f"   Success Rate: {success_count}/{len(sources)} ({success_count/len(sources)*100:.1f}%)")
    print(f"   Total Articles: {total_articles}")
    print(f"   Avg per Source: {total_articles/len(sources):.1f}")
    
    if success_count >= len(sources) * 0.8:
        print("🎉 Excellent! Configuration is working well.")
    elif success_count >= len(sources) * 0.6:
        print("👍 Good results. Minor tweaks may help.")
    else:
        print("⚠️  Results could be improved. Check configuration.")


async def show_source_configuration():
    """Display the RSS source configuration."""
    print("\n📋 RSS Source Configuration")
    print("=" * 50)
    
    print("\n🔥 Primary Sources (High Reliability):")
    for source in RSSSourceConfig.PRIMARY_SOURCES:
        reliability = source['reliability'].value
        name = source['name']
        response_time = source.get('avg_response_time', 'N/A')
        print(f"   ✅ {name} ({reliability}) - {response_time}s")
    
    print("\n🔄 Secondary Sources (Backup):")
    for source in RSSSourceConfig.SECONDARY_SOURCES:
        name = source['name']
        print(f"   🔗 {name}")
    
    print("\n⚠️  Problematic Sources (Known Issues):")
    for source in RSSSourceConfig.PROBLEMATIC_SOURCES:
        name = source['name']
        issue = source['issue']
        print(f"   ❌ {name} - {issue}")


async def main():
    """Run the optimized RSS test."""
    await show_source_configuration()
    await test_optimized_sources()
    
    print(f"\n⏰ Test completed at {datetime.now().strftime('%H:%M:%S')}")
    print("\n💡 Next Steps:")
    print("   1. If success rate >80%: Deploy to production")
    print("   2. If success rate 60-80%: Fine-tune configuration")  
    print("   3. If success rate <60%: Add more secondary sources")


if __name__ == "__main__":
    asyncio.run(main())