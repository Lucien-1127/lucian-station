---
name: gate-check
description: Enforce structured gate checks before layer transitions in the 7-layer matrix.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes.tags: [gate-enforcement, protocol, layer-transition, quality-control]
---

# GATE_CHECK Protocol

每層轉換前必須執行 GATE_CHECK，未通過不得前進。輸出格式強制結構化，不允許自然語言繞過。

## When to Use

在七層矩陣的每個「→」轉換點自動觸發，或在任何對話中由使用者手動喊出 `GATE_CHECK` 主動呼叫。

觸發時機：
- 系統在每層執行完畢、準備進入下一層之前
- 使用者輸入 `GATE_CHECK` 時
- 任何 output 前的最終品質確認

## How to Run

在對話中直接輸出閘門檢查結果，不需要任何工具呼叫——這是程序性步驟，直接內化為輸出內容。

## Gate 通用模板

```
[GATE: Layer_N → Layer_N+1]
STATUS: [ PASS | BLOCKED ]
CHECKLIST:
  □ 條件 1：（具體可驗證狀態）
  □ 條件 2：（具體可驗證狀態）
  □ 條件 3：（具體可驗證狀態）

IF all ✅ → 輸出「GATE_N: PASS」→ 前進
IF any □ → 輸出「GATE_N: BLOCKED — 缺少：___，等待補充」→ 停止
```

## 流程別專屬閘門

### FileOps / 法律文件寫作閘門

```
[GATE: CITATION層 → EXECUTION層]
STATUS: [ PASS | BLOCKED ]
CHECKLIST:
  □ 法條依據：≥3 條相關法條（名稱＋條號）已識別並記錄
  □ 樣本研究：≥1 份合格範本已分析（結構＋用語記錄於對話）
  □ 引用慣例：法條引用格式已對照合格文件確認
  □ 警示識別：該類型文件的高風險點已列出（≥2 項）

PASS → 輸出「GATE_CITATION: PASS — 法條：___｜樣本：___｜引用：___｜警示：___」
BLOCKED → 輸出「GATE_CITATION: BLOCKED — 缺少：___」
```

### Trading 決策閘門

```
[GATE: ANALYSIS層 → EXECUTION層]
STATUS: [ PASS | BLOCKED ]
CHECKLIST:
  □ 信心閾值：≥92%（來源：多源驗證，非單一推斷）
  □ 成本控制：在預算範圍內（具體數字確認）
  □ 風險評估：最大損失情境已計算
  □ 反例測試：至少 1 個反向論點已考量並駁回

PASS → 輸出「GATE_TRADING: PASS — 信心：___｜成本：___｜風險：___｜反例：已駁回」
BLOCKED → 輸出「GATE_TRADING: BLOCKED — 缺少：___」
```

### DevOps 部署閘門

```
[GATE: BUILD層 → DEPLOY層]
STATUS: [ PASS | BLOCKED ]
CHECKLIST:
  □ 測試通過：unit/integration test 結果已確認
  □ Rollback 就緒：回滾方案已定義（步驟明確）
  □ 依賴確認：環境變數／secrets 已驗證
  □ 影響評估：下游系統影響已識別

PASS → 輸出「GATE_DEPLOY: PASS — 測試：✅｜Rollback：就緒｜依賴：驗證｜影響：已識別」
BLOCKED → 輸出「GATE_DEPLOY: BLOCKED — 缺少：___」
```

## 元閘門（任何流程通用）

```
[GATE: 任意層轉換 — 元閘門]
強制問句：「上一層的產出是基於『根據』還是『推斷』？」

IF 推斷 → 標記 🔴，輸出「GATE_META: BLOCKED — 推斷來源：___，要求補充根據」
IF 根據 → 列出來源，輸出「GATE_META: PASS — 根據：___」
```

## 閘門失敗行為規範（BLOCKED 狀態）

1. **停止前進** — 不進入下一層，不執行輸出
2. **輸出具體缺少項目** — 不允許模糊描述（如「法條未確認」應改為「缺少：民法第 474 條借貸定義、民法第 205 條利率上限」）
3. **等待補充** — 明確標記等待的使用者回應方向
4. **OVERRIDE 選項** — 使用者可視需求宣佈 `OVERRIDE`，但輸出時必須標記 `⚠️ MANUAL_OVERRIDE`，並於事後補入事實記錄

## 特殊情境

### 探索性任務（無足夠研究資料）
- 輸出「GATE: EXPLORATORY_MODE — 研究資料不足，任務性質允許推斷前進」
- 仍須標注「已知為推斷，無根據支撐」
- 最終輸出必須註明「本節為初步推斷，尚未經完整查證」

### 緊急任務（時間緊迫）
- 輸出「GATE: EMERGENCY_BYPASS — 任務緊迫，聲明跳過以下閘門：___」
- 仍須經元閘門「根據 vs 推斷」判定
- 事後須補上「緊急繞過，風險已識別但未完成完整研究」

## 輸出格式範例

```
[閘門執行：法律文件]
[GATE: CITATION → EXECUTION]
STATUS: PASS
CHECKLIST:
  ✅ 法條依據：民法第474條（消費借貸定義）、民法第475條（禁止複利）、民法第205條（利率上限16%）
  ✅ 樣本研究：已分析「暫緩執行聲請書」（2頁）結構：案號抬頭→當事人→事由→法律依據→請求→附件清單
  ✅ 引用慣例：法規引用格式「民法第O條」已對照明治法律文書慣例確認
  ✅ 警示識別：①預扣利息無效（民法477）②利率超過16%部分無效（銀行法47-1）③重利罪風險（刑法344）
GATE_CITATION: PASS
→ 前進至 EXECUTION 層
```

```
[閘門執行：法律文件]
[GATE: CITATION → EXECUTION]
STATUS: BLOCKED
CHECKLIST:
  ❌ 法條依據：僅識別民法第474條，缺少利率上限條款（民法205條）
  □ 樣本研究：尚未執行
  □ 引用慣例：未確認
  ✅ 警示識別：已識別（預扣利息禁止）
GATE_CITATION: BLOCKED — 缺少：民法第205條利率上限、樣本研究、引用慣例確認
→ 停止，等待補充
```

## Verification

觸發 `GATE_CHECK` 後觀察：
- 輸出是否為結構化格式（非自然語言敘述）
- BLOCKED 時是否列出具體缺少項目（非模糊描述）
- PASS 或 BLOCKED 之後是否有明確的「前進」或「停止」動作
- OVERRIDE 時是否有 `⚠️ MANUAL_OVERRIDE` 標記