# 架構審查方法 — Codebase Audit

> 用於審查 zhiyan-legal 或其他法律 AI 系統程式碼與文檔是否一致的系統化流程

## 審查範圍

審查四層文件的交叉一致性：

```
SKILL.md  ←→  docs/  ←→  src/  ←→  README.md
   ↑            ↓         ↓           ↑
   └────── RESEARCH.md ───┘───────────┘
```

## 檢查清單

### 1. 架構層級一致性
- [ ] SKILL.md 聲稱的層數與 RESEARCH.md/README.md 是否一致？
- [ ] 每個 L0-L2 層是否在 docs/ 中有對應文件？
- [ ] manifest.py 的 CORE_LAYERS 是否包含所有必要的層？
- [ ] 層級順序是否在 code/compose/readme 中一致？

### 2. 引用政策版本
- [ ] SKILL.md 引用的 Citation 版本 vs docs/ 中的實際文件版本
- [ ] 引用編號體系在各文件中是否一致（[T][1][2][3]）
- [ ] 是否有文件仍引用舊版引用格式？

### 3. 程式碼-文件映射
- [ ] router.py 的 KEYWORD_MAP 是否與 docs/ 中的路由表一致？
- [ ] manifest.py 的 TASK_LAYERS 每個任務是否對應到正確的文件？
- [ ] runner.py 的預設模型是否與 SKILL.md 記載一致？
- [ ] 每個 TASK_LAYER 指向的文件是否真實存在？

### 4. 歷史文件標記
- [ ] RESEARCH.md 中的架構描述是否過期？
- [ ] 模型測試記錄中的模型是否與實際使用一致？
- [ ] CHANGELOG 是否有未記錄的重要變更？
- [ ] README badge 是否指向正確版本？

### 5. 風險分級

| 層級 | 條件 | 範例 |
|:----:|------|------|
| 🔴 P1 | 文檔間架構描述矛盾、引用格式缺漏 | RESEARCH.md 聲稱五層但 SKILL.md 為七層 |
| 🟡 P2 | 預設值過期、關鍵字缺漏 | MODEL_DEFAULT 為已退役模型 |
| 🔵 P3 | 命名不一致、語系混用 | 中英文件名混雜、sync 策略缺漏 |

## 常見失誤模式

| 模式 | 說明 | 修正 |
|:-----|:-----|:-----|
| 架構圖過期 | 新增 L0.7/L0.8 層後，所有文件中的「五層/六層」未同步更新 | 全局搜尋替換 |
| 引用版本滯後 | Citation Policy 升級到 v2.1 但 docs/ 文件仍為 v2.0 | 更新文件名及內部內容 |
| 路由映射錯層 | LEGAL_WRITER 指向訴訟策略模組而非書狀模組 | 修正或加 FIXME 標註 |
| 模型名稱過期 | runner.py 的 MODEL_DEFAULT 使用已退役模型 | 更新至實際使用模型 |

## 執行方式

```bash
# 逐層比對
1. 讀 SKILL.md → 提取架構描述、層級清單、Citation 版本
2. 讀 manifest.py → 提取 CORE_LAYERS、TASK_LAYERS
3. 讀 router.py → 提取 KEYWORD_MAP
4. 讀 runner.py → 提取 MODEL_DEFAULT
5. 讀 RESEARCH.md → 對比 §3.1 架構圖、§4.3 模型表
6. 讀 README.md → 對比 System Architecture、badge 版本
7. 讀 CHANGELOG.md → 確認是否有未記錄變更

# 測試驗證
8. python -m pytest tests/ -v  # 確保所有測試通過
9. git diff --stat             # 確認變更範圍
```
