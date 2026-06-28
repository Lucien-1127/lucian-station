# Credential Pool（憑證輪流池）操作手冊

## 概念

多個同廠商 API Key 可加入池中，Hermes 自動輪流使用。當一個 Key 回 429（額度耗盡）或標記 `exhausted`，自動切換下一個。

池資料存於 `~/.hermes/auth.json` 的 `credential_pool` 區塊（格式為 JSON）。

## 基本指令

```bash
# 添加 API Key 到 pool
hermes auth add --type api-key --api-key "<KEY>" --label "<自訂標籤>" <provider>

# 查看 pool 狀態
hermes auth list <provider>
# ← 標記目前使用的條目

# 查看詳細狀態
hermes auth status <provider>

# 移除條目（索引從 1 開始）
hermes auth remove <provider> <索引>

# 清除所有 exhausted 狀態（Key 加值後恢復）
hermes auth reset <provider>
```

## 池條目類型

| 來源標記 | 說明 | access_token 來源 |
|---------|------|-------------------|
| `env:GEMINI_API_KEY` | 從環境變數自動讀取 | 執行時讀取 env var |
| `manual` | 手動添加 | 儲存在 auth.json |
| `device_code` | OAuth 流程產生 | 儲存在 auth.json |

## 常見操作流程

### 場景 1：初次新增備援 Key

```bash
# 已有 env 金鑰在 pool #1，新增手動金鑰到 #2
hermes auth add --type api-key --api-key "AQ.Ab8RN6..." --label "gemini-backup" gemini
hermes auth list gemini
```

### 場景 2：舊 Key 用完，自動切換

```
#1 GEMINI_API_KEY  api_key env:GEMINI_API_KEY    status=exhausted
#2 gemini-backup   api_key manual               status=ok ←
```

不需要手動介入 — 429 錯誤觸發後自動標記 exhausted 並切換。

### 場景 3：移除損壞的 env 條目

若 env 變數值是「被安全遮罩攔截寫入的假值」（如 `***KEY}`），池條目指向空字串：

```bash
# 移除假條目，Hermes 還阻斷它被重新播種
hermes auth remove gemini 1
# 輸出: Suppressed env:GEMINI_API_KEY — it will not be re-seeded
```

### 場景 4：舊 Key 加值後恢復

```bash
hermes auth reset gemini
# 清除所有 exhausted 標記，所有條目回到 ok
```

## 陷阱

| 問題 | 根因 | 解法 |
|------|------|------|
| env 條目的 access_token 是空字串 | `.env` 被安全遮罩寫入假值 | 移除損壞條目，改用手動添加 |
| 移除的 env 條目又自動出現 | Hermes 自動播種 env var | `hermes auth remove` 會輸出 `Suppressed: will not be re-seeded` |
| 池中有正確的 manual 條目但還是用 broken 的 env | 池的輪流順序（手動條目排前面） | 移除 env 條目 |
