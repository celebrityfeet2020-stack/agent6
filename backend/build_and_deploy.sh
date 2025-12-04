#!/bin/bash

# M3 Agent System v2.2.0 - Build and Deploy Script
# 本脚本用于构建 Docker 镜像并部署到 Mac Studio

set -e

echo "🚀 M3 Agent System v2.2.0 - Build and Deploy"
echo "============================================="

# 检查必要文件
echo "📋 检查必要文件..."
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "requirements.txt"
    "main.py"
    "admin_app.py"
    ".env"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少文件: $file"
        exit 1
    fi
    echo "  ✓ $file"
done

# 检查目录
required_dirs=(
    "app"
    "config"
    "admin_ui"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ 缺少目录: $dir"
        exit 1
    fi
    echo "  ✓ $dir/"
done

echo ""
echo "✅ 所有必要文件和目录检查通过！"
echo ""

# 选择构建方式
echo "请选择构建方式:"
echo "1. 本地构建（推荐用于测试）"
echo "2. 推送到 GitHub 并使用 Actions 构建（推荐用于生产）"
echo "3. 只验证，不构建"
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "📦 开始本地构建..."
        docker build -t m3-agent:v2.2.0 .
        
        echo ""
        echo "✅ 构建完成！"
        echo ""
        echo "下一步："
        echo "1. 停止旧容器: docker-compose down"
        echo "2. 启动新容器: docker-compose up -d"
        echo "3. 查看日志: docker-compose logs -f m3-agent-api"
        ;;
    
    2)
        echo ""
        echo "📤 准备推送到 GitHub..."
        
        # 检查是否有 git 仓库
        if [ ! -d ".git" ]; then
            echo "初始化 Git 仓库..."
            git init
            git add .
            git commit -m "feat: M3 Agent System v2.2.0 - 完整的 Agent 工作流"
        else
            echo "Git 仓库已存在，添加更改..."
            git add .
            git commit -m "feat: M3 Agent System v2.2.0 - 完整的 Agent 工作流" || echo "没有新的更改"
        fi
        
        echo ""
        echo "请手动执行以下命令推送到 GitHub:"
        echo ""
        echo "  git remote add origin https://github.com/YOUR_USERNAME/m3-agent-system.git"
        echo "  git branch -M main"
        echo "  git push -u origin main"
        echo ""
        echo "然后在 GitHub 仓库中配置 Actions 进行自动构建。"
        ;;
    
    3)
        echo ""
        echo "✅ 验证完成！所有文件和目录结构正确。"
        ;;
    
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

echo ""
echo "🎉 脚本执行完成！"
