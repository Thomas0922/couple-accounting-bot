from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 直接寫死 (測試用)
LINE_CHANNEL_ACCESS_TOKEN = '6oJDYrICLrhln85HORAK8hOV7UxNekI7ZeUfVAz7hqZrphXddV/Jwc1077WEvpA9nhHTYP21yIUFOkr3QGKgUeYrlT5WbdgvtS0WUjt7dATVb1iypghur/v35+PPeHVOf+Ekgs5gCbqHzDzHMTqSHQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '6b6f99c9fa7b90df0c8cea5496384410'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    app.logger.info(f"Request body: {body}")
    app.logger.info(f"Signature: {signature}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Check your channel secret.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        abort(500)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"收到：{msg}")
    )

@app.route("/", methods=['GET'])
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
