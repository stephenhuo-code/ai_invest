#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立测试 run_report 函数的脚本
使用 AnalyzeAgent 进行分析并推送到 Slack
"""

import sys
import os
import re
from pathlib import Path
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.news_fetcher import fetch_latest_news
from fetchers.price_fetcher import get_latest_price
from fetchers.industry_data import get_sector_performance
from fetchers.macro_data import get_macro_indicators
from analyzers.analyze_agent import AnalyzeAgent
from utils.slack_notifier import send_to_slack
import datetime

# 常见大型科技股列表作为默认股票
DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NVDA']

def extract_tickers(text: str) -> list:
    """从文本中提取股票代码"""
    tickers = set()
    patterns = [
        r'\(([A-Z]{1,5})\)',  # (AAPL)
        r'NYSE:\s*([A-Z]{1,5})',  # NYSE: AAPL
        r'NASDAQ:\s*([A-Z]{1,5})',  # NASDAQ: AAPL
        r'(?:股票|股份|公司|stock|shares).*?([A-Z]{2,5})',  # 包含相关词的上下文
        r'\$([A-Z]{1,5})\b'  # $AAPL
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            ticker = match.group(1).strip()
            if ticker.isupper() and 2 <= len(ticker) <= 5:
                tickers.add(ticker)
    
    return list(tickers)

def run_report():
    """运行完整的报告生成流程"""
    print("开始生成市场分析报告...")
    
    try:
        # 初始化 AnalyzeAgent
        print("1. 初始化 AnalyzeAgent...")
        agent = AnalyzeAgent()
        
        # 1. 获取最新新闻
        print("2. 获取最新新闻...")
        news = fetch_latest_news()
        print(f"获取到 {len(news)} 条新闻")
        
        # 2. 提取主题分析
        print("3. 提取主题分析...")
        topic_analysis = agent.extract_topics(news)
        print(f"完成主题分析，共 {len(topic_analysis)} 个主题")
        
        # 3. 提取股票代码
        print("4. 提取股票代码...")
        tickers = []
        
        # 从分析结果中提取股票代码
        for result in topic_analysis:
            if result.get("analysis"):
                tickers.extend(extract_tickers(result["analysis"]))
        
        # 如果没有提取到股票代码，使用默认列表
        if not tickers:
            print("未提取到股票代码，使用默认股票列表")
            tickers = DEFAULT_TICKERS.copy()
        
        # 去重并限制数量
        tickers = list(set(tickers))[:10]
        print(f"提取到股票代码: {tickers}")
        
        # 4. 获取价格数据
        print("5. 获取价格数据...")
        price_data = get_latest_price(tickers)
        print(f"获取到 {len(price_data)} 只股票的价格数据")
        
        # 5. 获取行业数据
        print("6. 获取行业数据...")
        sector_data = get_sector_performance()
        print("行业数据获取完成")
        
        # 6. 获取宏观数据
        print("7. 获取宏观数据...")
        macro_data = get_macro_indicators()
        print("宏观数据获取完成")
        
        # 7. 生成每日报告
        print("8. 生成每日报告...")
        report_content, report_path = agent.generate_daily_report(sector_data, macro_data)
        print(f"报告已生成: {report_path}")
        
        # 提取报告的前300个字符作为摘要
        summary = report_content[:300] + "..."
        print(f"报告摘要: {summary}")
        
        # 8. 发送到 Slack
        print("9. 发送到 Slack...")
        send_to_slack(summary, report_path)
        print("Slack 通知已发送")
        
        return {
            "status": "success",
            "report_path": report_path,
            "topic_analysis": topic_analysis,
            "tickers": tickers,
            "summary": summary
        }
        
    except Exception as e:
        print(f"❌ 报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """主函数"""
    try:
        print("🚀 开始运行市场分析报告生成流程...")
        result = run_report()
        
        if result["status"] == "success":
            print("\n✅ 报告生成成功！")
            print(f"📊 报告路径: {result['report_path']}")
            print(f"📈 分析股票: {', '.join(result['tickers'])}")
            print("\n📝 报告摘要:")
            print("-" * 60)
            print(result["summary"])
            print("-" * 60)
        else:
            print(f"\n❌ 报告生成失败: {result['error']}")
        
        return result["status"] == "success"
    
    except Exception as e:
        print(f"\n❌ 程序执行错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)