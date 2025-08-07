#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级 Slack 通知器
支持文件上传和富文本消息
"""

import requests
import os
from utils.env_loader import get_optional_env

def send_to_slack_with_file(summary, report_path):
    """发送 Slack 通知并上传文件"""
    webhook = get_optional_env("SLACK_WEBHOOK_URL")
    bot_token = get_optional_env("SLACK_BOT_TOKEN")  # 可选，用于文件上传
    
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
            
            # 发送消息
            message = {
                "text": f"*📊 投资研究周报*\n摘要：{summary}\n📄 报告已生成，内容如下：",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 投资研究周报"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"摘要：{summary}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📄 报告内容："
                        }
                    }
                ]
            }
            
            # 添加报告内容块（分段发送以避免长度限制）
            content_chunks = split_content(report_content, 3000)
            for i, chunk in enumerate(content_chunks):
                if i == 0:
                    # 第一个块添加到现有消息中
                    message["blocks"].append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{chunk}```"
                        }
                    })
                else:
                    # 后续块作为单独消息发送
                    chunk_message = {
                        "text": f"报告内容（续 {i+1}）：",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"```{chunk}```"
                                }
                            }
                        ]
                    }
                    requests.post(webhook, json=chunk_message)
            
            # 发送主消息
            response = requests.post(webhook, json=message)
            response.raise_for_status()
            print("Slack 通知发送成功")
            
        else:
            # 如果文件不存在，发送摘要
            message = {
                "text": f"*📊 投资研究周报*\n摘要：{summary}\n📄 本地报告: `{report_path}`"
            }
            response = requests.post(webhook, json=message)
            response.raise_for_status()
            print("Slack 通知发送成功（仅摘要）")
        
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

def split_content(content, max_length):
    """将内容分割成指定长度的块"""
    chunks = []
    current_chunk = ""
    
    for line in content.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                # 单行太长，强制分割
                chunks.append(line[:max_length])
                current_chunk = line[max_length:]
        else:
            current_chunk += line + '\n'
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def send_simple_notification(summary, report_path):
    """发送简单的 Slack 通知（兼容原版本）"""
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