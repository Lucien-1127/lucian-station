# Hermes 記憶 Provider 對比

> 更新日期：2026-06-06
> 來源：Heremes Agent Docs + 實際驗證

## 概覽

Hermes 內建 8 個外部記憶 Provider plugin，一次只能啟用一個。
內建 MEMORY.md / USER.md 始終與外部 Provider 並行工作。

## Provider 對比表

| Provider | 類型 | 向量/RAG | 費用 | 工具數 | 安裝方式 |
|----------|------|----------|------|--------|---------|
| **Holographic** | 本地 SQLite | FTS5 + HRR | **免費** | 2 | `hermes memory setup` → holographic |
| **Hindsight** | 本地/雲端 | 知識圖譜 | 免費/付費 | 3 | `hermes memory setup` → hindsight |
| **OpenViking** | 自架 | 分層檢索 | 免費 | 5 | pip install openviking + server |
| **Honcho** | 雲端/自架 | 語義搜索+辯證推理 | 付費/免費自架 | 5 | `hermes memory setup` → honcho |
| **Mem0** | 雲端 | 語義+重排序 | 付費 | 3 | `hermes memory setup` → mem0 |
| **RetainDB** | 本地 | 向量 DB | 免費 | — | `hermes memory setup` → retaindb |
| **ByteRover** | 雲端 | 向量 | 付費 | — | `hermes memory setup` → byterover |
| **SuperMemory** | 雲端 | 向量 | 付費 | — | `hermes memory setup` → supermemory |

## 重點 Provider 詳解

### Holographic（推薦給零預算場景）
- 100% 本地，零依賴，SQLite 為底層
- FTS5 全文檢索 + HRR 代數組合查詢
- Trust scoring：事實可信度評分
- 最佳使用場景：空域隔離、筆記本無網路環境

### Hindsight（推薦給知識圖譜路線）
- 實體解析（entity resolution），多策略檢索
- Cross-memory 綜合：`hindsight_reflect` 工具可跨 session 綜合
- 雲端版需 API key，本地版需 PostgreSQL + LLM API key

### Honcho（推薦給需要使用者建模）
- 辯證推理（dialectic reasoning）：每 N 輪對話自動分析使用者模式
- Session-scoped context injection
- Multi-profile peer isolation（不同 Hermes profile 隔離）
- 三配置旋鈕：contextCadence / dialecticCadence / dialecticDepth

## Optional Skills（向量/RAG 專用）

這些不是記憶 Provider，而是可安裝的技能，提供向量搜尋能力：

### Qdrant Vector Search（生產級 RAG）
```bash
hermes skills install official/mlops/qdrant
```
- Rust 向量引擎，REST+gRPC
- 支援 hybrid search + metadata filtering
- 可用於自建知識庫（文件索引、對話記憶向量化）
- 需自行啟動 Qdrant server（Docker 或本地安裝）

## 選擇指南

| 你要什麼 | 選這個 |
|---------|-------|
| 完全免費、零依賴、本地運作 | **Holographic** |
| 知識圖譜、實體關聯 | **Hindsight** |
| 自動使用者建模、辯證推理 | **Honcho** |
| 自建生產級 RAG 知識庫 | **Qdrant**（optional skill） |
| 純文件搜尋、不需記憶 | Chroma / FAISS（自行開發） |

## 切換 Provider

```bash
# 互動式設定
hermes memory setup

# 檢查當前 Provider
hermes memory status

# 關閉外部 Provider
hermes memory off
```

注意：同時間只能啟用一個外部 Provider。切換後需 `/reset` 或重啟 Hermes 生效。
