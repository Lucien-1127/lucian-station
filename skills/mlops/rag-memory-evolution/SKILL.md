---
name: rag-memory-evolution
description: 建構 SQLite 結構化記憶與 ChromaDB 語義檢索的 RAG 閉環。
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [RAG, Persistence, SQLite, ChromaDB, Memory]
---

# 記憶演進 RAG 系統

本技能實現分層記憶架構，利用 SQLite 儲存結構化互動資料，ChromaDB 處理向量語義檢索，實現可持續演進的 RAG 系統。

## 當使用時
- 需要解決 AI 回應前後矛盾或「失憶」問題。
- 需要結合用戶偏好、會話歷史與語義內容進行精準檢索。
- 需要追蹤檢索績效以便持續優化。

## 必要條件
- 安裝套件：`pip install sqlite3 chromadb sentence-transformers`
- 具備基本的 Python 環境。

## 如何執行
透過 `execute_code` 呼叫資料處理函數：
1. **初始化**：設定 `rag_memory.db` (SQLite) 與 `./chroma_db` (Chroma)。
2. **檢索**：呼叫 `smart_retrieve(query, session_id)` 進行多路徑合併檢索。
3. **優化**：利用檢索日誌 (`retrieval_logs`) 進行重排序權重調整。

## 關鍵流程
1. **智慧檢索**：將用戶查詢與近期對話歷史融合為「增強型查詢」。
2. **多路徑檢索**：從文件庫 (`doc_collection`) 與高品質問答記憶庫 (`qa_memory_collection`) 同時檢索。
3. **提示詞合成**：將檢索到的資料與偏好動態組裝成最終 Prompt。

## 實務提示 (Pitfalls)
- **歷史窗口限制**：過長的歷史會增加雜訊，建議限制檢索最近 3-5 輪對話。
- **置信度門檻**：設定顯式的 `confidence_threshold` (例如 0.5)，低於此分數時應讓模型回覆「缺乏資訊」而非編造。
- **資料庫鎖定**：大檔案 SQLite 操作時應考慮分卷儲存，避免雲端同步鎖定衝突。
## 實務經驗更新 (2026-06-28)
- 檔案路徑與權限陷阱：Python 腳本中的 `open()` 和 `sqlite3.connect()` 必須使用 `os.path.expanduser()` 配合絕對路徑 (`~/law-rag/...`)，避免相對路徑在不同調度上下文導致的 `FileNotFoundError` 或多個資料庫實例衝突。
- Pipeline 閉環除錯：自動化 Pipeline 執行前必須先驗證模組路徑，若背景程序退出 (exit code 2)，應立即使用 `cat <log>` 診斷，而非反覆重試。
- 專屬金鑰分流：針對 Legal Writer 與 Research Agent，應在 `config.yaml` 中配置 `agents_config`，並在 Python 腳本中顯式指定對應金鑰，以達成資源隔離。
