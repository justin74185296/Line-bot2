"""
LINE 記帳機器人主程式
專業記帳機器人 - 對標 Money Manager EX、Wallet、Toshl 等專業記帳 App
"""
import os
import sys
import threading
import time
from datetime import datetime

from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent,
)

from config import Config
from services.storage import StorageService
from services.reminder import ReminderService
from handlers.message_handler import MessageHandler

# 初始化 Flask
app = Flask(__name__)

# 初始化 LINE Bot
configuration = Configuration(access_token=Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

# 初始化服務
storage = StorageService()
message_handler = MessageHandler(storage)
reminder_service = ReminderService()

# 設定提醒服務依賴
with ApiClient(configuration) as api_client:
    line_bot_api = MessagingApi(api_client)
    reminder_service.set_dependencies(line_bot_api, storage)


@app.route("/", methods=["GET"])
def index():
    """首頁 - 健康檢查端點"""
    return {
        "status": "ok",
        "service": "LINE 記帳機器人",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.route("/health", methods=["GET"])
def health():
    """健康檢查端點"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook 回調端點"""
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get("X-Line-Signature", "")
    
    # 取得請求體
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")
    
    # 驗證簽名並處理 webhook
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Check your channel access token/channel secret.")
        abort(400)
    
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息事件"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    app.logger.info(f"收到訊息: user={user_id}, text={text}")
    
    # 處理訊息
    reply_text = message_handler.handle_message(user_id, text)
    
    # 回覆訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )


@handler.add(FollowEvent)
def handle_follow(event):
    """處理用戶加入好友事件"""
    user_id = event.source.user_id
    
    app.logger.info(f"新用戶加入: {user_id}")
    
    # 發送歡迎訊息
    reply_text = message_handler.handle_follow(user_id)
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    """處理用戶取消好友事件"""
    user_id = event.source.user_id
    
    app.logger.info(f"用戶取消好友: {user_id}")
    
    # 處理取消好友邏輯
    message_handler.handle_unfollow(user_id)


def run_scheduler():
    """
    執行定時任務
    每小時檢查一次提醒和預算警告
    """
    while True:
        try:
            current_hour = datetime.now().hour
            
            # 早上 9 點檢查帳單提醒
            if current_hour == 9:
                app.logger.info("執行帳單提醒檢查...")
                count = reminder_service.check_and_send_reminders()
                app.logger.info(f"已發送 {count} 則帳單提醒")
            
            # 晚上 8 點檢查預算警告
            if current_hour == 20:
                app.logger.info("執行預算警告檢查...")
                count = reminder_service.check_and_send_budget_warnings()
                app.logger.info(f"已發送 {count} 則預算警告")
            
        except Exception as e:
            app.logger.error(f"定時任務執行失敗: {e}")
        
        # 每小時執行一次
        time.sleep(3600)


def start_scheduler():
    """啟動定時任務執行緒"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    app.logger.info("定時任務已啟動")


def keep_alive():
    """
    保持伺服器活躍
    在 Replit 免費版上，伺服器會在一段時間後休眠
    這個功能可以透過外部服務（如 UptimeRobot）定期 ping 來保持活躍
    """
    pass  # 實際的 keep-alive 邏輯由外部服務處理


if __name__ == "__main__":
    # 檢查環境變數
    if not Config.LINE_CHANNEL_ACCESS_TOKEN:
        print("錯誤：請設定 LINE_CHANNEL_ACCESS_TOKEN 環境變數")
        print("在 Replit 中，請前往 Secrets 設定")
        sys.exit(1)
    
    if not Config.LINE_CHANNEL_SECRET:
        print("錯誤：請設定 LINE_CHANNEL_SECRET 環境變數")
        print("在 Replit 中，請前往 Secrets 設定")
        sys.exit(1)
    
    print("=" * 50)
    print("LINE 記帳機器人啟動中...")
    print("=" * 50)
    print(f"伺服器位址: http://{Config.HOST}:{Config.PORT}")
    print(f"Webhook URL: http://your-domain/callback")
    print("=" * 50)
    
    # 啟動定時任務
    start_scheduler()
    
    # 啟動 Flask 伺服器
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
