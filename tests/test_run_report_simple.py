#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版测试脚本（使用 AnalyzeAgent）
可以跳过某些步骤进行快速测试
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.news_fetcher import fetch_latest_news
from fetchers.price_fetcher import get_latest_price
from fetchers.industry_data import get_sector_performance
from fetchers.macro_data import get_macro_indicators
from analyzers.analyze_agent import AnalyzeAgent
from utils.markdown_writer import write_markdown_report
import datetime

def run_report_simple(skip_slack=True, skip_macro=False, skip_sector=False):
    """运行简化的周报生成流程（使用 AnalyzeAgent）"""
    print("开始生成周报（简化版，AnalyzeAgent）...")
    
    # 1. 获取最新新闻
    print("1. 获取最新新闻...")
    news = fetch_latest_news()
    print(f"获取到 {len(news)} 条新闻")
    
    # 2. 提取主题分析（使用 AnalyzeAgent）
    print("2. 提取主题分析（AnalyzeAgent）...")
    agent = AnalyzeAgent()
    topic_analysis = agent.extract_topics(news)
    print(f"完成主题分析，共 {len(topic_analysis)} 个主题")
    
    # 3. 提取股票代码
    print("3. 提取股票代码...")
    tickers = []
    for i, result in enumerate(topic_analysis):
        stocks = result.get("stocks", [])
        print(f"   新闻 {i+1}: 找到 {len(stocks)} 只股票")
        print(f"   新闻 {i+1} 原始数据: {result}")
        for stock in stocks:
            stock_code = stock.get("stock_code", "").strip()
            company_name = stock.get("company_name", "").strip()
            if stock_code:
                tickers.append(stock_code)
                print(f"     - {company_name} ({stock_code})")
    
    # 如果没有提取到股票代码，使用一些默认的股票进行测试
    if not tickers:
        print("⚠️  未提取到股票代码，使用默认股票进行测试...")
        tickers = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN"]
    else:
        print(f"✅ 成功提取到股票代码: {tickers}")
    
    tickers = list(set(tickers))[:10]
    print(f"最终股票列表: {tickers}")
    
    # 4. 获取价格数据
    print("4. 获取价格数据...")
    price_data = get_latest_price(tickers)
    print(f"获取到 {len(price_data)} 只股票的价格数据")
    
    # 5. 获取行业数据（可选跳过）
    sector_data = None
    if not skip_sector:
        print("5. 获取行业数据...")
        sector_data = get_sector_performance()
        print("行业数据获取完成")
    else:
        print("5. 跳过行业数据获取")
    
    # 6. 获取宏观数据（可选跳过）
    macro_data = None
    if not skip_macro:
        print("6. 获取宏观数据...")
        macro_data = get_macro_indicators()
        print("宏观数据获取完成")
    else:
        print("6. 跳过宏观数据获取")
    
    # 7. 生成 Markdown 报告
    print("7. 生成 Markdown 报告...")
    markdown_path, summary = write_markdown_report(
        news=news,
        analysis=topic_analysis,
        prices=price_data,
        sectors=sector_data,
        macro=macro_data
    )
    print(f"报告已生成: {markdown_path}")
    print(f"报告摘要: {summary[:100]}...")
    
    # 8. 发送到 Slack（可选跳过）
    if not skip_slack:
        print("8. 发送到 Slack...")
        from utils.slack_notifier import send_to_slack
        send_to_slack(summary, markdown_path)
        print("Slack 通知已发送")
    else:
        print("8. 跳过 Slack 通知")
    
    return {"status": "success", "report": markdown_path}

if __name__ == "__main__":
    try:
        # 可以选择跳过某些步骤
        result = run_report_simple(
            skip_slack=True,    # 跳过 Slack 通知
            skip_macro=False,   # 不跳过宏观数据
            skip_sector=False   # 不跳过行业数据
        )
        print(f"\n✅ 周报生成成功！")
        print(f"报告路径: {result['report']}")
    except Exception as e:
        print(f"\n❌ 周报生成失败: {str(e)}")
        import traceback
        traceback.print_exc() 