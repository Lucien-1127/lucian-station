# RAG 資料清洗標準

## 每筆記錄必填欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| category | 主題分類 | line-bot / n8n / rag / prompt / legal / agent / gcp-certification |
| source_tier | 來源可信度 | 1=官方/一手數據, 2=專家分析, 3=業界評論, 4=社群/anecdotal |
| verified_income | 收入是否可驗證 | true / false |
| source_type | 收集方式 | agent_collected（子代理） / direct_search（自行搜尋） |
| effective_date | 資料時效標記 | 2026-06-27 |

## 去重原則
- 相同主題只保留最新/最完整的版本
- 每季重新審視時效性標記

## 來源分級（source_tier）

| Tier | 說明 | 範例來源 |
|:----:|------|---------|
| 1 | 官方/一手平台數據 | GitHub stars, 平台官方定價, 政府開放資料 |
| 2 | 專家分析/實證報告 | 技術部落格（有數據支撐）、真實收入案例 |
| 3 | 業界評論 | 比較文章、個人經驗分享 |
| 4 | 社群/anecdotal | Reddit/PTT、未驗證的收入宣稱 |

## 寫入目標
~/.hermes/rag/ai_learning/ai_learning.db（SQLite FTS5）
查詢用：python3 ~/.hermes/rag/ai_learning/search.py "關鍵字"
