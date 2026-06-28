# MCP 資料層壓力測試方法論

> 與 SKILL.md 的 LLM 層（幻覺防禦/引用正確性）測試不同，本文件是對 **底層資料源（MCP 工具）** 的驗證方法。

## 為什麼需要資料層測試

zhiyan-legal 的引用正確性有兩層依賴：

```
MCP Taiwan Legal DB（資料層）     ← 這邊先測
    ↓
LLM 引用 + 回答（推理層）         ← 原本 zhiyan-stress-test 測這邊
```

如果資料層回傳錯誤資料，LLM 層再怎麼防禦也沒用。**資料層測試是 LLM 層測試的前置條件。**

## 測試範圍（8 大工具）

| 工具 | 測試重點 | 驗證方式 |
|------|---------|---------|
| `search_judgments` | 搜尋是否回傳真實判決、時間過濾是否生效、法院層級是否正確 | HTTP POST `tools/list` + 實際呼叫 |
| `get_judgment` | 全文是否含事實+理由、引用法條/判決數量 | JID 查詢比對 |
| `query_regulation` | 條文內容是否正確、範圍查詢是否完整 | 比對 law.moj.gov.tw |
| `get_pcode` | 法規名稱→代碼轉換、模糊比對 | 已知 pcode 驗證 |
| `search_regulations` | 搜尋是否涵蓋 11,700+ 部法規 | 關鍵字比對 |
| `get_interpretation` | 離線快取解釋是否正確 | 已知釋字驗證 |
| `search_interpretations` | 搜尋是否回傳相關解釋 | 關鍵字比對 |
| `get_citations` | 引用關係圖是否完整 | 已知釋字驗證 |

## 測試方法（MCP 協議層）

### 直接 HTTP 測（任何 MCP Server 通用）

```bash
TOKEN=*** auth application-default print-access-token)
curl -s -X POST "https://<endpoint>/mcp" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

回傳 HTTP 200 + 工具列表 = 伺服器活著。

### Python 內部調用（mcp-taiwan-legal-db 專用）

見 `scripts/mcp-stress-test.py`，直接 import 內部 client 類別測試：

```python
from mcp_server.tools.judicial_search import JudicialSearchClient
from mcp_server.tools.judicial_doc import JudgmentDocClient
from mcp_server.tools.regulations import RegulationClient
from mcp_server.cache.db import CacheDB

cache = CacheDB()
await cache.initialize()
waf = JudicialWAFBypass()
jud_search = JudicialSearchClient(cache, waf)
result = await jud_search.search(keyword="詐欺", max_results=5)
```

### 邊界測試必測項目

| 類別 | 測試案例 | 預期 |
|------|---------|------|
| 空參數 | `keyword=""` | 拒絕，回傳 error |
| 非法值 | `max_results=0` 或負數 | 工具層驗證擋下 |
| 不存在資料 | `get_pcode("這法規不存在")` | 回傳 None |
| 超大結果 | `max_results=200` 極限 | 不超過硬上限 |
| 時間範圍 | `year_from=2099`（未來年） | 回傳空結果或小於上限 |

## 測試記錄

| 日期 | 結果 | 備註 |
|------|:----:|------|
| 2026-06-27 | 22/24 ✅ | 2 項為工具層驗證，非底層 bug。全文見 `devops/gcp-mcp-setup/references/stress-test-report.md` |

## 與 LLM 層測試的分工

```
資料層測試（本文件）
  1. MCP 工具是否活著？→ tools/list
  2. 搜尋是否回傳真實判決？→ 關鍵字測試
  3. 法規條文是否正確？→ 已知條文比對
  4. 邊界情況是否處理？→ 空值/非法值測試

LLM 層測試（SKILL.md）
  1. 模型是否捏造條號？→ G0 Grade 1-4
  2. 引用是否正確？→ Citation Accuracy
  3. 是否跨法域混淆？→ 中國法 vs 台灣法
  4. 是否觸發信心閾值？→ G0 邊界梯度
```

**鐵律**：每次 MCP 工具版本更新後，先跑資料層測試再跑 LLM 層測試。
