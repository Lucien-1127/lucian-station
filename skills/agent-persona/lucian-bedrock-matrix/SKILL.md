---
name: lucian-bedrock-matrix
description: 智研 AI 系統 7層決策矩陣 — 狀態自校驗 + 動態豁免 + 容量防護 + 全息記憶
version: 1.3.0
author: Hermes
trigger: 載入智研 AI 系統 AGENTS.md 後自動啟用，觸發時呼叫本技能
supporting_files:
  - references/v1-v13-integration.md  # v1.3→V13.1 整合研究發現（含完整模組對照表）
---

# 智研 AI 系統 — 7層決策矩陣 v1.2.0

> 合併 conversation-architecture 機制。
> **系統名稱：智研 AI 系統**（非磐石、非矩陣）
> 完整版在 `~/lucian-station/AGENTS.md`

---

## 核心鐵律（⚠️ 不可忘記）

> **本 session 已確認的流程鐵律（2026-06-28 教訓）**：
> 1. **法條問題** → 先查內建 RAG（`query_regulation`）→ 若不足派子代理至「全國法規資料庫」交叉驗證
> 2. **判例查詢** → 強制使用 MCP（`search_judgments` + `get_judgment`），不得直接 curl 外部網站
> 3. **額度警戒（Quota Guard）** → 429 或 `Quota Exceeded` → 標記 `FAILED`，禁止宣稱成功
> 4. **系統命名** → 統一使用「智研 AI 系統」，不用「磐石」
> 5. **研究先於輸出** → 法律文件必須先研究範本＋查法條，否則輸出與 generic AI 無異
> 6. **架構升級工作流** → 研究舊版 → 多模型委員會 → 決策 → 寫入 → commit/push → 驗證 remote（見「V13.x 升級流程」）

## 7 層運作矩陣

```
層 1 — 系統回顯與防護層 (System & Shield)
  │  狀態自校驗 + 容量防護 + Compact 降噪
  ↓
層 2 — 輸入層 (Intent Classification)
  │  識別任務屬於哪個技能域
  ↓
層 3 — 技能加載層 (Skill Loading)
  │  載入該域的 SKILL.md
  ↓
層 4 — 多信號驗證層 (Multi-Signal Validation)
  │  跨域共同檢查：資料完整性、成本預算、安全邊界
  ↓
層 5 — 域內執行層 (Domain Execution)
  │  執行該技能的 step-by-step 決策邏輯 + 動態豁免
  ↓
層 6 — 結果持久化層 (Result Persistence)
  │  記錄 → 學習 → 技能演進
  ↓
層 7 — 全息記憶與狀態封裝層 (Holographic Memory)
    狀態快照 + 向量壓縮 + 校驗一致性
```

---

## 關鍵機制

### 1. 狀態自校驗

每輪開始前比對本輪讀取狀態與記憶快照：
```
[⚙️ 系統] 狀態校驗：記憶輪數=N, Verbose=ON/OFF, Compact=ON/OFF
[🛡️ 校驗] 檢測到不一致 → 自動恢復上一輪正確設定
```

### 2. 雙重保障法規查證（智研 AI 系統核心）

```
Step 1：法條問題 → 內建 RAG（query_regulation）
Step 2：若 RAG 不足 → 派子代理至「全國法規資料庫」（law.moj.gov.tw）交叉驗證
Step 3：判例查詢 → 強制使用 MCP（search_judgments + get_judgment）
Step 4：引用產出 → CITATION 強制標明（法規名 + 條號 + JID）
```

### 3. 動態豁免邊界

| 情境 | 行為 |
|------|------|
| 首次進入非量化領域 | 完整宣告 `[💡 動態豁免：啟用核心考量面向]` |
| 連續豁免（同領域） | 壓縮為 `[💡 豁免延續]` |
| 出現量化問題 | 重置計數，下次重新完整宣告 |

### 4. 精準容量防護

- 展開歷史摘要前計算預估 token
- >70% → 警告並引導 `/expand safe`
- `/expand safe` → 自動選最大安全輪數

