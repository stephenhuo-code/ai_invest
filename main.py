
from fastapi import FastAPI
from fetchers.news_fetcher import fetch_latest_news
from fetchers.price_fetcher import get_latest_price
from fetchers.industry_data import get_sector_performance
from fetchers.macro_data import get_macro_indicators
from analyzers.topic_extractor import extract_topics_with_gpt
from analyzers.llm_analyzer import generate_weekly_report
from utils.markdown_writer import write_markdown_report
from utils.slack_notifier import send_to_slack
from config import APP_NAME, APP_VERSION, APP_DESCRIPTION, MAX_STOCKS_PER_ANALYSIS

import datetime

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

@app.get("/")
def home():
    return {"message": "AI Invest Trend API - Full Version"}

@app.get("/run/weekly-full-report")
def run_report():
    news = fetch_latest_news()
    topic_analysis = extract_topics_with_gpt(news)
    tickers = []
    for r in topic_analysis:
        # 从raw_analysis中提取股票代码
        raw_analysis = r.get("raw_analysis", "")
        for line in raw_analysis.splitlines():
            if any(tag in line.lower() for tag in ['股票代码', '公司']):
                tokens = line.split()
                for t in tokens:
                    if t.isupper() and 2 <= len(t) <= 5:
                        tickers.append(t.strip(",.;"))
    
    # 也从stocks字段中提取股票代码
    for r in topic_analysis:
        stocks = r.get("stocks", [])
        for stock in stocks:
            stock_code = stock.get("stock_code", "")
            if stock_code and stock_code not in tickers:
                tickers.append(stock_code)
    
    tickers = list(set(tickers))[:MAX_STOCKS_PER_ANALYSIS]
    price_data = get_latest_price(tickers)
    sector_data = get_sector_performance()
    macro_data = get_macro_indicators()
    markdown_path, summary = write_markdown_report(
        news=news,
        analysis=topic_analysis,
        prices=price_data,
        sectors=sector_data,
        macro=macro_data
    )
    send_to_slack(summary, markdown_path)
    return {"status": "success", "report": markdown_path}
