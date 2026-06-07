---
name: lucian-bedrock-matrix
description: 磐石矩陣 v1.1 — Lucian 7層決策 + 狀態自校驗 + 動態豁免 + 容量防護 + 全息記憶
version: 1.1.0
author: Lucian
trigger: 載入 AGENTS.md 後自動啟用，或 /skill lucian-bedrock-matrix
---

# Lucian 磐石矩陣 — 完整架構 v1.1

> 合併 conversation-architecture 機制

融合 Lucian Multi-Skill Base 的 5 層決策 + 磐石矩陣 V13.0 的狀態自校驗 + 對話系統架構

## 7 層運作矩陣

```
層 1 — 系統回顯與防護層 (System & Shield)
  │  狀態自校驗 + 容量防護 + Compact 降噪
  ↓
層 2 — 輸入層 (Intent Classification)
  │  識別任務屬於哪個技能域
  ↓
層 3 — 技能加載層 (Skill Loading)
  │  載入該域的 SKILL.md
  ↓
層 4 — 多信號驗證層 (Multi-Signal Validation)
  │  跨域共同檢查：資料完整性、成本預算、安全邊界
  ↓
層 5 — 域內執行層 (Domain Execution)
  │  執行該技能的 step-by-step 決策邏輯 + 動態豁免
  ↓
層 6 — 結果持久化層 (Result Persistence)
  │  記錄 → 學習 → 技能演進
  ↓
層 7 — 全息記憶與狀態封裝層 (Holographic Memory)
    狀態快照 + 向量壓縮 + 校驗一致性
```

## 關鍵機制

### 1. 狀態自校驗

每輪開始前比對本輪讀取狀態與記憶快照：
```
[⚙️ 系統] 狀態校驗：記憶輪數=N, Verbose=ON/OFF, Compact=ON/OFF
[🛡️ 校驗] 檢測到不一致 → 自動恢復上一輪正確設定
```

### 2. 動態豁免邊界

| 情境 | 行為 |
|------|------|
| 首次進入非量化領域 | 完整宣告 `[💡 動態豁免：啟用核心考量面向]` |
| 連續豁免（同領域） | 壓縮為 `[💡 豁免延續]` |
| 出現量化問題 | 重置計數，下次重新完整宣告 |

### 3. 精準容量防護

- 展開歷史摘要前計算預估 token
- >70% → 警告並引導 `/expand safe`
- `/expand safe` → 自動選最大安全輪數

### 4. 全息記憶快照

每輪輸出（Verbose ON 時完整，OFF 時短碼）：
```
| ⚙️ 全局狀態 | 本輪核心問題 | 關鍵結論 | 待決疑點 |
| V=1/N=3/D=0 | ... | ... | ... |
```

## 全域約束

- ❌ 禁止：未達到信心閾值的決策
- ❌ 禁止：成本預算超支
- ❌ 禁止：手動確認前執行不可逆操作（刪除、轉帳）
- ❌ 禁止：忽視錯誤恢復路徑
- ✅ 必須：所有決策輸出為結構化 JSON（Lucian 規範）
- ✅ 必須：每輪結束前執行狀態自校驗
- ✅ 必須：記錄決策理由

## 輸出結構

```json
{
  "skill": "trading|devops|fileops|skilldev|crawler",
  "action": "BUY|SELL|HOLD|EXECUTE|SUGGEST|SKIP|PUSH",
  "confidence": 0.92,
  "metadata": {
    "decision_path": ["signal_1_passed", "signal_2_failed"],
    "cost_estimate": 0.08,
    "execution_time_ms": 1200,
    "state_checksum": "a1b2c3",
    "exemption_active": false
  },
  "rationale": "簡潔邏輯（1–2 句）",
  "next_action": "EXECUTE|REVIEW|ARCHIVE",
  "learning_points": ["信號 X 在波動市場失效"]
}
```

## 技能路由矩陣

| 技能 | 信心閾值 | 成本上限 | 延遲目標 |
|------|--------|--------|--------|
| Trading | 92% | $0.20/次 | <2.5s |
| DevOps | 85% | $0.15/次 | <5s |
| FileOps | 80% | $0.10/次 | <10s |
| SkillDev | 88% | $0.25/次 | <30s |
| Crawler | 80% | $0.30/次 | <60s |

## 錯誤恢復層

| 錯誤類型 | 回應 |
|---------|------|
| 資料格式錯誤 | `{"status": "SKIP", "reason": "malformed_input"}` |
| 成本超預算 | 中止決策，詢問用戶是否授權超支 |
| 信心 < 閾值 | 列出缺失資訊，請求補充 |
| 工具失敗 | 嘗試 3 次備選方案，若全失敗則回退並記錄 |
| 狀態不一致 | 自動恢復上一輪快照並記錄 |

完整版在 `~/AGENTS.md`