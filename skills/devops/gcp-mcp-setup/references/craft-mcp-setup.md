# Craft MCP 設定記錄

> 驗證日期：2026-06-27
> 用戶：Lucien
> 初始 URL：`https://mcp.craft.do/links/8mNbuav3mqS/mcp`

---

## 架構

```
Hermes Agent → MCP (JSON-RPC over HTTPS) → Craft MCP Server
                                               ↓
                                          OAuth 審批
                                               ↓
                                        Craft 空間授權
```

Craft 的 MCP 是 **URL-based**（非 stdio），使用 **OAuth 審批授權**（非 Bearer token）。

---

## 設定步驟

### 1. 從 Craft App 取得 MCP URL

| 平台 | 路徑 |
|:-----|:------|
| **iOS** | 設定(Settings) → Connected Apps → MCP → 產生連結 |
| **macOS** | Craft 選單 → 設定 → Connected Apps → MCP → 產生連結 |

### 2. 寫入 Hermes Config

```yaml
mcp_servers:
  craft:
    url: "https://mcp.craft.do/links/8mNbuav3mqS/mcp"
```

直接加入 `~/.hermes/profiles/<profile>/config.yaml` 的 `mcp_servers:` 區塊。

### 3. 驗證與授權

```bash
hermes mcp test craft
```

首次執行會打開瀏覽器進行 OAuth 審批，需要：
1. 登入 Craft 帳號（如已登入則跳過）
2. 選擇要授權的空間（Space）
3. 按「Approve」

授權完成後，terminal 顯示：
```
✓ Connected
✓ Tools discovered: 3
```

### 4. 確認工具

| 工具 | 用途 | 注意 |
|:-----|:------|:------|
| `craft_read` | 讀取/搜尋文件；支援分號 `;` 批次多個查詢 | 關鍵字搜索語意較靈活 |
| `craft_write` | 寫入/更新；批次用分號分隔 | 可指定 type: doc / block / daily_note / task |
| `blocks_revert` | 復原上一次寫入 | 僅在 block 未經手動修改時有效 |

---

## 使用場景

### 智研 WRITER → Craft 直接寫入

WRITER 產出申論答案後，直接呼叫 `craft_write`：
- 指定 doc title（如「113年律師考試-憲法-模擬答案卷」）
- 選擇目標空間
- WRITER 輸出直接進 Craft，iOS 秒開

### 法律研究歸檔

每次法律查詢的核心結論可自動寫入 Craft 文件庫：
- 案件分類
- 法條摘要
- 實務見解

### WRITER 輸出範例指令

```
請使用 craft_read 搜尋「侵權行為 申論」找到既有範本，
再用 craft_write 將以下申論答案寫入 Craft 空間：
[WRITER 輸出內容]
```

---

## 已知限制

| 限制 | 影響 | 替代 |
|:-----|:------|:------|
| 單次寫入內容長度有限 | 長文需分段 | 分批 `craft_write` |
| `blocks_revert` 僅限未改動過的 block | 無法復原已編輯內容 | 手動復原 |
| OAuth token 在 session 重啟時可能需重新授權 | 非頻繁 | `/reload-mcp` 即可 |

---

## 與其他 MCP 的比較

| 項目 | Craft MCP | GCP MCP (BigQuery等) |
|:-----|:---------|:--------------------|
| 傳輸 | URL-based HTTPS | URL-based HTTPS |
| 授權 | OAuth 審批 | Bearer token (service account) |
| Token 管理 | 無需手動 | 需每 30 分鐘 cron 刷新 |
| 工具數 | 3 | 4-29 不等 |
| 可用平台 | iOS, macOS, Web | 僅伺服器端 |
