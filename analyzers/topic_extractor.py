
import os
from typing import List, Dict, Any

from utils.env_loader import get_required_env
from analyzers.analyze_agent import AnalyzeAgent

# 保留原始 API，内部委托给 LangChain Agent

def extract_topics_with_gpt(news_list: List[Dict[str, Any]]):
    agent = AnalyzeAgent()
    return agent.extract_topics(news_list)
