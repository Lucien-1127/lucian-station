# Gemini 免費 Key 多帳號輪流策略

## 核心原則

- Google Gemini API 的免費配額是 **per project**，不是 per key
- 同一個 Google 帳號下的所有 API Key 共享同一個專案的免費配額 → **換 Key 無效**
- 不同 Google 帳號 = 不同專案 = **獨立配額** → 這才有效

## 實戰配置（2026-06）

已配置 4 個 Key，來自 4 個不同 Google 帳號：

```bash
hermes auth list gemini
# #1  gemini-key-2  ← (帳號 1，免費，使用中)
# #2  gemini-key-3     (帳號 2，預付制 Tier 1，rate limit 最高)
# #3  gemini-key-4     (帳號 3，免費)
# #4  gemini-key-5     (帳號 4，免費)
```

## 建議優先順序

預付制 Key 放第一（Tier 1 高 rate limit），免費 Key 們做後備：

```bash
# 若需重排順序：移除再照順序加回
hermes auth remove gemini <索引>
hermes auth add --type api-key --api-key "<KEY>" --label "gemini-prepaid" gemini
hermes auth add --type api-key --api-key "<KEY2>" --label "gemini-free-1" gemini
```

## 自動 failover 機制

- 每個 Key 用完時，Hermes 標記 `exhausted`
- Pool 自動跳到下一個非 exhausted 的 Key
- 24 小時後 exhausted 標記自動清除（配額重置）
- 手動清除：`hermes auth reset gemini`

## 配額差異

| 類型 | Tier | RPM | Pro 模型 | 資料隱私 |
|------|------|-----|:--------:|:--------:|
| 免費 Key | Free | 低 | ❌ | Google 可能用於訓練 |
| 預付制 Key | Tier 1 | 高 | ✅ | 不用於訓練 |
