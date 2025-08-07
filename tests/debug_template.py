#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细调试模板替换问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from string import Template

def debug_template():
    """调试模板替换"""
    print("开始调试模板替换...")
    
    # 1. 读取模板文件
    print("1. 读取模板文件...")
    try:
        with open("prompts/trend_analysis_prompt.txt", "r", encoding="utf-8") as f:
            template_content = f.read()
        print(f"模板内容:\n{template_content}")
        print(f"模板长度: {len(template_content)}")
    except Exception as e:
        print(f"❌ 读取模板失败: {str(e)}")
        return
    
    # 2. 创建测试数据
    print("\n2. 创建测试数据...")
    test_news_text = "这是一条测试新闻内容，用于验证模板替换是否正常工作。"
    print(f"测试新闻文本: {test_news_text}")
    
    # 3. 创建模板对象
    print("\n3. 创建模板对象...")
    template = Template(template_content)
    print(f"模板对象: {template}")
    
    # 4. 执行替换
    print("\n4. 执行模板替换...")
    try:
        result = template.substitute(news_text=test_news_text)
        print(f"替换结果:\n{result}")
        print(f"结果长度: {len(result)}")
        
        # 检查替换是否成功
        if "{{news_text}}" in result:
            print("❌ 模板变量没有被替换！")
        elif test_news_text in result:
            print("✅ 模板替换成功！")
        else:
            print("⚠️ 模板替换可能有问题")
            
    except Exception as e:
        print(f"❌ 模板替换失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_template() 