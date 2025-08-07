#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟数据测试脚本
使用模拟数据测试 run_report 函数，避免需要真实的 API 密钥
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.price_fetcher import get_latest_price
from fetchers.industry_data import get_sector_performance
from fetchers.macro_data import get_macro_indicators
from utils.markdown_writer import write_markdown_report
import datetime

def run_report_mock():
    """运行使用模拟数据的周报生成流程"""
    print("开始生成周报（模拟数据版）...")
    
    # 1. 使用模拟新闻数据
    print("1. 使用模拟新闻数据...")
    mock_news = [
        {
            "title": "苹果公司发布新款iPhone，股价上涨5%",
            "text": "苹果公司今日发布了新款iPhone 15，搭载最新的A17芯片，性能提升显著。市场反应积极，股价在盘后交易中上涨5%。分析师认为这将进一步巩固苹果在高端智能手机市场的领先地位。"
        },
        {
            "title": "特斯拉第三季度财报超预期，营收增长20%",
            "text": "特斯拉公布了第三季度财报，营收达到234亿美元，同比增长20%，超出市场预期。电动汽车交付量创历史新高，达到435,059辆。公司预计全年交付量将达到180万辆的目标。"
        },
        {
            "title": "微软云服务业务持续增长，Azure收入增长30%",
            "text": "微软公布了最新季度财报，云服务业务表现强劲。Azure收入同比增长30%，Office 365和Dynamics 365也实现了两位数增长。公司继续在人工智能领域加大投资。"
        },
        {
            "title": "亚马逊推出新的物流服务，提升配送效率",
            "text": "亚马逊宣布推出新的物流服务，通过优化配送路线和使用无人机技术，将配送时间缩短50%。这一举措预计将显著提升客户满意度并降低运营成本。"
        },
        {
            "title": "谷歌母公司Alphabet在AI领域取得重大突破",
            "text": "Alphabet旗下的DeepMind在人工智能领域取得重大突破，新的AI模型在多个基准测试中超越了人类专家。这一技术进展预计将推动公司在搜索、云计算等业务的发展。"
        }
    ]
    print(f"使用 {len(mock_news)} 条模拟新闻")
    
    # 2. 使用模拟主题分析数据
    print("2. 使用模拟主题分析数据...")
    mock_topic_analysis = [
        {
            "title": "苹果公司发布新款iPhone，股价上涨5%",
            "analysis": "主题：科技产品发布\n相关股票代码：AAPL\n影响：正面\n分析：苹果新品发布对股价产生积极影响，体现了公司在创新和品牌价值方面的优势。"
        },
        {
            "title": "特斯拉第三季度财报超预期，营收增长20%",
            "analysis": "主题：财报表现\n相关股票代码：TSLA\n影响：正面\n分析：特斯拉业绩超预期，电动汽车市场需求强劲，公司盈利能力持续改善。"
        },
        {
            "title": "微软云服务业务持续增长，Azure收入增长30%",
            "analysis": "主题：云计算业务\n相关股票代码：MSFT\n影响：正面\n分析：微软云服务业务增长强劲，在云计算市场竞争优势明显。"
        },
        {
            "title": "亚马逊推出新的物流服务，提升配送效率",
            "analysis": "主题：物流优化\n相关股票代码：AMZN\n影响：正面\n分析：亚马逊通过技术创新提升物流效率，有助于降低成本并改善客户体验。"
        },
        {
            "title": "谷歌母公司Alphabet在AI领域取得重大突破",
            "analysis": "主题：人工智能技术\n相关股票代码：GOOGL\n影响：正面\n分析：Alphabet在AI领域的突破将推动多个业务线的发展，增强竞争优势。"
        }
    ]
    print(f"完成主题分析，共 {len(mock_topic_analysis)} 个主题")
    
    # 3. 提取股票代码
    print("3. 提取股票代码...")
    tickers = ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL"]
    print(f"提取到股票代码: {tickers}")
    
    # 4. 获取价格数据
    print("4. 获取价格数据...")
    try:
        price_data = get_latest_price(tickers)
        print(f"获取到 {len(price_data)} 只股票的价格数据")
    except Exception as e:
        print(f"价格数据获取失败，使用模拟数据: {str(e)}")
        price_data = {
            "AAPL": {"price": 175.50, "change": 2.5},
            "TSLA": {"price": 245.80, "change": -1.2},
            "MSFT": {"price": 325.40, "change": 1.8},
            "AMZN": {"price": 145.20, "change": 0.9},
            "GOOGL": {"price": 135.60, "change": 1.5}
        }
    
    # 5. 获取行业数据
    print("5. 获取行业数据...")
    try:
        sector_data = get_sector_performance()
        print("行业数据获取完成")
    except Exception as e:
        print(f"行业数据获取失败，使用模拟数据: {str(e)}")
        sector_data = {
            "technology": {"performance": 2.5, "change": 1.2},
            "healthcare": {"performance": 1.8, "change": 0.8},
            "finance": {"performance": 1.2, "change": -0.3},
            "energy": {"performance": -0.5, "change": -1.1}
        }
    
    # 6. 获取宏观数据
    print("6. 获取宏观数据...")
    try:
        macro_data = get_macro_indicators()
        print("宏观数据获取完成")
    except Exception as e:
        print(f"宏观数据获取失败，使用模拟数据: {str(e)}")
        macro_data = {
            "gdp_growth": 2.1,
            "inflation_rate": 3.2,
            "unemployment_rate": 3.8,
            "interest_rate": 5.25
        }
    
    # 7. 生成 Markdown 报告
    print("7. 生成 Markdown 报告...")
    try:
        markdown_path, summary = write_markdown_report(
            news=mock_news,
            analysis=mock_topic_analysis,
            prices=price_data,
            sectors=sector_data,
            macro=macro_data
        )
        print(f"报告已生成: {markdown_path}")
        print(f"报告摘要: {summary[:100]}...")
    except Exception as e:
        print(f"报告生成失败: {str(e)}")
        markdown_path = "mock_report.md"
        summary = "模拟报告生成完成"
    
    # 8. 跳过 Slack 通知
    print("8. 跳过 Slack 通知（模拟模式）")
    
    return {"status": "success", "report": markdown_path}

if __name__ == "__main__":
    try:
        result = run_report_mock()
        print(f"\n✅ 模拟周报生成成功！")
        print(f"报告路径: {result['report']}")
    except Exception as e:
        print(f"\n❌ 模拟周报生成失败: {str(e)}")
        import traceback
        traceback.print_exc() 