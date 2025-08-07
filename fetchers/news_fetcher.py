
import feedparser
from newspaper import Article
import yaml

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def fetch_latest_news(max_articles=5):
    config = load_config()
    feed_urls = config.get("rss_feeds", [])
    articles = []

    for feed_url in feed_urls:
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
            except Exception:
                continue

    return articles
