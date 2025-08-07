#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境变量加载器
支持从 .env 文件加载环境变量
"""

import os
from pathlib import Path

def load_env_file():
    """加载 .env 文件中的环境变量"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")

def get_required_env(key, description=""):
    """获取必需的环境变量"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"请设置环境变量 {key}{' - ' + description if description else ''}")
    return value

def get_optional_env(key, default=None):
    """获取可选的环境变量"""
    return os.getenv(key, default)

# 在模块加载时自动加载 .env 文件
load_env_file() 