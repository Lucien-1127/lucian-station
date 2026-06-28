---
name: gcp-mcp-setup
description: Google Cloud MCP 伺服器安裝與設定。6 組 remote HTTPS MCP（BigQuery/Cloud Storage/Cloud Run/Cloud Logging/Compute Engine/Resource Manager），token 自動刷新 cron。在 GCE VM 上驗證通過。亦可參考同目錄下 references/ 中的非 GCP MCP 整合（Craft 等）。
user-invocable: true
---

# GCP MCP Server 安裝手冊

> 將 Google Cloud 服務以 MCP 協議暴露給 Hermes Agent
> 驗證日期：2026-06-27（全 6 組 ✅ 通過）
> VM：GCE（附 service account）

---

## 原理

GCP MCP Server 是 **remote HTTPS** 型 — 不需要在本機安裝任何套件，直接設定 endpoint URL + Bearer token 即可。Hermes 的 `${ENV_VAR}` 在 runtime 自動代換 token。

```
Hermes Agent → HTTPS POST → https://bigquery.googleapis.com/mcp
                      ↓
                Authorization: Bearer ${GCP_MCP_TOKEN}
                      ↓
                Google Cloud IAM → 對應的 GCP 服務
```

---

## 已安裝的 6 組 MCP Server

| # | 名稱 | Endpoint | 工具數 | 用途 |
|---|------|----------|:------:|------|
| 1 | BigQuery | `bigquery.googleapis.com/mcp` | 4 | 列出資料集、查詢 SQL |
| 2 | Cloud Storage | `storage.googleapis.com/storage/mcp` | 9 | 管理 bucket、讀寫檔案 |
| 3 | Cloud Run | `run.googleapis.com/mcp` | 5 | 查服務、部署 |
| 4 | Cloud Logging | `logging.googleapis.com/mcp` | 6 | 查日誌、管理 bucket |
| 5 | Compute Engine | `compute.googleapis.com/mcp` | 29 | VM 生命週期、磁碟、快照 |
| 6 | Resource Manager | `cloudresourcemanager.googleapis.com/mcp` | 1 | 查詢專案 |

---

## Config 設定

寫在 `~/.hermes/config.yaml` 的 `mcp_servers:` 區塊：

```yaml
mcp_servers:
  gcp-bigquery:
    url: "https://bigquery.googleapis.com/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
  gcp-cloud-storage:
    url: "https://storage.googleapis.com/storage/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
  gcp-cloud-run:
    url: "https://run.googleapis.com/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
  gcp-logging:
    url: "https://logging.googleapis.com/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
  gcp-compute-engine:
    url: "https://compute.googleapis.com/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
  gcp-resource-manager:
    url: "https://cloudresourcemanager.googleapis.com/mcp"
    headers:
      Authorization: *** ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
```

⚠️ `Bearer` 後面的 `${GCP_MCP_TOKEN}` 是 Hermes 的 env var 代換機制，token 值存在 `~/.hermes/.env`。

---

## Token 自動刷新

GCP OAuth2 access token 效期 1 小時。透過 cron 每 30 分鐘刷新一次：

### 刷新腳本

`~/.hermes/profiles/lenien-gcp/scripts/refresh-gcp-token.py`：

```python
#!/usr/bin/env python3
"""Refresh GCP MCP token in ~/.hermes/.env"""
# 1. 先試 GCE metadata server（VM 有 service account 時）
# 2. 失敗則 fallback 到 gcloud auth application-default print-access-token
# 3. 更新 ~/.hermes/.env 中的 GCP_MCP_TOKEN 行
# 4. 成功時不輸出（no_agent 安靜模式），失敗時 print error + exit 1
```

### Cron 設定

```yaml
# hermes cron 排程
schedule: "*/30 * * * *"
no_agent: true  # 安靜模式，僅失敗時通知
script: refresh-gcp-token.py
```

---

## 驗證方式

每個 MCP Server 可用 `tools/list` 指令確認是否連通：

```bash
# 測試單一 MCP Server（以 BigQuery 為例）
TOKEN=$(gcloud auth application-default print-access-token)
curl -s -X POST "https://bigquery.googleapis.com/mcp" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 全部 6 組一次測完
python3 ~/.hermes/profiles/lenien-gcp/scripts/verify-gcp-mcp.py
```

