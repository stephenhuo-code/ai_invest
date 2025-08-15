# 🚀 快速开始 - Azure Container Apps 部署

## ⚡ 5分钟快速部署

### 1. 准备环境
```bash
# 克隆仓库
git clone https://github.com/stephenhuo-code/ai_invest.git
cd ai_invest

# 安装 Azure CLI (如果未安装)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 2. 配置 Azure
```bash
# 登录 Azure
az login

# 设置订阅
az account set --subscription <your-subscription-id>

# 创建资源组 (如果不存在)
az group create --name rg-ai --location southeastasia

# 创建 Container Apps 环境
az containerapp env create --name cae-agent --resource-group rg-ai --location southeastasia
```

### 3. 配置环境变量
```bash
# 复制模板文件
cp env.template .env

# 编辑 .env 文件，填入你的配置
nano .env
```

### 4. 一键部署
```bash
# 运行部署脚本
./deploy.sh
```

## 🔑 必需的配置

### GitHub Secrets (用于 CI/CD)
在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加:

| Secret 名称 | 值 | 说明 |
|-------------|-----|------|
| `AZURE_CREDENTIALS` | JSON 格式的服务主体凭据 | 从 `az ad sp create-for-rbac` 获取 |
| `AZURE_SUBSCRIPTION_ID` | 你的 Azure 订阅 ID | 从 Azure 门户获取 |

### 环境变量
在 `.env` 文件中设置:

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `AZURE_SUBSCRIPTION_ID` | ✅ | Azure 订阅 ID |
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 |
| `LANGCHAIN_API_KEY` | ❌ | LangSmith API 密钥 (可选) |
| `SLACK_WEBHOOK_URL` | ❌ | Slack Webhook URL (可选) |

## 🌐 访问应用

部署成功后，应用将在以下地址可用:
```
https://<your-app-name>.<environment-name>.<region>.azurecontainerapps.io
```

### 测试端点
- **健康检查**: `GET /`
- **生成报告**: `GET /run/weekly-full-report`
- **API 文档**: `GET /docs`

## 📊 监控部署

```bash
# 查看应用状态
az containerapp show --name agent --resource-group rg-ai

# 查看日志
az containerapp logs show --name agent --resource-group rg-ai --follow

# 查看修订版本
az containerapp revision list --name agent --resource-group rg-ai
```

## 🔄 更新部署

### 自动更新 (推荐)
推送代码到 `main` 分支，GitHub Actions 将自动部署。

### 手动更新
```bash
# 重新运行部署脚本
./deploy.sh
```

## 🆘 常见问题

### Q: 部署失败怎么办？
A: 检查 `.env` 文件配置，确保所有必需变量都已设置。

### Q: 应用无法访问？
A: 检查 Container Apps 环境是否创建成功，应用是否正在运行。

### Q: 如何查看错误日志？
A: 使用 `az containerapp logs show` 命令查看详细日志。

## 📞 获取帮助

- 📖 查看完整文档: [DEPLOYMENT.md](./DEPLOYMENT.md)
- 🐛 报告问题: GitHub Issues
- 💬 讨论: GitHub Discussions 