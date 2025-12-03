# M3 Agent System v3.5 - Fixed sshpass missing issue for RPA password authentication
# Base Image: Playwright (includes Chromium, Firefox, WebKit)
# This avoids browser compatibility issues

FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models to avoid runtime downloads
# This significantly speeds up first-time startup
RUN python3 -c "import easyocr; reader = easyocr.Reader(['en', 'ch_sim'], download_enabled=True)"

# Pre-download Whisper small model for Speech Recognition
# Model size: ~244MB, provides good accuracy and speed balance
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
