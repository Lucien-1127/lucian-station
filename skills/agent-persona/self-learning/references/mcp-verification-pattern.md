# MCP Server 驗證方法 — 自學循環的驗證階段實例

> 2026-06-27 驗證 GCP MCP (6台) + mcp-taiwan-legal-db (8工具) 的實戰記錄

## 核心原則

**每次安裝新的 MCP Server 後，都要執行驗證再正式使用。** 這不是可選步驟。

## 驗證流程

### 步驟 1：確認 MCP Server 活著

對 HTTP remote MCP Server，直接發 `tools/list`：

```bash
curl -s -X POST "https://<endpoint>/mcp" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

回傳 HTTP 200 + JSON 含 `result.tools` 即為活著。

### 步驟 2：確認工具清單符合預期

從 `tools/list` 的回傳中提取工具名稱，對比官方文件或 README。不一致 → 可能是版本差異或連到錯誤 endpoint。

### 步驟 3：實際調用每個工具

對每個工具至少執行一次參數呼叫，驗證：
- 回傳格式是否正確
- 資料是否真實（不是假資料或快取垃圾）
- 邊界情況是否處理（空參數、非法值、不存在資料）

### 步驟 4：修復失敗項

常見失敗：
- **URL 錯誤** → 查官方文件修正（如 IAM MCP 不存在，改用 Resource Manager）
- **授權失敗** → token 已過期或 scope 不足
- **參數不匹配** → 工具層驗證 vs 內部 client 驗證的邊界差異

### 步驟 5：產出驗證報告

包含：測試項目、通過/失敗數、失敗原因、修復狀態、下次關注事項。

## 本 session 的驗證數據

| 專案 | 工具數 | 結果 |
|------|:------:|:----:|
| GCP MCP (6 台) | 54 工具 | 6/6 ✅ |
| mcp-taiwan-legal-db (8 工具) | 24 測試項 | 22/24 ✅ 2項為工具層驗證 |

## 鐵律

- 不通過驗證的 MCP Server → **不可在正式任務中使用**
- 邊界測試失敗但確定為工具層（非底層）問題 → 記錄但不阻擋使用
- 資料錯誤 → 封鎖該工具直到修復
