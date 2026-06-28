# v1.3 → V13.1 整合研究發現（2026-06-28）

本檔案記錄 2026-06-28 對 v1.3（`docs/目錄導覽—育昇總務/`）與 V13.1 的深度對比分析結果。

## v1.3 完整模組樹

```
CORE_ENGINE
├─ PERSONALITY_ROUTER        → ❌ 已退役（V13.1 以 document_type routing 取代）
│   └─ LITIGATOR/SCHOLAR/EDUCATOR/PHILOSOPHER/CONSTITUTIONAL（固定溫度 0.20-0.70）
├─ TEMPERATURE_CONTROLLER   → ✅ V13.1 四種輸出類型各有預設溫度參數
├─ QUALITY_CONTROLLER       → ⚠️ 進化為 Confidence Engine（六因子動態評分）
└─ EXECUTION_SEQUENCE       → ✅ V13.1 Pipeline（11層）

FUNCTION_MODULES
├─ SCENE_MODES              → ✅ 對應 V13.1 四種輸出類型（書狀/論述/諮詢/摘要）
│   ├─ MODE_CONSUMER_COMPLAINT → 對應 諮詢型（temp: 0.30-0.40）
│   ├─ MODE_CONTRACT_DRAFTING  → 對應 書狀型（temp: 0.20-0.30）
│   ├─ MODE_LEGAL_REPORT       → 對應 論述型（temp: 0.35-0.45）
│   └─ MODE_ESSAY_ANSWER       → ⚠️ V13.1 無直接對應（屬於教育類）
├─ PARAGRAPH_CONTROLLER     → ✅ 新增至 V13.1 Utility Tools
│   （INTRO ±30% / EXPLANATION ±40% / STANDARD ±50% / CORE_ISSUE ±70% / CONCLUSION ±50%）
├─ RISK_ASSESSMENT          → ✅ V13.1 Strategy Engine（攻/守/分析/協商）
│   ├─ GREEN_LIGHT_EVALUATOR  → V13.1 Confidence ≥ 95（起訴狀）
│   ├─ YELLOW_LIGHT_EVALUATOR  → V13.1 Confidence 80-94（諮詢型）
│   └─ RED_LIGHT_EVALUATOR     → V13.1 Confidence < 75（摘要型）
├─ LANGUAGE_CONTROLLER      → ✅ V13.1 Utility Tools → LOCALIZATION_PROCESSOR
└─ FORBIDDEN_TERMS_FILTER   → ✅ 新增至 V13.1 Utility Tools（Tier 1/2/3 三層）

UTILITY_TOOLS
├─ legal_citation_checker()  → ✅ V13.1 三層引用鐵律（法條+釋字+判例）
├─ forbidden_terms_scanner() → ✅ FORBIDDEN_TERMS_FILTER
├─ risk_indicator_generator() → ✅ 🔴🟡🔴 燈號保留在 V13.1
├─ paragraph_length_monitor() → ✅ PARAGRAPH_CONTROLLER
├─ syllogism_checker()       → ✅ SYLLOGISM_CHECKER（V13.1 獨立 Tool）
├─ citation_format_checker() → ✅ LOCALIZATION_PROCESSOR（case_citation 格式）
├─ disclaimer_generator()    → ⚠️ V13.1 未來擴充建議
├─ quality_scorer()           → ✅ 整合進 Confidence Engine（六因子對齊表）
└─ paragraph_type_classifier() → ✅ Task Parser 的 document_type
```

## 重要設計對應關係

### 溫度參數對照表

| V13.1 輸出類型 | v1.3 對應模式 | v1.3 溫度 | V13.1 溫度 |
|--------------|-------------|---------|----------|
| 書狀型 | MODE_CONTRACT_DRAFTING | 0.20-0.30 | 0.20-0.30 ✅ 完全一致 |
| 論述型 | MODE_LEGAL_REPORT | 0.35-0.50 | 0.35-0.45（微調窄） |
| 諮詢型 | MODE_CONSUMER_COMPLAINT | 0.30-0.40 | 0.30-0.40 ✅ 完全一致 |
| 摘要型 | 無直接對應 | — | 0.25-0.35（新增）|

### Confidence Engine ↔ quality_scorer() 對齊

| V13.1 因子 | v1.3 quality_scorer | 權重對應 |
|-----------|-------------------|---------|
| 法源完整性（30%）| legal_citation | 直接對應 |
| 權威等級（25%）| case_support | 擴展為 Authority Ranking |
| 證據一致性（20%）| backup_plans（策略多元性）| 間接對應 |
| 推理一致性（15%）| syllogism_checker | 直接對應 |
| 資料新鮮度（10%）| version_manager | 對應 Snapshot |
| 禁用詞合規（新增）| forbidden_terms_count | V13.1 新增 |

## v1.3 設計中 V13.1 尚未實現的模組

| 模組 | 說明 | 建議 |
|------|------|------|
| `disclaimer_generator()` | 自動附加法律免責聲明 | 未來擴充 |
| `paragraph_type_classifier()` | 段落類型自動分類 | 已部分整合至 Task Parser |
| MODE_ESSAY_ANSWER | 申論題專用模式 | 可考慮新增「教育型」輸出類型 |

## 三個核心升級原則（來自太陽的回饋）

1. **系統工程比 Prompt 優化更重要**：V13.1 的 Self-Healing / Confidence / Provenance 是工程建設，不是 Prompt tuning
2. **研究先於 output**：法律文件範本研究是 V13.1 的強制流程，不是可選步驟
3. **引用必須可以拿出根據**：「為什麼這樣寫」的答案必須是法條+釋字+判例，不是「我認為」

## 閱讀建議

未來當需要對 V13.1 做架構審查或升級時，應：
1. 先完整閱讀 `~/zhiyan-legal/docs/目錄導覽—育昇總務/` 下的 v1.3 文件
2. 對照本檔案確認哪些模組已整合/待整合/已退役
3. 用「六步升級流程」（見 SKILL.md）來執行改動，而不是直接修改 AGENTS.md