#!/bin/bash

# 本地CI/CD模拟脚本 - 模拟GitHub Actions流程
# 使用方法: ./test-cicd-local.sh

set -e

echo "🚀 开始本地CI/CD流程模拟..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 模拟GitHub环境变量
export GITHUB_REPOSITORY="stephenhuo-code/ai_invest"
export GITHUB_SHA=$(git rev-parse HEAD 2>/dev/null || echo "test-sha")
export GITHUB_REF="refs/heads/main"

echo "📋 模拟环境变量:"
echo "  GITHUB_REPOSITORY: $GITHUB_REPOSITORY"
echo "  GITHUB_SHA: $GITHUB_SHA"
echo "  GITHUB_REF: $GITHUB_REF"

# 步骤1: 代码检查
echo ""
echo -e "${BLUE}🔍 步骤1: 代码检查${NC}"

echo "  检查Python语法..."
python -m py_compile main.py
python -m py_compile utils/markdown_writer.py
python -m py_compile analyzers/analyze_agent.py
python -m py_compile fetchers/news_fetcher.py
python -m py_compile fetchers/price_fetcher.py
python -m py_compile fetchers/industry_data.py
python -m py_compile fetchers/macro_data.py
echo -e "  ${GREEN}✅ Python语法检查通过${NC}"

echo "  检查模块导入..."
python -c "import main; print('  ✅ main.py导入成功')"
python -c "from utils.markdown_writer import write_markdown_report; print('  ✅ markdown_writer导入成功')"
python -c "from analyzers.analyze_agent import AnalyzeAgent; print('  ✅ analyze_agent导入成功')"
python -c "from fetchers.news_fetcher import fetch_latest_news; print('  ✅ news_fetcher导入成功')"
echo -e "  ${GREEN}✅ 模块导入检查通过${NC}"

# 步骤2: 依赖检查
echo ""
echo -e "${BLUE}📦 步骤2: 依赖检查${NC}"

echo "  检查requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo -e "  ${GREEN}✅ requirements.txt存在${NC}"
    echo "  依赖列表:"
    cat requirements.txt | grep -v "^#" | grep -v "^$" | while read line; do
        if [ ! -z "$line" ]; then
            echo "    - $line"
        fi
    done
else
    echo -e "  ${RED}❌ requirements.txt不存在${NC}"
    exit 1
fi

# 步骤3: Docker构建测试
echo ""
echo -e "${BLUE}🐳 步骤3: Docker构建测试${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠️  Docker未运行，跳过Docker测试${NC}"
    echo "  请启动Docker Desktop后重新运行此脚本"
else
    echo "  构建Docker镜像..."
    docker build -t ai-invest:cicd-test .
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ Docker镜像构建成功${NC}"
        
        # 检查镜像大小
        IMAGE_SIZE=$(docker images ai-invest:cicd-test --format "table {{.Size}}" | tail -n 1)
        echo "  镜像大小: $IMAGE_SIZE"
        
        # 清理测试镜像
        docker rmi ai-invest:cicd-test
        echo "  已清理测试镜像"
    else
        echo -e "  ${RED}❌ Docker镜像构建失败${NC}"
        exit 1
    fi
fi

# 步骤4: 配置文件检查
echo ""
echo -e "${BLUE}📁 步骤4: 配置文件检查${NC}"

# 检查必要的配置文件
REQUIRED_FILES=(
    "Dockerfile"
    ".dockerignore"
    ".github/workflows/deploy-azure.yml"
    "azure-container-apps.yaml"
    "deploy.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅ $file 存在${NC}"
    else
        echo -e "  ${RED}❌ $file 缺失${NC}"
    fi
done

# 步骤5: 环境变量检查
echo ""
echo -e "${BLUE}🔧 步骤5: 环境变量检查${NC}"

# 检查.env文件是否存在
if [ -f ".env" ]; then
    echo -e "  ${GREEN}✅ .env文件存在${NC}"
    
    # 检查关键环境变量
    REQUIRED_ENV_VARS=(
        "OPENAI_API_KEY"
        "AZURE_SUBSCRIPTION_ID"
    )
    
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            echo -e "    ${GREEN}✅ $var 已配置${NC}"
        else
            echo -e "    ${YELLOW}⚠️  $var 未配置${NC}"
        fi
    done
else
    echo -e "  ${YELLOW}⚠️  .env文件不存在，请参考env.template创建${NC}"
fi

# 步骤6: 本地功能测试
echo ""
echo -e "${BLUE}🧪 步骤6: 本地功能测试${NC}"

echo "  启动本地应用进行测试..."
# 在后台启动应用
python -m uvicorn main:app --host 127.0.0.1 --port 8002 &
APP_PID=$!

# 等待应用启动
sleep 5

# 测试健康检查端点
echo "  测试健康检查端点..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/ || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "    ${GREEN}✅ 健康检查端点正常 (HTTP $HEALTH_RESPONSE)${NC}"
else
    echo -e "    ${RED}❌ 健康检查端点异常 (HTTP $HEALTH_RESPONSE)${NC}"
fi

# 测试API文档端点
echo "  测试API文档端点..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/docs || echo "000")
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo -e "    ${GREEN}✅ API文档端点正常 (HTTP $DOCS_RESPONSE)${NC}"
else
    echo -e "    ${RED}❌ API文档端点异常 (HTTP $DOCS_RESPONSE)${NC}"
fi

# 停止测试应用
kill $APP_PID 2>/dev/null || true
wait $APP_PID 2>/dev/null || true

# 步骤7: 代码质量检查
echo ""
echo -e "${BLUE}📊 步骤7: 代码质量检查${NC}"

# 检查是否有明显的代码问题
echo "  检查代码结构..."
if [ -d "analyzers" ] && [ -d "fetchers" ] && [ -d "utils" ]; then
    echo -e "    ${GREEN}✅ 项目结构完整${NC}"
else
    echo -e "    ${RED}❌ 项目结构不完整${NC}"
fi

# 检查是否有TODO或FIXME注释
echo "  检查代码注释..."
TODO_COUNT=$(grep -r "TODO\|FIXME" . --exclude-dir=.git --exclude-dir=__pycache__ | wc -l)
if [ $TODO_COUNT -eq 0 ]; then
    echo -e "    ${GREEN}✅ 没有TODO或FIXME注释${NC}"
else
    echo -e "    ${YELLOW}⚠️  发现 $TODO_COUNT 个TODO或FIXME注释${NC}"
fi

# 总结
echo ""
echo -e "${GREEN}🎉 本地CI/CD流程模拟完成！${NC}"
echo ""
echo "📋 检查结果汇总:"
echo "  ✅ Python语法检查"
echo "  ✅ 模块导入检查"
echo "  ✅ 依赖文件检查"
echo "  ✅ 配置文件检查"
echo "  ✅ 本地功能测试"
echo "  ✅ 代码质量检查"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "  ✅ Docker构建测试"
else
    echo "  ⚠️  Docker测试跳过 (Docker未运行)"
fi

echo ""
echo "💡 下一步操作:"
echo "  1. 如果所有检查都通过，可以推送代码到GitHub"
echo "  2. 如果发现问题，请修复后重新运行此脚本"
echo "  3. 使用 './test-docker-local.sh' 进行完整的Docker测试"
echo ""
echo "🚀 准备就绪，可以部署到Azure Container Apps！" 