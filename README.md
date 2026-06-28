# lucian-station — 智研 AI 系統 (Legal Governance Runtime)

> **Zhiyan (智研)** 不是一個單純的法律 AI 模型，而是一個 **Legal Governance Runtime (LGR)**。
> 我們不生成「看似正確」的答案，我們生成「具備溯源與審計軌跡」的法律決策過程。

---

## 為什麼選擇智研 (Zhiyan vs. Generic Legal AI)

| 項目 | 一般 Legal AI | 智研 (LGR) |
| :--- | :---: | :---: |
| **核心目標** | 生成答案 | 決策治理 |
| **RAG 架構** | 檢索 (Retrieval) | 治理級檢索 (Governed Retrieval) |
| **決策邏輯** | 黑盒 LLM 推論 | 決策軌跡 (Traceable) |
| **安全邊界** | 提示詞防護 | 治理不變量 (Invariants) |
| **驗證機制** | 外部評測 | 治理覆蓋率 (Policy Coverage) |
| **決策可重播性** | ❌ 否 | ✅ 是 (Governance Replay) |

---

## 核心治理原則 (Three Core Principles)

1. **Every Decision Must Be Traceable**: 每一份法律論述，均可回溯至 SQLite 資料庫中的具體證據區塊。
2. **Every Policy Must Be Testable**: 所有的治理規則皆須通過 Replay Framework 驗證，拒絕主觀臆測。
3. **Every Evolution Must Be Replayable**: 任何對系統策略的更新，都必須通過全量案例回歸測試 (Regression Test)。

---

## 架構概覽 (Architecture Overview)

系統分為三大子系統，強制執行分離原則 (Separation of Concerns)：

```
zhiyan-legal/
├── governance/       # 治理契約：定義決策邏輯、Invariants 與 Policy 語法
├── verification/     # 稽核架構：Replay Engine、Coverage Generator 與測試案例
└── decision_os/      # 執行運行環境：Pipeline、Committee Agent 與各類 Agent 邏輯
```

---

## 架構概覽

```
lucian-station/
├── AGENTS.md              ← V13.1 法律 AI 工作流引擎（十一層 Pipeline + Self-Healing Engine + Confidence Engine）
├── schemas/              ← JSON Schema 定義
│   ├── outcome_record.schema.json
│   ├── lesson.schema.json
│   ├── signal_weights.schema.json
│   └── hard_track.schema.json
├── engine/               ← 自學引擎核心（Python）
│   ├── derive_lesson.py   # Phase 2: Template-driven lesson 衍生
│   ├── recalc_weights.py  # Phase 3: Darwin 信號加權演化
│   ├── evolve_thresholds.py  # Phase 3b: 閾值自動演化
│   ├── apply_hard_track.py    # Phase 4: Cooldowns / Blocklist
│   └── inject_prompt.py   # 三層 Prompt Injection 生成器
├── scripts/
│   ├── self_learning_cycle.py  # 觸發器（替換 weekly_report.sh）
│   └── run_v13_committee.py    # V13.0 多模型合議庭審查
├── data/                 ← 資料持久化層（JSONL）
│   ├── outcome_records.jsonl
│   ├── lessons.jsonl
│   ├── signal_weights.jsonl
│   ├── thresholds.jsonl
│   ├── cooldowns.json
│   └── blocklist.json
└── tests/
    └── test_engine.py    ← 單元測試
```

---

## 快速開始

```bash
# 首次：建立資料目錄
mkdir -p data schemas engine scripts tests

# 觸發完整自學 cycle
python3 scripts/self_learning_cycle.py

# 單相執行
python3 scripts/self_learning_cycle.py --phase 1   # 只收集 outcomes
python3 scripts/self_learning_cycle.py --dry-run     # 模擬（不寫入）
python3 scripts/self_learning_cycle.py --verbose    # 詳細輸出
python3 scripts/self_learning_cycle.py --phase 3 --min-samples 0  # 跳過冷啟動
```

---

## 雙軌自學架構

### Soft Track（文字 Prompt 注入）

| 層級 | 內容 | 來源 | 更新頻率 |
|------|------|------|----------|
| **PINNED** | Darwin 信號加權表 | `recalc_weights.py` | 每 Darwin 演化後 |
| **ROLE-MATCHED** | PREFER / AVOID 精華 | `derive_lesson.py` | 每 Lesson 衍生後 |
| **RECENT** | WORKED / FAILED 完整 Lesson | `data/lessons.jsonl` | 動態載入 |

### Hard Track（機械化過濾）

- **Cooldowns**：信號/實體的臨時冷卻期（由 `apply_hard_track.py` 管理）
- **Blocklist**：永久黑名單（由失敗模式觸發）

**關鍵原則**：LLM 只讀不寫。所有寫入由 Python script 機械完成。

---

## 冷啟動保護

| 函式 | 閾值 | 行為 |
|------|------|------|
| `recalc_weights.py` | `sample_count < 10` | 不執行權重演化，僅 log |
| `evolve_thresholds.py` | `sample_count < 20` | 不執行閾值演化，僅 log |

---

## V13.1 十一層法律 AI Pipeline

V13.1 是 lucian-station 的系統提示詞，定義了法律 AI 工作流引擎的標準行為。核心架構：

```
任務解析 → 研究引擎 → 證據建構 → 策略引擎 → 草稿生成
    ↓           ↓           ↓           ↓           ↓
[GATE_1]    [GATE_2]    [GATE_3]    [GATE_4]    [GATE_5]
                                              ↓
                         修復引擎 ← 閘門核查（Self-Healing Engine）
                             ↓              ↓
                      [GATE_7]        [GATE_6: 🟢🟡🔴]
                             ↓
                      信心評估 → 溯源引擎 → 最終輸出
                         ↓           ↓
                      [GATE_8]    [GATE_9]
```

詳見 [`AGENTS.md`](AGENTS.md)。

## V13.1 主要升級

1. **十一層 Pipeline**：從七層矩陣升級，新增 Research/Evidence/Strategy 三個前置層
2. **Self-Healing Engine**：🟢🟡🔴 三級修復協議
3. **Confidence Engine**：六因子動態加權，輸出 `95.3` 小數分數
4. **三層引用鐵律**：法條 + 大法官釋字 + 最高法院判例，缺一不可 BLOCKED
5. **Utility Tools**：PARAGRAPH_CONTROLLER / FORBIDDEN_TERMS_FILTER / LOCALIZATION_PROCESSOR / SYLLOGISM_CHECKER
6. **Authority 等級**：憲法★★★★★ > 法律★★★★☆ > 判例★★★☆☆ > AI推論★☆☆☆☆
7. **IAM 動態權重**：多模型委員會的 Veto 權因閘門而異（非靜態固定）

---

## 貢獻指南

- Engine 模組必須有 `if __name__ == "__main__":` 單機測試
- 所有寫入操作需通过冷啟動保護檢查
- Lesson 衍生使用 Template-driven 模式，不允許 LLM 自由創作
- 提交前執行：`python3 scripts/self_learning_cycle.py --dry-run --verbose`

---

## 版本

- V13.2 — 2026-06-28：Decision OS，導入 Policy Engine、Governance Contract 與多代理人 IAM 權限邊界管理
- V13.1 — 2026-06-28：法律 AI 工作流引擎，整合 v1.3 Utility Tools + Self-Healing + Confidence Engine + IAM 動態權重矩陣
- v2.0 — 2026-06-28：完整重寫，基於 V13.0 磐石矩陣
- v1.x — 早期版本（hermes-skills based）