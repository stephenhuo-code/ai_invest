
import openai
from string import Template
from utils.env_loader import get_required_env

# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=get_required_env("OPENAI_API_KEY", "OpenAI API 密钥"))

with open("prompts/weekly_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = Template(f.read())

def generate_weekly_report(sector_data, macro_data):
    prompt = base_prompt.substitute({
        "sector_data": str(sector_data),
        "macro_data": str(macro_data)
    })

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是金融市场分析专家"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content
