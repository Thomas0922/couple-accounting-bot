情侶記帳 Line Bot (Couple Accounting Bot)

這是一個專為情侶或小團體設計的 LINE 記帳機器人。透過簡單的對話指令，輕鬆記錄共同開銷、自動拆帳，並提供詳細的結算報表。

不再需要下載複雜的記帳 App，直接在 LINE 聊天室裡就能完成所有記帳需求！

✨ 功能特色

直覺記帳：支援口語化輸入，無需嚴格格式（例如：晚餐 200 或 飲料50）。

自動拆帳：輸入總金額與幫付金額，機器人自動計算並記錄雙方帳務。

代記帳功能：可以幫另一半記錄消費。

補帳功能：支援指定日期補記過去的帳目。

結算報表：提供全體流水帳與個人消費統計，支援日期顯示。

資料庫管理：自動初始化資料庫，並提供移除單筆紀錄與清空資料庫的功能。

📱 指令大全

在聊天室中輸入 說明 或 help 也可以隨時呼叫此列表。

1. 初次使用

註冊名字：我是 [名字]

範例：我是 小王

注意：使用前必須先註冊，機器人才知道你是誰。

2. 一般記帳

記自己：[項目] [金額]

範例：晚餐 200

範例：飲料50 (黏在一起也可以)

幫對方記：[對方名字] [項目] [金額]

範例：老公 飲料 50

補舊帳：[日期] [項目] [金額]

範例：2023-12-01 午餐 150

3. 自動拆帳 

適合情境：總共花了 400 元，其中 150 元是幫對方付的 (代表自己付 250，對方欠 150)。

語法：[項目] [總額] 幫 [欠款金額]

範例：晚餐 400 幫 150

機器人會自動記錄：你消費 $250，對方消費 $150 (並標記需給還款)。

4. 查詢與結算

全體結算：結算

列出所有人的詳細消費明細與總支出。

個人結算：[名字] 結算

範例：老公 結算

只查看該用戶的消費紀錄。

5. 修改與管理

移除指定項目：移除 [項目名稱]

範例：移除 飲料 (刪除最新一筆名稱為「飲料」的紀錄)

移除最新一筆：移除最後一筆

不管是什麼，直接刪除剛剛記的那一筆。

清空資料庫：清除

⚠️ 警告：這會刪除所有資料，一切重新開始。

🛠️ 技術架構

語言：Python 3.x

框架：Flask

介面：LINE Messaging API (line-bot-sdk)

資料庫：PostgreSQL (推薦使用 Supabase)

部署：支援 Render / Heroku / Docker

🚀 快速部署 (Render + Supabase)

本專案設計為可直接部署於 Render (Web Service)。

步驟 1：準備環境變數

在部署前，你需要準備以下三個變數：

LINE_CHANNEL_ACCESS_TOKEN: 從 LINE Developers Console 取得。

LINE_CHANNEL_SECRET: 從 LINE Developers Console 取得。

DATABASE_URL: PostgreSQL 的連線字串 (例如 Supabase 提供的 URI)。

步驟 2：部署到 Render

Fork 此專案到你的 GitHub。

在 Render 新增一個 Web Service。

連結你的 GitHub Repository。

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

在 Environment Variables 填入步驟 1 的三個變數。

部署完成後，取得 Render 提供的 URL (例如 https://xxx.onrender.com)。

步驟 3：設定 Webhook

回到 LINE Developers Console。

在 Webhook URL 填入：https://你的Render網址/callback

開啟 Use webhook。

點擊 Verify 確認連線成功。

步驟 4：開始使用

將機器人加入好友或拉入群組，輸入 我是 [名字] 開始記帳！

💻 本地開發 (Local Development)

如果你想在本地端執行或修改程式碼：

複製專案

git clone [https://github.com/your-username/couple-accounting-bot.git](https://github.com/your-username/couple-accounting-bot.git)
cd couple-accounting-bot


安裝依賴
建議使用虛擬環境 (venv)：

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt


設定環境變數
新增 .env 檔案或直接在終端機設定：

export LINE_CHANNEL_ACCESS_TOKEN='你的Token'
export LINE_CHANNEL_SECRET='你的Secret'
export DATABASE_URL='你的資料庫連線字串'


啟動伺服器

python app.py


注意：本地開發需要使用 ngrok 等工具將 localhost 對外公開，才能接收 LINE Webhook。

📝 資料庫結構

程式啟動時會自動檢查並建立以下 Table，無需手動執行 SQL。

users: 儲存 User ID 與顯示名稱對照。

expenses: 儲存每一筆記帳資料 (含日期、項目、金額)。

📄 License

MIT License
