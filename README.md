# AI Invest Trend

一个基于 FastAPI 的投资研究自动化工具。它会抓取最新财经新闻并使用 OpenAI GPT 模型进行主题分析，结合股票价格、行业表现和宏观经济指标生成每周研究报告，并可将摘要推送到 Slack。

## 功能概览
- **新闻抓取**：从 `config.yaml` 中配置的 RSS 源获取最新新闻，并解析文章内容。
- **主题分析**：调用 OpenAI API 根据提示词提取行业主题、股票代码及情绪。
- **市场数据获取**：
  - `yfinance` 获取股票最新价。
  - 抓取 Yahoo Finance 行业表现。
  - 抓取 TradingEconomics 宏观经济指标。
- **报告生成与通知**：将上述信息整理成 Markdown 周报，保存到 `reports/` 目录，并通过 Slack Webhook 发送摘要。

## 环境准备
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 配置 `config.yaml`：
   ```yaml
   openai_api_key: "你的 OpenAI API Key"
   rss_feeds:
     - https://finance.yahoo.com/news/rssindex
   slack_webhook: "你的 Slack Webhook URL"  # 可选，配置后才能发送通知
   ```

## 运行方式
1. 启动 API 服务：
   ```bash
   uvicorn main:app --reload
   ```
2. 访问接口：
   - `GET /`：健康检查。
   - `GET /run/weekly-full-report`：执行完整流程，生成周报并返回本地文件路径。

生成的 Markdown 报告位于 `reports/report_YYYY-MM-DD.md`，摘要信息会同步输出到 Slack（若已配置）。

## 目录结构
- `fetchers/`：抓取新闻、价格、行业和宏观数据。
- `analyzers/`：调用 GPT 进行主题提取和周报生成。
- `utils/`：Markdown 报告写入与 Slack 通知。
- `prompts/`：存放提示词模板。

## 注意事项
- 运行前需确认本地网络可访问相关数据源及 OpenAI API。
- 若未设置 Slack Webhook，仅生成本地报告，不会发送通知。

