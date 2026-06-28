# AI Learning RAG 使用說明

## 資料庫位置
~/.hermes/rag/ai_learning/ai_learning.db

## 搜尋工具
~/.hermes/rag/ai_learning/search.py

## 用法
```bash
# 搜尋關鍵字
python3 ~/.hermes/rag/ai_learning/search.py "prompt engineering free course"

# 查看統計
python3 ~/.hermes/rag/ai_learning/search.py --stats

# 列出分類
python3 ~/.hermes/rag/ai_learning/search.py --list
```

## 現有資料（26 筆）
- gcp-certification: 5 筆（ACE/CDL/PCA/4-words/主頁）
- ai-prompt: 2 筆（DAIR.AI 51k⭐ / Awesome 6.1k⭐）
- ai-agents: 4 筆（Awesome Agent / Free Resources / Microsoft / GenAI Agents）
- ai-rag: 2 筆（Awesome-RAG / Awesome GenAI Guide）
- agent-workflow-templates: 13 筆（n8n模板市場/定價/平台比較/Multi-Agent成本/AI代理變現）

## 爬取新資源
用 web_extract 抓到內容後，寫 Python 腳本 insert 進 DB。
