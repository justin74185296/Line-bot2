"""
LINE 記帳機器人 - 主程式入口
Flask 應用程式與 LINE Webhook 處理
"""
import os
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 建立 Flask 應用
from flask import Flask, request, abort, jsonify
app = Flask(__name__)

# LINE Bot 全域變數（延遲初始化）
_line_bot_initialized = False
_configuration = None
_handler = None


def get_line_config():
    """取得 LINE 配置（延遲載入）"""
    global _line_bot_initialized, _configuration, _handler
    
    if _line_bot_initialized:
        return _configuration, _handler
    
    # 載入配置
    line_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    line_secret = os.environ.get('LINE_CHANNEL_SECRET', '')
    
    if not line_token or not line_secret:
        logger.warning("LINE credentials not configured")
        _line_bot_initialized = True
        return None, None
    
    try:
        from linebot.v3 import WebhookHandler
        from linebot.v3.messaging import Configuration
        
        _configuration = Configuration(access_token=line_token)
        _handler = WebhookHandler(line_secret)
        
        # 註冊事件處理器
        register_handlers(_handler, _configuration)
        
        logger.info("LINE Bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LINE Bot: {e}")
    
    _line_bot_initialized = True
    return _configuration, _handler


def register_handlers(handler, configuration):
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
    
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        user_id = event.source.user_id
        text = event.message.text
        logger.info(f"Message from {user_id}: {text}")
        
        try:
            import handlers as msg_handlers
            reply_text = msg_handlers.handle_message(user_id, text)
            
            with ApiClient(configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            try:
                with ApiClient(configuration) as api_client:
                    MessagingApi(api_client).reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="😅 發生錯誤，請稍後再試")]
                        )
                    )
            except:
                pass

    @handler.add(FollowEvent)
    def handle_follow(event):
        user_id = event.source.user_id
        logger.info(f"New follower: {user_id}")
        try:
            import handlers as msg_handlers
            welcome = msg_handlers.handle_follow_event(user_id)
            with ApiClient(configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=welcome)]
                    )
                )
        except Exception as e:
            logger.error(f"Follow error: {e}")

    @handler.add(UnfollowEvent)
    def handle_unfollow(event):
        logger.info(f"Unfollowed: {event.source.user_id}")


@app.route('/')
def index():
    """首頁"""
    return '<h1>💰 LINE 記帳機器人</h1><p>✅ 服務運行中</p>'


@app.route('/health')
def health():
    """健康檢查"""
    return jsonify(status='ok')


@app.route('/callback', methods=['POST'])
def callback():
    """LINE Webhook"""
    configuration, handler = get_line_config()
    
    if not handler:
        return jsonify(error='LINE Bot not configured'), 503
    
    from linebot.v3.exceptions import InvalidSignatureError
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        abort(500)
    
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
