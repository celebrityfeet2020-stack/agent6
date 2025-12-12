# Agent6 Rebuilt Dockerfile
# 基于Python 3.11的官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制整个项目
COPY . .

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs

# 设置时区为北京时间
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 暴露端口
EXPOSE 8888

# 启动命令
CMD ["python3", "main.py"]
