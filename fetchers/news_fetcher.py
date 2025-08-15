
import feedparser
from newspaper import Article
from utils.env_loader import get_optional_env
from config import RSS_FEEDS, MAX_NEWS_ARTICLES

def fetch_latest_news(max_articles=None):
    """获取最新新闻"""
    # 使用配置文件中的默认值，如果传入参数则覆盖
    if max_articles is None:
        max_articles = MAX_NEWS_ARTICLES
    
    # 使用配置文件中的RSS源
    feed_urls = RSS_FEEDS
    
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
