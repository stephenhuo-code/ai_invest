#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版 AnalyzeAgent 测试脚本
快速验证核心功能，不依赖外部数据获取
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.analyze_agent import AnalyzeAgent

def quick_test():
    """快速测试 AnalyzeAgent 的基本功能"""
    print("⚡ 快速测试 AnalyzeAgent...")
    
    # 简单的测试新闻
    test_news = [
        {
            "title": "腾讯发布AI新产品，游戏板块受关注",
            "text": "腾讯控股(0700.HK)今日发布基于人工智能的新游戏引擎，预计将提升游戏开发效率。这一消息推动了整个游戏板块的股价上涨，网易(NTES)、完美世界等公司股价均有所表现。分析师认为AI技术将为游戏行业带来新的增长动力。"
        }
    ]
    
    # 简单的测试数据
    test_sector = {"科技": {"涨幅": 2.1}, "金融": {"涨幅": -0.5}}
    test_macro = {"GDP增长": 2.3, "通胀率": 2.8}
    
    try:
        # 初始化 Agent
        print("1. 初始化 AnalyzeAgent...")
        agent = AnalyzeAgent()
        print("✅ 初始化成功")
        
        # 测试主题提取
        print("\n2. 测试主题提取...")
        topics = agent.extract_topics(test_news)
        print(f"✅ 主题提取成功，结果:")
        print(f"   标题: {topics[0]['title']}")
        print(f"   分析: {topics[0]['analysis'][:100]}...")
        
        # 测试周报生成
        print("\n3. 测试周报生成...")
        report = agent.generate_weekly_report(test_sector, test_macro)
        print(f"✅ 周报生成成功，内容:")
        print(f"   {report[:150]}...")
        
        print(f"\n🎉 所有测试通过！AnalyzeAgent 工作正常")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)
