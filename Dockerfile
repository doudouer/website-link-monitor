FROM python:3.9-slim

# 安装Chrome和ChromeDriver依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p reports templates screenshots

# 设置环境变量
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PORT=5001

# 暴露端口
EXPOSE $PORT

# 启动命令
CMD gunicorn web_app_complete:app --bind 0.0.0.0:$PORT --timeout 120
