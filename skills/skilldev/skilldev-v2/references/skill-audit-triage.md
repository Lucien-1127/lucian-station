# 技能審計分層檢查法

從 50+ 技能中高效找出問題，而非逐一讀完整內容。

## 分級策略

| 分級 | 標準 | 預估佔比 | 檢查方式 |
|------|------|---------|---------|
| 🔴 高風險 | 用戶自建 + 近期常用 | ~30% | 逐一載入 SKILL.md 完整檢查 |
| 🟡 中風險 | 社群原生 + 偶爾用 | ~40% | 抽查 5-7 個，看 reference 檔案是否存活 |
| 🟢 低風險 | 依賴 GPU/特定硬體/已不用的服務 | ~30% | 只確認 skills_list() 可列出，不深讀 |

## 高風險檢查清單

對每個 🔴 技能，依序檢查：

```
1. Reference 檔案是否存在？
   → skill_view(name, file_path) 對每個 linked_files 內的檔案

2. prerequisites 是否宣告？
   → frontmatter 中有無 prerequisites.commands / pip
   → 引用的外部 CLI 用 which 確認存在

3. CLI 命令是否可執行？
   → terminal("which <cmd>") 確認

4. 版本 vs 實際最新是否一致？
   → frontmatter version 與實際工具版本比對

5. 有沒有指向不存在的目錄或檔案？
   → SKILL.md 內的路徑引用（~/path/）用 ls 確認

6. 有沒有 dead code？
   → PENDING / TODO / 「尚未 merge」等標記
   → 過期的模型/工具名稱

7. 有無未宣告的依賴？
   → SKILL.md 中出現 pip install / npm install / API key 但不在 prerequisites
```

## 常見問題模式

| 問題 | 範例 | 處理 |
|------|------|------|
| 空的目錄依賴 | deep-research v1 指向不存在的 research-skill-graph/ | 移除依賴或補內容 |
| 版本 reference 過時 | lucian-multi-skill-base 寫 deep-research v1.2.0（實為 v2.0.0） | patch 數字 |
| 未宣告 prerequisites | research-tools 用 arxiv/blogwatcher/py-cf2025 但沒寫 | 補 frontmatter |
| Dead code | skilldev-v2 有 4 個掛了半年的 PENDING | 清除或標完成 |
| 未 merge 的分支 | zhiyan-simulation-mode 描述 feat/ 分支 | 標 DRAFT 或更新 |
| 觀點偽裝成數據 | 報告中「95% RAG 可替代」無統計來源 | 移出數據區，標明為觀點 |
| 中位數稱平均數 | 「平均 $6,500」來自區間中點 | 改稱「區間中位數」 |

## 修復優先序

| 優先 | 類型 | 影響 |
|------|------|------|
| 🔴 P1 | 數字錯誤、內部矛盾、reference 斷鏈 | 下次載入直接壞 |
| 🟡 P2 | 未宣告依賴、過時版本、dead code | 特定使用情境才壞 |
| 🟢 P3 | frontmatter 格式不完整、缺少 status | 不影響功能但降低可維護性 |
