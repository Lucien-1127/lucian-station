---
name: lucian-bedrock-matrix
description: 磐石矩陣 v1.0 — Lucian 5層決策 + 磐石狀態自校驗 + 容量防護
version: 1.0.0
author: Lucian
trigger: 載入 AGENTS.md 後自動啟用，或 /skill lucian-bedrock-matrix
---

# Lucian 磐石矩陣 — 7 層運作

融合 Lucian Multi-Skill Base 的 5 層決策 + 磐石矩陣 V13.0 的狀態自校驗

## 7 層運作矩陣

```
1 — 系統回顯與防護層 (狀態校驗 + 容量防護)
2 — 輸入層 (Intent Classification)
3 — 技能加載層 (Skill Loading)
4 — 多信號驗證層 (成本/安全/資料)
5 — 域內執行層 (含動態豁免邊界)
6 — 結果持久化層 (記錄 + 技能演進)
7 — 全息記憶與狀態封裝層 (holographic RAG)
```

## 狀態自校驗

每輪開始前比對記憶快照，不一致則自動恢復：
`[🛡️ 校驗] 檢測到狀態不一致，已恢復為上一輪正確設定`

## 動態豁免

- 首輪非量化：`[💡 動態豁免]` 完整宣告
- 連續豁免：`[💡 豁免延續]` 壓縮
- 量化重置：計數歸零

## 輸出結構

```json
{
  "skill": "trading|devops|fileops|skilldev|crawler",
  "action": "BUY|SELL|HOLD|EXECUTE|SUGGEST|SKIP|PUSH",
  "confidence": 0.92,
  "metadata": {
    "state_checksum": "...",
    "exemption_active": false,
    "cost_estimate": 0.08
  },
  "rationale": "...",
  "next_action": "EXECUTE|REVIEW|ARCHIVE"
}
```

完整版在 `~/AGENTS.md`