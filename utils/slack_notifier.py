
import requests
import os
from utils.env_loader import get_optional_env

def send_to_slack(summary, report_path):
    """发送 Slack 通知"""
    webhook = get_optional_env("SLACK_WEBHOOK_URL")
    
    if not webhook:
        print("未设置 SLACK_WEBHOOK_URL 环境变量，跳过 Slack 通知")
        return
    
    # 检查是否是示例 URL
    if "your/webhook/url" in webhook or "T00000000" in webhook:
        print("检测到示例 webhook URL，跳过 Slack 通知")
        return
    
    try:
        # 读取报告内容
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # 截取报告内容（Slack 消息长度限制）
            max_length = 3000  # Slack 消息长度限制
            if len(report_content) > max_length:
                report_content = report_content[:max_length] + "\n\n... (内容已截断，完整报告请查看本地文件)"
            
            # 构建消息
            message = {
                "text": f"*📊 投资研究周报*\n\n{report_content}"
            }
        else:
            # 如果文件不存在，发送摘要
            message = {
                "text": f"*📊 投资研究周报*\n摘要：{summary}\n📄 本地报告: `{report_path}`"
            }
        
        response = requests.post(webhook, json=message)
        response.raise_for_status()
        print("Slack 通知发送成功")
        
    except Exception as e:
        print(f"Slack 通知发送失败: {str(e)}")
        # 发送简化消息作为备选
        try:
            fallback_message = {
                "text": f"*📊 投资研究周报*\n摘要：{summary}\n📄 本地报告: `{report_path}`"
            }
            requests.post(webhook, json=fallback_message)
            print("发送简化消息成功")
        except Exception as e2:
            print(f"发送简化消息也失败: {str(e2)}")
