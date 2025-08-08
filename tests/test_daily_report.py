#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试每日报告生成功能
"""

import sys
import os
from pathlib import Path
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.analyze_agent import AnalyzeAgent

def test_daily_report():
    """测试每日报告生成功能"""
    print("🔄 测试每日报告生成...")
    
    # 模拟行业数据
    mock_sector_data = {
        "科技": {
            "涨跌幅": "+2.5%",
            "成交量": "较高",
            "领涨股": ["AAPL", "MSFT", "GOOGL"],
            "概述": "科技股普遍走强，AI概念继续发力"
        },
        "新能源": {
            "涨跌幅": "+1.8%",
            "成交量": "中等",
            "领涨股": ["TSLA", "NIO", "PLUG"],
            "概述": "新能源汽车销量超预期"
        },
        "医药": {
            "涨跌幅": "-0.5%",
            "成交量": "较低",
            "领跌股": ["PFE", "JNJ", "MRK"],
            "概述": "医药股承压，政策面有不确定性"
        }
    }
    
    # 模拟宏观数据
    mock_macro_data = {
        "GDP增速": "5.2%",
        "CPI同比": "2.1%",
        "PPI同比": "-2.5%",
        "社会融资规模": "3.1万亿",
        "PMI": "50.2",
        "市场概况": "市场整体呈现震荡上行态势，成交量有所放大"
    }
    
    try:
        # 初始化 Agent
        agent = AnalyzeAgent()
        
        # 生成报告
        print("\n1. 生成每日报告...")
        report_content, report_path = agent.generate_daily_report(mock_sector_data, mock_macro_data)
        
        # 验证报告文件
        report_file = Path(report_path)
        if not report_file.exists():
            raise FileNotFoundError(f"报告文件未生成: {report_path}")
        
        # 读取并显示报告内容预览
        print("\n2. 报告生成成功！")
        print(f"📝 报告路径: {report_path}")
        print("\n3. 报告内容预览:")
        print("-" * 60)
        preview_lines = report_content.split("\n")[:10]  # 显示前10行
        print("\n".join(preview_lines))
        print("...")
        print("-" * 60)
        
        return True, report_path
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """运行测试"""
    print("🚀 开始测试每日报告生成功能...\n")
    success, report_path = test_daily_report()
    
    if success:
        print("\n✅ 测试通过！")
        print(f"📊 报告已生成在: {report_path}")
        print("\n下一步:")
        print("1. 检查报告内容和格式是否符合要求")
        print("2. 验证 LangSmith 中的追踪数据")
        print("3. 可以在浏览器中打开报告查看完整内容")
    else:
        print("\n❌ 测试失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
