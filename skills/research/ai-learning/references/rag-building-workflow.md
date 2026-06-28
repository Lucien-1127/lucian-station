# RAG 知識庫建置工作流程

## 適用場景
需要從網路資源（GitHub repo、文章、課程頁面）建立本地可搜尋的知識庫時。

## 標準步驟

### 1. 建立資料庫結構

```sql
-- SQLite + FTS5
CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subcategory TEXT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content TEXT NOT NULL,
    source_type TEXT DEFAULT 'github',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE resources_fts USING fts5(
    title, content, category, 
    content='resources', content_rowid='id'
);

-- 自動同步 FTS 的 trigger
CREATE TRIGGER resources_ai AFTER INSERT ON resources BEGIN
    INSERT INTO resources_fts(rowid, title, content, category)
    VALUES (new.id, new.title, new.content, new.category);
END;
```

### 2. 爬取內容

用 `web_extract(urls=[...])` 批次抓取頁面（一次最多 5 個 URL）。

### 3. 寫入資料庫

寫 Python 腳本將 `web_extract` 結果 INSERT 進 DB。每筆記錄：
- category: 分類（如 `ai-agents`、`gcp-certification`）
- subcategory: 子分類（如 `免費課程`、`認證大全`）
- title: 資源名稱（含 ⭐ 星數）
- url: 原始連結
- content: 摘要描述（<50000 字）
- source_type: 來源類型

### 4. 建立搜尋腳本

```python
def search(query, limit=10):
    terms = " OR ".join(f'"{w}"' for w in query.split())
    cursor = conn.execute("""
        SELECT r.id, r.category, r.title, r.url, 
               snippet(resources_fts, 1, '**', '**', '...', 50) as snippet
        FROM resources_fts 
        JOIN resources r ON r.id = resources_fts.rowid
        WHERE resources_fts MATCH ?
        ORDER BY rank LIMIT ?
    """, (terms, limit))
```

### 5. 掛載到技能

- 將搜尋指令加入技能的 SKILL.md
- 或在 `references/` 放使用說明
- 下次載入該技能時就知道有 RAG 可用

## 實作參考

本技能 (`ai-learning`) 的 RAG 即依此流程建立：
- DB: `~/.hermes/rag/ai_learning/ai_learning.db`
- 搜尋: `~/.hermes/rag/ai_learning/search.py`
- 爬取: `~/.hermes/rag/ai_learning/seed_data.py`
- 筆數: 13 筆（GCP 認證 5 + Prompt 2 + AI Agent 4 + RAG 2）
