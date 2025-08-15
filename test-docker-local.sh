#!/bin/bash

# 本地Docker测试脚本 - 模拟Azure Container Apps环境
# 使用方法: ./test-docker-local.sh

set -e

echo "🐳 开始本地Docker测试..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ 错误: Docker未运行，请启动Docker Desktop${NC}"
    exit 1
fi

# 清理旧的测试容器和镜像
echo "🧹 清理旧的测试资源..."
docker stop ai-invest-test 2>/dev/null || true
docker rm ai-invest-test 2>/dev/null || true
docker rmi ai-invest:test 2>/dev/null || true

# 构建测试镜像
echo "🔨 构建Docker镜像..."
docker build -t ai-invest:test .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker镜像构建成功${NC}"
else
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    exit 1
fi

# 创建测试环境变量文件
echo "📝 创建测试环境变量..."
cat > .env.test << EOF
OPENAI_API_KEY=test-key
LANGCHAIN_API_KEY=test-langchain-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai_invest_test
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/test/test/test
RSS_FEEDS=https://finance.yahoo.com/news/rssindex
MAX_NEWS_ARTICLES=2
EOF

# 运行测试容器
echo "🚀 启动测试容器..."
docker run -d \
    --name ai-invest-test \
    --env-file .env.test \
    -p 8001:8000 \
    --health-cmd="curl -f http://localhost:8000/ || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    ai-invest:test

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 检查容器状态
if docker ps | grep -q ai-invest-test; then
    echo -e "${GREEN}✅ 容器启动成功${NC}"
else
    echo -e "${RED}❌ 容器启动失败${NC}"
    docker logs ai-invest-test
    exit 1
fi

# 检查健康状态
echo "🏥 检查容器健康状态..."
if docker inspect ai-invest-test | grep -q '"Status": "healthy"'; then
    echo -e "${GREEN}✅ 容器健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  容器健康检查未通过，但继续测试${NC}"
fi

# 测试应用端点
echo "🧪 测试应用端点..."

# 测试健康检查端点
echo "  测试健康检查端点 /"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "  ${GREEN}✅ 健康检查端点正常 (HTTP $HEALTH_RESPONSE)${NC}"
else
    echo -e "  ${RED}❌ 健康检查端点异常 (HTTP $HEALTH_RESPONSE)${NC}"
fi

# 测试API文档端点
echo "  测试API文档端点 /docs"
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs || echo "000")
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo -e "  ${GREEN}✅ API文档端点正常 (HTTP $DOCS_RESPONSE)${NC}"
else
    echo -e "  ${RED}❌ API文档端点异常 (HTTP $DOCS_RESPONSE)${NC}"
fi

# 测试OpenAPI端点
echo "  测试OpenAPI端点 /openapi.json"
OPENAPI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/openapi.json || echo "000")
if [ "$OPENAPI_RESPONSE" = "200" ]; then
    echo -e "  ${GREEN}✅ OpenAPI端点正常 (HTTP $OPENAPI_RESPONSE)${NC}"
else
    echo -e "  ${RED}❌ OpenAPI端点异常 (HTTP $OPENAPI_RESPONSE)${NC}"
fi

# 显示容器日志
echo "📋 显示容器日志 (最近10行):"
docker logs --tail 10 ai-invest-test

# 显示容器资源使用情况
echo "📊 容器资源使用情况:"
docker stats --no-stream ai-invest-test

echo ""
echo -e "${GREEN}🎉 本地Docker测试完成！${NC}"
echo "🌐 应用地址: http://localhost:8001"
echo "📚 API文档: http://localhost:8001/docs"
echo ""
echo "💡 提示:"
echo "  - 使用 'docker logs -f ai-invest-test' 查看实时日志"
echo "  - 使用 'docker stop ai-invest-test' 停止测试容器"
echo "  - 使用 'docker rm ai-invest-test' 删除测试容器"
echo "  - 使用 'docker rmi ai-invest:test' 删除测试镜像" 