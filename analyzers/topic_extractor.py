
import openai
import yaml
from string import Template

def load_openai_key():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    openai.api_key = config["openai_api_key"]

load_openai_key()

with open("prompts/trend_analysis_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = Template(f.read())

def extract_topics_with_gpt(news_list):
    results = []
    for item in news_list:
        prompt = base_prompt.substitute(news_text=item["text"][:2000])
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是金融领域的分析专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        results.append({
            "title": item["title"],
            "analysis": response["choices"][0]["message"]["content"]
        })
    return results
