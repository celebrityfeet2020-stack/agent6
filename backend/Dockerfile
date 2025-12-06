# Agent System v3.6.1 - Fixed timezone, tools loading, and performance monitoring
# Base Image: Playwright (includes Chromium, Firefox, WebKit)
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Set timezone to Beijing (Asia/Shanghai) - FIX #1
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies including tzdata for timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Timezone data - FIX #1
    tzdata \
    # Tesseract OCR (multiple languages)
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    libtesseract-dev \
    # FFmpeg for audio/video processing
    ffmpeg \
    libavcodec-extra \
    # Image processing libraries
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    # OpenCV dependencies
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    # Essential utilities
    curl \
    wget \
    git \
    openssh-client \
    sshpass \
    ca-certificates \
    # RPA dependencies
    x11-utils \
    xdotool \
    scrot \
    python3-tk \
    python3-dev \
    # Cleanup and set timezone
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models
RUN python3 -c "import easyocr; reader = easyocr.Reader(['en', 'ch_sim'], download_enabled=True)"

# Pre-download Whisper small model
RUN python3 -c "import whisper; model = whisper.load_model('small'); print('Whisper small model loaded successfully')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads /tmp/m3_agent

# Expose ports
EXPOSE 8888 8889

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command (both main app and admin panel)
CMD ["sh", "-c", "python admin_app.py & python main.py"]
