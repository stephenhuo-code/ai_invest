#!/bin/bash

# Azure Container Apps 部署脚本
# 使用方法: ./deploy.sh

set -e

echo "🚀 开始部署到 Azure Container Apps..."

# 检查必要的环境变量
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "❌ 错误: 请设置 AZURE_SUBSCRIPTION_ID 环境变量"
    exit 1
fi

if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    echo "❌ 错误: 请设置 AZURE_RESOURCE_GROUP 环境变量"
    exit 1
fi

if [ -z "$CONTAINER_APP_NAME" ]; then
    echo "❌ 错误: 请设置 CONTAINER_APP_NAME 环境变量"
    exit 1
fi

# 设置默认值
AZURE_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-"rg-ai"}
CONTAINER_APP_NAME=${CONTAINER_APP_NAME:-"agent"}
LOCATION=${LOCATION:-"southeastasia"}
ENVIRONMENT_NAME=${ENVIRONMENT_NAME:-"cae-agent"}

echo "📍 部署信息:"
echo "   订阅ID: $AZURE_SUBSCRIPTION_ID"
echo "   资源组: $AZURE_RESOURCE_GROUP"
echo "   位置: $LOCATION"
echo "   环境: $ENVIRONMENT_NAME"
echo "   应用名称: $CONTAINER_APP_NAME"

# 登录Azure
echo "🔐 登录 Azure..."
az login

# 设置订阅
echo "📋 设置订阅..."
az account set --subscription $AZURE_SUBSCRIPTION_ID

# 检查资源组是否存在
if ! az group show --name $AZURE_RESOURCE_GROUP --query id -o tsv >/dev/null 2>&1; then
    echo "📦 创建资源组..."
    az group create --name $AZURE_RESOURCE_GROUP --location $LOCATION
fi

# 检查Container Apps环境是否存在
if ! az containerapp env show --name $ENVIRONMENT_NAME --resource-group $AZURE_RESOURCE_GROUP --query id -o tsv >/dev/null 2>&1; then
    echo "🏗️ 创建 Container Apps 环境..."
    az containerapp env create \
        --name $ENVIRONMENT_NAME \
        --resource-group $AZURE_RESOURCE_GROUP \
        --location $LOCATION
fi

# 构建并推送Docker镜像
echo "🐳 构建并推送 Docker 镜像..."
IMAGE_NAME="ghcr.io/stephenhuo-code/ai_invest:latest"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# 部署到Container Apps
echo "🚀 部署到 Container Apps..."
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $AZURE_RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $IMAGE_NAME \
    --target-port 8000 \
    --ingress external \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 5 \
    --env-vars LANGSMITH_TRACING=true LANGSMITH_PROJECT=ai_invest

echo "✅ 部署完成!"
echo "🌐 应用URL: https://$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $AZURE_RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"

# 显示应用状态
echo "📊 应用状态:"
az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $AZURE_RESOURCE_GROUP \
    --query "{Name:name,Status:properties.provisioningState,URL:properties.configuration.ingress.fqdn}" \
    -o table 