---
name: firecrawl-research
description: "Firecrawl Research Index — 論文搜尋、內文檢索、相關論文擴展、GitHub 實作搜尋"
version: 1.0.0
author: hermes
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Papers, arXiv, Firecrawl, API]
    homepage: https://docs.firecrawl.dev/features/research
prerequisites:
  commands: [curl]
---

# Firecrawl Research Index

Firecrawl 推出的專用論文索引，涵蓋 3M+ arXiv 論文 + GitHub 研究倉庫。
免 API Key 即可基本使用，加 `Authorization` header 可提高 rate limit。

Base URL: `https://api.firecrawl.dev/v2/search/research`

## 常用端點一覽

| 功能 | 端點 |
|------|------|
| 搜尋論文 | `GET /papers?query=...&k=20` |
| 查論文詳情 | `GET /papers/{id}` |
| 讀論文內文段落 | `GET /papers/{id}?query=...&k=4` |
| 找相關論文 | `GET /papers/{id}/similar?intent=...&mode=similar&k=20` |
| 搜尋 GitHub | `GET /github?query=...&k=10` |

## 論文 ID 格式

- arXiv: `arxiv:1706.03762`
- Semantic Scholar: `sem:...`
- DOI: `doi:10.xxxx/...`

## 使用範例

### 1. 搜尋論文（語意搜尋）

```bash
curl -s "https://api.firecrawl.dev/v2/search/research/papers?query=RAG%20knowledge%20graph%20enhanced&k=10"
```

**篩選參數：**
- `authors` — 作者子字串
- `categories` — arXiv 分類，如 `cs.LG`
- `from` / `to` — 日期範圍（YYYY-MM-DD）

### 2. 查論文詳情

```bash
curl -s "https://api.firecrawl.dev/v2/search/research/papers/arxiv:1706.03762"
```

### 3. 讀論文內文（驗證特定問題）

```bash
curl -s "https://api.firecrawl.dev/v2/search/research/papers/arxiv:1706.03762?query=what%20is%20the%20attention%20mechanism&k=4"
```

### 4. 找相關論文

三種模式：
- `similar` — co-citation / bibliographic coupling（相似論文）
- `citers` — 引用此論文的論文
- `references` — 此論文引用的論文

```bash
# 相似論文 + 指定意圖
curl -s "https://api.firecrawl.dev/v2/search/research/papers/arxiv:2306.15595/similar?intent=efficient%20transformer%20variants&mode=similar&k=20"

# 引用此論文的人
curl -s "https://api.firecrawl.dev/v2/search/research/papers/arxiv:2306.15595/similar?intent=follow-up%20work&mode=citers&k=20"
```

### 5. 搜尋 GitHub（實作討論）

搜尋 issues、PRs、READMEs 中的實作細節：

```bash
curl -s "https://api.firecrawl.dev/v2/search/research/github?query=flash%20attention%20implementation%20pitfalls&k=10"
```

### 6. 加入 API Key 提高限額

所有端點都支援加 header：

```bash
curl -s -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  "https://api.firecrawl.dev/v2/search/research/papers?query=diffusion%20models&k=20"
```

## 研究流程（Recommended Pattern）

### 快速查找某篇論文
```
1. search_papers → 找到 paperId
2. inspect_paper → 看 metadata（摘要、作者）
3. read_paper → 如果 needed，驗證內文細節
```

### 從一篇好論文擴展研究
```
1. search_papers → 找到 seed paper
2. related_papers(mode=similar) → 找相似論文
3. related_papers(mode=citers) → 看誰引用/延伸
4. 對 candidate papers 用 read_paper 驗證
5. 需要實作細節 → search_github
```

### 綜述某個領域
```
1. search_papers (query=領域關鍵字, k=20)
2. 取 top 3-5 篇當 seed
3. 各做 related_papers(mode=similar)
4. 合併去重
5. 對 candidate 做 read_paper 驗證
```

## Pitfalls

- **Rate limit**：免費使用有 rate limit，大量查詢建議加 API Key
- **非 arXiv 論文**：不涵蓋國內期刊、法學論文、IEEE 非 arXiv 論文
- **read_paper 只返回段落**：不返回全文，適合驗證特定問題（method used, score, affiliation）
- **搜尋是 abstract-level**：search_papers 只搜摘要，不是全文搜尋
- **GitHub 搜尋範圍**：只涵蓋研究相關倉庫，不是全部 GitHub

## 替代方案

| 工具 | 適用場景 |
|------|---------|
| Firecrawl Research | 論文語意搜尋 + 內文驗證 + GitHub 實作 |
| Semantic Scholar API | 更大範圍的學術論文（但不含 GitHub） |
| Google Scholar | 手動瀏覽引用網絡（無 API） |
| law.moj.gov.tw | 法學條文查詢（zhiyan-legal 使用） |
