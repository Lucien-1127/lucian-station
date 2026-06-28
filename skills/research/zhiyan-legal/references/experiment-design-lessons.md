# 消融實驗方法論教訓（2026-06-26）

## 來源

zhiyan-legal Citation Policy 消融實驗 v3，50 題 × 2 條件，gemini-3.1-flash-lite，100 calls，$0.05788。

## 核心教訓

### 1. Citation Rate ≠ Fabrication Rate

**量測的是格式，不是幻覺。** 實驗設計中最容易被忽略的代理指標陷阱。

```
你以為你在量：模型是否在捏造法條？
實際你在量：模型輸出中是否有符合正則的條號格式？

兩個完全不同的事，但消融實驗天然鼓勵研究者選「好量」的指標。
```

**具體影響**：RQ1 的原始量測指標（引用標記率）回答了錯誤的問題。修正為「內容真實性驗證率」後，需搭配 statute existence verification（ground-truth DB 交叉查詢）。

### 2. Citation Policy 在高能力模型上冗餘

```
條件 A（有 Citation Policy）：引用率 88%
條件 B（無 Citation Policy）：引用率 88%
差異：0%
```

兩種解釋需區分：
- **模型能力問題**：模型本身已內化引用行為，政策文件非必要
- **Prompt injection 問題**：政策文件根本沒被模型讀到

區分方法：加入只有政策才有的專用標記格式（如 [T1]），檢查輸出。v3 實測：0/88 次使用 [T1] → 政策被忽略。

### 3. G0 信心標記需要邊界測試才能驗證

100 次呼叫 0 次觸發，不代表 G0 沒問題。可能只代表測試集都是模型有信心的普通問題。

**設計修復**：加入 5 題刻意模糊 / 資訊不足的邊界問題（不存在的法條、過時的案號、衝突的資料要求）來強制測試低信心情境。

## 研究提案影響

RESEARCH.md 已更新：
- §2.3 RQ1 Test Method：改為「Measure content authenticity via statute existence verification」
- §4.5 新增 Pilot Findings 完整記錄
- §5 Metrics：Fabrication Rate 新增 ⚠️ 警語