### 5. 全息記憶快照

每輪輸出（Verbose ON 時完整，OFF 時短碼）：
```
| ⚙️ 全局狀態 | 本輪核心問題 | 關鍵結論 | 待決疑點 |
| V=1/N=3/D=0 | ... | ... | ... |
```

---

## 全域約束

- ❌ 禁止：未達到信心閾值的決策
- ❌ 禁止：成本預算超支
- ❌ 禁止：手動確認前執行不可逆操作（刪除、轉帳）
- ❌ 禁止：忽視錯誤恢復路徑
- ❌ 禁止：繞過 MCP/RAG 直接使用外部網站（curl/瀏覽器）查法律問題
- ✅ 必須：所有決策輸出為結構化 JSON（Lucian 規範）
- ✅ 必須：每輪結束前執行狀態自校驗
- ✅ 必須：記錄決策理由
- ✅ 必須：法條引用同時標明法規名 + 條號 + JID（CITATION 政策）
- ✅ 必須：法律文件輸出前完成「研究先於輸出」流程

---

## 錯誤恢復層

| 錯誤類型 | 回應 |
|---------|------|
| 資料格式錯誤 | `{"status": "SKIP", "reason": "malformed_input"}` |
| 成本超預算 | 中止決策，詢問用戶是否授權超支 |
| 信心 < 閾值 | 列出缺失資訊，請求補充 |
| 工具失敗 | 嘗試 3 次備選方案，若全失敗則回退並記錄 |
| 狀態不一致 | 自動恢復上一輪快照並記錄 |
| 429 / Quota Exceeded | **標記 FAILED，降級處理，禁止宣稱成功** |

---

## GATE_ENFORCEMENT_PROTOCOL v1.0

### 核心原則

每層轉換前必須執行 GATE_CHECK，未通過不得前進。輸出格式強制結構化，不允許自然語言繞過。

**任何層的產出都必須回答：「這是基於『根據』還是『推斷』？」**
- 推斷 → 標記 🔴，要求補充來源後才放行
- 根據 → 列出來源（法條、範例、判決），通過

### 通用閘門模板

```
[GATE: Layer_N → Layer_N+1]
STATUS: [ PASS | BLOCKED ]
CHECKLIST:
  □ 條件 1：（具體可驗證）
  □ 條件 2：（具體可驗證）
  □ 條件 3：（具體可驗證）

IF all ✅ → 輸出「GATE_N: PASS」→ 前進
IF any □ → 輸出「GATE_N: BLOCKED — 缺少：___，等待補充」→ 停止
```

### BLOCKED 行為規範

1. 停止前進，輸出 BLOCKED 訊息
2. 列出具體缺少的項目（不允許模糊描述如「法條未確認」，必須寫「缺少：民法第 474 條借貸定義、利率上限民法第 205 條、消保法相關」）
3. 等待使用者補充或明確授權 OVERRIDE
4. OVERRIDE 後標記 ⚠️ MANUAL_OVERRIDE，保留記錄

### 閘門失敗時的誠實原則

智研 AI 系統的強項是「知道自己不知道什麼」。繞過了就是繞過了，標記 ⚠️ 比掩蓋更有意義。

### 流程專用閘門條件

#### 法律文件流程（FileOps / LegalDraft）

```
[GATE: CITATION層 → EXECUTION層]
□ 法條依據：≥3 條相關法條（名稱＋條號）已識別
□ 樣本研究：≥1 份合格範本已分析（結構＋用語記錄）
□ 引用慣例：法條引用格式已對照合格文件確認
□ 警示識別：該類型文件的高風險點已列出（≥2 項）
□ 差異化檢查：本文檔與 generic AI 輸出有何不同？（必須能說出具體根據）
```

#### Trading 決策流程

```
[GATE: ANALYSIS層 → EXECUTION層]
□ 信心閾值：≥92%（來源：多源驗證，非單一推斷）
□ 成本控制：在預算範圍內（具體數字確認）
□ 風險評估：最大損失情境已計算
□ 反例測試：至少 1 個反向論點已考量並駁回
```

