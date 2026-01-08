"""
LINE 記帳機器人 - 主程式入口
Flask 應用程式與 LINE Webhook 處理
"""
import os
import logging
from flask import Flask, request, abort

import config

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 建立 Flask 應用
app = Flask(__name__)

# LINE Bot 全域變數
configuration = None
handler = None
line_bot_enabled = False


def init_line_bot():
    """初始化 LINE Bot"""
    global configuration, handler, line_bot_enabled
    
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_CHANNEL_SECRET:
        logger.warning("LINE credentials not configured. Bot features disabled.")
        return False
    
    try:
        from linebot.v3 import WebhookHandler
        from linebot.v3.messaging import Configuration
        
        configuration = Configuration(
            access_token=config.LINE_CHANNEL_ACCESS_TOKEN
        )
        handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
        
        # 註冊事件處理器
        register_line_handlers()
        
        logger.info("LINE Bot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize LINE Bot: {e}")
        return False


def register_line_handlers():
    """註冊 LINE 事件處理器"""
    from linebot.v3.messaging import (
        ApiClient,
        MessagingApi,
        ReplyMessageRequest,
        TextMessage
    )
    from linebot.v3.webhooks import (
        MessageEvent,
        TextMessageContent,
        FollowEvent,
        UnfollowEvent
    )
    import handlers as msg_handlers

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        """處理文字訊息事件"""
        user_id = event.source.user_id
        text = event.message.text
        
        logger.info(f"Received message from {user_id}: {text}")
        
        try:
            reply_text = msg_handlers.handle_message(user_id, text)
            
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
    def handle_follow(event):
        """處理用戶加入好友事件"""
        user_id = event.source.user_id
        logger.info(f"New follower: {user_id}")
        
        try:
            welcome_message = msg_handlers.handle_follow_event(user_id)
            
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
    def handle_unfollow(event):
        """處理用戶取消好友事件"""
        user_id = event.source.user_id
        logger.info(f"User unfollowed: {user_id}")
        
        try:
            msg_handlers.handle_unfollow_event(user_id)
        except Exception as e:
            logger.error(f"Error handling unfollow event: {e}")


@app.route('/')
def index():
    """首頁"""
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
    return {'status': 'healthy', 'service': 'line-accounting-bot', 'line_bot': line_bot_enabled}


@app.route('/callback', methods=['POST'])
def callback():
    """LINE Webhook 回調端點"""
    if not line_bot_enabled or handler is None:
        logger.error("LINE Bot not configured")
        return {'error': 'LINE Bot not configured'}, 503
    
    from linebot.v3.exceptions import InvalidSignatureError
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return 'OK'


# 初始化 LINE Bot
line_bot_enabled = init_line_bot()


if __name__ == '__main__':
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set!")
    if not config.LINE_CHANNEL_SECRET:
        logger.warning("LINE_CHANNEL_SECRET is not set!")
    
    port = int(os.environ.get('PORT', config.FLASK_PORT))
    logger.info(f"Starting LINE Accounting Bot on {config.FLASK_HOST}:{port}")
    
    app.run(
        host=config.FLASK_HOST,
        port=port,
        debug=config.FLASK_DEBUG
    )
