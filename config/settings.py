"""
应用配置文件
包含所有非敏感的配置信息，确保开发和生产环境一致
敏感信息（API keys）仍然通过环境变量配置
"""

import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
PROMPTS_DIR = BASE_DIR / "prompts"

# 应用配置
APP_NAME = "AI Invest Trend API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI驱动的投资趋势分析API"

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# OpenAI配置 (非敏感部分)
OPENAI_MODEL_ANALYZE = "gpt-4o"
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 4000
OPENAI_TIMEOUT = 120

# LangChain配置 (非敏感部分)
LANGCHAIN_PROJECT = "ai_invest"
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_TRACING_V2 = True  # 默认关闭，可通过环境变量覆盖

# RSS源配置
RSS_FEEDS = ["https://finance.yahoo.com/news/rssindex"]
MAX_NEWS_ARTICLES = 5

# 数据获取配置
NEWS_CACHE_DURATION = 3600  # 1小时
PRICE_CACHE_DURATION = 300  # 5分钟
SECTOR_CACHE_DURATION = 3600  # 1小时
MACRO_CACHE_DURATION = 86400  # 24小时

# 分析配置
MAX_NEWS_LENGTH = 2000  # 单条新闻最大长度
MAX_STOCKS_PER_ANALYSIS = 10  # 每次分析最大股票数
SENTIMENT_THRESHOLDS = {
    "positive": 0.6,
    "negative": 0.4
}

# 报告配置
REPORT_FORMAT = "markdown"  # markdown, html, pdf
REPORT_TEMPLATE = "default"
REPORT_LANGUAGE = "zh-CN"  # zh-CN, en-US

# Slack配置 (非敏感部分)
SLACK_ENABLED = False  # 默认关闭，可通过环境变量覆盖
SLACK_CHANNEL = "#ai-invest"
SLACK_USERNAME = "AI Invest Bot"
SLACK_ICON_EMOJI = ":chart_with_upwards_trend:"

# 缓存配置
CACHE_ENABLED = True
CACHE_TYPE = "memory"  # memory, redis, file
CACHE_TTL = 3600  # 默认1小时

# 限流配置
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS = 100  # 每分钟请求数
RATE_LIMIT_WINDOW = 60  # 时间窗口(秒)

# 健康检查配置
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_INTERVAL = 30  # 检查间隔(秒)
HEALTH_CHECK_TIMEOUT = 10  # 超时时间(秒)

# 监控配置
METRICS_ENABLED = True
METRICS_PORT = 9090

# 安全配置
CORS_ENABLED = True
CORS_ORIGINS = ["*"]
API_KEY_HEADER = "X-API-Key"

# 数据库配置 (如果将来需要)
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20

# 外部API配置
YAHOO_FINANCE_TIMEOUT = 30
NEWSPAPER_TIMEOUT = 60

# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [REPORTS_DIR, PROMPTS_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 配置验证
def validate_config():
    """验证配置的有效性"""
    errors = []
    
    if MAX_NEWS_ARTICLES <= 0:
        errors.append("MAX_NEWS_ARTICLES must be positive")
    
    if MAX_NEWS_LENGTH <= 0:
        errors.append("MAX_NEWS_LENGTH must be positive")
    
    if MAX_STOCKS_PER_ANALYSIS <= 0:
        errors.append("MAX_STOCKS_PER_ANALYSIS must be positive")
    
    if RATE_LIMIT_REQUESTS <= 0:
        errors.append("RATE_LIMIT_REQUESTS must be positive")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

# 初始化时确保目录存在并验证配置
ensure_directories()
validate_config() 