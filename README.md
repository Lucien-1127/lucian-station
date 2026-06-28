# lucian-station — 育昇自學引擎 v2.0

> 企業級常駐對話中樞的學習/演化域。透過 Outcome Record → Lesson 衍生 → Darwin 信號加權 → Hard Track 過濾的雙軌閉環，實現「狀態自校驗、動態豁免邊界、精準容量防護、可摺疊視覺降噪」的自動化自學。

---

## 架構概覽

```
lucian-station/
├── AGENTS.md              ← V13.0 磐石矩陣（系統提示詞）
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

## V13.0 磐石矩陣

V13.0 是 lucian-station 的系統提示詞，定義了企業級常駐對話中樞的標準行為。詳見 [`AGENTS.md`](AGENTS.md)。

---

## V13.0 審查結果

多模型合議庭（Claude Sonnet 4）審查後的 10 項發現已併入 AGENTS.md v13.0。
最高優先項目：

1. ✅ 任務邊界明確定義（涵蓋職責邊界與拒絕條件）
2. ✅ 關鍵變數 Z 的定義（影響機率結果的關鍵隨機變數）
3. ✅ 非量化領域的明確定義（論述、解釋、分類 vs 量化計算）
4. ✅ 配置指令完整列舉（/verbose, /expand, /compact, /status, /reset）
5. ✅ 連續校驗失敗處理（連續 3 次警告後暂停新任務）

---

## 貢獻指南

- Engine 模組必須有 `if __name__ == "__main__":` 單機測試
- 所有寫入操作需通过冷啟動保護檢查
- Lesson 衍生使用 Template-driven 模式，不允許 LLM 自由創作
- 提交前執行：`python3 scripts/self_learning_cycle.py --dry-run --verbose`

---

## 版本

- v2.0 — 2026-06-28：完整重寫，基於 V13.0 磐石矩陣
- v1.x — 早期版本（hermes-skills based）