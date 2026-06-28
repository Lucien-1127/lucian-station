# Gemini + Groq 設定實錄 v2（2026-06-26，修正版）

## ⚠️ 修正重點

初次設定時犯了兩個嚴重錯誤：
1. Groq 模型名稱猜測錯誤（`llama-4-scout` → 正確是 `meta-llama/llama-4-scout-17b-16e-instruct`）
2. **Groq 不是 Hermes 直接支援的 provider** — 必須走 OpenRouter
3. `.env` 寫入 Key 被安全遮罩攔截寫入假值

## 正確設定的完整流程

### 1. 先驗證模型名稱（不可跳過）

```bash
# Gemini 可用模型
curl "https://generativelanguage.googleapis.com/v1beta/models?key=<GEMINI_KEY>"

# Groq 可用模型（注意棄用日期）
curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer <GROQ_KEY>"
```

Gemini 當前（2026-06-26）免費可用模型：
- `gemini-2.5-flash`、`gemini-2.5-flash-lite`
- `gemini-2.0-flash`（舊版）
- `gemini-3-pro-preview`、`gemini-3.1-pro-preview`（預覽）
- `gemini-flash-latest`（alias）

Groq 當前可用模型（注意棄用日期）：
| ID | 狀態 |
|----|------|
| `meta-llama/llama-4-scout-17b-16e-instruct` | ⚠️ 2026-07-17 棄用 |
| `qwen/qwen3-32b` | ⚠️ 2026-07-17 棄用 |
| `openai/gpt-oss-120b` | ✅ 推薦替換 |
| `openai/gpt-oss-20b` | ✅ |
| `llama-3.3-70b-versatile` | ⚠️ 2026-08-16 棄用 |
| `llama-3.1-8b-instant` | ⚠️ 2026-08-16 棄用 |

### 2. 設定金鑰（不要在 .env 直接用 bash echo）

```bash
# Gemini — 寫入 config.yaml，不是 .env
hermes config set providers.gemini.api_key "AQ.Ab8RN6..."

# Groq — .env 用於 STT，不是 model provider
# OpenRouter 則已有自己的 key
hermes config set providers.groq.api_key "gsk_9l..."

# DeepSeek — .env 是正規路徑（DEEPSEEK_API_KEY）
```

⚠️ `.env` 寫入陷阱：`echo "GEMINI_API_KEY=***/>> ~/.hermes/.env` 可能被安全遮罩攔截，實際寫入的是遮罩字串（如 `***KEY}`）。改用 `hermes config set` 寫入 config.yaml 最安全。

### 3. 設定降級鏈

Groq 必須透過 OpenRouter：

```bash
hermes config set fallback_providers.0.provider gemini
hermes config set fallback_providers.0.model gemini-2.5-flash
hermes config set fallback_providers.1.provider openrouter
hermes config set fallback_providers.1.model "meta-llama/llama-4-scout-17b-16e-instruct"
hermes config set fallback_providers.2.provider openrouter
hermes config set fallback_providers.2.model "qwen/qwen3-32b:free"
```

### 4. 設定輔助任務

```bash
hermes config set auxiliary.vision.provider gemini
hermes config set auxiliary.vision.model gemini-2.5-flash
hermes config set auxiliary.compression.provider gemini
hermes config set auxiliary.compression.model gemini-2.5-flash
hermes config set auxiliary.title.provider gemini
hermes config set auxiliary.title.model gemini-2.5-flash
```

### 5. 設定 Credential Pool（多 Key 輪流）

單一 Gemini Key 配額有限，多個免費 Key 可加入池中輪流：

```bash
# 添加第二個 Key
hermes auth add --type api-key --api-key "AQ.Ab8RN6..." --label "gemini-key-2" gemini

# 查看池
hermes auth list gemini
# 輸出: gemini (2 credentials):
#   #1  GEMINI_API_KEY       api_key env:GEMINI_API_KEY ←
#   #2  gemini-key-2         api_key manual

# 移除損壞的 env 條目
hermes auth remove gemini 1
```

池行為：當一個 Key 回 429（額度耗盡），Hermes 自動標記 `exhausted` 並切換下一個。

## 驗證結果（2026-06-26）

| API | 狀態 | 備註 |
|-----|:----:|------|
| DeepSeek V4 Pro | ✅ 200 | 主力 |
| Gemini 2.5 Flash（新 Key） | ✅ 200 | 免費，輔助任務用 |
| Gemini 2.5 Flash（舊 Key） | ❌ 429 | 預付額度耗盡，需加值 |
| Groq Llama 4 Scout（經 OpenRouter） | ✅ | 免費 fallback |
| Groq Qwen3 32B（經 OpenRouter） | ✅ | 免費 fallback |
