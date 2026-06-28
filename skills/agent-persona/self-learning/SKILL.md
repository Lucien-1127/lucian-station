---
name: self-learning
description: 代理自主反思、研究、吸收、驗證的自學循環。支援雲端硬碟考古學、legacy 提示詞整合、技能交叉比對、第三方工具評估、雙軌學習引擎（Soft+Hard Track）。
version: 2.0.0
author: Lucian
trigger: "任務完成後（≥5工具調用）、用戶糾正後、legacy 檔案整合時、修正困難錯誤後、每週例行深度研究、自學 cycle cron 觸發"
---

# 代理自學技能 Self-Learning v2.0

## 核心概念

代理不只是在執行任務，還要從每次執行中學習、研究新知、持續進化。
這顆技能定義了兩個層級的學習循環：**日常學習（四階閉環）** 與 **深度研究（每週排程）**。

```
任務完成
  │
  ▼
① 反思 (Reflect)
   這次學到什麼？用戶糾正了什麼？可泛化到其他任務嗎？
  │
  ▼
② 研究 (Research)
   針對缺口搜尋 → 雲端硬碟 / web / deep-research
  │
  ▼
③ 吸收 (Absorb)
   memory / skill patch / fact_store / references
  │
  ▼
④ 驗證 (Verify)
   下次同類任務驗證改進
```

---

## 觸發時機

| 時機 | 行為 |
|------|------|
| 完成 ≥5 工具調用的複雜任務 | 完整執行 ①→②→③ |
| 用戶糾正錯誤或給了更好的做法 | 立即存 memory + patch 相關技能 |
| legacy 檔案整合（雲端硬碟舊提示詞） | 執行「legacy 提示詞整合流程」 |
| 修正了一個困難 bug 或坑 | 記錄到既有技能 pitfalls + 存 memory |
| 每週例行（週日晚） | ② 深研一個主題，③ 更新知識庫 |
| 發現不熟悉的領域 | ② 快速研究，③ 存 knowledge |

---

## ① 反思 — 自我提問清單

| 問題 | 用途 |
|------|------|
| 這次任務的本質是什麼？ | 確認是否誤解題意 |
| 有什麼意外的發現？ | 潛在可重複使用的模式 |
| 用戶糾正了我什麼？ | 最重要 — 立刻存 memory + patch 技能 |
| 哪個步驟可以做得更好？ | 流程改進點 |
| 這趟學到的東西可以泛化到其他任務嗎？ | 決定存成技能還是 memory |

如果答案都是「沒什麼特別的」→ 跳過研究吸收，只記錄到 session。

---

## ② 研究 — 路徑選擇

| 缺口類型 | 工具 |
|---------|------|
| 工具/API 用法類 | `web_search` + `web_extract` |
| 領域知識類 | 載入 `deep-research` |
| legacy 提示詞比對 | 雲端硬碟考古學（見下） |
| 法規/法律類 | `legal-rag` 查本地資料庫 |

---

## ③ 吸收 — 儲存目標

| 目標 | 工具 | 時機 |
|------|------|------|
| 使用者偏好/事實 | `memory(target='user')` | 立刻 |
| 環境/工具知識 | `memory(target='memory')` | 立刻 |
| 可重複的工作流程 | `skill_manage(action='create' or 'patch')` | 有完整步驟時 |
| session 細節、錯誤紀錄、API 參數 | `references/<topic>.md` | 不宜放 memory 但未來有用 |

---

## ④ 驗證

- 在相關技能的 `trigger` 欄位加註
- 或在 memory 記一筆待驗證項
- 新裝 MCP Server 後：跑 `references/mcp-verification-pattern.md` 流程再使用
- 申請研究 API credit：見 `references/researcher-access-programs.md`

---

## 深度檔案研究（雲端硬碟考古學）

當用戶說「搜尋我雲端硬碟」「研究一下XX資料」時，用 rclone 做實體存取：

```
① 盤點目錄：rclone lsf <remote>: --dirs-only -R
② 搜尋關鍵字：rclone ls <remote>:"目錄/" | grep "關鍵"
   注意：rclone search 不支援中文，用 ls + grep 取代
③ 讀內容：rclone cat <remote>:"路徑/檔案"
④ 新舊版本並排比較，分類為：
   ├── ✅ 已繼承（現有技能已涵蓋）
   ├── 🆕 新功能（值得整合）
   ├── 🔴 遺漏（舊版有但當前沒有的關鍵元件）
   └── 🗑️ 過時（已被取代）
⑤ 差異分析存 reference + memory + patch 技能
```

