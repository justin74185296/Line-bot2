# 💰 LINE 記帳機器人

專業級 LINE 記帳機器人，讓你輕鬆追蹤每一筆收支！

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-v3-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特色

### 📝 智能記帳
- **自動解析**：輸入「早餐 50」自動識別類別為「飲食」
- **支援備註**：「早餐 50 麥當勞」→ 類別「飲食」，備註「麥當勞」
- **收入識別**：「薪水 30000」自動識別為收入
- **多格式支援**：50、50元、$50、NT50 都能正確解析

### 📊 完整統計
- **儀表板**：本月總收入、支出、餘額、預算進度
- **類別分析**：支出類別分佈圖表化顯示
- **多維度統計**：今日、本週、本月、指定月份
- **現金流預測**：根據目前消費預測月底餘額

### 💰 預算管理
- **總預算設定**：控制整體支出
- **類別預算**：針對特定類別設定預算
- **超支提醒**：達到 80% 或超支時自動警告

### ⏰ 帳單提醒
- 設定固定帳單提醒（如每月 25 日房租）
- 到期自動推播通知

### 📤 資料匯出
- 匯出 CSV 格式，方便匯入 Excel

## 🚀 快速開始

### 前置需求

- Python 3.9 或以上版本
- LINE 開發者帳號

### 1️⃣ 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立新的 Provider（如果沒有的話）
3. 建立新的 Messaging API Channel
4. 記下以下資訊：
   - **Channel Secret**（在 Basic settings 頁面）
   - **Channel Access Token**（在 Messaging API 頁面，點擊 Issue）

### 2️⃣ 在 Cursor 中設置專案

```bash
# 1. 複製專案到你想要的位置
cd your-workspace

# 2. 建立虛擬環境
python -m venv venv

# 3. 啟動虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安裝依賴套件
pip install -r requirements.txt

# 5. 複製環境變數範例檔案
cp .env.example .env

# 6. 編輯 .env 檔案，填入你的 LINE Bot 資訊
```

### 3️⃣ 設定環境變數

編輯 `.env` 檔案：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的_Channel_Access_Token
LINE_CHANNEL_SECRET=你的_Channel_Secret
FLASK_DEBUG=True
```

### 4️⃣ 啟動應用程式

```bash
python main.py
```

應用程式將在 `http://localhost:5000` 啟動。

### 5️⃣ 使用 ngrok 進行本地測試

由於 LINE Bot 需要 HTTPS 網址，我們使用 ngrok 來建立安全通道：

```bash
# 1. 下載並安裝 ngrok
# https://ngrok.com/download

# 2. 啟動 ngrok
ngrok http 5000
```

ngrok 會給你一個 HTTPS 網址，例如：`https://xxxx-xx-xx-xxx-xx.ngrok.io`

### 6️⃣ 設定 LINE Webhook

1. 回到 LINE Developers Console
2. 進入你的 Channel → Messaging API
3. 設定 Webhook URL：`https://你的ngrok網址/callback`
4. 開啟 「Use webhook」
5. 關閉「Auto-reply messages」和「Greeting messages」（使用我們自己的回覆）

### 7️⃣ 開始使用！

掃描 Channel 的 QR Code 加入好友，開始記帳！

## 📖 使用說明

### 快速記帳

直接輸入文字即可記帳：

| 輸入 | 結果 |
|------|------|
| `早餐 50` | 飲食 -$50 |
| `咖啡 100 星巴克` | 飲食 -$100（備註：星巴克）|
| `捷運 30` | 交通 -$30 |
| `薪水 30000` | 收入 +$30,000 |
| `獎金 5000 年終` | 收入 +$5,000（備註：年終）|

### 查看統計

| 指令 | 說明 |
|------|------|
| `儀表板` | 本月財務總覽 |
| `今天` | 今日收支明細 |
| `本週` | 本週統計 |
| `本月` | 本月統計 |
| `統計 2026/01` | 指定月份統計 |

