# 多模型架構健康檢查 — 操作指南

## 適用場景

當使用者要求「健康檢查儲存庫」、「審查程式碼架構」、「找出技術債」時，使用多模型合議庭進行交叉審查。

## 前置步驟

### 1. 建立 Repo Profile

收集以下資訊後組合成一份結構化摘要：
- 目錄樹（排除 .venv/、__pycache__、node_modules/、site/）
- 各目錄總行數 (`find . -name "*.py" | xargs wc -l`)
- 關鍵檔案內容（__init__、router、runner、engine、config、pyproject.toml）
- 已知架構特徵（雙引擎、雙路由等）

### 2. 設計 4 角色審查 Lens

| 模型 | 視角 | 重點維度 |
|:----|:-----|:---------|
| DeepSeek V4 Flash | 結構完整性 | module 邊界、命名一致性、重複程式碼、設定管理 |
| Gemini 3.5 Flash | 文件一致性 | doc-code 對齊、導航斷鏈、命名規則、測試覆蓋 |
| Claude Sonnet 4 | 安全與錯誤 | 例外處理、資源洩漏、注入防護、測試缺口 |
| NVIDIA Nemotron Super 49B | 盲點偵測 | 隱含耦合、技術債、可維護性、擴展性 |

### 3. 平行呼叫 4 模型

使用 `asyncio.gather` 同時送出四份審查請求：
- 每個模型拿到相同的 Repo Profile
- 但各自有不同的 system prompt（不同審查 lens）
- temperature=0.2（一致性優先）
- max_tokens=4096

### 4. 彙整結果

統計嚴重度分布：
- 🔴 Critical：立即處理（系統性風險）
- 🟠 Major：優先改善（架構缺陷）
- 🔵 Minor：閒暇處理（維護性建議）

產出前 5 行動建議（依嚴重 × 影響 × 修復難度排序）。

## 模板：DeepSeek Lens

```
你是資深 Python 架構審查工程師。請對以下儲存庫進行「結構完整性審查」。
重點維度：
1. module 邊界是否清晰？命名是否一致？
2. import chain 是否合理？有無循環依賴？
3. 有無重複或冗餘模組？
4. 環境變數 vs 設定檔的使用是否一致？
5. pyproject.toml 依賴管理是否完善？
```

## 模板：NVIDIA Lens（盲點偵測）

```
你是一位架構盲點偵測專家。找出儲存庫中「大家都覺得正常但其實有問題」的架構瑕疵。
重點維度：
1. 隱含耦合：看似無關的模組之間存在隱含約定？
2. 技術債：為了快速迭代留下的「以後再修」？
3. 可維護性：新人上手需要多久？
4. 水平擴展性：流量成長 10 倍哪個元件先撐不住？
5. 未來風險：哪些選擇會在一年內變成瓶頸？
```

## 已知陷阱

- **Gemini 有時回傳 JSON 不符合預期格式** → 用 `extract_findings()` 嘗試多種解析策略（code block → direct parse → regex）
- **模型回應不一致嚴重度**（同個問題有的 critical 有的 minor）→ 不需要強制統一，分歧本身就是 insight
- **Repo profile 文字量不宜超過 15K chars** → 超過時模型可能忽略尾部內容
- **NVIDIA 回應最慢**（~49s 實測）→ 不能設 timeout < 60s
