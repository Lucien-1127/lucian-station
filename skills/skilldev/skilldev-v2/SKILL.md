---
name: skilldev-v2
description: 自動化技能創建、改進、版本化、Curator 整合、成本監控、部署管理
version: 2.2.0
author: Lucian
trigger: "完成 ≥5 工具調用的複雜任務、遇到新死端點並找到解決方案、定期 Curator 評分"
---

# SkillDev Skill v2.0

## 用途
自動化技能創建、改進、版本化、Curator 整合、部署管理。

## 決策框架

### 技能演進迴圈
1. **成功路徑** — 5+ 工具調用後，自動保存為 SKILL.md（或 patch 現有技能）
2. **失敗路徑** — 記錄死端點、根本原因、備選方案到 MEMORY.md
3. **版本化** — 每次非 trivial 更新遞增 minor version
4. **Curator 評分觸發** — 每週執行審查，產出技能評分與推薦操作

### 傳統中文描述規範（繁體臺灣）

所有技能的 `description` 欄位必須遵守以下規範：

| 規則 | 說明 | ❌ 錯誤範例 | ✅ 正確範例 |
|------|------|------------|------------|
| **簡潔** | 一句話講完核心功能，不超過 25 字 | `法律分析、查核與研究。六層架構：SRP→L0→L0.7 白話RAG（每日3AM自動sync）...` | `多層式法律分析系統，整合本地法條白話檢索。` |
| **純正傳統中文** | 避免中英夾雜、日製漢詞、簡體字 | `收錄四十七萬餘條法條白話摘要，支援本地檢索，每日自動同步。` | `法條白話翻譯檢索系統，收錄四萬七千餘條。` |
| **無環境細節** | description 不寫版本號、數量、技術名詞 | `全本地 SQLite FTS5，零套件依賴。每日凌晨3:00自動同步。` | `支援本地檢索，每日自動同步。` |
| **無重複名稱** | 開頭不重複技能名稱 | `智研法律白話 RAG — Google Sheets 法條白話翻譯檢索系統。` | `法條白話翻譯檢索系統。` |
| **單句為佳** | 優先單句完成，必要時用逗號分隔 | （同上） | `法條白話翻譯檢索系統，收錄四萬七千餘條。` |

### 寫法步驟

1. 先想：這個技能做什麼？一句話講完
2. 去掉：英文詞、日文詞、技術規格、數量數字、環境細節
3. 改成：純正傳統中文，字數控制在 15~25 字
4. 檢查：讀起來像人寫的，不是機器列規格

---

## 技能生命週期
| 階段 | 條件 | 行動 |
|------|------|------|
| DRAFT | 新建立 | 加入技能庫，設置信心閾值 |
| ACTIVE | 通過 3 次測試 | 可調用，Curator 周審 |
| STALE | 7 天未調用 | 降權重，標記為可歸檔 |
| ARCHIVED | Curator 評分 <60 且無替代 | 移出主路徑，保留歷史 |

## 部署步驟

### Step 1：配置 Hermes 環境
```bash
mkdir -p ~/.hermes/skills/
# 複製各 SKILL.md 內容到對應目錄
```

### Step 2：配置 Hermes 模型提供者（可選）
若使用 OpenRouter，確認 `~/.hermes/config.yaml` 中已設定 provider。
或直接在 AGENTS.md 整合系統提示詞（推薦，成本更低）。

### Step 4：技能加載驗證
使用以下方式確認技能已正確註冊：
- `skills_list()` — 列出所有可用技能
- `skill_view(name='<skill-name>')` — 載入指定技能的完整內容
- 或在 Hermes 中直接引用技能名稱，系統會自動匹配

### Step 5：測試各技能
- 交易：提供 RSI、ADX、MA、成交量、回撤數據
- 系統優化：提供 CPU/Memory/Disk 指標
- 檔案操作：指定目錄與操作等級
- 技能開發：回顧複雜任務，生成改進方案

### Step 6：成本與 Curator 整合
```yaml
WEEKLY_COST_LIMIT = 50  # USD
ALERT_AT_PERCENTAGE = 80
```

## Curator 整合
```bash
# 每週執行一次（dry-run 預覽，不存檔）
hermes curator run --dry-run

# 若無誤，正式執行
hermes curator run

# 關鍵技能保護
hermes curator pin trading
hermes curator pin devops

# 檢視評分結果
hermes curator status
```

## 成本監控
- 周上限：$50 USD
- 告警線：80%
- 超支行動：自動降溫度 + 禁用 SkillDev 域

## 任務優先級系統（已完成）

| 優先級 | 任務 | 狀態 |
|--------|------|------|
| 🔴 高 | 配置技能目錄並驗證加載 | ✅ 已完成 |

## 信心標記系統

