import os
import datetime
import json
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

    def extract_topics(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对新闻列表做主题提取。返回结构化的分析结果，包含股票信息。
        
        Returns:
            List[Dict]: 包含以下字段的结果列表：
            - title: 新闻标题
            - industry_themes: 行业主题列表
            - stocks: 股票信息列表 [{"company_name", "stock_code", "market"}]
            - sentiment: 情绪判断
            - summary: 简要总结
            - raw_analysis: 原始分析文本
        """
        results: List[Dict[str, Any]] = []
        for item in news_list:
            title = item.get("title", "无标题")
            news_text = (item.get("text") or "").strip()
            if not news_text:
                results.append({
                    "title": title, 
                    "industry_themes": [],
                    "stocks": [],
                    "sentiment": "未知",
                    "summary": "分析失败: 新闻内容为空",
                    "raw_analysis": "分析失败: 新闻内容为空"
                })
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
                print(analysis)
                
                # 尝试解析JSON结果
                try:
                    parsed_data = json.loads(analysis)
                    result = {
                        "title": title,
                        "industry_themes": parsed_data.get("industry_themes", []),
                        "stocks": parsed_data.get("stocks", []),
                        "sentiment": parsed_data.get("sentiment", "未知"),
                        "summary": parsed_data.get("summary", ""),
                        "raw_analysis": analysis
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始分析结果
                    result = {
                        "title": title,
                        "industry_themes": [],
                        "stocks": [],
                        "sentiment": "未知",
                        "summary": "JSON解析失败",
                        "raw_analysis": analysis
                    }
                
                results.append(result)
            except Exception as e:
                results.append({
                    "title": title,
                    "industry_themes": [],
                    "stocks": [],
                    "sentiment": "未知",
                    "summary": f"分析失败: {str(e)}",
                    "raw_analysis": f"分析失败: {str(e)}"
                })
        return results

    def extract_all_stocks(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """从分析结果中提取所有股票信息，用于后续股票分析。
        
        Args:
            analysis_results: extract_topics 方法返回的分析结果列表
            
        Returns:
            List[Dict]: 去重后的股票信息列表，每个元素包含：
            - company_name: 公司名称
            - stock_code: 股票代码
            - market: 市场
            - sentiment: 相关新闻的情绪
        """
        all_stocks = []
        seen_stocks = set()
        
        for result in analysis_results:
            stocks = result.get("stocks", [])
            sentiment = result.get("sentiment", "未知")
            
            for stock in stocks:
                stock_code = stock.get("stock_code", "").strip()
                company_name = stock.get("company_name", "").strip()
                market = stock.get("market", "").strip()
                
                if stock_code and stock_code not in seen_stocks:
                    seen_stocks.add(stock_code)
                    all_stocks.append({
                        "company_name": company_name,
                        "stock_code": stock_code,
                        "market": market,
                        "sentiment": sentiment
                    })
        
        return all_stocks

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