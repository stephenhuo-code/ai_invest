# 🚀 Azure Container Apps 部署指南

本指南将帮助你将 AI Invest 应用部署到 Azure Container Apps。

## 📋 前置要求

### 1. Azure 账户和订阅
- 有效的 Azure 订阅
- 足够的权限创建和管理资源

### 2. Azure CLI
```bash
# 安装 Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 或者使用 Homebrew (macOS)
brew install azure-cli
```

### 3. Docker
```bash
# 确保 Docker 已安装并运行
docker --version
```

### 4. GitHub 仓库设置
- 仓库: `github.com/stephenhuo-code/ai_invest`
- 分支: `main` 或 `master`

## 🔧 配置步骤

### 1. 设置 Azure 凭据

#### 方法 1: 使用 Azure CLI 登录
```bash
az login
az account set --subscription <your-subscription-id>
```

#### 方法 2: 创建服务主体 (推荐用于 CI/CD)
```bash
# 创建服务主体
az ad sp create-for-rbac --name "ai-invest-deploy" --role contributor \
    --scopes /subscriptions/<subscription-id>/resourceGroups/rg-ai \
    --sdk-auth

# 输出示例:
# {
#   "clientId": "xxx",
#   "clientSecret": "xxx",
#   "subscriptionId": "xxx",
#   "tenantId": "xxx"
# }
```

### 2. 配置 GitHub Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下 secrets:

#### 必需的 Secrets:
- `AZURE_CREDENTIALS`: 服务主体的完整 JSON 输出
- `AZURE_SUBSCRIPTION_ID`: Azure 订阅 ID

#### 可选的 Secrets:
- `REGISTRY_LOGIN_SERVER`: 容器注册表服务器 (ghcr.io)
- `REGISTRY_USERNAME`: 容器注册表用户名
- `REGISTRY_PASSWORD`: 容器注册表密码

### 3. 环境变量配置

创建 `.env` 文件并设置以下变量:
```bash
# OpenAI API 配置
OPENAI_API_KEY=sk-your-openai-api-key-here

# LangSmith 配置
LANGCHAIN_API_KEY=ls-your-langsmith-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai_invest

# Slack 通知配置 (可选)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx

# RSS 源配置
RSS_FEEDS=https://finance.yahoo.com/news/rssindex
MAX_NEWS_ARTICLES=5
```

## 🚀 部署方式

### 方式 1: 使用 GitHub Actions (推荐)

1. 推送代码到 `main` 分支
2. GitHub Actions 将自动:
   - 构建 Docker 镜像
   - 推送到 GitHub Container Registry
   - 部署到 Azure Container Apps

### 方式 2: 手动部署

#### 使用部署脚本:
```bash
# 设置环境变量
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="rg-ai"
export CONTAINER_APP_NAME="agent"

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

#### 使用 Azure CLI 直接部署:
```bash
# 构建并推送镜像
docker build -t ghcr.io/stephenhuo-code/ai_invest:latest .
docker push ghcr.io/stephenhuo-code/ai_invest:latest

# 创建 Container App
az containerapp create \
    --name agent \
    --resource-group rg-ai \
    --environment cae-agent \
    --image ghcr.io/stephenhuo-code/ai_invest:latest \
    --target-port 8000 \
    --ingress external \
    --cpu 1.0 \
    --memory 2.0Gi
```

## 📊 部署后验证

### 1. 检查应用状态
```bash
az containerapp show \
    --name agent \
    --resource-group rg-ai \
    --query "{Name:name,Status:properties.provisioningState,URL:properties.configuration.ingress.fqdn}"
```

### 2. 测试应用端点
```bash
# 获取应用 URL
APP_URL=$(az containerapp show --name agent --resource-group rg-ai --query properties.configuration.ingress.fqdn -o tsv)

# 测试健康检查
curl https://$APP_URL/

# 测试报告生成
curl https://$APP_URL/run/weekly-full-report
```

### 3. 查看日志
```bash
az containerapp logs show \
    --name agent \
    --resource-group rg-ai \
    --follow
```

## 🔍 故障排除

### 常见问题:

#### 1. 镜像拉取失败
- 检查 GitHub Container Registry 权限
- 验证镜像标签是否正确

#### 2. 应用启动失败
- 检查环境变量配置
- 查看容器日志
- 验证端口配置

#### 3. 健康检查失败
- 确保应用在 8000 端口正确响应
- 检查 `/` 端点是否可访问

### 调试命令:
```bash
# 查看应用详细信息
az containerapp show --name agent --resource-group rg-ai

# 查看修订版本
az containerapp revision list --name agent --resource-group rg-ai

# 查看环境变量
az containerapp show --name agent --resource-group rg-ai --query properties.template.containers[0].env

# 重启应用
az containerapp restart --name agent --resource-group rg-ai
```

## 📈 监控和维护

### 1. 设置 Azure Monitor
- 配置应用洞察
- 设置告警规则
- 监控性能指标

### 2. 自动扩缩容
- 基于 CPU 使用率自动扩缩容
- 基于 HTTP 请求数自动扩缩容
- 设置最小和最大副本数

### 3. 更新部署
- 推送新代码到 main 分支
- 或手动更新镜像标签
- 使用蓝绿部署策略

## 🔐 安全最佳实践

1. **网络安全**:
   - 使用私有网络
   - 配置网络安全组
   - 启用 TLS 加密

2. **身份验证**:
   - 使用托管身份
   - 最小权限原则
   - 定期轮换密钥

3. **容器安全**:
   - 扫描镜像漏洞
   - 使用非 root 用户
   - 限制容器权限

## 📞 支持

如果遇到问题，请:
1. 检查 Azure 门户中的错误信息
2. 查看 GitHub Actions 日志
3. 检查应用日志
4. 联系 Azure 支持或项目维护者 