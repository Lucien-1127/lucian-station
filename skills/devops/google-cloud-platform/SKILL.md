---
title: Google Cloud Platform 管理
name: google-cloud-platform
category: devops
description: GCP 專案管理：API 啟用、Secret Manager、Cloud Run、Logging、快照排程、服務帳號權限
---

# GCP 雲端管理

## 先確認環境

```bash
# 當前專案與帳號
gcloud config list

# 已啟用的 APIs
gcloud services list --enabled

# Compute Engine 服務帳號角色
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:*-compute@"
```

# 建立 Service Account 與 Key

```bash
gcloud iam service-accounts create <name> \
  --display-name="Display Name" \
  --project=$PROJECT_ID

# ⚠️ 陷阱：SA 剛建立時 IAM 綁定必失敗
# gcloud iam service-accounts create 是 eventually consistent（通常 5-30 秒），
# 綁定 roles/editor / secretmanager.admin 時若馬上執行，100% 失敗：
#   ERROR: INVALID_ARGUMENT: Service account X does not exist.
# 解決：補一次 gcloud projects add-iam-policy-binding（等待 5-10 秒再執行）即可，
#       gcloud 本身會在 SA 就緒後成功，不要誤會成是 project 或 permission 問題。

# 建立 JSON Key（一次性，之後無法從 GCP Console 再次下載）
gcloud iam service-accounts keys create <output-path>.json \
  --iam-account=<name>@<project>.iam.gserviceaccount.com \
  --project=$PROJECT_ID
```

### 雞蛋問題：Service Usage API 未啟用

`gcloud services enable` 本身需要 `serviceusage.googleapis.com` 已啟用。如果這個 API 沒開，所有 gcloud API 操作都會失敗。

**解法**：由代理透過瀏覽器導向啟用頁面，或請用戶手機操作：

```
https://console.developers.google.com/apis/api/serviceusage.googleapis.com/overview?project={PROJECT_ID}
```

### 使用者偏好：避免給手動連結

此用戶偏好「幫忙自動化」— 當 gcloud 權限不足時，先嘗試以下方式再請用戶協助：

1. 用瀏覽器工具導向啟用頁面（`browser_navigate`）
2. 走 `gcloud auth login --no-browser`（背景 PTY），從 remote-bootstrap URL 擷取 OAuth 參數，補 `redirect_uri` 後讓用戶在手機開啟。詳細流程見下方「GCP 帳號認證」章節。
3. 若 passkey 擋住，用戶手機上會跳出 Face ID 通知，告知用戶「請在手機上確認」
4. 以上都失敗才提供手動連結

啟用後才能從 gcloud 繼續：

```bash
gcloud services enable secretmanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable workstations.googleapis.com
gcloud services enable pubsub.googleapis.com
```

### 注意事項
- Compute Engine 預設服務帳號為 `roles/editor`，權限很廣但無法啟用 serviceusage API
- Google 帳號若啟用 passkey/2FA，瀏覽器自動登入會被擋，需用戶手機確認
- `gen-lang-client-` 前綴的專案為自動建立，可能跳過預設 API 啟用

## Secret Manager（金鑰管理）

```bash
# 從 .env 逐行存入金鑰
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  name=$(echo "$key" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
  echo -n "$value" | gcloud secrets create "${name}" \
    --data-file=- --project=${PROJECT_ID} --replication-policy=automatic
done < <(grep -v '^#' .env | grep '=')

# 讀取金鑰
gcloud secrets versions access latest --secret=<secret-name>

# 程式碼中取用（需 google-cloud-secret-manager pip 套件）
# 或使用專案中的 scripts/get_secret.py
python scripts/get_secret.py zhiyan-api-key
```

Compute Engine 服務帳號的 access token 可用於 secretmanager API 呼叫，但 workstations API 需要使用者 OAuth token。

## Cloud Logging

