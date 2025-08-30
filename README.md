# AI Invest Trend

一个基于Agent-Tool简化架构的智能投资研究平台。使用 PostgreSQL + pgvector 进行向量化分析，OpenAI GPT 模型进行新闻主题分析。

## 🏗️ 核心功能

- **🤖 智能Agent系统**：DataAgent负责数据获取，AnalysisAgent负责AI分析和报告生成
- **🧠 向量化分析**：使用 PostgreSQL + pgvector 进行新闻内容向量化和相似性搜索
- **📰 智能新闻分析**：基于 OpenAI GPT 的主题提取、情感分析和股票识别
- **🔧 工具化设计**：10个专业工具模块，支持Agent间协作和复用
- **📊 完整工作流**：从新闻抓取到分析报告的全流程自动化

### 简化架构 (v2.1)
```
src/
├── domain/           # 领域层：统一Repository + 简化数据模型
├── application/      # 应用层：Agent-Tool架构 + Use Cases
│   ├── agents/       # 智能体：DataAgent, AnalysisAgent
│   ├── tools/        # 工具集：数据源、分析、通知、存储工具
│   └── use_cases/    # 业务用例：新闻分析工作流
├── infrastructure/   # 基础设施层：数据库 + OpenAI直接集成
│   ├── database/     # PostgreSQL + pgvector + 统一Repository
│   └── openai/       # OpenAI客户端（简化直接集成）
└── presentation/     # 表示层：简化FastAPI
```

## 🚀 快速开始

### 步骤 1：环境准备

```bash
# 1. 确保在项目根目录
cd ai-invest

# 2. 创建并激活 conda 环境
conda create -n ai_invest python=3.11
conda activate ai_invest

# 3. 安装依赖
pip install -r requirements.txt
```

### 步骤 2：环境变量配置

```bash
# 1. 复制环境变量模板
cp env.template .env

# 2. 编辑 .env 文件，配置必需变量（使用文本编辑器）
# DATABASE_URL=postgresql+asyncpg://ai_invest:ai_invest_password@localhost:5432/ai_invest
# VECTOR_STORAGE_PROVIDER=postgresql
# VECTOR_DIMENSION=1536
# OPENAI_API_KEY=你的OpenAI密钥（可选，用于AI分析功能）
```

### 步骤 3：启动数据库

```bash
# 启动 PostgreSQL 数据库（需要 Docker）
cd docker
docker-compose up -d postgres

# 等待数据库完全启动（约30秒），检查状态
docker-compose ps
```

### 步骤 4：测试新架构

```bash
# 回到项目根目录
cd ..

# 运行简化架构测试（验证所有组件是否正常）
python scripts/test_new_architecture.py
```

**预期成功输出**：
```
🚀 AI Invest Architecture Test Suite
✅ PASS Database Initialization
✅ PASS Agent Creation
✅ PASS News Fetching
✅ PASS AI Analysis
✅ PASS Use Case Workflow

Results: 5/5 tests passed
🎉 All tests passed! New architecture is working correctly.
```

### 步骤 5：启动应用

```bash
# 方法 1：使用 uvicorn 启动（推荐开发）
uvicorn main:app --reload

# 方法 2：使用 Python 直接运行
python main.py

# 方法 3：使用 Docker（完整环境）
cd docker && docker-compose up --build
```

### 步骤 6：验证功能

**访问 Web 界面**：
- **Swagger API 文档**: http://localhost:8000/docs
- **应用状态**: http://localhost:8000/
- **健康检查**: http://localhost:8000/health

**或使用命令行测试**：
```bash
# 基本状态检查
curl http://localhost:8000/

# 向量存储测试
curl http://localhost:8000/test/vector-storage

# 向量搜索测试  
curl http://localhost:8000/test/vector-search
```

## 📊 API 端点 (简化架构 v2.1)

### 核心功能
- `GET /` - 应用信息和状态
- `GET /health` - 系统健康检查（数据库、Agent状态）
- `GET /docs` - Swagger API 文档

### Agent信息
- `GET /agents/info` - 查看DataAgent和AnalysisAgent信息和能力

### 智能分析工作流
- `POST /run/full-analysis` - 完整新闻分析工作流（抓取→分析→报告）
- `POST /run/analyze-existing` - 分析数据库中已存储的新闻
- `GET /run/weekly-full-report` - 生成智能投资周报（向后兼容）

### 数据查询
- `GET /data/recent-news` - 获取近期新闻数据
- `GET /data/recent-analysis` - 获取近期分析结果

## 🛠️ 开发指南

### 项目结构
```
ai-invest/
├── src/                    # 源代码（分层架构）
│   ├── domain/            # 领域层（业务实体和接口）
│   ├── application/       # 应用层（用例和服务）
│   ├── infrastructure/    # 基础设施层（数据库、外部服务）
│   └── presentation/      # 表示层（API 和 Web 接口）
├── docker/                # Docker 配置
├── deployment/            # 部署配置
├── scripts/               # 脚本和工具
├── resources/             # 资源文件（提示词、模板）
└── tests/                 # 测试文件
```

### 常用命令

**开发模式**：
```bash
# 启动数据库
cd docker && docker-compose up -d postgres

# 启动应用（自动重载）
cd .. && uvicorn main:app --reload

# 运行测试
python scripts/database/test_architecture.py
```

**生产部署**：
```bash
# Azure 部署
cd deployment && ./deploy.sh
```

## ⚡ 故障排除

### 数据库连接失败
```bash
# 检查容器状态
cd docker && docker-compose ps

# 重置数据库
docker-compose down -v postgres
docker-compose up -d postgres
```

### 导入错误
```bash
# 确保在正确环境中
conda activate ai_invest

# 测试基础导入
python -c "from src.domain.entities.news_article import NewsArticle; print('✅ Import OK')"
```

### 依赖问题
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt
```

## ✅ 快速验证清单

运行成功需要确保：
- ✅ conda 环境已激活（`ai_invest`）
- ✅ `.env` 文件已配置必需变量
- ✅ PostgreSQL 数据库运行中
- ✅ 架构测试全部通过
- ✅ API 服务在 http://localhost:8000 正常响应
- ✅ `/health` 端点返回健康状态

## 🎯 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + pgvector（向量扩展）
- **AI 分析**: OpenAI GPT + LangChain
- **架构模式**: Domain-Driven Design (DDD)
- **容器化**: Docker + Docker Compose
- **部署**: Azure Container Apps

## 📄 相关文档

- [CLAUDE.md](./CLAUDE.md) - 详细的架构和开发文档
- [API 文档](http://localhost:8000/docs) - 在线 API 文档（需启动服务）
- [环境配置](./env.template) - 环境变量配置模板

## 🔐 安全注意事项

- 不要提交 `.env` 文件到版本控制
- 定期更换 API 密钥和 Webhook URL
- 生产环境请使用安全的数据库配置
- 限制 API 访问权限和频率

---

如果遇到问题，请先检查 [故障排除](#⚡-故障排除) 部分，或查看 [CLAUDE.md](./CLAUDE.md) 获取详细的技术文档。