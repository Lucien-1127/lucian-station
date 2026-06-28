---
name: legal-reasoning-optimizer
description: 智研法律 AI 自動化思考強度調度引擎，整合七層決策矩陣與 pipeline 分流
version: 1.0.0
author: Lucien (Implemented by Hermes)
---

# Legal Reasoning Optimizer

本技能為智研法律 AI 系統的思考強度決策核心，根據輸入任務的「輸出類型」自動分配 API 計算資源 (Reasoning Effort) 與模型路由。

## 自動化思考強度路由矩陣

| 任務分類 | 輸出類型 | 路由與強度 (Reasoning Effort) | 專屬子代理路由 |
| :--- | :--- | :--- | :--- |
| **簡單檢索/爬蟲** | 摘要型 | `low` | Research Agent |
| **法規與解釋比對** | 諮詢型 | `medium` | Research Agent |
| **法律申論分析** | 論述型 | `high` | Legal Writer |
| **書狀攻防/壓力測試** | 書狀型 | `xhigh` | Legal Writer + Committee Agent |

## 執行邏輯 (智研決策流程)

1. **Gate 1 (Task Parser)**: 識別任務類型，對應路由矩陣。
2. **Gate 2 (Research Engine)**: 自動讀取 `Research Agent` 專屬配置。
3. **Gate 3 (Evidence Builder)**: 若幻覺偵測機制 (Committee Agent) 發現置信度 < 0.8，觸發自動升級 (Reasoning Effort: `xhigh`)。
4. **Gate 4 (Strategy Engine)**: 執行最終輸出。

## 自動恢復邏輯 (Self-Healing)

若 API 觸發 Quota Exceeded (429) 或 401:
1. 立即標記任務為 `FAILED`。
2. 禁止宣稱成功。
3. 自動降級至 `OFFLINE_MODE` 或改用 `Gemini/DeepSeek` Fallback 鏈。