```bash
# 寫入日誌（注意：MESSAGE 是必要參數，不是 pipe）
gcloud logging write <log-name> "訊息內容" --severity=NOTICE

# JSON 結構化日誌（也需要 MESSAGE 參數）
gcloud logging write <log-name> '{"event":"crawler","status":"ok"}' --payload-type=json

# 查詢日誌
gcloud logging read "severity>=ERROR" --limit=10

# 查特定資源
gcloud logging read "resource.type=gce_instance AND severity>=WARNING"
```

GCE 預設會送系統 logs 到 Cloud Logging，不需額外設定。

## 磁碟快照（備份）

```bash
# 手動快照
gcloud compute disks snapshot <disk-name> \
  --zone=<zone> --snapshot-names=<name>-$(date +%Y%m%d)

# 查看快照排程
gcloud compute resource-policies list --filter="snapshotSchedule"
gcloud compute resource-policies describe <policy-name> --region=<region>

# 列出最近快照
gcloud compute snapshots list --sort-by=~creationTimestamp --limit=5

# 刪除快照
gcloud compute snapshots delete <snapshot-name>
```

排程格式範例（保留 14 天、每天 05:00）：
```json
{
  "snapshotSchedulePolicy": {
    "schedule": {"dailySchedule": {"daysInCycle": 1, "startTime": "05:00"}},
    "retentionPolicy": {"maxRetentionDays": 14, "onSourceDiskDelete": "KEEP_AUTO_SNAPSHOTS"}
  }
}
```

## 磁碟快照 — 清理與成本控制\n\n### 找出孤兒快照（屬於已刪除 VM 的快照）\n\n```bash\n# 列出所有快照與來源磁碟\ngcloud compute snapshots list --format=\"table(name, sourceDisk, creationTimestamp, storageBytes, status)\"\n\n# 對照目前存在的磁碟\ngcloud compute disks list --format=\"value(name)\"\n\n# 不在現有磁碟清單中的 sourceDisk = 孤兒快照，安全刪除\n```\n\n### 刪除孤兒快照\n\n```bash\n# 列出孤兒名稱後一次刪除\ngcloud compute snapshots delete <name1> <name2> ... --quiet\n```\n\n> ⚠️ 快照儲存計費 $0.026/GB/月。舊 VM 刪掉但快照沒刪 = 每個月白燒錢。增量快照雖小，積少成多。\n\n### 關閉自動快照排程\n\n```bash\n# 查磁碟掛了哪些資源政策\ngcloud compute disks describe <disk-name> --zone=<zone> --format=\"value(resourcePolicies)\"\n\n# 移除自動快照排程（不刪快照本身）\ngcloud compute disks remove-resource-policies <disk-name> \\\n  --resource-policies=<policy-name> --zone=<zone> --quiet\n```\n\n### VM 成本估算\n\n```bash\n# 查機器類型與區域\ngcloud compute instances list --format=\"table(name, zone, machineType, status)\"\n\n# 查磁碟類型和大小\ngcloud compute disks list --format=\"yaml(name, sizeGb, type)\"\n```\n\n| 資源 | 計價方式 |\n|------|------|\n| n2d-standard-2 | $0.0926/hr → 持續使用折扣 30% → ~$47/月 |\n| pd-standard 100GB | $0.04/GB/月 → $4/月 |\n| 靜態 IP（掛執行中 VM） | 免費 |\n| 靜態 IP（未使用） | ~$7/月 |\n| 快照 | $0.026/GB/月 |\n| 網路輸出 | $0.12/GB（0-1TB） |\n\n> 💡 **關機時 VM 不收費，但靜態 IP 開始計費**。若長期不用，釋放靜態 IP 或改用 ephemeral IP。\n\n## Cloud Run（容器部署）

專案中的 `docker/Dockerfile` 和 `docker/api_server.py` 為可參考的實作範例。

```bash
# 打包與部署
gcloud run deploy <service-name> --source . --region=asia-east1

# 需要 Dockerfile
```

## GCP MCP Servers（AI Agent 工具層）

