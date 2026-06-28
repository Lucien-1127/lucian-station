# 提示詞優化委員會 — 多模型共識審查架構

## 用途
用多模型平行審查 + ConsensusMapper 機制，對任意寫手 prompt 做品質評估與修復建議路由。

## 架構

```
Round 1: 平行審查（async, 3 models）
  ├─ DeepSeek V4 Flash → 結構/完整性/精準度
  ├─ Gemini 3.5 Flash  → 可讀性/AI味/受眾校準
  └─ Claude Sonnet 4   → 邊界案例/壓力測試/矛盾偵測

Round 2: Normalizer（各模型自由格式 JSON → 統一 PromptClaim list）

Round 3: 共識分群（跨模型主張匹配 → ConsensusLabel 標示）

Round 4: Dispatch 路由
  ├─ CONSENSUS      → AUTO_FIX (subagent)
  ├─ DISAGREEMENT   → USER_CHOICE (使用者決定)
  ├─ BLIND_SPOT     → HUMAN_REVIEW (最高優先級)
  └─ UNIQUE_INSIGHT → VERIFY_APPLY (驗證後套用)

Round 5: Quality Gates G1–G5
  ├─ G1 結構完整性（ROLE/TASK/OUTPUT/CONSTRAINTS）
  ├─ G2 最低密度（≥50 words）
  ├─ G3 AI味偵測（機械序列詞 ≤1/1000 words）
  ├─ G4 包含示例
  └─ G5 佔位符平衡
```

## ReviewerClient 設計要點

- **Connection pooling**: 共用 httpx.AsyncClient（max=5, keepalive=2）
- **Retry**: tenacity 指數退避 ×3（timeout/connect/remote error）
- **Timeout**: 30s per call
- **Schema sanity check**: 移除 empty issue、confidence out of range、unknown dimension
- **Error isolation**: 一個模型 fail，pipeline 不中斷（structured error report）
- **Auto .env discovery**: Hermes profile .env → ~/.hermes/.env → cwd/.env
- **API key resolution**: explicit override → env var → OPENAI_API_KEY fallback

## 三模型選擇原則

來自不同訓練族系以最大化 blind spot 偵測：
- DeepSeek V4 Flash（CN）— 結構審查
- Gemini 3.5 Flash（US/Google）— 可讀性審查（免費）
- Claude Sonnet 4 via OpenRouter（US/Anthropic）— 壓力測試

## 實作位置

`zhiyan-legal/committee/prompt_optimization/`

模組清單：
- `prompt_quality.py` — schema + data classes（6 dimensions, 3 severities）
- `prompt_normalizer.py` — JSON parsing + validation
- `reviewer_client.py` — API adapter with retry/timeout/schema check
- `consensus.py` — cross-model claim clustering
- `dispatch.py` — ConsensusLabel → action routing
- `quality_gate.py` — G1–G5 validation
- `pipeline.py` — async entry point
- `templates/` — 3 × reviewer system prompts

## 成本

| 模型 | 單次 | 月 ×100 |
|:-----|:----|:--------|
| DeepSeek | ~$0.00006 | ~$0.006 |
| Gemini | $0 (Free) | $0 |
| Claude (OR) | ~$0.006 | ~$0.60 |
| **合計** | **~$0.006** | **~$0.60** |
