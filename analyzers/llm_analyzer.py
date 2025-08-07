
import openai
import yaml
from string import Template

def load_openai_key():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    openai.api_key = config["openai_api_key"]

load_openai_key()

with open("prompts/weekly_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = Template(f.read())

def generate_weekly_report(sector_data, macro_data):
    prompt = base_prompt.substitute({
        "sector_data": str(sector_data),
        "macro_data": str(macro_data)
    })

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是金融市场分析专家"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response["choices"][0]["message"]["content"]
