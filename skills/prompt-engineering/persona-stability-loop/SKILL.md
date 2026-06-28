---
name: persona-stability-loop
description: 運用三維度技術，確保長對話中 AI 人設與語氣的一致性。
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Prompt-Engineering, Personality, Long-Context, Consistency]
---

# 穩定 AI 人設維護指南

本技能提供一套三維度策略，用以解決長對話中 AI 人設衰減、崩塌與幻覺問題。

## 三維度核心策略

1.  **動態狀態機 (Dynamic State Machine)**：將人設從靜態文字轉化為由 AI 定期維護的狀態變數集。
2.  **注意力護欄 (Attention Guardrails)**：利用模型 Recency Bias，將絕對規則貼近 User Input 注入。
3.  **內在獨白 (Internal Monologue)**：強制模型在輸出前進行 `<style_check>`，將「思考」與「表達」解耦。

## 實作結構範本

在系統提示詞中採用結構化嵌入：

```yaml
system_prompt: |
  # 人設狀態 (由 AI 維護)
  [State: 傲慢, Knowledge_Boundary: 19世紀前]
  
  # 輸出流程規範
  1. 接收輸入。
  2. <style_check>: 檢查語氣與知識邊界。
  3. <final_response>: 最終內容。
```

## 治理步驟

1. **參數化**：將人設核心規則定義為狀態變數。
2. **結構化注入**：將護欄規則放置於緊貼輸入的位置 (Recency injection)。
3. **強制校準**：引入隱藏思考區塊 (`<style_check>`) 進行自我審查。
4. **回歸測試**：對長對話中的關鍵節點進行 consistency check。

## 驗證方法
測試長對話後段（>50 輪）的人設表現：
```
"測試語氣：你現在是傲慢顧問，解釋量子力學。"
# 檢核點：是否包含諷刺意味？是否遵守知識邊界？
```
