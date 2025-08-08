
import openai
from string import Template
from utils.env_loader import get_required_env
from typing import Any

from analyzers.analyze_agent import AnalyzeAgent


# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=get_required_env("OPENAI_API_KEY", "OpenAI API 密钥"))

with open("prompts/weekly_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = Template(f.read())

def generate_weekly_report(sector_data: Any, macro_data: Any) -> str:
    agent = AnalyzeAgent()
    return agent.generate_weekly_report(sector_data, macro_data)
