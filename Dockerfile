# Agent6 Rebuilt Dockerfile
# 基于Playwright官方镜像(包含Chromium浏览器)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# 设置工作目录
WORKDIR /app

# 安装系统依赖和Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 预下载AI模型(避免每次部署都下载)
RUN echo "🔧 预下载EasyOCR模型..." && \
    python3 -c "import easyocr; reader = easyocr.Reader(['en', 'ch_sim']); print('✅ EasyOCR模型下载完成')" && \
    echo "🔧 预下载Whisper模型..." && \
    python3 -c "import whisper; model = whisper.load_model('small'); print('✅ Whisper模型下载完成')"

# 复制整个项目
COPY . .

# 构建聊天室前端
RUN cd chatroom_ui && \
    pnpm install && \
    pnpm build && \
    echo "✅ 聊天室前端构建完成"

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs

# 设置时区为北京时间
ENV TZ=Asia/Shanghai

# 抑制CUDA/MPS警告(容器内没有GPU)
ENV PYTORCH_ENABLE_MPS_FALLBACK=1
ENV CUDA_VISIBLE_DEVICES=""
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 暴露端口
EXPOSE 12111

# 启动命令
CMD ["python3", "main.py"]
