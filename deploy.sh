#!/bin/bash
# Agent6 Rebuilt 部署脚本

echo "=========================================="
echo "Agent6 Rebuilt 部署脚本"
echo "=========================================="

# 1. 安装依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 2. 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data logs

# 3. 启动应用
echo "🚀 启动Agent6..."
python3 main.py
