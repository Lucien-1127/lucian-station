# 戰略定位 — Legal Engineering Platform

> 來源：太陽（技術總監 Review, 2026-06-28）
> 完整文件：`docs/strategy/review-by-太陽-20260628.md`（GitHub repo）

## 核心定位

**不是 AI Lawyer，是 AI Legal Operating System（法律作業系統）**

```
Zhiyan
├── 🧠 AI Core
├── ⚖ Taiwan Legal Knowledge
├── 📚 Knowledge Graph
├── 🤖 AI Agents
├── 🔍 Legal Search
├── 📝 Document Generator
├── 🔗 MCP Ecosystem
├── 📦 Prompt Library
├── 🔌 API Platform
├── 📖 Documentation
└── 🌍 Community
```

## 命名策略

「Legal Engineering Platform」比「法律AI」更適合：
- 可持續擴充，不需要改名字
- 涵蓋 Legal AI、RAG、Prompt Library、Knowledge Base、Agent、MCP、Workflow、API、Dataset、Plugin

## 五階段 Roadmap

| Phase | 內容 | 現狀 |
|:------|:-----|:-----|
| ① Legal Knowledge | 法條/判決/解釋/法律知識 | ✅ 法規監控 + 白話RAG |
| ② Legal Workflow | 收案→整理事實→找法條→分析→產生文件 | 🔄 router.py + 合議庭 |
| ③ AI Agent | Case/Research/Draft/Evidence/Judge Agent | 🏗 committee/ 雛形 |
| ④ Prompt Library | 刑法/民法/行政法 Prompt 模組化 | ⏳ 等待品牌重塑後 |
| ⑤ MCP Ecosystem | 司法院/法規資料庫/裁判書 MCP 化 | 📌 時機成熟 |

## 品牌優先事項

1. **重寫 README** — 企業級首頁（`⚖️ The Open Legal Engineering Platform for Taiwan`）
2. **設計 Logo/Banner/Social Preview**
3. **製作架構圖與 Roadmap 圖**
4. **建立完整 Documentation site**
5. **開源協作規範**（Issue/PR/Contributing 模板）

> 最高優先：GitHub 門面重構 > 增加功能。當 README、品牌、架構圖完成後，外部開發者能一眼看出「這是 Legal Engineering Platform，不是聊天機器人」。
