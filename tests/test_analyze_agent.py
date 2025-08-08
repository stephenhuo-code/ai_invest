#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立测试 AnalyzeAgent 类的脚本
测试主题提取和周报生成功能
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.analyze_agent import AnalyzeAgent
from fetchers.news_fetcher import fetch_latest_news
from fetchers.industry_data import get_sector_performance
from fetchers.macro_data import get_macro_indicators
import datetime

def test_extract_topics():
    """测试主题提取功能"""
    print("📰 测试主题提取功能...")
    
    # 创建测试用的模拟新闻数据
    mock_news = [
        {
            "title": "苹果公司发布新款iPhone，AI功能引关注",
            "text": "苹果公司今日发布了搭载最新AI芯片的iPhone 15，新增多项人工智能功能。分析师认为这将推动苹果股价上涨。AAPL股票在盘后交易中上涨3%。",
            "date": "2024-01-15",
            "source": "财经新闻"
        },
        {
            "title": "特斯拉Q4交付量超预期，电动车板块走强",
            "text": "特斯拉(TSLA)公布第四季度交付量达到48万辆，超出分析师预期。受此消息推动，整个电动车板块走强，比亚迪(BYD)、蔚来(NIO)等股票均有不同程度上涨。",
            "date": "2024-01-15",
            "source": "汽车新闻"
        }
    ]
    
    try:
        agent = AnalyzeAgent()
        results = agent.extract_topics(mock_news)
        
        print(f"✅ 成功提取 {len(results)} 个主题分析")
        for i, result in enumerate(results, 1):
            print(f"\n--- 分析结果 {i} ---")
            print(f"标题: {result['title']}")
            print(f"分析: {result['analysis'][:200]}...")
            
        return results
        
    except Exception as e:
        print(f"❌ 主题提取测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_weekly_report():
    """测试周报生成功能"""
    print("\n📊 测试周报生成功能...")
    
    # 创建测试用的模拟数据
    mock_sector_data = {
        "Technology": {"change": 2.5, "leaders": ["AAPL", "MSFT", "GOOGL"]},
        "Healthcare": {"change": 1.2, "leaders": ["JNJ", "PFE", "UNH"]},
        "Energy": {"change": -0.8, "leaders": ["XOM", "CVX", "COP"]}
    }
    
    mock_macro_data = {
        "GDP_growth": 2.1,
        "inflation_rate": 3.2,
        "unemployment_rate": 3.7,
        "interest_rate": 5.25
    }
    
    try:
        agent = AnalyzeAgent()
        report = agent.generate_weekly_report(mock_sector_data, mock_macro_data)
        
        print("✅ 周报生成成功")
        print(f"报告内容 (前500字符): {report[:500]}...")
        
        return report
        
    except Exception as e:
        print(f"❌ 周报生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_with_real_data():
    """使用真实数据测试 AnalyzeAgent"""
    print("\n🔄 使用真实数据测试...")
    
    try:
        agent = AnalyzeAgent()
        
        # 1. 获取真实新闻数据并提取主题
        print("1. 获取最新新闻...")
        news = fetch_latest_news()
        print(f"获取到 {len(news)} 条新闻")
        
        if news:
            print("2. 进行主题提取...")
            topic_analysis = agent.extract_topics(news[:3])  # 只测试前3条新闻
            print(f"完成主题分析，共 {len(topic_analysis)} 个分析结果")
            
            for i, analysis in enumerate(topic_analysis, 1):
                print(f"\n--- 真实数据分析 {i} ---")
                print(f"标题: {analysis['title']}")
                print(f"分析: {analysis['analysis'][:150]}...")
        
        # 2. 获取真实行业和宏观数据并生成周报
        print("\n3. 获取行业数据...")
        sector_data = get_sector_performance()
        
        print("4. 获取宏观数据...")
        macro_data = get_macro_indicators()
        
        print("5. 生成周报...")
        report = agent.generate_weekly_report(sector_data, macro_data)
        print(f"✅ 真实数据周报生成成功")
        print(f"报告内容 (前300字符): {report[:300]}...")
        
        return {
            "topic_analysis": topic_analysis if news else [],
            "weekly_report": report
        }
        
    except Exception as e:
        print(f"❌ 真实数据测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始测试 AnalyzeAgent...")
    print("=" * 60)
    
    # 测试1: 模拟数据主题提取
    mock_topics = test_extract_topics()
    
    # 测试2: 模拟数据周报生成
    mock_report = test_weekly_report()
    
    # 测试3: 真实数据测试
    real_data_results = test_with_real_data()
    
    print("\n" + "=" * 60)
    print("📋 测试总结:")
    print(f"✅ 主题提取 (模拟数据): {'通过' if mock_topics else '失败'}")
    print(f"✅ 周报生成 (模拟数据): {'通过' if mock_report else '失败'}")
    print(f"✅ 真实数据集成测试: {'通过' if real_data_results else '失败'}")
    
    # 计算成功率
    tests_passed = sum([
        bool(mock_topics),
        bool(mock_report), 
        bool(real_data_results)
    ])
    success_rate = tests_passed / 3 * 100
    
    print(f"\n🎯 总体成功率: {success_rate:.1f}% ({tests_passed}/3)")
    
    if success_rate == 100:
        print("🎉 所有测试通过！AnalyzeAgent 工作正常")
    elif success_rate >= 66:
        print("⚠️ 大部分测试通过，但有部分功能需要检查")
    else:
        print("❌ 多个测试失败，需要检查配置和依赖")
    
    return {
        "mock_topics": mock_topics,
        "mock_report": mock_report,
        "real_data_results": real_data_results,
        "success_rate": success_rate
    }

if __name__ == "__main__":
    try:
        results = run_all_tests()
        print(f"\n✅ AnalyzeAgent 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
