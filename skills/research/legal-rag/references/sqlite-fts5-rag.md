# SQLite FTS5 零套件依賴 RAG 模式

> 適用場景：需要本地檢索但無法安裝 ML 套件（chromadb / sentence-transformers / faiss）時。
> 不適用：需要語義向量檢索（同義詞匹配、跨語言檢索）的場景。

## 核心架構

```
┌─────────────────────┐
│   原始資料 (CSV/     │
│   TSV/JSON/Sheets)   │
└─────────┬───────────┘
          ↓ parse
┌─────────────────────┐
│   SQLite 主表        │  ← 原始欄位 + metadata
│   (laws)             │
└─────────┬───────────┘
          ↓
┌─────────────────────┐  ┌─────────────────────┐
│   FTS5 全文索引       │  │   Tag 倒排索引       │
│   (laws_fts)         │  │   (tag_index)        │
│   tokenize='unicode61│  │   PK(tag, law_id)    │
│     remove_diacritics│  └─────────────────────┘
│     2'               │
└─────────┬───────────┘
          ↓
    三層搜尋策略
  FTS5 → LIKE → Tag
```

## Schema 範本

### 主表
```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    tags TEXT
);
```

### FTS5 全文索引
```sql
CREATE VIRTUAL TABLE items_fts USING fts5(
    title, content, summary, tags,
    content='items',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- 同步 FTS5 內容
INSERT INTO items_fts(items_fts) VALUES('rebuild');
```

- `unicode61` 支援 unicode 分詞，對中文基本夠用
- `remove_diacritics 2` 去除變音符號

### Tag 倒排索引
```sql
CREATE TABLE tag_index (
    tag TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    PRIMARY KEY (tag, item_id)
);
```

## 三層搜尋策略

### 第一層：FTS5 全文檢索（最佳召回）
```python
def _build_fts_query(query: str) -> str:
    clean = re.sub(r"[^\w\s]", " ", query)
    terms = [t for t in clean.split() if len(t) >= 2]
    return " AND ".join(terms[:8])

sql = """
    SELECT i.* FROM items_fts f
    JOIN items i ON f.rowid = i.id
    WHERE items_fts MATCH ?
    ORDER BY rank
    LIMIT ?
"""
```

### 第二層：LIKE 模糊搜尋（FTS5 無結果時 fallback）
```python
sql = """
    SELECT * FROM items
    WHERE LOWER(content) LIKE '%' || LOWER(?) || '%'
       OR LOWER(summary) LIKE '%' || LOWER(?) || '%'
    ORDER BY LENGTH(content) ASC
    LIMIT ?
"""
```

### 第三層：Tag 精確比對
```python
sql = """
    SELECT DISTINCT i.* FROM tag_index ti
    JOIN items i ON ti.item_id = i.id
    WHERE ti.tag LIKE ?
    LIMIT ?
"""
```

## 排序加權設計

不同欄位對相關性的貢獻不同，用 LIKE 命中次數加權：

| 欄位 | 權重 | 理由 |
|------|:----:|------|
| summary / 摘要 | ×3 | 濃縮核心資訊 |
| content / 內容 | ×2 | 原始資料 |
| tags | ×1.5 | 分類關鍵字 |
| issues / 備註 | ×1.0 | 輔助資訊 |

## 重點實作技巧

1. **天然 chunk**：結構化資料（法條、論文條目、產品規格）每一行就是一個 chunk，不用額外分割
2. **metadata 過濾**：用 `category` 欄位 + WHERE 子句做 domain filter，比 vector search 的 metadata filter 更直接
3. **去重**：三層搜尋結果合併時用 `existing_ids = {r["id"] for r in results}` 去重
4. **FTS5 query 失敗處理**：FTS5 MATCH 對特殊字元敏感，用 try/except 包住，失敗就跳 LIKE

## 與 Vector RAG 的比較

| 面向 | SQLite FTS5 | Vector RAG (chromadb) |
|------|:-----------:|:---------------------:|
| 依賴 | stdlib only | 需安裝 ML 套件 |
| DB 大小 | ~42MB / 47K docs | ~同量級 |
| 語義匹配 | ✗ 精確關鍵字 | ✓ 同義詞、近似概念 |
| 速度 | 極快（ms 級） | 中等（embedding + 搜索） |
| 中文支援 | unicode61 夠用 | embedding 較強 |
| 離線可用 | ✓ 完全離線 | ✓ 若 embedding 本機 |
| 更新 | 直接 SQL INSERT | 需 embedding 再 insert |

## 何時該升級到 Vector RAG

- 需要同義詞匹配（「車禍」→「交通事故」）
- 自然語言查詢偏離關鍵字很遠
- 需要跨語言檢索（中文查英文資料）
- 文本非結構化（長文段落、對話記錄）
