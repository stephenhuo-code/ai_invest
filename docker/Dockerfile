# Phase 1 Architecture Dockerfile
# Supports PostgreSQL + pgvector layered architecture
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# 安装系统依赖（包括curl用于健康检查）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p reports cache logs

# 创建非root用户用于安全运行
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查 - 使用新架构的健康检查端点
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令 - 使用新的 main_new.py 入口点
CMD ["uvicorn", "main_new:app", "--host", "0.0.0.0", "--port", "8000"]

# 为开发环境提供备选启动命令
# 开发模式: docker run -e ENVIRONMENT=development your-image
# 这将启用 reload 模式

# 构建时标签
LABEL maintainer="AI Invest Team"
LABEL version="2.0.0"
LABEL description="AI Invest Trend - Phase 1 Architecture with PostgreSQL + pgvector" 