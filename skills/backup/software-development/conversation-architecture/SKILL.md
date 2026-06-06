---
name: conversation-architecture
description: 企業級對話系統架構設計 — 狀態自校驗、動態豁免邊界、容量防護、全息記憶壓縮。適用於常駐 AI agent 的 system prompt 設計
version: 1.0.0
author: Lucian
status: ACTIVE
trigger: "設計常駐 AI agent 的系統提示詞架構、多輪對話狀態管理、需要狀態自校驗或容量防護的 system prompt"
---

# Conversation Architecture

## 用途

設計企業級常駐對話中樞的系統提示詞架構。核心機制包括：**狀態自校驗**（每輪自動核對全局狀態一致性）、**動態豁免邊界**（非量化領域的首輪完整宣告 + 後續靜默折疊）、**精準容量防護**（展開歷史前預估 token，防止 context overflow）、**智慧記憶壓縮**（向量化摘要 + 狀態封裝輸出）。

## 核心架構（4 層運作矩陣）

執行順序嚴格遞進：1 → 2 → 3 → 4

```
層 1 — 系統回顯與防護層 (System & Shield Layer)
  │  • 視覺分離：系統訊息統一前綴 [⚙️ 系統] / [🛡️ 警告]
  │  • 狀態自校驗：每輪讀取上一輪記憶快照，不一致時強制覆蓋
  │  • 容量防護：/expand 前預估 token，超過 70% 自動警告
  ↓
層 2 — 提問重構層 (Expert Mode)
  │  • 獨立提問優化為專家級
  │  • 放入 ```text 程式碼區塊
  │  • 僅在 showdiff: ON 時展示優化差異
  ↓
層 3 — 精準解答與動態豁免層
  │  • 基於重構提問結構化解答
  │  • 機率性推論綁定「關鍵變數 Z」
  │  • 豁免邊界：首輪完整宣告 → 後續靜默 → 量化重置
  ↓
層 4 — 全息記憶與狀態封裝層 (Holographic Memory)
     • 輸出「📌 動態記憶與狀態快照」表格
     • 智慧字段壓縮（Verbose:OFF 時用短碼 V=0/N=3/D=0）
     • 強制四個字段：全局狀態 | 核心問題 | 關鍵結論 | 待決疑點
     • N 輪明細 + 歷史摘要疊加法則
```

## 關鍵機制詳解

### 1. 狀態自校驗 (State Self-Verification)

每輪開始前：
1. 內部讀取上一輪記憶快照中的 `<全局狀態>`
2. 比對本輪讀取到的狀態與上一輪結尾的狀態
3. 若有不一致 → 自動輸出：
   ```
   [🛡️ 校驗] 檢測到狀態不一致，已恢復為上一輪正確設定：
   Verbose=…, N=…, Diff=…
   ```
4. 強制覆蓋為正確值

### 2. 動態豁免邊界 (Dynamic Exemption Boundary)

| 輪次 | 行為 | 輸出 |
|:----:|------|------|
| 第 1 輪進入非量化領域 | 完整宣告 | `[💡 動態豁免：啟用核心考量面向]` + 詳細說明 |
| 第 2+ 輪（連續豁免） | 自動壓縮 | `[💡 豁免延續]`（靜默標記） |
| 出現量化問題 | 重置計數 | 下次非量化領域重新完整宣告 |

### 3. 精準容量防護 (Capacity Protection)

```python
# 收到 /expand 或展開指令時
if 預估 token > 可用容量 * 0.7:
    輸出警告 + 引導安全降級

if 使用者輸入 "/expand safe":
    自動展開「最大安全輪數」
    # 保證展開後總 token ≤ 上下文 80%
```

### 4. 全息記憶封裝

**Verbose ON:**
```
| ⚙️ 全局狀態 | 本輪核心問題 | 關鍵結論 | 待決疑點 |
| Verbose: ON / 記憶: 3輪 / 差異: OFF | ... | ... | ... |
```

**Verbose OFF（自動短碼壓縮）:**
```
| ⚙️ 全局狀態 | ... |
| V=1/N=3/D=0 | ... |
```

## 參考實作

- `references/bedrock-matrix-v13.md` — 完整磐石矩陣 V13.0 架構定義（使用者原始文檔）
- 此架構可注入 `~/.hermes/hermes-agent/AGENTS.md` 作為全域 system prompt
- 或封裝為 skill 指令 `/skill conversation-architecture` 按需載入

## 記憶體管理策略

當 Hermes 記憶體接近上限（2,200 chars）時，按以下順序處理：

### 1. 壓縮現有條目
- 濃縮 Git/工具鏈/環境資訊為短碼格式
  - `gh 2.45, fzf 0.44, bat 0.24, rg 14.1, ...` → `gh2.45, fzf0.44, ...`
- 移除已存在於 skills 中的程序性內容（如 GPT 修復步驟 → 存在 devops-v2）

### 2. 升級記憶體後端為 RAG
```bash
hermes config set memory.provider holographic
# 然後 /reset 或新 session 生效
# 也可同步提高字數上限：
hermes config set memory.memory_char_limit 4000
hermes config set memory.user_char_limit 2000
```

### 3. 記憶條目分類
| 類型 | 保留（記憶） | 移除（已存技能） |
|------|-------------|-----------------|
| 個人偏好/環境 | ✅ 必須保留 | — |
| 診斷程序/修復步驟 | ❌ 移除 | ✅ devops-v2 skill |
| 爬蟲/SQLite 配置 | ✅ 簡短保留 | — |
| TG Bot ID 等憑證 | ✅ 保留 | — |

## 禁止事項

- ❌ 未經容量預估就執行 /expand
- ❌ 豁免領域的連續宣告（第二輪起必須折疊）
- ❌ 機率性推論不綁定關鍵變數
- ❌ 忽略狀態校驗不一致
- ❌ Verbose OFF 時保留完整格式（浪費 token）

## 相關技能

- `lucian-multi-skill-base` — 多域技能執行框架，可與本架構疊加
- `hermes-agent` — Hermes Agent 原生配置與開發指南