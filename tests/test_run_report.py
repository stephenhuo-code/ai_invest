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

def print_stock_summary(topic_analysis: list) -> dict:
    """打印股票提取汇总信息"""
    print("\n🎯 股票提取汇总:")
    print("=" * 60)
    
    total_stocks = 0
    market_stats = {}
    sentiment_stats = {}
    
    for result in topic_analysis:
        stocks = result.get('stocks', [])
        sentiment = result.get('sentiment', '未知')
        
        for stock in stocks:
            total_stocks += 1
            market = stock.get('market', '未知')
            stock_code = stock.get('stock_code', 'N/A')
            company_name = stock.get('company_name', 'N/A')
            
            # 统计市场分布
            market_stats[market] = market_stats.get(market, 0) + 1
            
            # 统计情绪分布
            sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
            
            print(f"   • {company_name} ({stock_code}) - {market} - {sentiment}")
    
    print(f"\n📊 统计信息:")
    print(f"   - 总股票数: {total_stocks}")
    print(f"   - 市场分布: {market_stats}")
    print(f"   - 情绪分布: {sentiment_stats}")
    print("=" * 60)
    
    return {
        "total_stocks": total_stocks,
        "market_stats": market_stats,
        "sentiment_stats": sentiment_stats
    }

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
        
        # 打印详细的分析结果
        print("\n📊 详细分析结果:")
        print("=" * 80)
        for i, result in enumerate(topic_analysis, 1):
            print(f"\n--- 新闻 {i}: {result['title']} ---")
            print(f"🎯 行业主题: {result.get('industry_themes', [])}")
            print(f"📈 情绪: {result.get('sentiment', '未知')}")
            print(f"💡 总结: {result.get('summary', '无')}")
            
            stocks = result.get('stocks', [])
            if stocks:
                print(f"📋 涉及股票 ({len(stocks)} 只):")
                for stock in stocks:
                    print(f"   • {stock.get('company_name', 'N/A')} ({stock.get('stock_code', 'N/A')}) - {stock.get('market', 'N/A')}")
            else:
                print("   • 未识别到具体股票")
            
            # 打印原始分析文本（用于调试）
            raw_analysis = result.get('raw_analysis', '')
            if raw_analysis and len(raw_analysis) > 200:
                print(f"📄 原始分析 (前200字符): {raw_analysis[:200]}...")
            elif raw_analysis:
                print(f"📄 原始分析: {raw_analysis}")
        
        print("=" * 80)
        
        # 打印股票提取汇总
        stock_summary = print_stock_summary(topic_analysis)
        
        # 3. 提取股票代码
        print("\n4. 提取股票代码...")
        tickers = []
        
        # 从新的结构化结果中提取股票代码
        for result in topic_analysis:
            stocks = result.get('stocks', [])
            for stock in stocks:
                stock_code = stock.get('stock_code', '').strip()
                if stock_code:
                    tickers.append(stock_code)
                    print(f"   ✅ 提取到股票: {stock.get('company_name', 'N/A')} ({stock_code})")
        
        # 如果结构化提取失败，尝试从原始分析文本中提取
        if not tickers:
            print("   ⚠️  结构化提取未获得股票代码，尝试从原始文本提取...")
            for result in topic_analysis:
                raw_analysis = result.get('raw_analysis', '')
                if raw_analysis:
                    extracted = extract_tickers(raw_analysis)
                    if extracted:
                        tickers.extend(extracted)
                        print(f"   🔍 从文本提取: {extracted}")
        
        # 如果没有提取到股票代码，使用默认列表
        if not tickers:
            print("未提取到股票代码，使用默认股票列表")
            tickers = DEFAULT_TICKERS.copy()
        
        # 去重并限制数量
        tickers = list(set(tickers))[:10]
        print(f"\n📈 最终股票列表: {tickers}")
        print(f"📊 股票数量: {len(tickers)}")
        
        # 4. 获取价格数据
        print("\n5. 获取价格数据...")
        price_data = get_latest_price(tickers)
        print(f"获取到 {len(price_data)} 只股票的价格数据")
        
        # 打印价格数据详情
        if price_data:
            print("\n💰 价格数据详情:")
            print("-" * 60)
            for ticker, data in price_data.items():
                if isinstance(data, dict):
                    price = data.get('price', 'N/A')
                    change = data.get('change', 'N/A')
                    change_pct = data.get('change_pct', 'N/A')
                    print(f"   {ticker}: ${price} ({change_pct})")
                else:
                    print(f"   {ticker}: {data}")
            print("-" * 60)
        
        # 5. 获取行业数据
        print("\n6. 获取行业数据...")
        sector_data = get_sector_performance()
        print("行业数据获取完成")
        
        # 打印行业数据详情
        if sector_data:
            print("\n🏭 行业数据详情:")
            print("-" * 60)
            if isinstance(sector_data, dict):
                for sector, data in sector_data.items():
                    if isinstance(data, dict):
                        performance = data.get('performance', 'N/A')
                        change = data.get('change', 'N/A')
                        print(f"   {sector}: {performance} ({change})")
                    else:
                        print(f"   {sector}: {data}")
            else:
                print(f"   数据格式: {type(sector_data)}")
                print(f"   数据内容: {str(sector_data)[:200]}...")
            print("-" * 60)
        
        # 6. 获取宏观数据
        print("\n7. 获取宏观数据...")
        macro_data = get_macro_indicators()
        print("宏观数据获取完成")
        
        # 打印宏观数据详情
        if macro_data:
            print("\n🌍 宏观数据详情:")
            print("-" * 60)
            if isinstance(macro_data, dict):
                for indicator, value in macro_data.items():
                    print(f"   {indicator}: {value}")
            else:
                print(f"   数据格式: {type(macro_data)}")
                print(f"   数据内容: {str(macro_data)[:200]}...")
            print("-" * 60)
        
        # 7. 生成每日报告
        print("\n8. 生成每日报告...")
        print(f"📊 输入数据:")
        print(f"   - 行业数据: {type(sector_data)} (长度: {len(str(sector_data)) if sector_data else 0})")
        print(f"   - 宏观数据: {type(macro_data)} (长度: {len(str(macro_data)) if macro_data else 0})")
        
        report_content, report_path = agent.generate_daily_report(sector_data, macro_data)
        print(f"✅ 报告已生成: {report_path}")
        
        # 打印报告统计信息
        print(f"\n📄 报告统计:")
        print(f"   - 文件大小: {len(report_content)} 字符")
        print(f"   - 行数: {len(report_content.split(chr(10)))} 行")
        
        # 提取报告的前300个字符作为摘要
        summary = report_content[:300] + "..." if len(report_content) > 300 else report_content
        print(f"\n📝 报告摘要:")
        print("-" * 60)
        print(summary)
        print("-" * 60)
        
        # 8. 发送到 Slack
        print("\n9. 发送到 Slack...")
        print(f"📤 发送内容:")
        print(f"   - 摘要长度: {len(summary)} 字符")
        print(f"   - 报告文件: {report_path}")
        
        send_to_slack(summary, report_path)
        print("✅ Slack 通知已发送")
        
        return {
            "status": "success",
            "report_path": report_path,
            "topic_analysis": topic_analysis,
            "tickers": tickers,
            "summary": summary,
            "stock_summary": stock_summary,
            "price_data": price_data,
            "sector_data": sector_data,
            "macro_data": macro_data
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