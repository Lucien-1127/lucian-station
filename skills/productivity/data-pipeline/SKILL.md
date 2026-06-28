---
name: data-pipeline
description: 每日數據管線：爬蟲 → 分析 → Telegram 推播（Tasker + 小任務）。支援 --daily / --briefing / --weekly / --stats 四種模式
version: 1.1.0
author: Lucian
status: ACTIVE
trigger: "建立每日爬蟲、數據管線、定時推播 Telegram，或需要 LLM 生成市場週報/快訊的自動化工作"
---

# Data Pipeline Skill v1.0

## 用途
自動化台灣接案市場數據管線：多平台爬取 → SQLite 去重 → 統計分析 → LLM 摘要 → Telegram 定時推播。

## 實際架構

```
爬蟲層 (requests + BS4)
  ├─ Tasker出任務 → 完整案件詳情（標題、預算、連結、提案人數）
  └─ 小任務     → 列表資料（標題、日期、分類、標籤）
        ↓
去重層 (SQLite fingerprint)
  ├─ 30天後自動清理
  └─ 標記 AI 分類（is_ai, ai_category）
        ↓
輸出模式 (--briefing / --weekly / --daily / --stats)
  ├─ 每日快訊 (LLM) → Telegram 優化格式
  ├─ 每週週報 (LLM) → 5 章節完整市場分析
  ├─ 每日推播      → 新案件列表
  └─ 統計 JSON     → 供其他程式使用
        ↓
推播層 (Telegram Bot API → 群組/個人)
```

## 腳本位置

```
~/.hermes/scripts/tw_freelance_crawler.py
```

## 四種執行模式

### --daily（預設）
爬新案 → 推播 TG
```bash
~/.hermes/scripts/tw_freelance_crawler.py
~/.hermes/scripts/tw_freelance_crawler.py --pages 5  # 爬 5 頁
```

### --briefing（每日快訊）
LLM 生成每日 AI 接案快訊，TG 優化格式
```bash
~/.hermes/scripts/tw_freelance_crawler.py --briefing
~/.hermes/scripts/tw_freelance_crawler.py --briefing --days 7 --no-tg
```

### --weekly（每週週報）
LLM 生成完整市場週報（5 大章節）
```bash
~/.hermes/scripts/tw_freelance_crawler.py --weekly --days 7
~/.hermes/scripts/tw_freelance_crawler.py --weekly --days 30  # 月報
```

### --stats（統計 JSON）
```bash
~/.hermes/scripts/tw_freelance_crawler.py --stats --days 7
```

## 平台細節

| 平台 | 方式 | 內容 | 限制 |
|------|------|------|------|
| Tasker出任務 | requests + BS4 | 標題、預算、地點、提案數、連結、標籤 | 每頁 20 案 |
| 小任務 | requests + BS4 | 標題、日期、分類、標籤 | 無個案連結（SPA）|

## 每日快訊格式（--briefing）

```
━━━━━━━━━━━━━
🎯 今日 AI 接案快訊
📆 {日期} · 第{週數}週 · {星期}
━━━━━━━━━━━━━

🔥 熱門案件 Top 5

1️⃣ {標題}
💰 NT${金額} · 🏢 {平台}
⏱ {工期} · 🏷 {技術標籤}
🔗 {連結}

━━━━━━━━━━━━━

📊 市場結構

🧩 案件類型
・{類型}:{百分比}

💰 預算分布
・低預算 <1 萬:{n} 筆
・中預算 1-5 萬:{n} 筆
・高預算 5-10 萬:{n} 筆
・企業級 >10 萬:{n} 筆

📈 市場熱度
今日約 {n} 筆 · vs 本週平均 {熱絡/持平/冷清}

━━━━━━━━━━━━━

🔑 今日熱門關鍵詞

1. {關鍵詞}({n}筆)

━━━━━━━━━━━━━

✨ 新興需求

🆕 {趨勢}
📝 {說明}

━━━━━━━━━━━━━

💡 重點推案

🎯 {案件}
💬 {分析}
🔗 {連結}

━━━━━━━━━━━━━

📌 明日觀察
・{一句觀察}

━━━━━━━━━━━━━
```

### 快訊硬規則
- 預算統一用 NT$，美元以當前匯率換算並標註 (原 $X)
- 禁用 Markdown 表格、程式碼區塊、深度縮排
- emoji 限視覺區隔用途，每段 1-3 個
- 連結必須真實可點擊，查不到寫「資料不足」
- 投案分析用客觀第三人稱
- 引用來源附在最後

## 每週週報格式（--weekly）

```
📊 **AI 接案市場週報**

1. 本週 AI 接案市場概況
   - 案件總數（與上週比較）
   - 主要來源平台
   - 案件類型分布

2. 熱門 AI 應用需求排名（Top 5）

3. 預算水平分析
   - 低/中/高案件分布
   - 最高預算案件類型

4. 新興趨勢與機會
   - 新出現的 AI 應用方向
   - 值得關注的市場信號

5. 本週推薦關注案件（3 件）
   - 案件標題、平台、值得關注的理由
```

## Telegram 推送設定

### .env 必要變數
```
TELEGRAM_BOT_TOKEN=7896384336:ABCdef...   # 從 @BotFather
TELEGRAM_HOME_CHANNEL=8236290134           # 個人或群組 chat_id
# 群組 chat_id 需加 -100 前綴（如 -1003711803841）
```

### ⚠️ 常見陷阱
- **Bot ID ≠ 使用者 ID** — Token 前半段是 Bot 的 ID，不能當 chat_id
- **群組 ID 需加 -100** — 如 `-1003711803841`，由 @getidsbot 取得
- **Bot 需先加入群組** — 否則回傳 "chat not found"
- **.env 不會自動 export** — 腳本需要自行讀取（內建 fallback loader）

## Cron 排程範例

### 每日快訊（agent 模式 — 含 web_search 跨平台搜尋）
```bash
cronjob action=create \
  name="每日快訊" \
  schedule="0 0 * * *" \            # TW 08:00 = UTC 00:00
  enabled_toolsets="web,terminal,file" \
  prompt="先跑 crawler --briefing --no-tg，再用 web_search 補 Upwork/Fiverr..."
```

### 每週週報（no_agent 模式 — 零 token 成本）
```bash
# 包裝腳本（因為需要傳参）
cat ~/.hermes/scripts/weekly_report.sh
#!/bin/bash
source ~/.hermes/scripts/.venv/bin/activate
exec ~/.hermes/scripts/tw_freelance_crawler.py --weekly --days 7

cronjob action=create \
  name="週報" \
  schedule="0 0 * * 0" \            # 週日 TW 08:00
  script="weekly_report.sh" \
  no_agent=true
```

## 參考文件
- `references/taiwan-job-platforms.md` — 台灣接案平台爬取分析
- `references/daily-briefing-format.md` — 每日快訊格式規範（完整版）
- `references/weekly-report-format.md` — 每週週報格式規範（完整版）
- `references/telegram-setup.md` — Telegram Bot 設定
- `references/tw-ai-pricing-research-2026.md` — 台灣 AI 接案市場行情參考（2026年6月）：5 級價格帶、6 種進階專案類型、實際案件分布、接案月收入潛力

## 禁止事項
- ❌ 爬蟲頻率過高（間隔 >2s）
- ❌ 使用 Bot Token 前段數字當 User ID
- ❌ 編造連結或預算數據（寫「資料不足」）
- ❌ LLM 週報/快訊使用 Markdown 表格或縮排
- ❌ 假設 Hermes Gateway 已啟動 — 優先走 Bot API 直推