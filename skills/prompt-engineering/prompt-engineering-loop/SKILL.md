---
name: prompt-engineering-loop
description: 建立提示詞工程的自動化觀測、評估、回饋與部署閉環機制。
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [prompt-engineering, system-governance, continuous-improvement]
---

# Prompt Engineering Loop

本技能為提示詞工程提供從「觀測」到「修正」的結構化閉環架構，旨在將 Prompt 從一次性輸入提升為可管理的系統元件。

## 核心機制

一個成熟的提示詞閉環包含五個環節：
1. **輸入定義**：設定任務目標、內容上下文與模型限制。
2. **執行層**：模型產生結果。
3. **評估層**：透過規則型檢核（JSON/格式）與語意型檢核（評分器/審核）判斷品質。
4. **修正層**：根據預定義的錯誤分類（Taxonomy）調整模板或規則。
5. **再部署層**：版本化並更新工作流。

## 實作模式

### 1. 規則型檢核範本 (Python)
用於快速過濾低階錯誤（JSON 合法性、必備欄位）：

```python
def validate_output(data: dict) -> list[str]:
    errors = []
    required = ["title", "summary", "risks"]
    for field in required:
        if field not in data or not data[field]:
            errors.append(f"missing:{field}")
    return errors
```

### 2. 結構化錯誤分類 (Taxonomy)
將失敗案例歸類，以精準修正：
- `FORMAT_ERROR`: JSON 解析失敗、欄位缺失
- `LOGIC_DEVIATION`: 推論跳躍、偏離任務目標
- `CONTEXT_MISSING`: 引用依據不足、虛構法條
- `CONSTRAINT_VIOLATION`: 超出長度限制、格式不符

## 操作步驟

1. **定義輸出契約**：在每個任務開始前，定義欄位結構與品質門檻。
2. **建立自動檢核**：使用 `execute_code` 或獨立驗證腳本定義規則。
3. **錯誤分類記錄**：將驗證失敗的樣本分類儲存至 `./failures/` 目錄。
4. **回饋修正**：累計失敗樣本後，使用 `delegate_task` 觸發 `committee-prompt-review` 進行修正建議。

## 監控指標 (Observability)
監控以下指標以評估閉環成熟度：
- 版本變更頻率
- 規則檢核通過率 (Pass Rate)
- 人工介入修正率 (Intervention Rate)
- 平均自動修正耗時

## 注意事項
閉環真正的成熟度在於「評估機制是否穩定」。若評估器本身不穩定，閉環將成為「用錯誤修正錯誤」的災難。請始終先驗證評估規則的穩定性。
