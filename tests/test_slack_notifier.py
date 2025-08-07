#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 Slack 通知功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.slack_notifier import send_to_slack

def test_slack_notification():
    """测试 Slack 通知"""
    print("开始测试 Slack 通知...")
    
    # 测试数据
    test_summary = "这是一条测试摘要，用于验证 Slack 通知功能是否正常工作。"
    test_report_path = "reports/test_report.md"
    
    print(f"测试摘要: {test_summary}")
    print(f"测试报告路径: {test_report_path}")
    
    # 发送测试通知
    send_to_slack(test_summary, test_report_path)
    
    print("Slack 通知测试完成")

if __name__ == "__main__":
    test_slack_notification() 