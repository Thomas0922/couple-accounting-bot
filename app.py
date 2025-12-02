import os
import re
import psycopg2
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 設定 Log 顯示 (方便除錯)
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# === 1. 從環境變數讀取設定 ===
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
DATABASE_URL = os.environ.get('DATABASE_URL')

# 初始化 Line Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === 2. 資料庫連線輔助函式 ===
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 Header 簽名
    signature = request.headers.get('X-Line-Signature', '')
    # 取得訊息內容
    body = request.get_data(as_text=True)
    
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip() # 去除前後空白
    user_id = event.source.user_id   # 取得發話者的 Line ID
    
    # === 功能 A：記帳 (格式：項目 金額) ===
    # Regex 解析：抓取 "任意文字" + "空格" + "數字"
    match = re.match(r'^(.+?)\s+(\d+)$', msg)
    
    if match:
        item = match.group(1)
        amount = int(match.group(2))
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # 寫入資料庫
            cur.execute(
                "INSERT INTO expenses (user_id, item, amount) VALUES (%s, %s, %s)",
                (user_id, item, amount)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            # 嘗試取得用戶暱稱 (讓回覆更有溫度)
            try:
                profile = line_bot_api.get_profile(user_id)
                user_name = profile.display_name
            except:
                user_name = "親愛的"

            reply_text = f"✅ {user_name} 記帳成功！\n項目：{item}\n金額：${amount}"
        except Exception as e:
            app.logger.error(f"Database Error: {e}")
            reply_text = "❌ 記帳失敗，資料庫連線可能有問題。"
            
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # === 功能 B：查詢結算 (指令：結算) ===
    if msg == "結算":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # 統計每個人的總金額
            cur.execute("SELECT user_id, SUM(amount) FROM expenses GROUP BY user_id")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            if not rows:
                reply_text = "目前還沒有任何消費紀錄喔！"
            else:
                reply_text = "📊 本期消費統計：\n"
                total_all = 0
                
                for row in rows:
                    target_user_id = row[0]
                    total = row[1]
                    total_all += total
                    
                    # === 關鍵修改：呼叫 LINE API 取得真實暱稱 ===
                    try:
                        profile = line_bot_api.get_profile(target_user_id)
                        display_name = profile.display_name
                    except LineBotApiError:
                        # 如果抓不到名字 (可能沒加好友)，就顯示後4碼
                        display_name = f"用戶({target_user_id[:4]})"
                    
                    reply_text += f"{display_name}: ${total}\n"
                
                reply_text += f"----------------\n💰 總支出: ${total_all}"
                    
        except Exception as e:
            app.logger.error(f"Database Error: {e}")
            reply_text = "❌ 查詢失敗，請稍後再試。"
            
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # === 功能 C：清除所有資料 (指令：清除) ===
    if msg == "清除":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # 刪除 expenses 資料表內的所有資料
            cur.execute("DELETE FROM expenses")
            conn.commit()
            cur.close()
            conn.close()
            
            reply_text = "🗑️ 已清除所有記帳資料！\n一切重新開始 ✨"
        except Exception as e:
            app.logger.error(f"Database Error: {e}")
            reply_text = "❌ 清除失敗，請檢查資料庫。"
            
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

@app.route("/", methods=['GET'])
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
