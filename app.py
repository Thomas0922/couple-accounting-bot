import os
import re
import sys
import psycopg2
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- 讀取環境變數 (不再寫死) ---
# 請確認 Render 的 Environment Variables 都有設定這三個變數
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
DATABASE_URL = os.environ.get('DATABASE_URL')

# 檢查變數是否存在，若不存在印出錯誤 (方便除錯)
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET or not DATABASE_URL:
    print("錯誤: 環境變數尚未設定完成！請至 Render Dashboard 設定。", file=sys.stderr)
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# --- 資料庫連線函式 ---
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 Header 的簽章
    signature = request.headers.get('X-Line-Signature', '')
    # 取得 Body 內容
    body = request.get_data(as_text=True)

    # 印出 Log 方便觀察 (在 Render Logs 可以看到)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip() # 去除前後空白
    user_id = event.source.user_id   # 取得發送者的 User ID
    
    # === 功能 1：記帳邏輯 ===
    # 格式：項目 空白 金額 (例如：晚餐 200)
    # Regex 解析：(.+?) 代表項目, (\d+) 代表數字
    match = re.match(r'^(.+?)\s+(\d+)$', msg)
    
    if match:
        item = match.group(1)
        amount = int(match.group(2))
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            # SQL: 寫入記帳表
            cursor.execute(
                "INSERT INTO expenses (user_id, item, amount) VALUES (%s, %s, %s)",
                (user_id, item, amount)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            reply_text = f"✅ 記帳成功！\n項目：{item}\n金額：${amount}"
        except Exception as e:
            print(f"Database Error: {e}", file=sys.stderr)
            reply_text = "❌ 記帳失敗，請檢查資料庫連線設定。"
            
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # === 功能 2：查詢結算 ===
    # 指令：結算
    if msg == "結算":
        try:
            conn = get_db()
            cursor = conn.cursor()
            # SQL: 撈出每個人的總花費 (SUM)
            cursor.execute("SELECT user_id, SUM(amount) FROM expenses GROUP BY user_id")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not rows:
                reply_text = "目前還沒有任何記帳紀錄喔！"
            else:
                reply_text = "📊 目前消費統計：\n"
                reply_text += "------------------\n"
                for row in rows:
                    # 因為 User ID 很長，我們只顯示前 4 碼當作代號
                    uid_short = row[0][:4]
                    total = row[1]
                    reply_text += f"用戶 ({uid_short}..) : ${total}\n"
                reply_text += "------------------\n"
                reply_text += "詳細結算請自行計算差額。"
                    
        except Exception as e:
            print(f"Database Error: {e}", file=sys.stderr)
            reply_text = "❌ 查詢失敗，請稍後再試。"
            
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # === 其他：說明 ===
    # 如果輸入「說明」或「help」，回傳教學
    if msg.lower() in ["說明", "help", "教學"]:
        help_text = (
            "📖 記帳機器人使用教學：\n\n"
            "1️⃣ 記帳：\n"
            "輸入「項目 空白 金額」\n"
            "例如：晚餐 250\n\n"
            "2️⃣ 結算：\n"
            "輸入「結算」查看統計"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

    # 其他未知的文字訊息，已讀不回 (避免在群組太吵)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
