#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试高级 Slack 通知功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.slack_advanced import send_to_slack_with_file, send_simple_notification

def test_advanced_slack_notification():
    """测试高级 Slack 通知功能"""
    print("开始测试高级 Slack 通知...")
    
    # 测试数据
    test_summary = "这是一条测试摘要，用于验证高级 Slack 通知功能。"
    test_report_path = "reports/report_2025-08-07_19-04.md"  # 使用现有的报告文件
    
    print(f"测试摘要: {test_summary}")
    print(f"测试报告路径: {test_report_path}")
    
    # 检查报告文件是否存在
    if not os.path.exists(test_report_path):
        print(f"⚠️ 报告文件不存在: {test_report_path}")
        # 创建一个测试报告文件
        test_report_path = "reports/test_report.md"
        with open(test_report_path, 'w', encoding='utf-8') as f:
            f.write("# 测试报告\n\n这是一个测试报告文件，用于验证 Slack 通知功能。\n\n## 内容\n\n包含一些测试内容...")
        print(f"创建测试报告文件: {test_report_path}")
    
    # 测试简单通知
    print("\n1. 测试简单通知...")
    send_simple_notification(test_summary, test_report_path)
    
    # 测试高级通知
    print("\n2. 测试高级通知...")
    send_to_slack_with_file(test_summary, test_report_path)
    
    print("\n高级 Slack 通知测试完成")

if __name__ == "__main__":
    test_advanced_slack_notification() 