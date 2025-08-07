
import feedparser
from newspaper import Article
from utils.env_loader import get_optional_env

def fetch_latest_news(max_articles=5):
    """获取最新新闻"""
    # 从环境变量获取 RSS 源，如果没有则使用默认值
    rss_feeds_str = get_optional_env("RSS_FEEDS", "https://finance.yahoo.com/news/rssindex")
    
    # 支持多个 RSS 源，用逗号分隔
    if "," in rss_feeds_str:
        feed_urls = [url.strip() for url in rss_feeds_str.split(",")]
    else:
        feed_urls = [rss_feeds_str]
    
    articles = []

    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:max_articles]:
                try:
                    url = entry.link
                    article = Article(url)
                    article.download()
                    article.parse()
                    articles.append({
                        "title": article.title,
                        "text": article.text
                    })
                except Exception as e:
                    print(f"处理文章失败 {url}: {str(e)}")
                    continue
        except Exception as e:
            print(f"处理 RSS 源失败 {feed_url}: {str(e)}")
            continue

    return articles
