# AI Invest Trend

一个基于 FastAPI 的投资研究自动化工具。它会抓取最新财经新闻并使用 OpenAI GPT 模型进行主题分析，结合股票价格、行业表现和宏观经济指标生成每周研究报告，并可将摘要推送到 Slack。

## 功能概览
- **新闻抓取**：从环境变量配置的 RSS 源获取最新新闻，并解析文章内容。
- **主题分析**：调用 OpenAI API 根据提示词提取行业主题、股票代码及情绪。
- **市场数据获取**：
  - `yfinance` 获取股票最新价。
  - 抓取 Yahoo Finance 行业表现。
  - 抓取 TradingEconomics 宏观经济指标。
- **报告生成与通知**：将上述信息整理成 Markdown 周报，保存到 `reports/` 目录，并通过 Slack Webhook 发送摘要。

## 环境准备

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### 必需的环境变量

**OpenAI API 密钥**
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

**获取 OpenAI API 密钥的步骤：**
1. 访问 [OpenAI 平台](https://platform.openai.com/account/api-keys)
2. 登录你的账户
3. 点击 "Create new secret key"
4. 复制生成的 API 密钥

#### 可选的环境变量

**Slack Webhook URL（用于发送通知）**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
```

**获取 Slack Webhook URL 的步骤：**
1. 访问 [Slack API 网站](https://api.slack.com/apps)
2. 点击 "Create New App"
3. 选择 "From scratch"
4. 输入应用名称（如 "AI Invest Bot"）
5. 选择你的工作区
6. 在左侧菜单选择 "Incoming Webhooks"
7. 点击 "Activate Incoming Webhooks"
8. 点击 "Add New Webhook to Workspace"
9. 选择要发送消息的频道（如 #general）
10. 点击 "Allow"
11. 复制生成的 Webhook URL

**Slack Bot Token（可选，用于高级功能）**
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
```

**获取 Slack Bot Token 的步骤：**
1. 在 Slack App 设置页面，选择 "OAuth & Permissions"
2. 在 "Scopes" 部分添加以下权限：
   - `files:write`（用于文件上传）
   - `chat:write`（用于发送消息）
3. 点击 "Install to Workspace"
4. 复制 "Bot User OAuth Token"

**RSS 源配置**
```bash
export RSS_FEEDS="https://finance.yahoo.com/news/rssindex"
```

**支持多个 RSS 源：**
```bash
export RSS_FEEDS="https://finance.yahoo.com/news/rssindex,https://feeds.reuters.com/reuters/businessNews"
```

**最大新闻数量**
```bash
export MAX_NEWS_ARTICLES="5"
```

### 3. 设置方法

#### 使用 .env 文件（推荐）
```bash
# 复制示例文件
cp env.example .env

# 编辑 .env 文件，填入你的配置
# OPENAI_API_KEY=sk-your-actual-api-key-here
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
# RSS_FEEDS=https://finance.yahoo.com/news/rssindex
```

#### 临时设置（当前会话有效）
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

#### 永久设置

**macOS/Linux**
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows**
```cmd
setx OPENAI_API_KEY "sk-your-api-key-here"
```

## 运行方式
1. 启动 API 服务：
   ```bash
   uvicorn main:app --reload
   ```
2. 访问接口：
   - `GET /`：健康检查。
   - `GET /run/weekly-full-report`：执行完整流程，生成周报并返回本地文件路径。

生成的 Markdown 报告位于 `reports/report_YYYY-MM-DD_HH-MM.md`，摘要信息会同步输出到 Slack（若已配置）。

## 测试和验证

### 验证环境变量设置
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 或者运行测试
python -c "from utils.env_loader import get_optional_env; print('API Key:', get_optional_env('OPENAI_API_KEY', '未设置'))"
```

### 测试 Slack 通知功能
```bash
python tests/test_slack_notifier.py
```

### 测试完整流程
```bash
python tests/test_run_report_simple.py
```

### 测试模拟版本（无需 API 密钥）
```bash
python tests/test_run_report_mock.py
```

## 消息格式

### 基础通知
发送到 Slack 的消息包含报告摘要和本地文件路径：
```
*📊 投资研究周报*
摘要：[报告摘要]
📄 本地报告: [报告文件路径]
```

### 增强通知（推荐）
现在支持将完整的报告内容直接发送到 Slack：
- 自动读取报告文件内容
- 智能分割长内容以适应 Slack 消息长度限制
- 使用富文本格式（Blocks）提供更好的阅读体验
- 支持分段发送，确保完整内容都能收到

### 通知方式选择
- **简单通知**：只发送摘要和文件路径
- **增强通知**：发送完整报告内容（推荐）
- **高级通知**：支持文件上传和更丰富的格式

## 故障排除

### 错误：404 Not Found
- 检查 Webhook URL 是否正确
- 确认 Slack 应用已正确配置
- 验证频道权限

### 错误：403 Forbidden
- 检查 Webhook URL 是否有效
- 确认应用有发送消息的权限

### 跳过 Slack 通知
如果不想使用 Slack 通知，可以：
1. 不设置 `SLACK_WEBHOOK_URL` 环境变量
2. 在 `.env` 文件中注释掉 `SLACK_WEBHOOK_URL` 行
3. 使用模拟测试脚本：`python tests/test_run_report_mock.py`

## 目录结构
```
ai-invest/
├── .env                    # 环境变量文件（不要提交到 git）
├── env.example            # 示例环境变量文件
├── fetchers/              # 抓取新闻、价格、行业和宏观数据
├── analyzers/             # 调用 GPT 进行主题提取和周报生成
├── utils/                 # Markdown 报告写入与 Slack 通知
├── prompts/               # 存放提示词模板
├── tests/                 # 测试脚本
└── reports/               # 生成的报告文件
```

## 注意事项
- 运行前需确认本地网络可访问相关数据源及 OpenAI API
- 若未设置 Slack Webhook，仅生成本地报告，不会发送通知
- 请确保 API 密钥的安全性，不要提交到版本控制系统
- `.env` 文件已添加到 `.gitignore` 中
- 项目会自动从 `.env` 文件加载环境变量
- 如果没有设置必需的环境变量，程序会给出清晰的错误提示
- Webhook URL 包含敏感信息，不要提交到版本控制系统
- 定期轮换 Webhook URL
- 限制应用的权限范围

