---
name: hermes-community-skills
description: Guide for discovering, evaluating, and installing community-contributed Hermes Agent skills from GitHub. Covers search strategies, installation patterns, and common pitfalls.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Hermes Community Skills Guide

Guide for discovering, evaluating, and installing community-contributed Hermes Agent skills from GitHub.

## GitHub 技能搜尋策略

單一關鍵字往往不夠。有效搜尋組合：

### 深度研究（Deep Research）
```
"hermes agent skill" "deep research"
"hermes" deep-research
"hermes" multi-agent research
```

### 自我迭代/進化（Self-Evolution）
```
"hermes agent skill" self-improving OR self-evolving OR self-iterating OR auto-skill
"hermes" DSPy GEPA
"hermes" RL skill
```

### 熱門來源
- **NousResearch/** — 官方團隊，star 最高（如 hermes-agent-self-evolution 4.4k⭐）
- **community forks** — 常有更實用的 SKILL.md 格式
- 排序：stars > recent commits > README 完整性

## 安裝模式

### 標準安裝（推薦）
```bash
hermes skills install <hub-id>
```

### 手動安裝（GitHub repo）
```bash
# 1. Clone
git clone <repo-url> /tmp/temp-skill

# 2. Find SKILL.md location
find /tmp/temp-skill -name "SKILL.md"

# 3. Copy to skills directory
mkdir -p ~/.hermes/skills/<category>/<skill-name>/
cp -r /tmp/temp-skill/* ~/.hermes/skills/<category>/<skill-name>/

# 4. Reload
hermes skills check
```

### 目錄分類建議
- `research/` — 研究相關技能
- `autonomous-ai-agents/` — 自我進化、多 agent 協調
- `productivity/` — 文書、試算表、會議
- `media/` — 影音、圖片
- `devops/` — 部署、監控、CI/CD

## 常見坑

1. **SKILL.md 位置不統一** — 有的在根目錄，有的在 `skills/` 子目錄，有的在 `references/`。安裝前先 `find` 確認。

2. **缺少 frontmatter** — 有些 repo 的 SKILL.md 只有標題沒有 YAML frontmatter。需要手動補上 `name:`、`description:`、`version:`。

3. **安裝後未 reload** — 複製檔案後需要 `/reload-skills` 或新 session 才能識別。

4. **依賴未安裝** — 有些技能需要額外套件（如 `dspy`、`gepa`）。安裝前讀 README 確認依賴。

5. **名稱衝突** — 如果已有同名技能，新版本會覆蓋舊內容。先確認是否要替換。

## 技能品質評估清單

安裝前快速檢查：
- [ ] README 有明確的功能說明和使用範例
- [ ] SKILL.md 有完整的 frontmatter（name, description, version）
- [ ] 最近有 commit（3 個月內）
- [ ] 有 LICENSE 檔案
- [ ] Stars/Forks 數量合理（非零）
- [ ] 依賴明確，不需特殊硬體