Google 已推出 50+ 個**全託管 remote MCP Server**，讓 Hermes/Claude/任何 MCP client 透過 HTTPS 直接操作 GCP 服務，不需裝本地套件。

### 已啟用的 GCP MCP Servers

| Server | Endpoint | 工具 |
|--------|----------|------|
| **BigQuery** | bigquery.googleapis.com/mcp | 查資料表、執行 SQL |
| **Cloud Storage** | storage.googleapis.com/storage/mcp | 管理 bucket、讀寫檔案 |
| **Cloud Run** | run.googleapis.com/mcp | 查 deployments、logs |
| **Cloud Logging** | logging.googleapis.com/mcp | 查錯誤日誌 |
| **Compute Engine** | compute.googleapis.com/mcp | 查 VM 狀態、規格 |
| **IAM** | iam.googleapis.com/v1/mcp | 查權限政策 |

### 設定方式

GCP MCP 為 remote HTTP 類型，寫在 `mcp_servers:` 區塊。使用 `${ENV_VAR}` 代換 token：

```yaml
mcp_servers:
  gcp-bigquery:
    url: "https://bigquery.googleapis.com/mcp"
    headers:
      Authorization: Bearer ${GCP_MCP_TOKEN}"
    enabled: true
    timeout: 120
```

### 認證方式

GCP MCP 使用 IAM OAuth2 認證（不支援 API key）。Token 來源：

1. **GCE VM（有服務帳號）** — metadata server token endpoint + Header `Metadata-Flavor: Google`
2. **ADC** — `gcloud auth application-default print-access-token`
3. **OAuth Client ID** — 在 GCP Console 註冊，配合 Hermes `auth: oauth`（需互動授權）

**限制**：GCP MCP 不支援 OAuth 動態客戶端註冊（DCR），無法直接用 `auth: oauth`。

### Token 自動刷新（GCE VM）

Token 有效 1 小時，需定期刷新。用 no_agent watchdog 腳本每 30 分鐘更新 .env（`scripts/refresh-gcp-mcp-token.py`）：

```python
import urllib.request, json, re
from pathlib import Path
req = urllib.request.Request(
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
    headers={"Metadata-Flavor": "Google"}
)
token = json.loads(urllib.request.urlopen(req, timeout=5).read())["access_token"]
env_path = Path.home() / ".hermes" / ".env"
content = env_path.read_text()
new_content = re.sub(r"^GCP_MCP_TOKEN=.*", f"GCP_MCP_TOKEN={token}", content, flags=re.MULTILINE)
if new_content == content:
    new_content = content.rstrip() + f"\nGCP_MCP_TOKEN={token}\n"
env_path.write_text(new_content)
```

Cron: `*/30 * * * *`, no_agent=True（成功安靜，僅失敗通知）。

config 路徑：`mcp_servers` 寫在 `~/.hermes/config.yaml` 頂層（非 profile config）。

## Cloud Workstations（雲端 IDE）

建立工作站需要三步：叢集 → 設定 → 工作站。

```bash
# 1. 建立叢集（一次，耗時 2-5 分鐘）
gcloud workstations clusters create <cluster-name> \
  --region=asia-east1

# 2. 建立設定檔（一次）
gcloud workstations configs create <config-name> \
  --cluster=<cluster-name> \
  --region=asia-east1 \
  --machine-type=e2-standard-4 \
  --pd-disk-size=200 \
  --idle-timeout=7200 \
  --running-timeout=43200

# 3. 建立工作站
gcloud workstations create <ws-name> \
  --cluster=<cluster-name> \
  --config=<config-name> \
  --region=asia-east1
```

### 注意事項
- `--pd-disk-size` 最小 200GB
- `--idle-timeout` 和 `--running-timeout` 單位為秒（7200s = 2h）
- `--machine-type` 是 config 的參數，不是 workstation create 的參數
- Cluster 必須 READY 才能建立 config
- 連線：https://console.cloud.google.com/workstations/list?project=PROJECT_ID

## Cloud Scheduler（排程觸發）

