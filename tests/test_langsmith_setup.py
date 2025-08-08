#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 LangSmith 配置是否正确
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_env_setup():
    """测试环境变量设置"""
    print("🔍 检查环境变量设置...")
    
    # 加载环境变量
    load_dotenv()
    
    required_vars = {
        "LANGCHAIN_API_KEY": "LangSmith API 密钥",
        "OPENAI_API_KEY": "OpenAI API 密钥",
    }
    
    optional_vars = {
        "LANGCHAIN_PROJECT": "项目名称 (默认: ai_invest)",
        "LANGCHAIN_ENDPOINT": "API 端点 (默认: https://api.smith.langchain.com)",
    }
    
    # 检查必需的环境变量
    missing_vars = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"- {var}: {desc}")
    
    if missing_vars:
        print("\n❌ 缺少必需的环境变量:")
        print("\n".join(missing_vars))
        print("\n请在 .env 文件中设置这些变量")
        return False
    
    # 检查可选的环境变量
    print("\n✅ 所有必需的环境变量已设置")
    print("\n📝 可选环境变量状态:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        status = "已设置" if value else "使用默认值"
        print(f"- {var}: {status}")
    
    # 验证 LANGCHAIN_TRACING_V2
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in {"true", "1", "yes"}
    print(f"\nLangSmith 追踪状态: {'启用' if tracing_enabled else '禁用'}")
    
    return True

def test_langchain_imports():
    """测试 LangChain 相关包的导入"""
    print("\n📦 测试包导入...")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        print("✅ LangChain 相关包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 包导入失败: {str(e)}")
        print("\n可能的解决方案:")
        print("1. 确保已安装所有依赖: pip install langchain langchain-openai")
        print("2. 检查 Python 环境是否正确")
        return False

def test_simple_chain():
    """测试简单的 LangChain 调用"""
    print("\n🔄 测试 LangChain 调用...")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # 创建一个简单的链
        llm = ChatOpenAI()
        prompt = ChatPromptTemplate.from_template("用一句话解释什么是 {topic}")
        chain = prompt | llm | StrOutputParser()
        
        # 执行调用
        result = chain.invoke({"topic": "人工智能"})
        
        print("✅ LangChain 调用成功")
        print(f"测试结果: {result}")
        return True
    except Exception as e:
        print(f"❌ LangChain 调用失败: {str(e)}")
        print("\n可能的原因:")
        print("1. API 密钥无效")
        print("2. 网络连接问题")
        print("3. 配置错误")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("🚀 开始测试 LangSmith 设置...\n")
    
    # 运行测试
    env_ok = test_env_setup()
    imports_ok = test_langchain_imports()
    chain_ok = test_simple_chain() if env_ok and imports_ok else False
    
    # 输出总结
    print("\n📋 测试总结:")
    print(f"环境变量设置: {'✅' if env_ok else '❌'}")
    print(f"包导入测试: {'✅' if imports_ok else '❌'}")
    print(f"LangChain 调用: {'✅' if chain_ok else '❌'}")
    
    if all([env_ok, imports_ok, chain_ok]):
        print("\n🎉 所有测试通过！LangSmith 设置成功")
        print("\n下一步:")
        print("1. 访问 https://smith.langchain.com/ 查看追踪数据")
        print("2. 在项目中开始使用 LangChain")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
    
    return all([env_ok, imports_ok, chain_ok])

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