```
信心：84%
低分因素：
- DeepSeek Flash 在 4 個異質領域的推論品質差異未量化
- 技能加載與 OpenRouter 路由的完整相容性未驗證
- Curator 對不同任務類型的評分偏見未評估
- 4 技能共存可能導致提示詞膨脹 >4K tokens

補強條件（提供任一項 → 信心升至 90%）：
1. Hermes v0.16.0 技能加載 & 路由整合指南
2. DeepSeek Flash 在 4 域各 5 個案例的準確度 & 成本採樣
3. Curator 混合工作負載下的評分穩定性測試報告
4. 系統提示詞完整注入後的平均 token 計數 & 緩存命中率
```

## 部署快速檢查清單

### 新增/修改技能時的跨參考同步檢查（重要）

當你在一個系統中新增或修改模組，**必須檢查所有參考到該模組的文件**，否則會產生斷鏈。

| 檢查項目 | 範例 |
|---------|------|
| 🔗 路由表 | 該模組是否在路由表中有對應路由？ |
| 📇 目錄索引 | 索引文件有沒有加入？ |
| 📊 檔案清單 | 檔案數量與描述是否更新？ |
| 📋 SKILL.md 模式表 | 模式路由表有沒有加入新模式？ |

> 此教訓來自實際 session：新增法庭模擬模組時，5 個跨參考文件未同步。

```bash
# 1. 檢查 Hermes 版本
hermes --version          # 應為 0.14.0+

# 2. 確認技能目錄結構
ls -la ~/.hermes/skills/  # 各域應有對應的技能子目錄

# 3. 驗證技能可載入
skills_list()             # 應列出所有已註冊技能

# 4. 測試基礎系統提示詞注入 — JSON 結構化輸出

# 5. 驗證成本預算
hermes telemetry stats    # 顯示每周累積成本

# 6. 測試 Curator
hermes curator status     # 顯示各技能評分與推薦操作
```

## 參考文件

| 檔案 | 用途 |
|------|------|
| `references/temperature-zoning.md` | 溫度分區架構（創作高溫🔥0.8 vs 事實低溫🔥0.1） |
| `references/deployment-state.md` | 當前環境部署狀態快照與 CLI 指令對照 |
| `references/hermes-memory-providers.md` | Hermes 8 大外部記憶 Provider 對比 |
| `references/skill-audit-triage.md` | 🔴/🟡/🟢 三級技能審計篩選 + 常見問題模式 + 修復優先序（實戰驗證 52 技能） |

## 成本與參數
- ❌ 無審查直接歸檔活躍技能
- ❌ 超預算後繼續執行（自動中止）
- ❌ 修改被 pin 保護的技能

## 已知問題與解決方案

### Curator 前台執行卡住
- **症狀**：`hermes curator run` 前台執行無輸出或 process wait timeout
- **原因**：LLM 審查階段（_run_llm_review）建立 AIAgent fork，對大量技能逐步評估需要 2-5+ 分鐘
- **根因**：stdout/stderr 被 redirect 到 /dev/null，pipe buffering 吃掉前期的 print 輸出
- **修復一（推薦）**：使用 `hermes curator run --background` 讓 LLM pass 在 daemon thread 運行，立即返回 CLI。用 `hermes curator status` 檢查結果
- **修復二（輔助）**：在 `~/.hermes/config.yaml` 中明確設定 `auxiliary.curator` 的 provider/model，避免 auto 模式解析失敗導致卡住：
  ```bash
  hermes config set auxiliary.curator.provider openrouter
  hermes config set auxiliary.curator.model deepseek/deepseek-v4-flash
  ```
- **注意**：`--background` 模式是最穩定的執行方式

### no_agent cron 腳本需要 CLI 旗標
- **症狀**：設定 `no_agent=true` 的 cron job 用 `--weekly` 或 `--briefing` 旗標的 Python 腳本，但 cron 直接執行腳本沒傳任何參數
- **原因**：`cronjob` 的 `script` 欄位只能指定腳本檔名，不支援傳遞參數
- **修復**：建立一個 `.sh` wrapper 腳本，在裡面 source venv + 傳參：
  ```bash
  # ~/.hermes/scripts/weekly_report.sh
  #!/bin/bash
  source ~/.hermes/scripts/.venv/bin/activate
  exec ~/.hermes/scripts/tw_freelance_crawler.py --weekly --days 7 "$@"
  ```
  然後 cron 的 `script` 設為 `weekly_report.sh`（.sh 尾綴自動用 bash 執行）

### 腳本路徑必須是相對路徑
- **症狀**：`cronjob` 的 `script` 傳絕對路徑 → 錯誤 "Script path must be relative to ~/.hermes/scripts/"
- **修復**：只傳檔名（如 `tw_freelance_crawler.py`），自動對應到 `~/.hermes/scripts/`

### AGENTS.md 路徑
- Hermes 會自動從工作目錄（`os.getcwd()`）載入 AGENTS.md/CLAUDE.md/.cursorrules
- 放置在 `~/AGENTS.md` 即可全域生效（因工作目錄是 home）
- 注意：不同 profile 可能有不同工作目錄

## 成本與參數
- 溫度：0.25（輕度創造性）
- 最大輸出 Token：512
- 信心閾值：88%
- 成本上限：$0.25/次
- 延遲目標：<30s