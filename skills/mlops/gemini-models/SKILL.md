---
name: gemini-models
description: 2026年6月 Gemini API 模型選擇與價格對照。適用於子代理、低成本實驗、文字/法律分析。
---

# Gemini API 模型參考（2026年6月）

## 關鍵選擇原則

**不要用 2.5 系列** — 太舊。優先選 3 系列。

**⚠️ 實測教訓：Gemini 2.5 Flash 比 DeepSeek V4 Flash 更貴**。使用者實測回報：Gemini 2.5 Flash 的實際有效成本（token 量 × 品質調整後）高於 DeepSeek V4 Flash。不要只看 Gemini 官方定價表或 billing 報表上的數字（0.06 EUR/month）就以為它便宜——同樣的查詢量，DeepSeek V4 Flash 花得更少、回應更快（~24s vs ~10-15s）。消融實驗中發現 DeepSeek 每題約 $0.0035（~7K system prompt），Gemini 同條件成本更高。優先選 DeepSeek 作為主力模型，Gemini 僅作為 cross-provider 對照組。

**混合策略為預設推薦**：不是全換最便宜的，而是依任務分級選模型。Vision 和 Compression 是品質敏感任務（法律文件/上下文不能錯），用 3.5-flash；Title、Fallback、Curator 是輕量任務，用 3.1-flash-lite 即可。全換 lite 省不到錢（Free Tier 都免費），但會損失關鍵品質。

### 混合策略（推薦）

| 任務 | 模型 | 理由 |
|------|------|------|
| **Vision**（看圖、文件辨識） | `gemini-3.5-flash` | 法律文件不能讀錯，品質優先 |
| **Compression**（壓縮上下文） | `gemini-3.5-flash` | 壓錯會丟關鍵資訊，上下文完整性優先 |
| **Title**（取標題） | `gemini-3.1-flash-lite` | 一句話，最輕量即可 |
| **Fallback**（備援對話） | `gemini-3.1-flash-lite` | 備援夠用就好 |
| **Curator**（技能整理） | `gemini-3.1-flash-lite` | 每週一次背景任務 |

> 💡 Free Tier 下成本都是零，差異只在 rate limit 和模型品質。品質敏感的任務（vision/compression）不值得為省錢降級，title/fallback 用 lite 足矣。

## 模型對照表

定價來源：[ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)（**必須以官方頁為準，不可憑第三方文章**）

| 模型 | 適用情境 | Free Tier | Paid Standard (per 1M) |
|------|---------|:---:|:---:|
| **gemini-3.5-flash** | Vision、Compression、法律分析、多模態。需要品質的場景。 | 🆓 | $1.50 / $9.00 |
| **gemini-3.1-flash-lite** | Title、Fallback、高頻輕量任務。最省錢。 | 🆓 | $0.25 / $1.50 |
| gemini-3.1-pro-preview | 高難度分析、agentic coding | ❌ 需付費 | $2.00 / $12.00 |
| gemini-3-flash-preview | 舊版備選 | 🆓 | $0.50 / $3.00 |
| gemini-2.5-flash-lite | 舊，不要用 | 🆓 | $0.075 / $0.30 |

> 📊 **3.1-flash-lite 比 3.5-flash 便宜 6 倍**（input: $0.25 vs $1.50, output: $1.50 vs $9.00）。Free Tier 兩者皆免費。混合策略在 Free Tier 下不省錢但省品質損失。

### Rate Limits（官方，2026-06）

| 限制 | Free Tier | Tier 1（付費/預付制） |
|------|:---:|:---:|
| RPM | ~10 | ~200-2000 |
| TPM | ~1M | ~4M |
| RPD | ~1,500 | 無硬上限 |
| Spend limit | N/A | $10/10min |
| 資料隱私 | ❌ 用於訓練 | ✅ 不外洩 |

> ⚠️ 精確 RPM 數字官方頁未公布，請在 [AI Studio](https://aistudio.google.com/rate-limit) 查看實際配額。

## API 關鍵注意事項

### Key 格式
- Gemini API key 有兩種前綴：
  - `AIza...` — 標準格式，支援 OpenAI-compatible 端點
  - `AQ.` — 某些專案/帳戶格式，**只支援原生 REST API**
- 原生 REST 端點：`https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- 使用 `X-goog-api-key` header 而非 `Authorization: Bearer`

### 呼叫範例（原生 REST）
```python
data = {
    "system_instruction": {"parts": [{"text": system_prompt}]},
    "contents": [{"parts": [{"text": user_message}]}],
    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json", "X-goog-api-key": key},
    method="POST",
)
```

## 已知實測數據

### zhiyan-legal 消融實驗
- **gemini-2.5-flash-lite**: 64-66% citation rate, 0% confidence markers, $0.08/100 calls
- **gemini-3.1-flash-lite**: **88% citation rate**, 0% confidence markers, **$0.06/100 calls**
- 結論：Gemini 原生引用能力隨版本提升（3.1 > 2.5），Citation Policy 邊際效應接近零
- 信心標記（G0 規則）在所有 Gemini 模型上皆為 0% — 架構層問題

### 效能
- 含 26K chars system prompt 約 10-15 秒/呼叫
