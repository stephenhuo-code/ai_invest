#!/bin/bash

# 问题修复脚本 - 自动修复CI/CD测试中发现的问题
# 使用方法: ./fix-issues.sh

set -e

echo "🔧 开始修复发现的问题..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 问题1: 配置AZURE_SUBSCRIPTION_ID
echo ""
echo -e "${BLUE}🔧 问题1: 配置AZURE_SUBSCRIPTION_ID${NC}"

if [ -f ".env" ]; then
    if ! grep -q "^AZURE_SUBSCRIPTION_ID=" .env; then
        echo "  添加AZURE_SUBSCRIPTION_ID到.env文件..."
        echo "" >> .env
        echo "# Azure配置" >> .env
        echo "AZURE_SUBSCRIPTION_ID=your-subscription-id-here" >> .env
        echo -e "  ${GREEN}✅ 已添加AZURE_SUBSCRIPTION_ID占位符${NC}"
        echo "  ⚠️  请手动填入真实的Azure订阅ID"
    else
        echo -e "  ${GREEN}✅ AZURE_SUBSCRIPTION_ID已配置${NC}"
    fi
else
    echo "  创建.env文件..."
    cp env.template .env
    echo -e "  ${GREEN}✅ 已创建.env文件${NC}"
fi

# 问题2: 检查TODO/FIXME注释
echo ""
echo -e "${BLUE}🔧 问题2: 检查TODO/FIXME注释${NC}"

TODO_FILES=$(grep -r "TODO\|FIXME" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=reports --exclude=*.md | head -5)

if [ ! -z "$TODO_FILES" ]; then
    echo "  发现以下TODO/FIXME注释:"
    echo "$TODO_FILES" | while read line; do
        echo "    $line"
    done
    echo -e "  ${YELLOW}⚠️  请检查这些注释，确保不是未完成的工作${NC}"
else
    echo -e "  ${GREEN}✅ 没有发现TODO/FIXME注释${NC}"
fi

# 问题3: 验证Docker配置
echo ""
echo -e "${BLUE}🔧 问题3: 验证Docker配置${NC}"

if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        echo "  测试Docker构建..."
        docker build -t ai-invest:fix-test . >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✅ Docker构建测试通过${NC}"
            # 清理测试镜像
            docker rmi ai-invest:fix-test >/dev/null 2>&1 || true
        else
            echo -e "  ${RED}❌ Docker构建测试失败${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  Docker未运行，请启动Docker Desktop${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Docker未安装${NC}"
fi

# 问题4: 检查Git状态
echo ""
echo -e "${BLUE}🔧 问题4: 检查Git状态${NC}"

if [ -d ".git" ]; then
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "  发现未提交的更改:"
        git status --short
        echo ""
        echo -e "  ${YELLOW}⚠️  建议提交所有更改后再推送${NC}"
        echo "  使用以下命令提交更改:"
        echo "    git add ."
        echo "    git commit -m '修复f-string语法错误，准备部署到Azure'"
    else
        echo -e "  ${GREEN}✅ 工作目录干净，没有未提交的更改${NC}"
    fi
    
    # 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    echo "  当前分支: $CURRENT_BRANCH"
    
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        echo -e "  ${GREEN}✅ 在正确的分支上${NC}"
    else
        echo -e "  ${YELLOW}⚠️  建议切换到main或master分支${NC}"
        echo "  使用: git checkout main"
    fi
else
    echo -e "  ${RED}❌ 不是Git仓库${NC}"
fi

# 问题5: 验证GitHub Actions配置
echo ""
echo -e "${BLUE}🔧 问题5: 验证GitHub Actions配置${NC}"

if [ -f ".github/workflows/deploy-azure.yml" ]; then
    echo "  检查GitHub Actions工作流语法..."
    
    # 检查YAML语法
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import yaml
try:
    with open('.github/workflows/deploy-azure.yml', 'r') as f:
        yaml.safe_load(f)
    print('    ✅ GitHub Actions YAML语法正确')
except Exception as e:
    print(f'    ❌ GitHub Actions YAML语法错误: {e}')
"
    else
        echo -e "  ${YELLOW}⚠️  无法验证YAML语法，请手动检查${NC}"
    fi
    
    # 检查必需的secrets
    echo "  检查必需的GitHub Secrets:"
    REQUIRED_SECRETS=(
        "AZURE_CLIENT_ID"
        "AZURE_TENANT_ID" 
        "AZURE_SUBSCRIPTION_ID"
        "AZURE_RESOURCE_GROUP"
        "AZURE_CONTAINERAPP_NAME"
        "GHCR_PAT"
    )
    
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if grep -q "\${{ secrets.$secret }}" .github/workflows/deploy-azure.yml; then
            echo -e "    ✅ $secret 在工作流中被引用"
        else
            echo -e "    ⚠️  $secret 在工作流中未被引用"
        fi
    done
else
    echo -e "  ${RED}❌ GitHub Actions工作流文件不存在${NC}"
fi

# 总结
echo ""
echo -e "${GREEN}🎉 问题修复检查完成！${NC}"
echo ""
echo "📋 修复状态汇总:"
echo "  ✅ 环境变量配置检查"
echo "  ✅ TODO/FIXME注释检查"
echo "  ✅ Docker配置验证"
echo "  ✅ Git状态检查"
echo "  ✅ GitHub Actions配置验证"
echo ""
echo "💡 下一步操作:"
echo "  1. 手动填入真实的Azure订阅ID到.env文件"
echo "  2. 检查并处理TODO/FIXME注释"
echo "  3. 确保Docker正常运行"
echo "  4. 提交所有代码更改"
echo "  5. 配置GitHub Secrets"
echo "  6. 推送代码到GitHub触发CI/CD"
echo ""
echo "🚀 准备就绪后，可以安全地部署到Azure Container Apps！" 