---
name: obsidian-article-loop
description: 建立基於 Obsidian 的提示詞閉環治理 SOP。
version: 1.0.0
author: Hermes
metadata:
  hermes:
    tags: [prompt-engineering, obsidian, continuous-improvement, governance]
---

# Obsidian Article Loop

本技能為一套基於 Obsidian 的提示詞閉環（Loop）治理框架，將提示詞（Prompt）從單純文字提升為可管理的「系統元件」。

## 閉環運作機制 (Article Pipeline)

本系統採用分階段驗證模式，確保每個環節皆可觀測、版本化與回歸測試。

```yaml
# Pipeline 配置參考
stages:
  - name: draft_generation
    model: primary-llm
    template: technical_article_v3
  - name: format_validation
    validator: markdown_structure_check
    on_fail: rewrite_format
  - name: semantic_review
    evaluator: article_quality_rubric_v2
    threshold: 0.82
    on_fail: rewrite_semantic
  - name: final_cleanup
    sanitizer: remove_inline_source_tags
```

## 實務治理技巧

### 1. 模板參數化 (Decoupling)
避免將上下文寫死，改為參數注入：
- 變因拆離：`{{role}}`, `{{audience}}`, `{{output_format}}`, `{{risk_policy}}`
- 優點：降低分支爆炸，便於跨模型遷移與比較品質。

### 2. 版本治理 (Changelog)
每個核心 Prompt 必須附帶 Changelog，記錄：
- 版本號 (vX.Y.Z)
- 具體變更事項（如：欄位強制、段落優化、Few-shot 順序）
- 變更原因（對照失敗的錯誤分類）

### 3. 可量測指標
每個閉環必須具備以下指標，方能進行優化：
- **格式通過率 (Format Pass Rate)**: 規則檢核的通過比率。
- **最終通過率 (Final Pass Rate)**: 語意審核與人工通過之比率。
- **平均修正輪數 (Avg Iteration Rounds)**: 閉環收斂效率。

## 錯誤 taxonomy (錯誤分類法)
每次失敗必須歸類，嚴禁使用「寫不好」這種模糊詞彙：
- `FORMAT_ERROR`: JSON/Markdown 結構缺失。
- `LOGIC_DEVIATION`: 推論跳躍或邏輯錯誤。
- `CONTEXT_MISSING`: 引用依據缺失。
- `CONSTRAINT_VIOLATION`: 違反長度或語氣限制。

## 在 Obsidian 中的管理建議

- **實驗筆記**：在 `Prompts/Experiments` 目錄中，使用 Dataview 管理實驗：
  ```dataview
  TABLE status, model, score, updated
  FROM "Prompts/Experiments"
  WHERE contains(tags, "提示詞工程")
  SORT updated DESC
  ```
- **回歸測試**：維護一組「固定測試案例集」，每次優化 Prompt 前務必先跑回歸。

## 執行流程
1. 定義輸出契約 (Output Contract)。
2. 執行並捕獲錯誤。
3. 結構化記錄失敗樣本至 Taxonomy。
4. 依修正策略更新版本並跑回歸。
