---
name: sqlite-chroma-rag
description: 建立具備 SQLite 結構化記憶與 ChromaDB 向量檢索的 RAG 系統。
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [RAG, SQLite, ChromaDB, MLOps, Vector-Search]
---

# SQLite + ChromaDB 持久化 RAG 實作指南

本指南旨在提供一套可複製、模組化的 Python 實作，建構具備「記憶」的 RAG 系統。

## 三階段實作架構

1.  **初始化資料庫層**：建立 SQLite (結構化記憶) 與 ChromaDB (向量儲存)。
2.  **智慧檢索核心**：實作融合歷史記憶與多路徑檢索的 `smart_retrieve` 邏輯。
3.  **提示詞合成層**：結合檢索上下文與動態置信度調整的 `build_prompt`。

## 初始化腳本 (`scripts/init_memory.py`)

```python
import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

# 1. 初始化 SQLite (結構化記憶)
conn = sqlite3.connect('rag_memory.db')
conn.execute('PRAGMA foreign_keys = ON')
conn.execute('''CREATE TABLE IF NOT EXISTS retrieval_logs 
                (id INTEGER PRIMARY KEY, session_id TEXT, query TEXT, latency_ms INTEGER, timestamp DATETIME)''')

# 2. 初始化 ChromaDB (向量儲存)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
doc_collection = chroma_client.get_or_create_collection(name="documents")
qa_collection = chroma_client.get_or_create_collection(name="qa_memory")

# 3. 初始化嵌入模型
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
```

## 智慧檢索核心 (`scripts/smart_retrieve.py`)

實現融合歷史記憶與多路徑檢索的邏輯：

```python
def smart_retrieve(user_query, session_id):
    # 步驟1：載入歷史記憶 (SQLite)
    # 步驟2：建構增強查詢
    # 步驟3：ChromaDB 多路徑檢索 (doc + qa)
    # 步驟4：加權重排序與記錄 Log
    ...
```

## 提示詞合成策略 (`scripts/build_prompt.py`)

動態調整提示詞模板，並根據檢索分數判斷置信度，實現 `Low Confidence` 降級：

```python
confidence_instruction = "若資訊不足請告知，勿編造。" if avg_score < 0.5 else ""
prompt = prompt_template.format(history=history, context=context, confidence_instruction=confidence_instruction)
```

## 閉環優化路線圖

| 維度 | 優化建議 |
| :--- | :--- |
| **嵌入模型** | 準確度優先時，升級至 `e5-mistral-7b` 或呼叫 OpenAI API。 |
| **檢索策略** | 透過 `retrieval_logs` 數據進行 A/B 測試。 |
| **自動化** | 將高評分 (rating=1) 問答自動寫入 `qa_memory_collection`。 |

## 實作建議
- 使用 **Canvas 白板** 視覺化 SQLite 表結構與 ChromaDB 集合關係。
- 透過 **Kanban 看板** 管理 `RAG 優化` 任務（待測試/進行中/已驗證）。
- 嚴格遵守 **「研究先於輸出」** 原則，並透過 `retrieval_logs` 進行品質回溯。
