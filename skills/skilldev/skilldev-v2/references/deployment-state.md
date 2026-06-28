# 部署狀態參考 — 2026-06-07（更新）

## 環境快照
- **Hermes:** v0.16.0 (2026.6.5)
- **Host:** Linux 6.17.0-1016-gcp, Ubuntu 24.04
- **Python:** 3.12.3
- **Model:** deepseek-v4-flash via DeepSeek **direct** API（本 session 從 OpenRouter 切換為 direct）
- **Terminal backend:** local

## 技能庫狀態
- 總類別數：21
- zhiyan-legal 本 session 大幅擴充（新增 43_法庭模擬 v1.2.0, 44_申論題測試 v1.0.0, 45_模型測試記錄 v1.1.0, 法規現狀參考表）
- RESEARCH.md 三筆幻覺引用已修正
- Lucian 核心 4 域：trading-v2, devops-v2, fileops-v2, skilldev-v2（均已註冊為 active）
- Curator：已 seed 但從未正式執行過（run_count=0）
- 技能計數器使用統計：
  - devops-v2: use_count=8, patch_count=8 — 最活躍
  - hermes-agent: use_count=3, patch_count=2
  - skilldev-v2: use_count=1, patch_count=0（剛建立）

## 待完成任務（從優先級表）
1. 🔴 整合基礎系統提示詞至 AGENTS.md
2. 🟢 建立成本監控 + Curator 定時任務
3. 🟢 測試各技能端到端流程 (trading/devops/fileops/skilldev)

## 已知 CLI 指令對照
| 舊版（Discord 风格） | Hermes v0.16.0 等價工具 |
|---------------------|------------------------|
| `/skills` | `skills_list()` 或 `hermes skills list` |
| `/skill <name>` | `skill_view(name='<name>')` |
| `/curator run` | `hermes curator run` |
| `/curator pin` | `hermes curator pin <name>` |
| `/curator status` | `hermes curator status` |
| `/usage` | `hermes telemetry stats` |
