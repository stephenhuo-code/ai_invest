import os
import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

from utils.env_loader import get_required_env, get_optional_env

# LangChain / LangSmith
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except Exception as e:
    raise RuntimeError("需要安装 langchain-openai 和 langchain 依赖: pip install langchain langchain-openai langchain-community langsmith") from e


def _load_prompt_file_to_template(path: str) -> str:
    """读取提示词文件并将 $var 或 ${var} 形式转换为 {var} 以兼容 ChatPromptTemplate。
    保持文本内容不变，仅替换变量占位符。
    """
    content = Path(path).read_text(encoding="utf-8")
    # 兼容 ${var} -> {var}
    content = content.replace("${sector_data}", "{sector_data}")
    content = content.replace("${macro_data}", "{macro_data}")
    # 兼容 $news_text -> {news_text}
    content = content.replace("$news_text", "{news_text}")
    return content


class AnalyzeAgent:
    """使用单一 LangChain Agent 完成主题提取与周报生成。支持 LangSmith 监控。"""

    def __init__(self) -> None:
        # OpenAI 配置
        openai_api_key = get_required_env("OPENAI_API_KEY", "OpenAI API 密钥")
        model_name = get_optional_env("OPENAI_MODEL_ANALYZE", "gpt-4o")

        # LangSmith 监控（可选，通过环境变量开启）
        # 推荐：LANGCHAIN_TRACING_V2=true 且设置 LANGCHAIN_API_KEY
        # 兼容：LANGSMITH_TRACING=true
        tracing_enabled = (
            get_optional_env("LANGCHAIN_TRACING_V2", "false").lower() in {"1", "true", "yes"}
            or get_optional_env("LANGSMITH_TRACING", "false").lower() in {"1", "true", "yes"}
        )
        if tracing_enabled:
            os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
            project = get_optional_env("LANGCHAIN_PROJECT", get_optional_env("LANGSMITH_PROJECT", "ai_invest"))
            if project:
                os.environ.setdefault("LANGCHAIN_PROJECT", project)

        # 初始化 LLM（单例，用于两类任务）
        self.llm = ChatOpenAI(model=model_name, api_key=openai_api_key, temperature=0.3)
        self.output_parser = StrOutputParser()

        # 构建 Prompt 模板
        trend_prompt_text = _load_prompt_file_to_template("prompts/trend_analysis_prompt.txt")
        daily_prompt_text = _load_prompt_file_to_template("prompts/daily_report_prompt.txt")

        self.trend_prompt = ChatPromptTemplate.from_template(trend_prompt_text)
        self.daily_prompt = ChatPromptTemplate.from_template(daily_prompt_text)

        # 组合链（LCEL）
        self.trend_chain = self.trend_prompt | self.llm | self.output_parser
        self.daily_chain = self.daily_prompt | self.llm | self.output_parser

    def extract_topics(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """对新闻列表做主题提取。返回 [{title, analysis}]。"""
        results: List[Dict[str, str]] = []
        for item in news_list:
            title = item.get("title", "无标题")
            news_text = (item.get("text") or "").strip()
            if not news_text:
                results.append({"title": title, "analysis": "分析失败: 新闻内容为空"})
                continue

            truncated = news_text[:2000]
            try:
                analysis = self.trend_chain.invoke(
                    {"news_text": truncated},
                    config={
                        "run_name": "analyze_agent:extract_topics",
                        "tags": ["analyze_agent", "extract_topics"],
                        "metadata": {"title": title},
                    },
                )
                results.append({"title": title, "analysis": analysis})
            except Exception as e:
                results.append({"title": title, "analysis": f"分析失败: {str(e)}"})
        return results

    def generate_daily_report(self, sector_data: Any, macro_data: Any) -> Tuple[str, str]:
        """基于行业与宏观数据生成每日报告。
        
        Returns:
            Tuple[str, str]: (报告内容, 报告文件路径)
        """
        try:
            # 生成报告内容
            report = self.daily_chain.invoke(
                {
                    "sector_data": str(sector_data),
                    "macro_data": str(macro_data)
                },
                config={
                    "run_name": "analyze_agent:daily_report",
                    "tags": ["analyze_agent", "daily_report"],
                },
            )
            
            # 生成报告文件名
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            
            report_path = report_dir / f"report_{timestamp}.md"
            
            # 替换日期并写入报告文件
            current_date = datetime.datetime.now().strftime("%Y年%m月%d日")
            report_content = report.replace("{current_date}", current_date)
            report_path.write_text(report_content, encoding="utf-8")
            
            return report, str(report_path)
        except Exception as e:
            raise RuntimeError(f"生成每日报告失败: {str(e)}")