### 預算管理

| 指令 | 說明 |
|------|------|
| `預算` | 查看預算設定 |
| `設定預算 10000` | 設定每月總預算 |
| `設定預算 飲食 5000` | 設定飲食類別預算 |

### 帳單提醒

| 指令 | 說明 |
|------|------|
| `提醒` | 查看提醒列表 |
| `設定提醒 房租 10000 每月25日` | 新增帳單提醒 |

### 其他功能

| 指令 | 說明 |
|------|------|
| `類別` | 查看類別列表 |
| `新增類別 旅行` | 新增自訂類別 |
| `刪除類別 旅行` | 刪除自訂類別 |
| `匯出` | 匯出本月 CSV |
| `刪除` | 查看可刪除的記錄 |
| `刪除 123` | 刪除指定記錄 |
| `清空` | 清除所有記錄 |
| `幫助` | 查看完整說明 |

## 📂 專案結構

```
line-accounting-bot/
├── main.py           # Flask 應用程式入口
├── config.py         # 配置檔案
├── database.py       # SQLite 資料庫操作
├── parser.py         # 智能文字解析
├── handlers.py       # 訊息處理器
├── utils.py          # 工具函數
├── requirements.txt  # 依賴套件
├── .env.example      # 環境變數範例
├── .env              # 環境變數（不納入版控）
├── data.db           # SQLite 資料庫（自動建立）
└── README.md         # 專案說明
```

## 🎨 類別系統

### 預設支出類別

| 類別 | 關鍵字範例 |
|------|-----------|
| 🍽️ 飲食 | 早餐、午餐、晚餐、咖啡、便當、餐廳... |
| 🚗 交通 | 捷運、公車、加油、停車、計程車... |
| 🛒 購物 | 衣服、網購、日用品、3C... |
| 🎮 娛樂 | 電影、遊戲、Netflix、旅遊... |
| 💊 醫療 | 看診、藥、醫院、健檢... |
| 🏠 居住 | 房租、水電、瓦斯、網路... |
| 📦 其他 | 未分類支出 |

### 收入類別

| 類別 | 關鍵字範例 |
|------|-----------|
| 💰 收入 | 薪水、獎金、紅包、利息、投資收益... |

## 🚀 部署指南

### Railway 部署

1. 在 [Railway](https://railway.app/) 建立新專案
2. 連接 GitHub 儲存庫
3. 設定環境變數：
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_CHANNEL_SECRET`
4. 部署完成後，更新 LINE Webhook URL

### Render 部署

1. 在 [Render](https://render.com/) 建立新的 Web Service
2. 連接 GitHub 儲存庫
3. 設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
4. 設定環境變數
5. 部署完成後，更新 LINE Webhook URL

### Fly.io 部署

1. 安裝 [flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. 執行以下命令：

```bash
fly launch
fly secrets set LINE_CHANNEL_ACCESS_TOKEN=your_token
fly secrets set LINE_CHANNEL_SECRET=your_secret
fly deploy
```

3. 更新 LINE Webhook URL

### 建立 Dockerfile（可選）

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## 🔧 進階設定

### 定時提醒（使用 APScheduler）

如果要啟用定時提醒功能，可以在 `main.py` 中加入：

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_reminders, 'cron', hour=9)  # 每天早上 9 點
scheduler.start()
```

### 資料備份

SQLite 資料庫儲存在 `data.db`，可以定期備份此檔案。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 這個專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [LINE Messaging API](https://developers.line.biz/en/services/messaging-api/)
- [Flask](https://flask.palletsprojects.com/)
- [line-bot-sdk-python](https://github.com/line/line-bot-sdk-python)

---

💡 **提示**：在 Cursor 中，你可以使用 Claude 來幫助你擴充更多功能！

例如：
- 「幫我新增週報功能」
- 「幫我優化智能分類邏輯」
- 「幫我加入多幣別支援」

Happy Accounting! 🎉
