---
name: zhiyan-simulation-mode
description: 模擬模式 + frontmatter 時態標記功能（zhiyan-legal 專用）
version: 1.0.0
status: ⚠️ DRAFT — 此技能描述 feat/simulation-mode-and-temporal 分支，尚未 merge 到 main。使用前請確認分支狀態。
---

# zhiyan-legal 模擬模式與時態標記

實作在 feat/simulation-mode-and-temporal 分支，尚未 merge 到 main。

## 變更範圍

### loader.py
- 新增 `parse_frontmatter(text)` 解析 YAML frontmatter 的 status/as_of_date/version/title
- compose() 新增 `simulation_mode` 參數，啟用時加入模擬模式前言
- 有 frontmatter 的文件自動產生時態標頭：
  - ✅ status: active
  - 📝 status: draft
  - ⚠️ status: deprecated

### router.py
- 新增 SIMULATION 任務關鍵字：假設/模擬/推演/假定/如果
- 路由優先序：SAFETY > LITIGATION > SIMULATION > QC > RESEARCH > REPORT > PERSONA

### cli.py
- 新增 `--simulate` 參數（手動啟用模擬模式）
- 自動偵測 SIMULATION 路由並啟用模擬模式
- --list-tasks 顯示 SIMULATION 項目

## 測試
- test_loader.py: 新增 parse_frontmatter 測試（3 cases）+ compose 時態標頭測試（3 cases）
- test_routing.py: 新增 SIMULATION 路由測試（5 cases）
- 共 71 個測試全部通過

## 如何啟用
```bash
# 自動路由（輸入含「假設」等關鍵詞）
python -m zhiyan_legal "假設某判決已作廢"

# 手動強制模擬模式
python -m zhiyan_legal "某判決被違憲宣告" --simulate
```
