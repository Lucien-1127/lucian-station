# lucian-station — 智研 AI 系統 V13.2 (Decision OS)

> 法律 AI 工作流引擎的學習/演化域。透過十一層 Pipeline（研究 → 引用 → 策略 → 草稿 → 閘門 → 修復 → 信心 → 溯源）與 Decision OS 治理層，實現「零信任 (Zero Trust) 檢索、委員會審議 (Veto Gate)、量化自我演化」的自動化系統。

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