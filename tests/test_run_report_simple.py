#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版测试脚本
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
from analyzers.topic_extractor import extract_topics_with_gpt
from utils.markdown_writer import write_markdown_report
import datetime

def run_report_simple(skip_slack=True, skip_macro=False, skip_sector=False):
    """运行简化的周报生成流程"""
    print("开始生成周报（简化版）...")
    
    # 1. 获取最新新闻
    print("1. 获取最新新闻...")
    news = fetch_latest_news()
    print(f"获取到 {len(news)} 条新闻")
    
    # 2. 提取主题分析
    print("2. 提取主题分析...")
    topic_analysis = extract_topics_with_gpt(news)
    print(f"完成主题分析，共 {len(topic_analysis)} 个主题")
    
    # 3. 提取股票代码
    print("3. 提取股票代码...")
    tickers = []
    for r in topic_analysis:
        for line in r["analysis"].splitlines():
            if any(tag in line.lower() for tag in ['股票代码', '公司']):
                tokens = line.split()
                for t in tokens:
                    if t.isupper() and 2 <= len(t) <= 5:
                        tickers.append(t.strip(",.;"))
    
    tickers = list(set(tickers))[:10]
    print(f"提取到股票代码: {tickers}")
    
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