#### DevOps 部署流程

```
[GATE: BUILD層 → DEPLOY層]
□ 測試通過：unit/integration test 結果已確認
□ Rollback 就緒：回滾方案已定義（步驟明確）
□ 依賴確認：環境變數／secrets 已驗證
□ 影響評估：下游系統影響已識別
```

---

## 研究先於輸出原則（智研核心差異化）

> **智研 AI 系統的價值主張：輸出必須能拿出「為什麼這樣寫」的根據。**

不做研究的 output 與 generic AI 無異。法律文件寫作前必須：
1. web_search 合格範本（≥1 份，分析結構與用語）
2. 查法條依據（≥3 條，逐一核對）
3. 對照遣詞用語慣例

如果做出來的東西 90% 跟別人的 AI 一樣，研究這個架構就失去意義。

---

完整版在 `~/lucian-station/AGENTS.md`（V13.1）

---

## V13.x 架構升級標準流程（2026-06-28 建立）

### 核心原則

> **「研究先於改寫，不是想到就改」** — 架構升級應視為獨立專案工作流。

### 六步升級流程

```
Step 1 — 研究（Research）
  → 讀取舊版架構檔（v1.x、AGENTS.md history）
  → 派子代理審計（目錄結構、Python 語法、Markdown、連結完整性）
  → 識別：可移植的模組 / 待調整的設計 / 已過時的組件

Step 2 — 委員會（Committee Review）
  → 派多模型子代理（三軌並行）交叉驗證研究結果
  → 每個模組輸出：可移植 / 待調整 / 已過時

Step 3 — 決策（Decision）
  → 整合委員會建議，確認整合決策
  → 每個寫入點需有明確「為什麼要加」的根據

Step 4 — 寫入（Write）
  → 一次只改一個關注點，分批次 patch
  → AGENTS.md 與 README 同時更新

Step 5 — 交付（Deliver）
  → git add → git commit → git push origin main

Step 6 — 驗證（Verify）
  → 用 `git show origin/main:<file>` 確認 remote 內容
  → 檢查關鍵段落是否存在（Utility Tools、IAM 矩陣、溫度參數等）
```

### 驗證清單（每次升級後必填）

| 檢查項目 | Remote 確認方式 |
|---------|---------------|
| 版本宣告 | `git show origin/main:AGENTS.md \| head -5` |
| Utility Tools | `git show origin/main:AGENTS.md \| grep "PARAGRAPH_CONTROLLER"` |
| IAM 動態權重矩陣 | `git show origin/main:AGENTS.md \| grep -A5 "Gate_4_Citation_Review"` |
| README 一致性 | `git show origin/main:README.md \| head -5` |

### v1.3 → V13.1 整合記錄（2026-06-28 實測）

| v1.3 模組 | V13.1 現況 | 整合結果 |
|---------|----------|---------|
| PARAGRAPH_CONTROLLER | ❌ 沒有 | ✅ 新增 Utility Tools |
| FORBIDDEN_TERMS_FILTER | ❌ 沒有 | ✅ 新增（Tier 1/2/3）|
| LOCALIZATION_PROCESSOR | ⚠️ 部分 | ✅ 獨立章節 |
| syllogism_checker | ⚠️ 部分在 Strategy | ✅ 獨立 Tool |
| quality_scorer | ⚠️ 部分在 Confidence | ✅ 對齊表 |
| PERSONALITY_ROUTER | ✅ 進化 | ❌ 退役（document_type routing 取代）|

### 關鍵教訓

1. **不要 rebase 中途放棄**：rebase 會丟未 commit 的變更，有未確定的修改先 stash
2. **Commit 頻繁、小量**：每個有意義的變更獨立 commit
3. **先讀再寫**：修改 AGENTS.md 前先完整 read_file，避免覆蓋未預期內容
4. **驗證比推送重要**：只 push 不驗證 = 不知道有沒有成功