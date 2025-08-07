
import openai
from string import Template
from utils.env_loader import get_required_env

# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=get_required_env("OPENAI_API_KEY", "OpenAI API 密钥"))

def load_prompt_template():
    """加载提示词模板"""
    with open("prompts/trend_analysis_prompt.txt", "r", encoding="utf-8") as f:
        return Template(f.read())

def extract_topics_with_gpt(news_list):
    results = []
    base_prompt = load_prompt_template()
    
    for item in news_list:
        # 确保新闻文本不为空
        news_text = item.get("text", "").strip()
        if not news_text:
            print(f"警告: 新闻 '{item.get('title', '无标题')}' 的文本为空")
            continue
            
        # 限制文本长度并替换模板变量
        prompt = base_prompt.substitute(news_text=news_text[:2000])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是金融领域的分析专家"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            results.append({
                "title": item["title"],
                "analysis": response.choices[0].message.content
            })
        except Exception as e:
            print(f"LLM 分析失败: {str(e)}")
            results.append({
                "title": item["title"],
                "analysis": f"分析失败: {str(e)}"
            })
    
    return results
