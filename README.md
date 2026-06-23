# 🦞 Lucian Station

> **Hermes Agent 技能備份庫 · 系統配置記錄 · 自動化同步中樞**

這是我（Lucian）的 Hermes Agent 技能備份與系統配置倉庫。  
所有技能、腳本、運作記錄都會自動雙向同步，確保在任何環境都能快速還原工作狀態。

---

## 📂 目錄結構

```
lucian-station/
├── skills/          # Hermes 技能備份
│   ├── backup/      # 完整技能 SKILL.md（依類別分類）
│   ├── scripts/     # Hermes 輔助腳本
│   └── inventory.txt
├── vm/              # 系統配置快照（OS、套件、網路、服務等）
├── logs/            # 日常運作日誌
├── AGENTS.md        # 磐石矩陣系統提示詞
├── sync.log         # 同步紀錄
└── README.md        # ← 你正在看這裡
```

---

## 🧠 當前技能庫一覽（31 個類別）

| 類別 | 說明 |
|------|------|
| 🧠 **Agent Persona** | 磐石矩陣決策框架、多技能基礎框架 |
| 🍎 **Apple** | Apple 備忘錄、提醒事項、iMessage、FindMy、macOS 操控 |
| 🤖 **Autonomous AI Agents** | Claude Code、Codex、OpenCode、Hermes Agent 設定 |
| 🎨 **Creative** | 架構圖、ASCII 藝術、Excalidraw、p5.js、影片提示詞 |
| 📊 **Data Science** | Jupyter 即時核心開發 |
| 🖥 **DevOps** | 系統監控、看板管理、WSL 橋接 |
| 🐛 **Dogfood** | Web 應用 QA 測試 |
| 📧 **Email** | 終端機郵件收發 |
| 📁 **FileOps** | 檔案組織、備份管理、儲存最佳化 |
| 🐙 **GitHub** | PR 工作流程、程式碼審查、Issue 管理 |
| 🎵 **Media** | GIF 搜尋、音樂生成、YouTube 內容處理 |
| 🧪 **MLOps** | LLM 評測、模型服務、HuggingFace、vLLM |
| 📝 **Note-Taking** | Obsidian 筆記庫操作 |
| ⚡ **Productivity** | Airtable、Google Workspace、Notion、PDF 編輯 |
| 🔬 **Research** | 論文搜尋、RSS 監控、預測市場 |
| 📘 **SkillDev** | 技能自動化開發與管理 |
| 💬 **Social Media** | X/Twitter 操作 |
| 💻 **Software Development** | 除錯工具、TDD、計畫模式、程式碼審查 |
| 💰 **Trading** | 股票/ETF 交易決策與風險控制 |
| 🧧 **Yuanbao** | 元寶群組操作 |

> 詳細技能清單請見 [`skills/inventory.txt`](skills/inventory.txt)

---

## 🔄 同步機制

- **自動雙向同步**：`~/.hermes/skills/` ↔ `lucian-station/skills/backup/`
- **推送目標**：GitHub `Lucien-1127/lucian-station`
- **同步腳本**：`~/.hermes/scripts/sync_hermes_skills.sh`
- **記錄檔**：每次同步自動寫入 `sync.log`

---

## 🖥 系統環境

| 項目 | 規格 |
|------|------|
| 主機 | Windows 11 24H2, AMD Ryzen 5 7535HS |
| 開發環境 | WSL2 (Ubuntu) |
| GPU | NVIDIA GeForce RTX 2050 (4GB) |
| 記憶體 | ~16GB |
| 預設模型 | DeepSeek v4 Flash |
| 本地模型 | Ollama (Gemma-4, 8B) |

---

## 📜 更新週期

- **技能備份**：每次新增/修改技能後觸發同步
- **VM 配置**：重大系統變更後更新快照
- **運作日誌**：不定期記錄

---

*Lucian Station · 2026-06-23*