驗證腳本 `verify-gcp-mcp.py` 會對所有 6 組 endpoint 發送 `tools/list`，回傳 HTTP 200 + 工具列表即為通過。

---

## 注意事項

- **驗證腳本**：`~/.hermes/profiles/lenien-gcp/scripts/verify-gcp-mcp.py` — 一鍵測試全部 6 組 MCP，回傳 HTTP 狀態 + 工具列表
- **不是 IAM MCP**：Google 沒有獨立的 IAM MCP，用 Resource Manager 代替（查專案層級 IAM Policy）
- **Token 過期**：access token 1 小時過期，cron 每 30 分鐘刷新一次。如果看到 MCP 工具突然無法使用，先檢查 token
- **GCE VM 限定**：metadata server 只在 GCE VM 上可用，非 GCE 環境會 fallback 到 `gcloud auth`
- **只讀為主**：大部分工具是 readOnly，但 `execute_sql`（BigQuery）、`deploy_service_from_image`（Cloud Run）、`delete_instance`（Compute Engine）等是寫入操作，請注意安全
- **新開 session 才生效**：MCP Server 在 Hermes 啟動時載入，現有 session 需重啟才會看到新工具

---

## URL-based MCP 的兩種授權模式

MCP 伺服器使用 `url:` 傳輸時（有別於 `command:` + `args:` 的 stdio 模式），
授權方式主要有兩種：

| 授權模式 | 設定方式 | 代表服務 | 驗證方法 |
|:--------:|:---------|:---------|:---------|
| **Bearer Token** | `headers.Authorization` | GCP 系列 | `curl -H "Authorization: Bearer ..."` |
| **OAuth 審批** | `url:` 直連 + 瀏覽器授權 | Craft, ChatGPT MCP | `hermes mcp test <name>` 確認連通 |

### Craft MCP（OAuth 審批模式範例）

Craft（craft.do）是一款 iOS/桌面筆記 App，提供原生 MCP 伺服器，採用
OAuth 授權流程（非 Bearer token）：

**設定步驟：**
1. 在 Craft iOS App 中：設定 → Connected Apps → MCP → 產生 MCP 連結
2. 取得 URL 如 `https://mcp.craft.do/links/xxxx/mcp`
3. 寫入 Hermes config：
   ```yaml
   mcp_servers:
     craft:
       url: "https://mcp.craft.do/links/xxxx/mcp"
   ```
4. 執行 `hermes mcp test craft` → 瀏覽器開啟 OAuth 審批頁面
5. 在 Craft 中選取空間 → 按「Approve」

**已知工具（驗證通過）：**
| 工具 | 功能 |
|:-----|:------|
| `craft_read` | 讀取/搜尋 Craft 文件（支援分號批次） |
| `craft_write` | 寫入/更新文件（docs, blocks, daily notes, tasks） |
| `blocks_revert` | 復原上一次寫入 |

**適用場景：**
- 智研 WRITER 輸出直接寫入 Craft → 用戶 iOS 秒開
- 法律研究結果存入 Craft 文件庫
- 每次 session 關鍵結論自動歸檔

**與 GCP MCP 的差異：**
- Craft 不需要 token 刷新 cron（非短期效期 token）
- Craft 的 OAuth 審批在首次連線時一次完成，後續自動沿用
- 頁面重新整理（hermes chat 重啟）會自動反映新 MCP

詳細設定步驟見 `references/craft-mcp-setup.md`。

---

## 其他補充的 GCP MCP Server

Google 官方有 50+ MCP Server，以上 6 組是最常用的。其他值得關注的：

| 服務 | Endpoint | 備註 |
|------|----------|------|
| Cloud Monitoring | `monitoring.googleapis.com/mcp` | 查 metrics、alert |
| Cloud SQL | `sqladmin.googleapis.com/mcp` | 管理 MySQL/PostgreSQL |
| Cloud Asset Inventory | `cloudasset.googleapis.com/mcp` | 資源盤點 |
| GKE | `container.googleapis.com/mcp` | 管理 Kubernetes 叢集 |
| Firestore | `firestore.googleapis.com/mcp` | NoSQL 資料庫 |
| Bigtable | `bigtableadmin.googleapis.com/mcp` | 管理 Bigtable |
| Pub/Sub | `pubsub.googleapis.com/mcp` | 訊息佇列 |
