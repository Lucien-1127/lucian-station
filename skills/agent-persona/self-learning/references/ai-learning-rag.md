# AI Learning RAG — 查詢與維護

深度研究的知識庫，累積市場數據、技術方案、產品化方向。

## 位置
~/.hermes/rag/ai_learning/ai_learning.db

## 查詢
```bash
python3 ~/.hermes/rag/ai_learning/search.py "關鍵字"
python3 ~/.hermes/rag/ai_learning/search.py --stats   # 統計
python3 ~/.hermes/rag/ai_learning/search.py --list    # 分類
```

## 寫入新資料
研究結果清洗後寫入 DB，每筆記錄含：
- category：主題分類（line-bot / n8n / rag / prompt / legal / agent）
- source_tier：1=官方一手 / 2=專家分析 / 3=業界評論 / 4=社群
- verified_income：true/false
- source_type：agent_collected（子代理）或 direct_search（自行搜尋）
- effective_date：資料時效

## 現有資料（~15 筆）
- gcp-certification：GCP 免費認證訓練
- ai-prompt：DAIR.AI 76k⭐ / Awesome Prompt 6.1k⭐
- ai-agents：Awesome Agent / Free Resources / Microsoft 68k⭐ / GenAI Agents 22.9k⭐
- ai-rag：Awesome-RAG / Awesome GenAI Guide 28k⭐
- template-market：n8n / Make.com / 多代理定價數據
- scraping-targets：接案平台爬蟲評估
