# 📋 预部署检查清单

在推送代码到GitHub并触发CI/CD流程之前，请确保完成以下检查项目。

## 🔍 代码质量检查

### ✅ Python语法检查
- [ ] 所有Python文件语法正确
- [ ] 没有语法错误或导入错误
- [ ] 模块依赖关系正确

**检查命令:**
```bash
# 检查主要文件语法
python -m py_compile main.py
python -m py_compile utils/markdown_writer.py
python -m py_compile analyzers/analyze_agent.py

# 检查所有Python文件
find . -name "*.py" -exec python -m py_compile {} \;
```

### ✅ 模块导入测试
- [ ] 所有模块能正常导入
- [ ] 没有循环导入问题
- [ ] 依赖包已正确安装

**检查命令:**
```bash
python -c "import main; print('main.py导入成功')"
python -c "from utils.markdown_writer import write_markdown_report; print('导入成功')"
```

## 🐳 Docker环境测试

### ✅ Docker构建测试
- [ ] Dockerfile语法正确
- [ ] 镜像能成功构建
- [ ] 容器能正常启动
- [ ] 应用在容器中正常运行

**检查命令:**
```bash
# 运行本地Docker测试
./test-docker-local.sh

# 或手动测试
docker build -t ai-invest:test .
docker run -d --name test-container -p 8001:8000 ai-invest:test
curl http://localhost:8001/
docker stop test-container && docker rm test-container
```

### ✅ 容器健康检查
- [ ] 健康检查端点响应正常
- [ ] 应用在容器中稳定运行
- [ ] 日志输出正常

## 📁 配置文件检查

### ✅ 必需文件存在
- [ ] `Dockerfile`
- [ ] `.dockerignore`
- [ ] `.github/workflows/deploy-azure.yml`
- [ ] `azure-container-apps.yaml`
- [ ] `deploy.sh`
- [ ] `requirements.txt`

### ✅ 配置文件语法正确
- [ ] YAML文件语法正确
- [ ] Dockerfile指令正确
- [ ] GitHub Actions工作流配置正确

## 🔧 环境变量配置

### ✅ 本地环境变量
- [ ] `.env`文件已创建
- [ ] 必需的环境变量已设置
- [ ] 敏感信息没有提交到Git

**必需环境变量:**
```bash
OPENAI_API_KEY=your-openai-api-key
AZURE_SUBSCRIPTION_ID=your-subscription-id
LANGCHAIN_API_KEY=your-langchain-key  # 可选
SLACK_WEBHOOK_URL=your-slack-webhook  # 可选
```

### ✅ GitHub Secrets配置
- [ ] `AZURE_CLIENT_ID` 已设置
- [ ] `AZURE_TENANT_ID` 已设置
- [ ] `AZURE_SUBSCRIPTION_ID` 已设置
- [ ] `AZURE_RESOURCE_GROUP` 已设置
- [ ] `AZURE_CONTAINERAPP_NAME` 已设置
- [ ] `GHCR_PAT` 已设置 (GitHub Container Registry Personal Access Token)

## 🧪 功能测试

### ✅ 本地功能测试
- [ ] 应用能正常启动
- [ ] 健康检查端点响应正常
- [ ] API文档端点可访问
- [ ] 主要功能正常工作

**测试命令:**
```bash
# 启动本地应用
python -m uvicorn main:app --host 127.0.0.1 --port 8002

# 测试端点
curl http://127.0.0.1:8002/
curl http://127.0.0.1:8002/docs
```

### ✅ 集成测试
- [ ] 新闻获取功能正常
- [ ] AI分析功能正常
- [ ] 报告生成功能正常
- [ ] Slack通知功能正常 (如果配置)

## 📊 性能和安全检查

### ✅ 性能检查
- [ ] 应用启动时间合理
- [ ] 内存使用量合理
- [ ] 响应时间可接受

### ✅ 安全检查
- [ ] 没有硬编码的敏感信息
- [ ] 环境变量正确配置
- [ ] 容器权限设置合理

## 🚀 部署前最终检查

### ✅ 运行完整测试套件
```bash
# 运行CI/CD模拟测试
./test-cicd-local.sh

# 运行Docker测试
./test-docker-local.sh
```

### ✅ 代码审查
- [ ] 代码已通过审查
- [ ] 没有明显的bug
- [ ] 代码风格符合项目规范

### ✅ 文档更新
- [ ] README.md已更新
- [ ] 部署文档完整
- [ ] API文档正确

## 📝 检查结果记录

**检查日期:** _______________
**检查人员:** _______________

**检查结果:**
- [ ] 所有检查项目通过
- [ ] 发现的问题已修复
- [ ] 准备推送代码到GitHub

**发现的问题:**
```
1. 
2. 
3. 
```

**修复状态:**
- [ ] 问题1: 已修复 / 未修复
- [ ] 问题2: 已修复 / 未修复
- [ ] 问题3: 已修复 / 未修复

## 🎯 下一步操作

如果所有检查项目都通过：

1. **提交代码更改**
   ```bash
   git add .
   git commit -m "修复f-string语法错误，准备部署到Azure"
   git push origin main
   ```

2. **监控GitHub Actions**
   - 查看构建状态
   - 监控部署进度
   - 检查部署日志

3. **验证Azure部署**
   - 检查Container App状态
   - 测试应用端点
   - 验证功能正常

## ⚠️ 注意事项

- 确保没有敏感信息提交到Git
- 检查GitHub Actions的权限设置
- 验证Azure资源的访问权限
- 准备回滚方案以防部署失败

---

**记住:** 在CI/CD环境中，小问题可能被放大。本地测试越充分，部署成功率越高！ 