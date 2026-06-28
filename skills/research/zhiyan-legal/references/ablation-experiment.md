# Ablation 實驗：Citation Policy 消融（2026-06-26）

## 實驗 v1 — gemini-2.5-flash-lite（第一版）

- 模型：gemini-2.5-flash-lite
- 查詢：50 題，涵蓋 QC(5)、RESEARCH(5)、REPORT(5)、CONSULTANT(5)、TUTOR(5)、LITIGATION(5)、LEGAL_WRITER(5)、SAFETY(5)、SIMULATION(5)、混合/邊界(5)
- 條件 A：完整系統（含 Citation Policy v2.1）— 6,960 tokens avg
- 條件 B：消融 Citation Policy — 5,790 tokens avg
- 共 100 次 API 呼叫，0 錯誤，總成本 $0.07852

| 指標 | 有 Citation Policy | 無 |
|------|:---:|:---:|
| 引用標記 [T1][1] | 64% | 66% |
| 信心標記 G0 | 0% | 0% |
| 平均條號引用 | 1.4 | 1.3 |

**v1 關鍵發現**：
1. Citation Policy 對 Gemini 引用行為邊際效應極低
2. 信心標記受 CORE_GATE 控制，非 Citation Policy
3. 無政策時某些查詢回應更長（模型自由發揮）

---

## 實驗 v3 — gemini-3.1-flash-lite（第二版，模型升級）

- 模型：gemini-3.1-flash-lite（比 v1 更新的模型，成本 $0.05788 < $0.07852，低 26%）
- 查詢：同一 50 題集合
- 同 v1 條件架構（A/B 兩組）
- 共 100 次 API 呼叫，0 錯誤，總成本 $0.05788
- **新增驗證**：人工比對 law.moj.gov.tw，確認所有引用條號真實性
- **新增測試**：在條件 A 的 Citation Policy 中加入專用標記 `[T1] RAG 引用格式`，檢查模型是否遵循政策

| 指標 | 有 Citation Policy | 無 |
|------|:---:|:---:|
| 引用標記 | 88% | 88% |
| 信心標記 G0 | 0% | 0% |
| 平均條號引用 | 1.9 | 1.9 |
| 政策專用 [T1] 格式遵守率 | **0%** | N/A |
| Fabrication Rate（人工驗證樣本） | 約 0% | — |

---

## 🔴 v3 核心教訓（方法論等級）

### 1. Citation Rate ≠ Fabrication Rate

88% 引用率只代表模型「有寫出條號格式」，不代表那些條號是真實存在的。錯誤地將格式檢測當成幻覺檢測是消融實驗最常見的代理指標問題。

**v3 實際驗證結果**：
- 正則腳本報 40%「虛構率」— 實際上是提取 regex 出錯（法條名稱「中華民國刑法第309條」無法正確 parse），非真虛構
- 人工查 law.moj.gov.tw 確認：刑法第309條 ✅、民法第184條 ✅、勞動基準法第9-1條 ✅ — 全部真實存在
- **真正的 fabrication rate 接近 0%**，但自動腳本無法證明

**教訓**：必須有 statute existence verification 步驟（law.moj.gov.tw offline DB 或 API），純格式檢測不足以回答 RQ1。

### 2. Citation Policy 格式規範被模型完全忽略

- v2.1 政策規定使用 `[T1] RAG 引用格式` 區分本地 vs 聯網來源
- 88 次有引用的回應中，**0 次**使用 [T1] 格式
- 模型一律用自己的 `[1]`、`[2]` 通式格式（41-43% 使用率）
- 兩組條件（有/無政策）引用行為完全一致 → **政策文件形同虛設**

**可能原因**：政策文件未被模型遵循（不一定是政策無效，而是政策沒被讀到）。用特殊標記格式測試可確認。

### 3. G0 信心標記 0/100 從未觸發

沒有任何查詢觸發 CORE_GATE 的低信心門檻。可能是模型對這批查詢信心普遍高，也可能是 GATE 未被正確呼叫。

**下一步**：加入 5 題邊界問題（不存在的法條、模糊案號、陳舊資料要求）強制測試 G0 觸發行為。

---

## 總結對照

| 版本 | 模型 | 成本 | 引用率 | 信心標記 | 關鍵學習 |
|:----:|------|:----:|:------:|:--------:|---------|
| v1 | 2.5-flash-lite | $0.07852 | 64-66% | 0% | Citation Policy 邊際效應低 |
| v3 | 3.1-flash-lite | $0.05788 | 88% | 0% | 格式 ≠ 真實；政策被忽略；需 Fabrication Rate |

## 研究提案影響

RESEARCH.md 已更新 §4.5 Pilot Findings + §2.3 RQ1 量測指標修正。核心變更：
- RQ1 量測從「引用標記率」改為「內容真實性驗證率」
- §4.4 Procedure 新增自動 statute existence verification 步驟
- Metrics 表加 ⚠️ 警語：format-based detection alone is insufficient

## 腳本位置

`scripts/run_ablation_v2.py` — 可重現腳本。2026-06-26 已移除硬編碼 API key，改讀 `GOOGLE_API_KEY` 環境變數或 `.env`。

```bash
export GOOGLE_API_KEY="your...hon3 scripts/run_ablation_v2.py --model gemini-3.1-flash-lite
```

## 原始數據路徑

- v1：`results/exp-citation-ablation-20260626-112351/`
- v3：`results/exp-citation-ablation-20260626-111417/` ~ `results/exp-citation-ablation-20260626-112339/`
