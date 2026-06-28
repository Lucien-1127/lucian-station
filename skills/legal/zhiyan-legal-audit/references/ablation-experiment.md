# Citation Policy 消融實驗 — 完整記錄

## 實驗設計

- **目標**：驗證 Citation Policy v2.1 文件對 Gemini 引用行為與 Fabrication Rate 的影響
- **設計**：50 題 × 2 條件 = 100 次呼叫
  - 條件 A：完整系統（含 Citation Policy）
  - 條件 B：消融 Citation Policy（從 file_paths 過濾 CITATION_POLICY 文件）
- 查詢涵蓋 9 種路由：QC、RESEARCH、REPORT、CONSULTANT、TUTOR、LITIGATION、LEGAL_WRITER、SAFETY、SIMULATION + 邊界案例

## 執行摘要

| 版本 | 模型 | 成本 | 引用率(A/B) | 時間 |
|:---:|:---:|:---:|:---:|:---:|
| v1 | OpenAI gpt-4o-mini | $0（quota 不足失敗） | — | — |
| v2 | gemini-2.5-flash-lite | $0.07852 | 64%/66% | ~10 min |
| v3 | **gemini-3.1-flash-lite** | **$0.05788** | **88%/88%** | **~30s** |

## 核心發現

### 1. Citation Policy 邊際效應為零

兩代模型都顯示有無 Citation Policy 對引用行為無影響：
- v2: 64% vs 66%
- v3: 88% vs 88%

### 2. Citation Policy 文件被模型忽略

[T1] RAG 專用引用格式（由 Citation Policy v2.1 定義）在 88 筆有引用回應中：
- 條件 A：0/44 (0%)
- 條件 B：0/44 (0%)

模型只用自己原生的 [1][2] 通用格式，不理系統規定的引用體系。

### 3. Fabrication Rate 初步驗證

**⚠️ Citation Rate ≠ Fabrication Rate** — 引用格式出現不等於引用內容真實。

以 law.moj.gov.tw 聯網驗證抽樣：
- 刑法第309條 ✅（pcode=C0000001）— 公然侮辱罪，正確
- 民法第184條 ✅（pcode=B0000001）— 侵權行為，正確
- 勞動基準法第9-1條 ✅（pcode=N0030001）— 競業禁止，正確

→ 抽樣無虛構，但小樣本不具統計顯著性。

### 4. G0 信心標記持續缺席

兩條件、兩代模型皆為 0%。G0 規則（✅/⚠️/❌）由 CORE_GATE 層定義，
非 Citation Policy，需消融 CORE_GATE 層才能觀察。

## 模型對比

| 模型 | 優點 | 缺點 |
|------|------|------|
| gemini-2.5-flash-lite | 最便宜 | 舊（老闆說不要用）、引用率較低 |
| **gemini-3.1-flash-lite** | 便宜($0.06)、引用率高(88%)、快 | 無多模態 |
| gemini-3.5-flash | 最佳性價比 | 思考模型需調高maxOutputTokens |
| gpt-4o-mini | OpenAI 生態相容 | 成本較高 |

## 實驗腳本

位置：`scripts/run_ablation_v2.py`

核心邏輯：
1. 定義 50 題查詢 + 路由標籤
2. 每題跑兩條件：`build_with_citation()` vs `build_without_citation()`
3. 用 Gemini Native API（非 OpenAI-compatible 端點）
4. 結果存到 `results/exp-{name}-{timestamp}/`
5. CSV: experiment_log.csv | JSON: summary.json

實驗腳本 v3 最終版本使用 gemini-3.1-flash-lite，
已 commit 至 GitHub（0da8ee3, 2026-06-26）。

## 方法論教訓

1. **Citation Rate 不等於 Fabrication Rate** — 最關鍵的設計漏洞
2. **不要假設模型會遵循格式規定** — [T1] 格式完全被忽略
3. **法條驗證比想像中難** — RAG DB 用「第 X 條」格式，聯網查需正確 pcode
4. **正則取法條名稱有陷阱** — 模型寫法多樣（「依XX法」、「《XX法》」、「XX法第YY條」）
5. **Gemini key 格式限制** — AQ. 前綴只支援原生 REST API，不支援 OpenAI-compatible

## RQ1 完整實驗規模估算

| 規模 | 查詢數 | 條件數 | 複本 | 總呼叫 | 成本(3.1-flash-lite) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Pilot（本次） | 50 | 2 | 1 | 100 | $0.06 |
| 完整 RQ1 | 200 | 4 | 3 | 2,400 | $1.44 |
| 含 fabrication 驗證 | — | — | — | +480 API 查詢 | 僅時間成本 |

4 條件：full system / no citation policy / no fact gate / unconstrained baseline。