## ⚠️ 鐵律級工作流程（不可跳過）

處理任何法律問題時，以下順序**不可顛倒，不可跳過**：

```
Step 1：內建 RAG（query_regulation）→ 法條查詢
Step 2：若 RAG 不足 → 全國法規資料庫（law.moj.gov.tw）子代理交叉驗證
Step 3：MCP 司法檢索（search_judgments + get_judgment）→ 判例查詢
Step 4：CITATION 引用產出（法規名+條號+JID 三元素齊備）
```

**❌ 錯誤（本次 session 犯過）**：直接用 curl/瀏覽器搜外部網站，繞過 MCP 與 RAG。  
**✅ 正確**：先 MCP+RAG，不足才派子代理至 law.moj.gov.tw。

違反此順序會導致：
- 引用未經雙重驗證（錯誤的條文內容進入文件）
- 判例 JID 指向錯誤或不存在
- 浪費外部網站存取成本，而內建工具有完整快取

## 常見陷阱

| 陷阱 | 解法 |
|:----|:-----|
| emoji 目錄名可能讓 `rclone lsf` exit 3 | 分層進入，不要一次太深 |
| `rclone search` 不支援中文 | 改用 `rclone ls \| grep` |
| 大檔案拖慢進度 | 用 `head -100` 節省時間 |
| `.md.docx` 是匯出浮水印 | 內容通常打不開，跳過 |
| `.md.docx` 是匯出浮水印 | 內容通常打不開，跳過 |
| **子代理未回報前 cron 就結束** | `delegate_task` 在 cron 中執行時，主 session 可能在子代理回報前就結束。解法：若必須等結果，設 `notify_on_complete=true`；若只需背景蒐集，確保主流程有自己的直接搜索路徑不依賴子代理 |

---

## Legacy 提示詞整合流程 🔄（本 session 驗證 — v1.3 新增）

從雲端硬碟或備份中發現舊版提示詞檔案時，按照以下五步進行「一個一個整合」（用戶偏好：一次只做一個）：

```
① 取源：rclone cat 讀取 legacy 檔案全文
    └── 紀錄來源路徑、版本號、最後修改日期
    │
    ▼
② 差異分析：比對 legacy vs 現有 SKILL.md / 模組文件
    └── 分類：已涵蓋 / 新功能 / 關鍵缺失 / 已過時
    │
    ▼
③ 產出整合清單（給用戶確認順序）
    └── 用戶決定先做哪一個 — 「一個一個整合」
    │
    ▼
④ 逐項整合（一次一項，以下為標準模板）
    ├── a. 建立人格/模組文件（docs/40_模組與人格層/）
    ├── b. 建立 executable prompt reference（references/）
    ├── c. 更新對應模組文件（串接流程、新增狀態）
    ├── d. 更新主 SKILL.md（MODE_ROUTER、參考文件清單）
    └── e. 更新來源追蹤文件（標記 ✅ 已整合）
    │
    ▼
⑤ 版本更新
    └── 更新 CHANGELOG / 更新說明 + CITATION.cff + SKILL.md version
```

### 整合原則

| 原則 | 說明 |
|:----:|------|
| 🎯 **一次一個** | 用戶明確偏好單項整合，不要批次 — 容易遺漏或混亂 |
| 📄 **兩份文件** | 每個人格/模組產出 `NN_人格_名稱.md` + `references/PROMPT_NAME.md` |
| 🔗 **雙向串接** | 新文件要 upstream 指向主 SKILL，主 SKILL 要 downstream 列出新文件 |
| 🏷️ **來源標記** | 所有從 legacy 整併的內容必須在 frontmatter 或開頭注明來源（檔案名 + 版本） |
| ✅ **來源追蹤** | 完成後更新 `references/drive-essay-modules.md` 等追蹤文件，標記已整合 |

### 整合後驗證清單

```
□ 人格/模組文件存在（docs/40_模組與人格層/）
□ executable prompt 存在（references/PROMPT-prompt.md）
□ 模組文件已更新串接（相關 44_/43_ 等）
□ SKILL.md MODE_ROUTER 已新增（若有新模式）
□ SKILL.md 參考文件清單已更新
□ 來源追蹤文件已標記 ✅
□ CHANGELOG / 更新說明已記錄
```