### 先建立 Pub/Sub Topic

Cloud Scheduler 的 Pub/Sub 目標需要先有 topic：

```bash
gcloud pubsub topics create <topic-name>
```

### 建立排程

```bash
gcloud scheduler jobs create pubsub <job-name> \
  --schedule="0 * * * *" \
  --topic=<topic-name> \
  --message-body='{"mode":"daily"}'
```

## GCP 帳號認證（gcloud auth login）

### 在無頭 VM（無瀏覽器）上認證個人帳號

VM 上預設只有 Compute Engine 服務帳號。個人帳號認證的完整流程、遠端啟動 URL 的陷阱、HTTPS 包裝技巧，詳見 `references/gcloud-auth-headless.md`。

```bash
# VM 上的服務帳號只能做基本 API 操作
gcloud auth list
# → * 674313935168-compute@developer.gserviceaccount.com

# 需連結個人 Google 帳號
gcloud auth login --no-browser
```

### remote-bootstrap 限制

現代 gcloud（≥372.0.0）的 `--no-browser` 不再使用舊的 OOB 驗證碼流程（已棄用），而是輸出一個 `gcloud auth login --remote-bootstrap="<URL>"` 指令，**要求在有瀏覽器的機器上執行 gcloud**。這在純手機環境無法直接使用。

### 解法：手動 OAuth URL + PTY 背景進程

```bash
# 1. 在背景 PTY 啟動 gcloud auth login
terminal(command="gcloud auth login --no-browser", background=true, pty=true)

# 2. 回答 Y（process submit）
process(action="submit", data="Y", session_id="...")

# 3. 從 remote-bootstrap URL 中提取 OAuth 參數，補上 redirect_uri
#    remote-bootstrap 的 URL 缺少 redirect_uri 參數
python3 -c "
from urllib.parse import urlencode
params = {
    'response_type': 'code',
    'client_id': '32555940559.apps.googleusercontent.com',
    'redirect_uri': 'http://localhost:8085/',
    'scope': 'openid https://www.googleapis.com/auth/userinfo.email ...',
    'state': '<從 remote-bootstrap 擷取>',
    'access_type': 'offline',
    'code_challenge': '<從 remote-bootstrap 擷取>',
    'code_challenge_method': 'S256',
}
print('https://accounts.google.com/o/oauth2/auth?' + urlencode(params))
"

# 4. 用戶在手機瀏覽器打開 URL，登入後複製重定向網址
#    （會導向 localhost:8085 失敗，但網址列有 state 和 code 參數）

# 5. 將重定向網址貼回 gcloud（process submit）
process(action="submit", 
       data="http://localhost:8085/?state=...&code=4/0Ad...",
       session_id="...")
```

⚠️ **URL scope 編碼陷阱**：Safari 會誤解 scope 參數中的 `+` 和 `:`，必須用 `urllib.parse.urlencode` 正確編碼（`https%3A%2F%2F...`）。

### 🔴 關鍵陷阱：gcloud 拒絕 HTTP redirect URL

這是無頭 VM 上 gcloud 認證最棘手的 bug。流程如下：

1. 用戶在手機瀏覽器打開 OAuth URL（redirect_uri=`http://localhost:8085/`）
2. Google 登入成功，頒發 code，重導向到 `http://localhost:8085/?state=...&code=4/0Ad...`
3. 用戶複製重導向 URL 給代理
4. 代理 `process submit` 給 gcloud
5. **gcloud 報錯：`(insecure_transport) OAuth 2 MUST utilize https.`**

原因：gcloud 在本地 parse 回應 URL 時強制檢查 HTTPS。

**但 Google OAuth 只接受 `http://localhost:8085/`** 的 redirect_uri（這個 client 未註冊 HTTPS localhost），改成 `https://` 會報 `redirect_uri_mismatch`。

**唯一可行的解法：HTTP 申請 code + HTTPS 包裝回應**

