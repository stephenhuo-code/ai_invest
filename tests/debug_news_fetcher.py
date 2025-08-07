#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试新闻获取器
检查新闻获取过程中的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
from newspaper import Article
from utils.env_loader import get_optional_env

def load_config():
    """从环境变量加载配置"""
    rss_feeds_str = get_optional_env("RSS_FEEDS", "https://finance.yahoo.com/news/rssindex")
    
    # 支持多个 RSS 源，用逗号分隔
    if "," in rss_feeds_str:
        feed_urls = [url.strip() for url in rss_feeds_str.split(",")]
    else:
        feed_urls = [rss_feeds_str]
    
    return {"rss_feeds": feed_urls}

def debug_news_fetch():
    """调试新闻获取过程"""
    print("开始调试新闻获取...")
    
    # 1. 加载配置
    print("1. 加载配置...")
    config = load_config()
    feed_urls = config.get("rss_feeds", [])
    print(f"RSS 源: {feed_urls}")
    
    if not feed_urls:
        print("❌ 没有配置 RSS 源")
        return []
    
    articles = []
    
    for i, feed_url in enumerate(feed_urls):
        print(f"\n2. 处理 RSS 源 {i+1}: {feed_url}")
        
        try:
            # 2. 解析 RSS
            print("   解析 RSS...")
            feed = feedparser.parse(feed_url)
            print(f"   找到 {len(feed.entries)} 条条目")
            
            if not feed.entries:
                print("   ⚠️  RSS 源没有返回条目")
                continue
            
            # 3. 处理前几条条目
            for j, entry in enumerate(feed.entries[:3]):
                print(f"\n   处理条目 {j+1}: {entry.get('title', '无标题')}")
                print(f"   链接: {entry.get('link', '无链接')}")
                
                try:
                    url = entry.link
                    print(f"   下载文章: {url}")
                    
                    # 4. 下载和解析文章
                    article = Article(url)
                    article.download()
                    article.parse()
                    
                    print(f"   标题: {article.title}")
                    print(f"   文本长度: {len(article.text)} 字符")
                    print(f"   文本预览: {article.text[:100]}...")
                    
                    if article.text.strip():
                        articles.append({
                            "title": article.title,
                            "text": article.text
                        })
                        print("   ✅ 文章添加成功")
                    else:
                        print("   ⚠️ 文章文本为空")
                        
                except Exception as e:
                    print(f"   ❌ 处理文章失败: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ 处理 RSS 源失败: {str(e)}")
            continue
    
    print(f"\n总结: 成功获取 {len(articles)} 篇文章")
    return articles

if __name__ == "__main__":
    articles = debug_news_fetch()
    
    if articles:
        print("\n获取的文章:")
        for i, article in enumerate(articles):
            print(f"\n文章 {i+1}:")
            print(f"标题: {article['title']}")
            print(f"文本长度: {len(article['text'])}")
            print(f"文本预览: {article['text'][:200]}...")
    else:
        print("\n❌ 没有获取到任何文章") 