---

## 用戶偏好記錄

| 偏好 | 來源 | 適用場景 |
|:----|:----|:---------|
| **先深度研究再行動** — 不要只表面搜尋就開始做。用戶期望先「上網深度搜尋」、完整學習後再產出。這是研究階段的品質要求，不是時間約束。 | 2026-06-28 Craft 排版研究時用戶糾正 | 任何涉及工具/產品/領域知識的新任務 |
| 一次整合一個，不批次 | legacy 提示詞整合 session | legacy 提示詞整合 |
| 每項整合產出兩份文件（人格 + prompt） | legacy 提示詞整合 session | 任何新人格/模組建立 |
| 完整流程圖高於文字敘述 | 觀察用戶反饋 | 任何結構化文件 |
| 繁體中文命名（基礎級/進階級/高階級，不用 L1/L2/L3） | 用戶指定 | 所有難度/評分/路由標籤 |
| 輸出自然語言，避免過度工程術語 | 用戶指定 | 所有文件與輸出 |

---

## 與其他技能的關係

| 技能 | 協作方式 |
|------|---------|
| zhiyan-eval | 評估框架（待新建）— 為 zhiyan-legal 建立 evaluation pipeline，Darwin 信號驗證所需的量化基礎 |

---

## 第三方工具評估 — 冷郵件／新服務分析模式 🆕

收到陌生工具的推銷信件或推薦時，採用四層評估架構：

### ① 來源驗證

| 檢查項 | 做法 |
|:-------|:------|
| 網站真實性 | 訪問官網，看 documentation、pricing、FAQ 是否存在且合理 |
| 社群足跡 | 搜尋 MCP 目錄（Claude Marketplace、Glama、mcpmarket）、GitHub、Reddit |
| Live 數據 | 注意網站上的使用統計（開發者數、請求量）是否可信 |
| 替代搜尋 | 搜尋 `"產品名" scam` / `"產品名" review` / `"產品名" MCP` 三方驗證 |

### ② 價值匹配

```
給定工具的「宣稱功能」
  → 對照現有技能庫的「已覆蓋範圍」
  → 判斷：無重疊（新能力）／部分重疊（可替代）／完全重疊（不需引入）
```

### ③ 風險邊界

| 評估項 | 門檻 |
|:-------|:------|
| 免費方案 | 無免費方案 → 先存 reference，等需要使用時再評估 |
| 定價合理 | $0-50/mo 可試，>$50/mo 需明確 ROI |
| 資料安全 | 涉及個案資料的工具需確認資料處理政策 |
| 廠商風險 | 太新的公司（<6個月）→ 降低信任等級 |

### ④ 推薦分級

| 結論 | 輸出 |
|:-----|:------|
| ✅ 值得立刻試 | 提供具體步驟 |
| ↳ 可開免費帳號試 | 附條件（哪些功能有價值、哪些沒有） |
| ❌ 不需花錢 | 明確說明為什麼不匹配 |
| ⏸️ 存參考，暫不引入 | 存到相關技能的 reference 或 memory，附評估日期 |

### Katzilla.dev 實測案例

```
來源驗證 → 網站真實 ✅、MCP 目錄上架 ✅、有 Live 數據 ✅
價值匹配 → CourtListener（美國判決）有用，但台灣法域已覆蓋
風險邊界 → 免費 2,500 req/mo ✅
推薦分級 → ↳ 可開免費帳號試 CourtListener，不必投 $49/mo
```

---

## v2.0 實作：lucian-station 雙軌學習引擎（2026-06-28）

> **實作位置**：`~/lucian-station/`（GitHub: `Lucien-1127/lucian-station`）
> **核心原則：LLM 是讀者，不是作者。所有學習由 deterministic code 計算產出。**

### 目錄結構

