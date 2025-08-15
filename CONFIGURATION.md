# ⚙️ 配置系统说明

## 📋 配置架构概述

本项目采用分层配置架构，确保开发和生产环境的一致性：

1. **配置文件** (`config/settings.py`) - 包含所有非敏感配置
2. **环境变量** (`.env`) - 仅包含敏感信息（API Keys等）
3. **运行时配置** - 应用启动时自动加载

## 🗂️ 配置文件结构

### `config/settings.py`
包含所有非敏感的配置信息，直接写入代码中：

```python
# 应用配置
APP_NAME = "AI Invest Trend API"
APP_VERSION = "1.0.0"

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# OpenAI配置 (非敏感部分)
OPENAI_MODEL_ANALYZE = "gpt-4o"
OPENAI_TEMPERATURE = 0.3

# RSS源配置
RSS_FEEDS = ["https://finance.yahoo.com/news/rssindex"]
MAX_NEWS_ARTICLES = 5
```

### `.env` 文件
仅包含敏感信息和环境特定配置：

```bash
# 敏感信息
OPENAI_API_KEY=sk-your-openai-api-key-here
LANGCHAIN_API_KEY=ls-your-langsmith-api-key-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx

# Azure部署配置
AZURE_SUBSCRIPTION_ID=your-subscription-id-here
AZURE_RESOURCE_GROUP=rg-ai

# 可选的环境特定配置
DEBUG=true
LANGCHAIN_TRACING_V2=true
```

## 🔧 配置项分类

### ✅ 直接写入配置文件的项
- 应用基本信息（名称、版本、描述）
- 服务器配置（主机、端口）
- 默认参数值（超时时间、缓存时间、限流设置）
- 业务逻辑配置（最大新闻数量、分析参数）
- 非敏感的第三方服务配置

### 🔐 保留在环境变量中的项
- API密钥和访问令牌
- 数据库连接字符串
- 外部服务的认证信息
- 环境特定的开关（调试模式、追踪开关）

## 📖 使用方法

### 1. 导入配置
```python
from config import APP_NAME, MAX_NEWS_ARTICLES, RSS_FEEDS

# 使用配置
app = FastAPI(title=APP_NAME)
news_count = MAX_NEWS_ARTICLES
```

### 2. 环境变量覆盖
如果需要在特定环境中覆盖配置，可以在`.env`文件中设置：

```bash
# 覆盖默认配置
MAX_NEWS_ARTICLES=10
DEBUG=true
```

### 3. 配置验证
应用启动时会自动验证配置的有效性：

```python
# 自动验证
validate_config()
```

## 🚀 部署配置

### 开发环境
```bash
# 复制环境变量模板
cp env.template .env

# 填入真实的API密钥
OPENAI_API_KEY=sk-xxx
LANGCHAIN_API_KEY=ls-xxx
```

### 生产环境
```bash
# 在Azure Container Apps中设置环境变量
az containerapp update \
  --name agent \
  --resource-group rg-ai \
  --set-env-vars \
    OPENAI_API_KEY=sk-xxx \
    LANGCHAIN_API_KEY=ls-xxx
```

## 🔄 配置更新流程

### 1. 修改配置文件
```python
# 在 config/settings.py 中修改
MAX_NEWS_ARTICLES = 10  # 从5改为10
```

### 2. 测试配置
```bash
# 运行配置验证
python -c "from config import validate_config; validate_config()"
```

### 3. 部署更新
```bash
# 提交代码
git add config/settings.py
git commit -m "更新配置：增加最大新闻数量"
git push origin main
```

## 📊 配置监控

### 健康检查端点
```bash
# 检查应用状态
curl http://localhost:8000/

# 查看配置信息
curl http://localhost:8000/docs
```

### 日志输出
应用启动时会输出关键配置信息：

```
INFO: 应用配置加载完成
INFO: 服务器配置: HOST=0.0.0.0, PORT=8000
INFO: OpenAI配置: MODEL=gpt-4o, TEMPERATURE=0.3
```

## ⚠️ 注意事项

### 1. 敏感信息保护
- 永远不要将API密钥提交到代码仓库
- 使用`.env`文件存储敏感信息
- 确保`.env`文件已添加到`.gitignore`

### 2. 配置一致性
- 开发和生产环境使用相同的配置文件
- 通过环境变量控制环境差异
- 定期同步配置文件更新

### 3. 配置验证
- 应用启动时自动验证配置
- 配置错误会导致应用启动失败
- 提供清晰的错误信息

## 🎯 最佳实践

1. **配置分层**: 敏感信息环境变量，非敏感信息配置文件
2. **默认值**: 为所有配置提供合理的默认值
3. **验证**: 启动时验证配置的有效性
4. **文档**: 为每个配置项提供清晰的说明
5. **测试**: 在不同环境中测试配置的正确性

## 📞 配置问题排查

### 常见问题
1. **配置导入失败**: 检查`config/__init__.py`文件
2. **环境变量未生效**: 确认`.env`文件格式正确
3. **配置验证失败**: 检查配置值的合理性

### 调试命令
```bash
# 检查配置加载
python -c "from config import *; print('配置加载成功')"

# 查看特定配置
python -c "from config import MAX_NEWS_ARTICLES; print(MAX_NEWS_ARTICLES)"

# 验证配置
python -c "from config import validate_config; validate_config()"
``` 