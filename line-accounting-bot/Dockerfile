# LINE 記帳機器人 Dockerfile
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 設定環境變數
ENV FLASK_HOST=0.0.0.0
ENV FLASK_DEBUG=False

# 使用 PORT 環境變數（Fly.io/Railway/Render 會自動設定）
ENV PORT=8080

# 暴露端口
EXPOSE 8080

# 啟動應用（使用 $PORT 環境變數）
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 main:app
