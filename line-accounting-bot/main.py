"""
LINE 記帳機器人 - 主程式入口
Flask 應用程式與 LINE Webhook 處理
"""
import os
import logging
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent
)
from linebot.v3.exceptions import InvalidSignatureError

import config
import handlers

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 建立 Flask 應用
app = Flask(__name__)

# LINE Bot 配置
configuration = Configuration(
    access_token=config.LINE_CHANNEL_ACCESS_TOKEN
)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)


@app.route('/')
def index():
    """首頁 - 用於健康檢查"""
    return '''
    <html>
        <head>
            <title>LINE 記帳機器人</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #00B900 0%, #00D900 100%);
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 40px 60px;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }
                h1 { color: #00B900; margin-bottom: 10px; }
                p { color: #666; margin: 5px 0; }
                .status { 
                    display: inline-block;
                    padding: 5px 15px;
                    background: #00B900;
                    color: white;
                    border-radius: 20px;
                    margin-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💰 LINE 記帳機器人</h1>
                <p>專業記帳小幫手</p>
                <p class="status">✅ 服務運行中</p>
            </div>
        </body>
    </html>
    '''


@app.route('/health')
def health():
    """健康檢查端點"""
    return {'status': 'healthy', 'service': 'line-accounting-bot'}


@app.route('/callback', methods=['POST'])
def callback():
    """
    LINE Webhook 回調端點
    接收並處理來自 LINE Platform 的事件
    """
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get('X-Line-Signature', '')
    
    # 取得請求內容
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")
    
    # 驗證簽名並處理 Webhook
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    """
    處理文字訊息事件
    
    Args:
        event: LINE 訊息事件
    """
    user_id = event.source.user_id
    text = event.message.text
    
    logger.info(f"Received message from {user_id}: {text}")
    
    try:
        # 處理訊息並取得回覆
        reply_text = handlers.handle_message(user_id, text)
        
        # 發送回覆
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        
        logger.info(f"Replied to {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        
        # 發送錯誤訊息
        try:
            with ApiClient(configuration) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="😅 抱歉，處理訊息時發生錯誤，請稍後再試")]
                    )
                )
        except Exception as reply_error:
            logger.error(f"Error sending error reply: {reply_error}")


@handler.add(FollowEvent)
def handle_follow(event: FollowEvent):
    """
    處理用戶加入好友事件
    
    Args:
        event: LINE 追蹤事件
    """
    user_id = event.source.user_id
    
    logger.info(f"New follower: {user_id}")
    
    try:
        # 取得歡迎訊息
        welcome_message = handlers.handle_follow_event(user_id)
        
        # 發送歡迎訊息
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=welcome_message)]
                )
            )
        
        logger.info(f"Sent welcome message to {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling follow event: {e}")


@handler.add(UnfollowEvent)
def handle_unfollow(event: UnfollowEvent):
    """
    處理用戶取消好友/封鎖事件
    
    Args:
        event: LINE 取消追蹤事件
    """
    user_id = event.source.user_id
    
    logger.info(f"User unfollowed: {user_id}")
    
    try:
        handlers.handle_unfollow_event(user_id)
    except Exception as e:
        logger.error(f"Error handling unfollow event: {e}")


def push_message(user_id: str, message: str) -> bool:
    """
    主動推送訊息給用戶（用於提醒功能）
    
    Args:
        user_id: 用戶 ID
        message: 訊息內容
    
    Returns:
        是否成功發送
    """
    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )
        logger.info(f"Pushed message to {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error pushing message to {user_id}: {e}")
        return False


def check_and_send_reminders():
    """
    檢查並發送今日到期的提醒
    
    這個函數可以被定時任務調用
    """
    import database
    import utils
    from datetime import datetime
    
    logger.info("Checking reminders...")
    
    # 這裡需要遍歷所有用戶
    # 在實際部署時，建議使用背景任務（如 APScheduler）
    # 並維護一個活躍用戶列表
    
    # 示範代碼（需要根據實際情況調整）
    # for user_id in get_active_users():
    #     reminders = database.get_today_reminders(user_id)
    #     for reminder in reminders:
    #         msg = f"⏰ 帳單提醒\n\n📌 {reminder['name']}\n💰 金額：${utils.format_amount(reminder['amount'])}\n\n今天記得繳費喔！"
    #         push_message(user_id, msg)
    #         database.update_reminder_notified(user_id, reminder['id'])


if __name__ == '__main__':
    # 檢查必要的環境變數
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set!")
    if not config.LINE_CHANNEL_SECRET:
        logger.warning("LINE_CHANNEL_SECRET is not set!")
    
    logger.info(f"Starting LINE Accounting Bot on {config.FLASK_HOST}:{config.FLASK_PORT}")
    logger.info(f"Debug mode: {config.FLASK_DEBUG}")
    
    # 啟動 Flask 應用
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
