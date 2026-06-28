---
name: research-tools
description: 研究工具集 — 論文搜尋、RSS 監控、知識庫、預測市場查詢
version: 1.0.0
author: Lucian
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [python3, curl]
  pip:
    - arxiv
    - blogwatcher-cli
    - py-cf2025
---

# 研究工具集

合併自：arxiv、blogwatcher、llm-wiki、polymarket

---

## 1. arXiv 論文搜尋

透過關鍵字、作者、分類或 ID 搜尋 arXiv 論文。

```bash
# 安裝工具
pip install arxiv

# 關鍵字搜尋
python3 -c "
import arxiv
search = arxiv.Search(query='transformer attention', max_results=5)
for r in search.results():
    print(f'{r.title}')
    print(f'  作者: {\", \".join(a.name for a in r.authors)}')
    print(f'  日期: {r.published}')
    print(f'  連結: {r.entry_id}')
"

# 作者搜尋
python3 -c "
import arxiv
search = arxiv.Search(query='au:karpathy', max_results=5)
for r in search.results():
    print(f'{r.title} ({r.published.strftime(\"%Y-%m\")})')
"
```

## 2. 部落格／RSS 監控

透過 blogwatcher-cli 監控部落格與 RSS/Atom feed。

```bash
# 安裝
pip install blogwatcher-cli

# 監控一個 feed
blogwatcher add https://example.com/rss

# 列出所有 feed
blogwatcher list

# 檢查新文章
blogwatcher check

# 設定 cron 定期檢查（每小時）
echo "0 * * * * cd ~ && blogwatcher check --notify" | crontab -
```

## 3. LLM Wiki 知識庫

Karpathy 風格的 LLM 知識庫 — 建立／查詢相互連結的 Markdown 筆記。

```bash
# 初始化知識庫
mkdir -p ~/llm-wiki
cd ~/llm-wiki

# 建立一篇筆記
cat > attention.md << 'EOF'
# Attention Mechanism

## 核心概念
Attention 讓模型在產生輸出時「專注於」輸入的特定部分。

## 關聯
- [[transformer]]
- [[self-attention]]
- [[multi-head-attention]]

## 論文
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
EOF

# 全文搜尋
grep -r "attention" ~/llm-wiki/ --include="*.md" -l

# 使用 ripgrep 搜尋（更快）
rg "transformer" ~/llm-wiki/
```

## 4. Polymarket 預測市場

查詢 Polymarket 市場、價格、訂單簿與歷史資料。

```bash
# 安裝工具
pip install py-cf2025

# 查詢市場
python3 -c "
from polymarket import CategoricalMarket
market = CategoricalMarket('0x1234...')
print(f'問題: {market.question}')
print(f'機率: {market.outcome_prices}')
"

# 查詢訂單簿
python3 -c "
from polymarket import CategoricalMarket
market = CategoricalMarket('0x1234...')
bids, asks = market.get_order_book()
print(f'買單: {len(bids)}, 賣單: {len(asks)}')
"

# 或使用 curl + API
curl -s 'https://clob.polymarket.com/markets?limit=5' | python3 -m json.tool
```

## 5. 免費 API 模型探索

查詢 OpenRouter 免費模型清單、評估本機 vs API 取捨、探索新模型。

詳見 `references/free-api-model-discovery.md`。
