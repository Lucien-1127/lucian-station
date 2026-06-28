---
name: legal-rag
description: 法條白話翻譯檢索系統，收錄四萬七千餘條，支援本地檢索，每日自動同步。
user-invocable: true
---

# 智研法律白話 RAG

## 架構

```
Google Sheets (Legal_DB_Full_Part1)
    ↓ curl export TSV (8 tabs)
    ↓ build_index.py → SQLite FTS5
    ↓
query_rag.py / rag.py ← zhiyan-legal 呼叫
```

## 檔案位置

| 路徑 | 說明 |
|------|------|
| `~/.hermes/rag/legal_translation/legal_rag.db` | SQLite FTS5 資料庫（41.8 MB） |
| `~/.hermes/rag/legal_translation/raw/*.tsv` | 原始 TSV export |
| `~/.hermes/rag/legal_translation/build_index.py` | 索引建構工具 |
| `~/.hermes/rag/legal_translation/query_rag.py` | Python API（可被程式 import） |
| `~/.hermes/rag/legal_translation/rag.py` | CLI 整合工具（zhiyan-legal 直接 call） |

## 用法

### CLI 查詢

```bash
python3 ~/.hermes/rag/legal_translation/rag.py "公然侮辱"
python3 ~/.hermes/rag/legal_translation/rag.py "強制執行 查封" --category 民法 --top-k 5
python3 ~/.hermes/rag/legal_translation/rag.py "離婚 贍養費" --json
```

### 從 Python import

```python
import sys
sys.path.insert(0, os.path.expanduser("~/.hermes/rag/legal_translation"))
from query_rag import search, format_citation

result = search("公然侮辱", top_k=5, category="刑法")
for i, r in enumerate(result["results"], 1):
    print(format_citation(r, i))
```

### 輸出格式（Citation v2.0 相容）

結果以 `[T1]`, `[T2]`… 格式標記，與 zhiyan-legal 引用政策整合。

## Google Sheets 對應

| 分頁 | GID |
|------|:---:|
| 憲法 | 1413326165 |
| 民法 | 1711771356 |
| 刑法 | 987305053 |
| 行政法 | 1701242106 |
| 商事法 | 697621982 |
| 勞動社會法 | 1177369378 |
| 小法及其他 | 1214602671 |
| 術語庫 | 2099190532 |

## 重建索引

### 自動（推薦）
每天凌晨 3:00 自動 sync（cronjob id: `7d893df2b826`），不需手動操作。

### 手動
```bash
bash ~/.hermes/scripts/sync_rag.sh
```

### 📖 引用格式（與 zhiyan-legal Citation v2.1 整合）

RAG 結果以 `[T1]`, `[T2]`… 標記，與聯網引用 `[1]`, `[2]`… 區分：

```
[T1] 中華民國刑法 第 309 條 — 白話摘要：如果有人公開侮辱別人…
```

引用優先序：有白話摘要的 RAG 結果 [T1] ＞ 聯網官方條文 [1] ＞ 判決書 [2]

---

## 💡 技術核心：零套件依賴 RAG 模式

本系統不使用 chromadb / sentence-transformers / faiss 等外部 ML 套件，完全依賴 Python stdlib + SQLite FTS5。此模式適用於任何**結構化文本**的本地檢索場景。

核心元件：
- **SQLite FTS5** — 全文檢索，支援多詞 AND 查詢、rank 排序
- **Tag 倒排索引表** — `(tag, law_id)` 精準過濾
- **LIKE 模糊備援** — FTS5 無結果時 fallback

詳見 `references/sqlite-fts5-rag.md`。

## ⚠️ 已知邊界案例

各分頁欄位結構有差異（憲法 header 不同、民法多 Debug_Log 欄、術語庫 3 欄），建構時已處理。
詳見 `references/build-edge-cases.md`。

各法域白話摘要覆蓋率不同（小法及其他僅約 30% 有摘要），詳見 `references/summary-coverage.md`。

## 📂 參考文件

- `references/build-edge-cases.md` — 各分頁欄位差異、白話摘要覆蓋率、GID 對照表
- `references/stdlib-rag-pattern.md` — Zero-dependency RAG 架構決策框架（SQLite FTS5 vs embedding RAG）

## 搜尋策略（三層遞進）

1. **FTS5 全文檢索** — 最佳召回，支援多詞 AND 查詢
2. **LIKE 模糊搜尋** — FTS5 無結果時 fallback
3. **Tag 精準比對** — 透過 tag_index 表做關鍵字過濾

排序加權：白話摘要 ×3 > 條文內容 ×2 > 關鍵字 ×1.5 > 實務爭點 ×1.0
