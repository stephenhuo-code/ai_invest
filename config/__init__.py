"""
配置包
导出所有配置项
"""

from .settings import *

__all__ = [
    # 基础配置
    'BASE_DIR', 'REPORTS_DIR', 'PROMPTS_DIR',
    
    # 应用配置
    'APP_NAME', 'APP_VERSION', 'APP_DESCRIPTION',
    
    # 服务器配置
    'HOST', 'PORT',
    
    # 日志配置
    'LOG_LEVEL', 'LOG_FORMAT',
    
    # OpenAI配置
    'OPENAI_MODEL_ANALYZE', 'OPENAI_TEMPERATURE', 'OPENAI_MAX_TOKENS', 'OPENAI_TIMEOUT',
    
    # LangChain配置
    'LANGSMITH_PROJECT', 'LANGSMITH_ENDPOINT', 'LANGSMITH_TRACING',
    
    # RSS源配置
    'RSS_FEEDS', 'MAX_NEWS_ARTICLES',
    
    # 数据获取配置
    'NEWS_CACHE_DURATION', 'PRICE_CACHE_DURATION', 'SECTOR_CACHE_DURATION', 'MACRO_CACHE_DURATION',
    
    # 分析配置
    'MAX_NEWS_LENGTH', 'MAX_STOCKS_PER_ANALYSIS', 'SENTIMENT_THRESHOLDS',
    
    # 报告配置
    'REPORT_FORMAT', 'REPORT_TEMPLATE', 'REPORT_LANGUAGE',
    
    # Slack配置
    'SLACK_ENABLED', 'SLACK_CHANNEL', 'SLACK_USERNAME', 'SLACK_ICON_EMOJI',
    
    # 缓存配置
    'CACHE_ENABLED', 'CACHE_TYPE', 'CACHE_TTL',
    
    # 限流配置
    'RATE_LIMIT_ENABLED', 'RATE_LIMIT_REQUESTS', 'RATE_LIMIT_WINDOW',
    
    # 健康检查配置
    'HEALTH_CHECK_ENABLED', 'HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_TIMEOUT',
    
    # 监控配置
    'METRICS_ENABLED', 'METRICS_PORT',
    
    # 安全配置
    'CORS_ENABLED', 'CORS_ORIGINS', 'API_KEY_HEADER',
    
    # 数据库配置
    'DATABASE_POOL_SIZE', 'DATABASE_MAX_OVERFLOW',
    
    # 外部API配置
    'YAHOO_FINANCE_TIMEOUT', 'NEWSPAPER_TIMEOUT',
    
    # 工具函数
    'ensure_directories', 'validate_config',
] 