# Telegram Bot Setup for Hermes Data Pipeline

## 完整設定步驟（以 @xiaoyu_agent_bot 為例）

### Step 1: 建立 Bot
1. 搜尋 Telegram 上的 **@BotFather**
2. 發送 `/newbot`
3. 輸入 Bot 名稱（例：`🦐代理 | 蝦蝦`）
4. 輸入使用者名稱（例：`xiaoyu_agent_bot`）
5. 取得 API Token（格式：`7896384336:AAEQ97joqLb0JrnAKRfjNpXQEKqc5PBUSaw`）

### Step 2: 取得個人 User ID
1. 搜尋 **@userinfobot**
2. 發送 `/start`
3. 回傳格式：
```
Id: 8236290134
First: 六
Last: 六
Lang: zh-hant
```
4. **記住**：此數字是個人 ID，不是 Bot Token 前面的數字

### Step 3: 寫入 .env
```bash
TELEGRAM_BOT_TOKEN=7896384336:AAEQ97***Saw
TELEGRAM_ALLOWED_USERS=8236290134
TELEGRAM_HOME_CHANNEL=8236290134
TELEGRAM_HOME_CHANNEL_NAME=蝦蝦代理
```

### Step 4: 驗證
```bash
# 確認 Token 有效
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# 發送測試訊息
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=8236290134" \
  -d "text=🤖 蝦蝦代理已連線 ✅"
```

## 已知陷阱
| 問題 | 錯誤訊息 | 解法 |
|------|---------|------|
| Bot 傳給自己 | error 403: Forbidden: the bot can't send messages to the bot | 用 @userinfobot 拿真實 User ID |
| Token 無效 | error 401: Unauthorized | 重新從 @BotFather `/api` 取得 |
| chat_id 錯誤 | error 400: Bad Request: chat not found | 確認數字無空格，無負號 |

## 已驗證環境
- Hermes Agent v0.16.0
- 使用直接 curl 操作 Telegram Bot API (非 Hermes Gateway)
- .env 路徑：`~/.hermes/.env`
