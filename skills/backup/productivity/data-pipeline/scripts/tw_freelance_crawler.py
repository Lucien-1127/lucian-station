#!/home/hsieh89t_gmail_com/.hermes/scripts/.venv/bin/python3
"""
台灣 AI 接案市場爬蟲 + 統計分析 + LLM 週報/快訊

Platforms:
  - Tasker出任務 (tasker.com.tw)  → 完整案件詳情
  - 小任務 (task.tw)              → 列表資料

Modes:
  --daily   爬新案 + 基本推播 (default)
  --briefing 每日快訊 (LLM生成 TG格式)
  --weekly   每週完整市場週報 (LLM生成)
  --stats    僅輸出統計 JSON

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_HOME_CHANNEL (from ~/.hermes/.env)
     OPENROUTER_API_KEY (for LLM report/briefing)
"""
# Full implementation at ~/.hermes/scripts/tw_freelance_crawler.py