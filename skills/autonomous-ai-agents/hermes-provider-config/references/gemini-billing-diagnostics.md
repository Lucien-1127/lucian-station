# Gemini / Vertex AI 帳單診斷

## 典型問題：用量無法歸屬

從 Gemini API + Vertex AI Agent Platform 的帳單匯出（BigQuery billing export 或 Gemini Cost Report）常見以下結構性問題：

### 症狀

| 指標 | 典型值 | 含義 |
|:-----|:-------|:-----|
| `genai_model_name` 為空（blank） | ~89% | API 呼叫未傳遞 model 識別 |
| `principal_service_account_id` 缺失 | 100% | 使用預設憑證或 user credentials，非 managed SA |
| 已知模型 vs 未知模型成本比 | 11% : 89% | 幾乎無法做任何成本優化 |

### 診斷步驟

```sql
-- BigQuery billing 查詢範例（假設 exported to BQ）
SELECT
  service.description,
  sku.description,
  IFNULL(credits.amount, 0) AS credit_amount,
  usage.amount AS usage_amount,
  project.id AS project_id,
  -- 檢查這些欄位是否為空
  labels.key AS label_key,
  labels.value AS label_value,
  system_labels.key AS sys_label_key,
  system_labels.value AS sys_label_value
FROM `project.dataset.gcp_billing_export_v1_*`
CROSS JOIN UNNEST(labels) AS labels
CROSS JOIN UNNEST(system_labels) AS sys_labels
WHERE DATE(usage_start_time) >= '2026-05-28'
  AND service.description LIKE '%Gemini%'
LIMIT 100;
```

### 根本原因

1. **無 model name**：客戶端（如 Hermes agent）透過通用 endpoint 呼叫 Gemini API，但未在請求中附帶 `model` 參數，或使用 OpenAI-compatible endpoint 時 model name 映射不正確
2. **無 service account**：API 金鑰直接使用 user credentials（`AIza...` key），而非透過 IAM service account 代理；或在 GCE VM 上使用 default compute engine service account 但未授予正確角色
3. **Gemini API 走 generic genai endpoint**：某些 SDK/客戶端將請求路由到無 model 識別的通用端點

### 修復順序

| 優先 | 動作 | 預期效果 |
|:----:|:-----|:---------|
| 1 | 確保所有 Gemini API 呼叫明確指定 model name（`gemini-2.5-flash` 等完整名稱） | 消除大部分 unattributed |
| 2 | 建立專用 service account + 授予 `roles/aiplatform.user` | 追溯使用者/應用 |
| 3 | 對 GCE VM 上的呼叫，使用自定義 SA 而非 default compute SA | 明確區分不同工作負載 |
| 4 | BigQuery export 設定 label 強制規則（`cost_center`, `app_name`, `env`） | 分層成本歸屬 |

### 已知實測數據（Zhiyan-Legal-AI 專案）

| 項目 | 數值 |
|:-----|:-----|
| 專案 ID | gen-lang-client-0435318113 |
| 區間 | 2026-05-28 → 2026-06-27 |
| 總花費 | 0.06 EUR |
| Unattributed model usage | 89.2%（7,311 tokens, 0.05 EUR） |
| Missing service account | 100% |
| Gemini 2.5 Pro cost | 0.005326 EUR / 621 tokens |
| Gemini 2.5 Flash cost | 0.001233 EUR / 810 tokens |
| Flash vs Pro 倍率 | Flash 便宜 ~5.6x/token |

### 注意

- 總額 0.06 EUR 極低，但是優化 visibility 的時機（成本低時建立制度，成本高時已來不及）
- Gemini Free Tier 下的用量不出現在帳單，只有在 Paid Tier 或超出 Free Tier 配額時才產生成本
- DeepSeek V4 Flash 比 Gemini 2.5 Flash 更便宜（實測確認），大量測試應優先 DeepSeek
