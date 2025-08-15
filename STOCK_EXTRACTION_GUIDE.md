# 股票提取功能指南

## 概述

本次更新增强了趋势分析功能，现在可以从财经新闻中精确提取股票代码和公司名称，为后续的股票分析提供结构化数据。

## 主要改进

### 1. 提示词优化 (`prompts/trend_analysis_prompt.txt`)

- 要求返回JSON格式的结构化结果
- 明确指定股票代码格式（美股、港股、A股等）
- 包含市场信息标注
- 增加简要总结字段

### 2. 分析代理增强 (`analyzers/analyze_agent.py`)

#### 新增功能：
- **结构化结果解析**：自动解析JSON格式的分析结果
- **股票信息提取**：`extract_all_stocks()` 方法提取所有股票信息
- **错误处理**：JSON解析失败时的优雅降级
- **去重功能**：自动去除重复的股票代码

#### 返回数据结构：
```python
{
    "title": "新闻标题",
    "industry_themes": ["行业主题1", "行业主题2"],
    "stocks": [
        {
            "company_name": "公司名称",
            "stock_code": "股票代码",
            "market": "市场"
        }
    ],
    "sentiment": "积极/中性/消极",
    "summary": "简要总结",
    "raw_analysis": "原始分析文本"
}
```

## 使用方法

### 基本使用

```python
from analyzers.analyze_agent import AnalyzeAgent

# 初始化分析代理
agent = AnalyzeAgent()

# 新闻数据
news_list = [
    {
        "title": "苹果发布新产品",
        "text": "苹果公司(AAPL)今日发布新款iPhone..."
    }
]

# 提取主题和股票信息
results = agent.extract_topics(news_list)

# 提取所有股票信息用于后续分析
all_stocks = agent.extract_all_stocks(results)
```

### 股票信息处理

```python
# 获取所有股票代码
stock_codes = [stock['stock_code'] for stock in all_stocks]

# 按情绪分类
positive_stocks = [stock for stock in all_stocks if stock['sentiment'] == '积极']
negative_stocks = [stock for stock in all_stocks if stock['sentiment'] == '消极']

# 按市场分类
us_stocks = [stock for stock in all_stocks if stock['market'] == '美股']
hk_stocks = [stock for stock in all_stocks if stock['market'] == '港股']
cn_stocks = [stock for stock in all_stocks if stock['market'] == 'A股']
```

## 支持的股票格式

### 美股
- 格式：`AAPL`, `TSLA`, `GOOGL`
- 市场标注：`美股`

### 港股
- 格式：`00700.HK`, `09988.HK`
- 市场标注：`港股`

### A股
- 格式：`000001.SZ`, `600000.SH`
- 市场标注：`A股`

### 其他市场
- 格式：根据具体市场规则
- 市场标注：具体市场名称

## 测试和示例

### 运行测试
```bash
python tests/test_stock_extraction.py
```

### 运行示例
```bash
python examples/stock_analysis_example.py
```

## 后续分析建议

提取的股票信息可以用于：

1. **价格数据获取**：使用 `price_fetcher` 获取实时价格
2. **技术分析**：计算技术指标
3. **基本面分析**：获取财务数据
4. **投资组合构建**：基于情绪分析构建组合
5. **风险分析**：评估投资风险

## 错误处理

- JSON解析失败时，会保留原始分析文本
- 网络错误或API调用失败时，会记录错误信息
- 空新闻内容会被标记为分析失败

## 注意事项

1. 确保OpenAI API密钥已正确配置
2. 新闻文本长度限制为2000字符
3. 股票代码识别依赖于LLM的准确性
4. 建议对重要结果进行人工验证 