```
lucian-station/
├── AGENTS.md                   ← V13.0 磐石矩陣系統提示詞
├── schemas/                    ← JSON Schema 定義（4個）
│   ├── outcome_record.schema.json
│   ├── lesson.schema.json
│   ├── signal_weights.schema.json
│   └── hard_track.schema.json
├── engine/                     ← 核心引擎（Python, 1565 行）
│   ├── derive_lesson.py        # Phase 2: Template-driven lesson
│   ├── recalc_weights.py        # Phase 3: Darwin 信號加權演化
│   ├── evolve_thresholds.py    # Phase 3b: 閾值自動演化（10% nudge cap）
│   ├── apply_hard_track.py      # Phase 4: Cooldowns / Blocklist
│   └── inject_prompt.py         # 三層 Prompt Injection 生成器
├── scripts/
│   ├── self_learning_cycle.py  # 觸發器（Phases 1-5）
│   └── run_v13_committee.py    # V13.0 多模型合議庭審查
├── data/                       ← JSONL 持久化層（空目錄，首次執行後自動建立）
└── tests/
    └── test_engine.py          # 18 個單元測試（18/18 ✅）
```

### Soft Track vs Hard Track（對齊 V13.0 架構）

| 軌別 | 對應 V13.0 層 | 機制 | LLM 可見 |
|:-----|:-------------|:-----|:---------|
| **Soft** | 層 2 提問重構 + 層 3 動態豁免 | 三層 prompt injection | ✅ |
| **Hard** | 層 1 系統防護 | 機械化 cooldowns/blocklist | ❌ |

**三層 Injection 對應 V13.0：**
| Tier | 內容 | 對應 |
|------|------|------|
| PINNED | Darwin 信號加權表 | V13.0 全息記憶快照（世界觀層）|
| ROLE-MATCHED | PREFER/AVOID lesson | V13.0 提問重構（人格匹配）|
| RECENT | WORKED/FAILED 完整 lesson | V13.0 動態豁免（情境學習）|

### 觸發指令

```bash
# 完整執行（建議 cron daily）
python3 ~/lucian-station/scripts/self_learning_cycle.py

# 單相執行
python3 ~/lucian-station/scripts/self_learning_cycle.py --phase 1   # 收集 outcomes
python3 ~/lucian-station/scripts/self_learning_cycle.py --phase 2   # 衍生 lesson
python3 ~/lucian-station/scripts/self_learning_cycle.py --phase 3   # Darwin 演化
python3 ~/lucian-station/scripts/self_learning_cycle.py --dry-run --verbose

# 測試
cd ~/lucian-station && PYTHONPATH=$PWD:$PWD/engine python3 -m pytest tests/test_engine.py -v
```

### 多代理交叉審查模式（v2.1 新增 — 2026-06-28）

**觸發情境**：完成 4 個以上的成功案例或重要交付物後，用并行子代理從不同專業視角做交叉驗證。

**標準結構**：3 個并行 leaf 代理，每個專注一個維度：

| 代理 | 職責 | 驗證工具 |
|------|------|---------|
| 司法審查員 | 引用正確性（法條是否出現在真实 cited_statutes）| `search_judgments` + `get_judgment` |
| 法務策略師 | 事實分類準確性、是否遺漏法條/抗辯 | `search_judgments` + `get_judgment` |
| 系統審查員 | 法規內容描述是否與實際條文一致 | `query_regulation`（需先 resolve_pcode）|

**工作流程**：
```
交付完成 → delegate_task(3並行代理) → 各代理寫入 /tmp/verify_*.json
  → 匯總結果 → 識別差異 → 更新案例文件
```

**⚠️ 子代理 context 設計原則**：
- 子代理沒有當前對話的歷史，context 必須包含：目標 JIDs、精確的核查方法、輸出格式
- 結果檔案路徑寫在 context 中，不要依賴子代理自己決定路徑
- 使用 `cd ~/zhiyan-legal && PYTHONPATH=$PWD/src python3 -c "..."` 確保 import 正確

**驗證案例參考**（2026-06-28 實測）：
- 4 個成功案例（漏水侵權、口頭解僱、車位糾紛、押金不退）經三代理審查
- 每個 JID 的 `cited_statutes` 與文件中聲稱的法條逐一比對
- 法規描述正確性由 `query_regulation` 抽樣驗證

### 冷啟動保護（已驗證）

| 函式 | 閾值 | 行為 |
|------|------|------|
| `recalc_weights.py` | `sample_count < 10` | 回傳 `cold_start`，不寫入 |
| `evolve_thresholds.py` | `sample_count < 20` | 回傳 `cold_start`，不寫入 |
| `derive_lesson.py` | `\|outcome_value\| < 0.1` | 跳過 lesson 生成 |

