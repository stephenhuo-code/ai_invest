#!/usr/bin/env python3
"""
Minimal test of tools implementation.
"""
import asyncio
from datetime import datetime


# Test RSS parsing
async def test_rss_parsing():
    print("🔄 Testing RSS parsing...")
    try:
        import feedparser
        import requests
        
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible)'}
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if feed.entries:
                print(f"  ✅ RSS working: {len(feed.entries)} entries")
                print(f"  📰 Sample: {feed.entries[0].get('title', '')[:50]}...")
                return True
            else:
                print("  ⚠️  RSS feed has no entries")
                return False
        else:
            print(f"  ❌ HTTP {response.status_code}")
            return False
    except ImportError:
        print("  ⚠️  Install: pip install feedparser requests")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


# Test market data
async def test_yfinance():
    print("🔄 Testing yfinance...")
    try:
        import yfinance as yf
        
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        history = ticker.history(period="1d")
        
        if not history.empty:
            price = history['Close'].iloc[-1]
            print(f"  ✅ YFinance working: AAPL = ${price:.2f}")
            return True
        else:
            print("  ❌ No data returned")
            return False
    except ImportError:
        print("  ⚠️  Install: pip install yfinance")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


# Test OpenAI
async def test_openai():
    print("🔄 Testing OpenAI...")
    try:
        import os
        if not os.getenv("OPENAI_API_KEY"):
            print("  ⚠️  OPENAI_API_KEY not set")
            return False
        
        from openai import OpenAI
        client = OpenAI()
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test text"
        )
        
        embedding = response.data[0].embedding
        print(f"  ✅ OpenAI working: {len(embedding)} dimensions")
        return True
    except ImportError:
        print("  ⚠️  Install: pip install openai")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


async def main():
    print("🚀 Minimal Dependencies Test")
    print("=" * 40)
    
    tests = [
        test_rss_parsing,
        test_yfinance, 
        test_openai
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} working")
    
    if passed == total:
        print("🎉 All dependencies working!")
    else:
        print("⚠️  Some dependencies need setup")


if __name__ == "__main__":
    asyncio.run(main())