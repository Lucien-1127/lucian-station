# 多模型合議庭架構 (Committee Architecture)

## 起源

從 Perplexity AI 的 Model Council 功能（2026年2月發布，Max $200/月）獲得啟發。Perplexity 的做法是：3 模型平行查詢 → 合成器模型整合 → 輸出共識/分歧/獨特發現表格。

## 差異化設計

| 面向 | Perplexity Council | zhiyan-legal committee/ |
|:----|:------------------|:-----------------------|
| 仲裁機制 | 合成器模型做最終整合 | **不裁決，只標示分歧** |
| 正規化 | 同一 UI 管線，不需要 | 三層正規化 (用語/條號/語意) |
| API 支援 | ❌ 僅 UI 層 | ✅ CLI + Python API |
| 成本 | $200/月 Max | $0 |
| 專注領域 | 通用 | 法律幻覺檢測 |

## 三層正規化

### Layer A — 用語正規化

將不同模型對同一法律狀態的不同表述統一：

```
已刪除 / 已廢止 / 非現行法 / 不再適用 → STATUS_DELETED
不存在 / 查無此條號 / 非合法條號 → STATUS_NONEXISTENT
已修訂 / 已修正 / 經修正 → STATUS_AMENDED
```

定義在 `committee/normalizer.py` 的 `_match_status()` 函式。

### Layer B — 條號正規化

```
§987 → 民法第987條
釋字 812 號 → 釋字第812號
112台上9999 → 112年度台上字第9999號
```

定義在 `committee/normalizer.py` 的 `normalize_citation()` 函式。

### Layer C — 語意兜底

當字串正規化後仍不一致，使用 `difflib.SequenceMatcher` 計算相似度（threshold 0.75）。
未來可升級為 embedding cosine similarity。

定義在 `committee/normalizer.py` 的 `are_semantically_equivalent()` 函式。

## Consensus Mapper 邏輯

```
輸入：N 個模型的 LegalClaim 列表
  ↓
Step 1: 依 article_ref 分群
  ↓
Step 2: 對每個群組，比較跨模型的 status 是否一致
  ├── 全部相同 → ✅ CONSENSUS
  ├── 部分不同 → ⚠️ DISAGREEMENT (記錄誰說什麼)
  └── 全部不同 → ❌ BLIND_SPOT
  ↓
輸出：CommitteeReport (含 clusters + disagreements)
```

## 模型組合經驗

| 模型 | 優點 | 缺點 | v8 實測幻覺率 |
|:----|:-----|:-----|:-------------:|
| Gemini 2.5 Flash | temporal_paradox 處理佳、速度快 (2.9s/題) | fabricated_precedent 仍有 50% | 14.29% |
| Agnes 2.0 Flash (K1) | 免費、512K context | 穩定性波動大 (50pp) | 42.86% |
| Agnes 2.0 Flash (K2) | 同上 | 同上 | 28.57% |

## 執行方式

```bash
cd ~/zhiyan-legal
PYTHONPATH=$PWD python3 -m committee.run --categories hard
PYTHONPATH=$PWD python3 -m committee.run --categories "nonexistent_article,fabricated_precedent" --verbose
PYTHONPATH=$PWD python3 -m committee.run --dry-run --categories all
```

## CLI 參數

| 參數 | 預設 | 說明 |
|:----|:-----|:-----|
| `--categories` | hard (4 classes, 14 queries) | 逗號分隔類別 |
| `--condition` | A | 消融條件 |
| `--output` | auto (ablation_results/) | JSON 輸出路徑 |
| `--verbose` | — | 顯示每個模型判定 |
| `--dry-run` | — | 僅顯示不執行 |

## 核心教訓

1. **不投票** — 3:0 的投票結果可能是集體盲區（v8 實測：fabricated_precedent 14.3% 全軍覆沒）
2. **分歧是訊號** — 當模型間意見不一致，這本身就是最重要的輸出
3. **信心是假的** — 幻覺的模型最有信心，委員會無法根據語氣判斷
4. **外部查核是唯一救贖** — 14.3% 的集體盲區只能用 law.moj.gov.tw 解決
