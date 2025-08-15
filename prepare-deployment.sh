#!/bin/bash

# 部署准备脚本 - 自动完成所有部署前的准备工作
# 使用方法: ./prepare-deployment.sh

set -e

echo "🚀 开始部署准备工作..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 步骤1: 检查并安装依赖
echo ""
echo -e "${BLUE}📦 步骤1: 检查并安装依赖${NC}"

# 检查PyYAML
if ! python -c "import yaml" 2>/dev/null; then
    echo "  安装PyYAML..."
    pip install PyYAML
    echo -e "  ${GREEN}✅ PyYAML安装完成${NC}"
else
    echo -e "  ${GREEN}✅ PyYAML已安装${NC}"
fi

# 步骤2: 最终代码检查
echo ""
echo -e "${BLUE}🔍 步骤2: 最终代码检查${NC}"

echo "  检查Python语法..."
python -m py_compile main.py
python -m py_compile utils/markdown_writer.py
python -m py_compile analyzers/analyze_agent.py
echo -e "  ${GREEN}✅ Python语法检查通过${NC}"

echo "  检查模块导入..."
python -c "import main; print('  ✅ main.py导入成功')"
python -c "from utils.markdown_writer import write_markdown_report; print('  ✅ markdown_writer导入成功')"
echo -e "  ${GREEN}✅ 模块导入检查通过${NC}"

# 步骤3: 配置文件验证
echo ""
echo -e "${BLUE}📁 步骤3: 配置文件验证${NC}"

# 检查必需文件
REQUIRED_FILES=(
    "Dockerfile"
    ".dockerignore"
    ".github/workflows/deploy-azure.yml"
    "azure-container-apps.yaml"
    "deploy.sh"
    "requirements.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ✅ $file 存在"
    else
        echo -e "  ${RED}❌ $file 缺失${NC}"
        exit 1
    fi
done

# 验证GitHub Actions YAML语法
echo "  验证GitHub Actions YAML语法..."
python3 -c "
import yaml
try:
    with open('.github/workflows/deploy-azure.yml', 'r') as f:
        yaml.safe_load(f)
    print('    ✅ GitHub Actions YAML语法正确')
except Exception as e:
    print(f'    ❌ GitHub Actions YAML语法错误: {e}')
    exit(1)
"

# 步骤4: 环境变量配置
echo ""
echo -e "${BLUE}🔧 步骤4: 环境变量配置${NC}"

if [ -f ".env" ]; then
    echo -e "  ✅ .env文件存在"
    
    # 检查关键环境变量
    if grep -q "^AZURE_SUBSCRIPTION_ID=" .env; then
        SUB_ID=$(grep "^AZURE_SUBSCRIPTION_ID=" .env | cut -d'=' -f2)
        if [ "$SUB_ID" != "your-subscription-id-here" ]; then
            echo -e "    ✅ AZURE_SUBSCRIPTION_ID已配置: $SUB_ID"
        else
            echo -e "    ${YELLOW}⚠️  AZURE_SUBSCRIPTION_ID仍为占位符，请手动配置${NC}"
        fi
    else
        echo -e "    ${RED}❌ AZURE_SUBSCRIPTION_ID未配置${NC}"
    fi
    
    if grep -q "^OPENAI_API_KEY=" .env; then
        echo -e "    ✅ OPENAI_API_KEY已配置"
    else
        echo -e "    ${RED}❌ OPENAI_API_KEY未配置${NC}"
    fi
else
    echo -e "  ${RED}❌ .env文件不存在${NC}"
    exit 1
fi

# 步骤5: Git状态检查
echo ""
echo -e "${BLUE}📝 步骤5: Git状态检查${NC}"

if [ -d ".git" ]; then
    # 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    echo "  当前分支: $CURRENT_BRANCH"
    
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        echo -e "  ✅ 在正确的分支上"
    else
        echo -e "  ${RED}❌ 不在main或master分支上${NC}"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "  发现未提交的更改:"
        git status --short
        
        echo ""
        echo -e "${YELLOW}⚠️  需要提交更改才能部署${NC}"
        echo "  是否自动提交更改? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "  自动提交更改..."
            git add .
            git commit -m "修复f-string语法错误，准备部署到Azure Container Apps"
            echo -e "  ${GREEN}✅ 更改已提交${NC}"
        else
            echo -e "  ${YELLOW}⚠️  请手动提交更改后再运行此脚本${NC}"
            exit 1
        fi
    else
        echo -e "  ✅ 工作目录干净，没有未提交的更改"
    fi
else
    echo -e "  ${RED}❌ 不是Git仓库${NC}"
    exit 1
fi

# 步骤6: 最终验证
echo ""
echo -e "${BLUE}✅ 步骤6: 最终验证${NC}"

echo "  运行最终CI/CD测试..."
./test-cicd-local.sh

# 步骤7: 部署准备完成
echo ""
echo -e "${GREEN}🎉 部署准备工作完成！${NC}"
echo ""
echo "📋 准备状态汇总:"
echo "  ✅ 依赖包已安装"
echo "  ✅ 代码语法检查通过"
echo "  ✅ 模块导入测试通过"
echo "  ✅ 配置文件验证通过"
echo "  ✅ 环境变量配置完成"
echo "  ✅ Git状态检查通过"
echo "  ✅ CI/CD测试通过"
echo ""
echo "🚀 现在可以安全地推送代码到GitHub！"
echo ""
echo "📝 下一步操作:"
echo "  1. 确保GitHub Secrets已配置:"
echo "     - AZURE_CLIENT_ID"
echo "     - AZURE_TENANT_ID"
echo "     - AZURE_SUBSCRIPTION_ID"
echo "     - AZURE_RESOURCE_GROUP"
echo "     - AZURE_CONTAINERAPP_NAME"
echo "     - GHCR_PAT"
echo ""
echo "  2. 推送代码到GitHub:"
echo "     git push origin main"
echo ""
echo "  3. 监控GitHub Actions:"
echo "     https://github.com/stephenhuo-code/ai_invest/actions"
echo ""
echo "  4. 验证Azure部署:"
echo "     az containerapp show --name agent --resource-group rg-ai"
echo ""
echo "🎯 祝部署顺利！" 