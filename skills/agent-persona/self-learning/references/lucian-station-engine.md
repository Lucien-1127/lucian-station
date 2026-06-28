# lucian-station Engine 實作筆記

> 2026-06-28 首次建構，基於 v2.0 磐石矩陣架構

## 模組地圖

| 模組 | 主要函式 | 冷啟動保護 |
|------|---------|-----------|
| `derive_lesson.py` | `derive_single_outcome(outcome)` → lesson dict | `\|outcome_value\| < 0.1` → None |
| `recalc_weights.py` | `recalculate_signal_weights(outcomes, current)` | `sample_count < 10` → cold_start |
| `evolve_thresholds.py` | `evolve_thresholds(outcomes, current)` | `sample_count < 20` → cold_start |
| `apply_hard_track.py` | `check(entity)` → (blocked, reason) | N/A（直接讀寫狀態檔）|
| `inject_prompt.py` | `build_injection(role, tags)` → markdown str | N/A（無資料時回傳 ""）|

## 已知陷阱（已解決）

### 1. engine 檔案曾被截斷成 `...` stub
- **原因**：初次實作時使用 `...` 作為內文佔位，直接寫入後未替換
- **解法**：完整重寫所有 engine 為實際可執行代碼（1565 行）
- **驗證**：`python3 engine/*.py` 全通過（無錯誤輸出）

### 2. NVIDIA_API_KEY 未設定導致 committee 1/3 模型失敗
- **原因**：`pipeline.py` 的 `DEFAULT_REVIEWERS` 包含 `ReviewerModel.NVIDIA`，但環境變數未設定
- **解法**：執行前檢查 key 存在性，或在 `run_v13_committee.py` 中明確指定 `reviewers=[DEEPSEEK, GEMINI, CLAUDE]`

### 3. inject_prompt.py 縮排錯誤
- **原因**：patch 時整個 function body 被錯誤地多包了一層縮排
- **解法**：完整重寫 `build_injection` 函式

## 資料檔案位置

所有 JSONL/JSON 檔案集中在 `data/` 目錄：
- `outcome_records.jsonl` — 每次任務結果
- `lessons.jsonl` — 衍生 lesson
- `signal_weights.jsonl` — Darwin 權重快照
- `thresholds.jsonl` — 閾值快照
- `cooldowns.json` — Hard Track cooldown 狀態
- `blocklist.json` — Hard Track 黑名單
- `hard_track.json` — 合併的 cooldowns+blocklist 狀態

## inject_prompt.py 輸出格式

```
## 📊 Darwin 信號權重快照
| 信號 | 權重 | 視覺化 |
|------|------|--------|
| `quality_score` | `1.620` | `████████░░` |

## 🧭 角色匹配教訓
### ✅ PREFER
- 當 quality_score 指標偏高時，維持當前策略

### ❌ AVOID
- 避免在所有信號同時低迷時做高風險決策

## 📎 最近案例
### ✅ WORKED
- WORKED 案例
```

## 單元測試覆蓋

18 tests, 18 passed：
- `derive_lesson`: worked/failed/neutral/batch
- `recalc_weights`: cold_start/no_signal_change/weights_bounded/insufficient_contrast
- `apply_hard_track`: cooldown/blocklist/remove/expired
- `inject_prompt`: empty/pinned_block/role_matched/recent_block