### 關鍵 lesson learned（本 session）

> **Committee 審查時 NVIDIA_API_KEY 未設定導致 1/3 模型失敗 → 先檢查 `NVIDIA_API_KEY` 是否存在再列入 `DEFAULT_REVIEWERS`**，否則浪費 token 且產出不完整。

### Soft Track vs Hard Track

| 軌別 | 機制 | LLM 是否可見 | 範例 |
|:-----|:-----|:------------|:-----|
| **Soft** | 文字注入 prompt | ✅ 可見 | episodic lessons、signal weights、role-matched lessons |
| **Hard** | 代碼直接修改過濾器 | ❌ 不可見 | cooldowns、blocklists、threshold evolution |

> ⚠️ 如果全是 Soft，LLM 知道但高壓下仍會忽略。如果全是 Hard，LLM 無法推理邊角案例。**兩軌並用才有效。**

### Outcome Record Schema

每次決策/任務完成後記錄（存於 `data/outcome_records.jsonl`）：

```json
{
  "id": "uuid",
  "ts": "ISO8601",
  "entity": "task-name or skill-name",
  "outcome_value": 0.85,
  "outcome_type": "success|failure|partial",
  "close_reason": "completed|failed|user_corrected",
  "signal_snapshot": {
    "tool_calls": 3,
    "cost_usd": 0.04,
    "duration_ms": 2100,
    "skill_used": "zhiyan-legal",
    "mode": "CONSULTANT",
    "corrected": false
  }
}
```

### Template-Driven Lesson 生成（LLM 只讀不寫）

```python
# derive_lesson.py — Template rules（不含 LLM 自行創作）
if outcome_type == "success" and corrected == False:
    lesson = f"WORKED: {skill_used} + {mode} → success"
elif outcome_type == "failure":
    lesson = f"FAILED: {skill_used} 因 {close_reason}"
elif corrected:
    lesson = f"PREFER: 替代方案（用戶糾正）→ {skill_used} 的新做法"
# neutral → skip，nothing to learn
```

Lesson 存入 `data/lessons.jsonl`，格式：
```json
{"id","rule","tags":["skill_used"],"role":"default","confidence":0.8,"pinned":false,"created_at":"ISO8601"}
```

### 三層 Prompt Injection

每次任務完成後inject lesson，prompt 格式：

```
── LESSONS ──
[PINNED]   (always present, ≤5)
[PREFERRED] matching current skill/mode (≤6)
[RECENT]   recent lessons (≤10)
Sort: mistakes first (bad/poor before good).
```

### Darwin 信號加權（每 N 筆結果觸發）

自動計算每個信號的預測 lift，動態調整權重：
- `quality_score > 0.7` → weight ×1.05（上限 2.5）
- `cost_usd > 0.10` → weight ×0.95（下限 0.3）

觸發條件：≥10 筆結果（minSamples）+ 需要同時有正負樣本才能計算 lift。

### 閾值自動演化（每 5 筆結果）

```python
winners = [r for r in recent if r.outcome_value > 0]
losers = [r for r in recent if r.outcome_value <= 0]
target_pct = percentile([r.signal_snapshot.quality_score for r in winners], 25)
config.minQuality = clamp(nudge(config.minQuality, target_pct, max_step=0.10), floor=0.3, ceil=1.0)
```

### Hard Track：Cooldowns + Blocklist

機械化寫入，LLM 看不到：
- 任務失敗一次 → 4h cooldown on entity
- 同一失敗模式 ×3 → 12h cooldown + 標記 parent entity
- 寫入 `data/cooldowns_blocklist.json`，每次決策前由 code check，Not prompt

---

## 版本履歷

| 版本 | 日期 | 說明 |
|:----:|:----:|:-----|
| v1.0 | 2026-06-?? | 初始版本：四階閉環 |
| v1.1 | 2026-06-?? | 深度研究子代理模型 |
| v1.2 | 2026-06-?? | 雲端硬碟考古學、MCP 驗證模式 |
| v1.3 | 2026-06-27 | 新增 Legacy 提示詞整合流程、用戶「一次一個」偏好、清理 v1.0/v1.1 重複內容 |
| v2.0 | 2026-06-28 | 雙軌學習架構（Soft+Hard）、Template-driven lesson、Outcome Record schema、Darwin 信號加權、閾值演化、cooldown/blocklist |