```
# Google OAuth URL → 使用 http://localhost:8085/（Google 接受）
# 但回應 URL 餵給 gcloud 時 → 改前綴為 https://
process(action="submit", 
       data="https://localhost:8085/?state=...&code=...",
       session_id="...")
```

這樣 gcloud 的本地 parse 通過（看到 `https://`），而 token exchange 時 gcloud 會用正確的 `http://localhost:8085/` 去換 token（gcloud 內部是從 remote-bootstrap 參數重建 redirect_uri，不是從用戶輸入提取）。

> ⚠️ 這需要用戶配合操作兩次授權（第一次嘗試 http 會報 insecure_transport），第二次才知道要包裝 https。完整操作筆錄與 Python 程式碼範例見 `references/gcloud-auth-headless.md`。

## Hermes 整合注意事項（API Key / 憑證管理）

本機 Hermes Agent 與 GCP 服務互動時的常見陷阱。

### 🔴 寫入 .env 的陷阱

```bash
# ❌ 千萬不要用 bash echo/heredoc 寫 Key 到 .env
echo "GEMINI_API_KEY=*** >> .env  # 安全遮罩會攔截，寫入假值 "***KEY}"

# ✅ 正確做法：一律用 hermes config set
hermes config set providers.gemini.api_key "AQ.Ab8RN6..."
```

### 多 Key 輪流池（Credential Pool）

免費 API（如 Gemini）配額用完時，用 credential pool 自動切換不同帳號的 Key：

```bash
hermes auth add --type api-key --api-key "KEY" --label "gemini-key-N" gemini
hermes auth list gemini  # ← 箭頭標示當前使用中的 Key
```

池中 Key 遇到 429 會自動標記 `exhausted` 並切換下一個。配額恢復後 `hermes auth reset gemini` 重置。

### 新增 Provider 時務必驗證模型名稱

不要猜測模型名稱。先查 API 的 model list，確認名稱後再設定 fallback / auxiliary。

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | jq '.models[].name'
# 範例正確名稱：gemini-2.5-flash, gemini-3-pro-preview
```

## Google Drive 備份（rclone）

VM 設定備份到個人 Google Drive 的完整流程，含無頭 OAuth 認證，詳見 `references/rclone-drive-headless.md`。

```bash
# 手動執行備份
bash ~/.hermes/scripts/vm_backup.sh

# 備份內容：Hermes Agent 設定 + 專案 + .bashrc/.ssh + 套件清單 + 系統設定
# 目標：Google Drive /vm-backup/vm-backup-YYYYMMDD-HHMMSS.tar.gz
```

## 常見問題

| 問題 | 原因 | 解決 |
|:-----|:------|:------|
| `gcloud services enable` 失敗 | Service Usage API 未啟用 | 先用瀏覽器開 console 啟用 serviceusage |
| 無法登入 GCP Console | Google passkey/2FA | 用戶手機確認，或使用 remote-bootstrap + 手動 OAuth URL |
| `gcloud auth login --no-browser` 不給驗證碼 | 新 gcloud 改用 remote-bootstrap，已棄用 OOB | 參考上方「remote-bootstrap 限制」的解法 |
| OAuth URL 在 Safari 報 `invalid_scope` | scope 參數未正確 URL 編碼 | 用 `urllib.parse.urlencode` 編碼 scope |
| 🔴 gcloud 報 `(insecure_transport)` | gcloud 本地 parse 要求 HTTPS，但 Google 只接受 HTTP redirect_uri | **HTTP 拿 code + HTTPS 包裝回應**（詳見上方陷阱） |
| gcloud 報 `(redirect_uri_mismatch)` | Google OAuth URL 用了 `https://` redirect_uri | 改回 `http://localhost:8085/`，回應時再用 `https://` 包裝 |
| `PERMISSION_DENIED` | 服務帳號權限不足 | 檢查 IAM roles，預設 editor 但不含某些 API |
| 快照上傳慢 | pd-standard 100GB 以上 | pd-standard 快照時間依磁碟大小，30s+ 正常 |
