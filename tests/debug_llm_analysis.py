#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试 LLM 分析过程
检查 LLM 分析过程中的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.news_fetcher import fetch_latest_news
from analyzers.topic_extractor import extract_topics_with_gpt
from string import Template

def debug_llm_analysis():
    """调试 LLM 分析过程"""
    print("开始调试 LLM 分析...")
    
    # 1. 获取新闻
    print("1. 获取新闻...")
    news = fetch_latest_news(max_articles=2)  # 只获取2条用于测试
    print(f"获取到 {len(news)} 条新闻")
    
    if not news:
        print("❌ 没有获取到新闻")
        return
    
    # 2. 检查新闻内容
    print("\n2. 检查新闻内容...")
    for i, item in enumerate(news):
        print(f"\n新闻 {i+1}:")
        print(f"标题: {item['title']}")
        print(f"文本长度: {len(item['text'])}")
        print(f"文本预览: {item['text'][:200]}...")
        
        # 检查文本是否为空
        if not item['text'].strip():
            print("⚠️ 新闻文本为空！")
        else:
            print("✅ 新闻文本正常")
    
    # 3. 检查提示词模板
    print("\n3. 检查提示词模板...")
    try:
        with open("prompts/trend_analysis_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
        print(f"提示词模板长度: {len(prompt_template)}")
        print(f"提示词模板内容:\n{prompt_template}")
    except Exception as e:
        print(f"❌ 读取提示词模板失败: {str(e)}")
        return
    
    # 4. 测试单个新闻的 LLM 分析
    print("\n4. 测试单个新闻的 LLM 分析...")
    if news:
        test_news = news[0]
        print(f"测试新闻标题: {test_news['title']}")
        
        # 构建提示词
        template = Template(prompt_template)
        prompt = template.substitute(news_text=test_news['text'][:2000])
        
        print(f"构建的提示词长度: {len(prompt)}")
        print(f"提示词预览:\n{prompt[:500]}...")
        
        # 检查提示词中是否包含新闻内容
        if "{{news_text}}" in prompt:
            print("❌ 提示词模板中的变量没有被替换！")
        elif test_news['text'][:100] in prompt:
            print("✅ 提示词中包含了新闻内容")
        else:
            print("⚠️ 提示词中可能没有正确包含新闻内容")
            print(f"新闻内容前100字符: {test_news['text'][:100]}")
            print(f"提示词中是否包含新闻内容: {test_news['text'][:50] in prompt}")
        
        # 尝试 LLM 分析
        try:
            print("\n5. 执行 LLM 分析...")
            result = extract_topics_with_gpt([test_news])
            print(f"LLM 分析结果: {result[0]['analysis']}")
        except Exception as e:
            print(f"❌ LLM 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_llm_analysis() 