
import os  # 添加 os 导入
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

# 强制启用 LangSmith 跟踪
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "ai_invest"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

@app.on_event("startup")
async def startup_event():
    """应用启动时验证配置"""
    print("🚀 AI Invest Trend API 启动中...")
    print(f"📊 LangSmith 跟踪状态: {os.getenv('LANGSMITH_TRACING', '未设置')}")
    print(f"🏗️  LangSmith 项目: {os.getenv('LANGSMITH_PROJECT', '未设置')}")
    print(f"🌐 LangSmith 端点: {os.getenv('LANGSMITH_ENDPOINT', '未设置')}")
    print(f"🔑 LangSmith API 密钥: {'已设置' if os.getenv('LANGSMITH_API_KEY') else '未设置'}")
    
    # 检查 Slack 配置
    from config import SLACK_ENABLED, SLACK_CHANNEL, SLACK_USERNAME
    print(f"📱 Slack 通知: {'启用' if SLACK_ENABLED else '禁用'}")
    print(f"📱 Slack 频道: {SLACK_CHANNEL}")
    print(f"📱 Slack 用户名: {SLACK_USERNAME}")
    print(f"🔗 Slack Webhook: {'已设置' if os.getenv('SLACK_WEBHOOK_URL') else '未设置'}")
    
    print("✅ 应用启动完成！")

@app.get("/")
def home():
    return {"message": "AI Invest Trend API - Full Version"}

@app.get("/test/slack")
def test_slack():
    """测试 Slack 通知功能"""
    from utils.slack_notifier import send_to_slack
    
    test_summary = "这是一条测试消息，用于验证 Slack 通知功能是否正常工作。"
    test_report_path = "test_report.md"
    
    # 创建测试报告文件
    with open(test_report_path, 'w', encoding='utf-8') as f:
        f.write("# 测试报告\n\n这是一个测试报告，用于验证 Slack 通知功能。")
    
    try:
        send_to_slack(test_summary, test_report_path)
        return {"status": "success", "message": "Slack 测试通知已发送"}
    except Exception as e:
        return {"status": "error", "message": f"Slack 测试失败: {str(e)}"}

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
