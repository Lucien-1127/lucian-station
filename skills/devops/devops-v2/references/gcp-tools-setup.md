# GCP 工具設定速查

## 專案與 VM 資訊格式

```
專案 ID:    gen-lang-client-0435318113
VM 名稱:    instance-20260606-124442
VM 機型:    n2d-standard-2 (2vCPU, 7.3GB RAM, 100GB pd-standard)
VM 區域:    asia-east1-a
服務帳號:   674313935168-compute@developer.gserviceaccount.com
```

## Compute Engine 服務帳號的限制

預設的 Compute Engine 服務帳號可以：
- ✅ `gcloud compute instances/list/snapshots/disks` — 管理運算資源
- ✅ `gcloud compute disks snapshot` — 建立快照
- ✅ `gcloud compute snapshots list` — 列出快照
- ✅ `gcloud logging write` — 寫入自訂日誌
- ✅ `gcloud logging logs list` — 查詢日誌

預設的 Compute Engine 服務帳號**不能**：
- ❌ `gcloud services enable` — 啟用 APIs（需要 Service Usage Admin 角色）
- ❌ `gcloud services list --enabled` — 列出已啟用 APIs（需要 Service Usage Viewer）
- ❌ `gcloud iam` — 管理 IAM 權限

## 需要使用者手動啟用的 APIs

在 GCP Console → APIs & Services → Library 搜尋並啟用：

| API | 關鍵字 | 用途 |
|:----|:-------|:------|
| Secret Manager API | `secretmanager.googleapis.com` | 儲存 API 金鑰 |
| Cloud Run API | `run.googleapis.com` | 容器化部署 |
| Cloud Workstations API | `workstations.googleapis.com` | 手機開發環境 |
| Cloud Scheduler API | `cloudscheduler.googleapis.com` | 受管排程（可選） |
| Cloud Pub/Sub API | `pubsub.googleapis.com` | 事件驅動（搭配 Scheduler） |

啟用連結格式：
```
https://console.cloud.google.com/apis/library/<API_NAME>?project=<PROJECT_ID>
```

## 確認哪些 APIs 已啟用

使用者可以從自己的瀏覽器執行：
```
https://console.cloud.google.com/apis/dashboard?project=<PROJECT_ID>
```

## GCP 現成功能（不需額外啟用）

### 每日磁碟快照

asia-east1 區域已存在 `default-schedule-1` 排程政策：
- 快照時間：每日 05:00 (UTC+8)
- 保留天數：14 天
- 自動清理：超出保留期自動刪除

查詢現有快照：
```bash
gcloud compute snapshots list --sort-by=~creationTimestamp --limit=5
```

### Cloud Logging

GCE VM 預設將系統 logs 送至 Cloud Logging。也可手動寫入自訂日誌：
```bash
gcloud logging write <LOG_NAME> "訊息" --severity=NOTICE
```

查詢日誌：
```bash
gcloud logging logs list
gcloud logging read "severity>=ERROR AND resource.type=gce_instance"
```

### Cloud Monitoring

無需啟用即可在 Console 看到 VM 基礎指標（CPU、記憶體、磁碟 IO）。

## Secret Manager 啟用後的設定流程

啟用 API 後，需要**授予 Compute Engine 服務帳號存取權**：

```bash
# 讓 VM 可以讀取 secrets
gcloud secrets add-iam-policy-binding <SECRET_NAME> \
  --member="serviceAccount:674313935168-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

存放金鑰：
```bash
gcloud secrets create <NAME> --data-file=<FILE>
gcloud secrets versions access latest --secret=<NAME>
```

## Cloud Run 啟用後的部署流程

```bash
# 啟用 API 後授予 Cloud Run 角色
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:674313935168-compute@developer.gserviceaccount.com" \
  --role="roles/run.admin"

# 建立 Dockerfile + 部署
gcloud run deploy <SERVICE_NAME> --source . --region=asia-east1 --allow-unauthenticated
```

## Cloud Workstations 設定流程

啟用 Workstations API 後，依序建立叢集 → 設定 → 工作站：

```bash
# 1. 建立叢集（耗時 3-5 分鐘）
gcloud workstations clusters create <CLUSTER_NAME> \
  --region=asia-east1 \
  --project=<PROJECT_ID>

# 2. 建立設定檔（需叢集 ready 後才能建立）
gcloud workstations configs create <CONFIG_NAME> \
  --cluster=<CLUSTER_NAME> \
  --region=asia-east1 \
  --machine-type=e2-standard-4 \
  --pd-disk-size=200 \
  --idle-timeout=7200 \
  --running-timeout=43200

# 3. 建立工作站
gcloud workstations create <WS_NAME> \
  --cluster=<CLUSTER_NAME> \
  --config=<CONFIG_NAME> \
  --region=asia-east1

# 4. 連線
# 瀏覽器打開：https://console.cloud.google.com/workstations/list?project=<PROJECT_ID>
# 點工作站名稱 → Start → 瀏覽器內 VS Code
```

**注意：**
- `pd-disk-size` 最小值 200GB（pd-standard 限制）
- `idle-timeout` 和 `running-timeout` 單位是秒（非 `7200m` 格式）
- 叢集佈建期間無法建立設定檔（`parent resource not in ready state`），需等幾分鐘
- `e2-standard-4` (4vCPU, 16GB) 約 $0.15/hr，閒置 2h 自動關閉

## 磁碟快照排程（如果需要手動建立）

已存在的 policy 不需要重複建立。若需要在不同區域建立：
```bash
gcloud compute resource-policies create snapshot-schedule <NAME> \
  --region=<REGION> \
  --max-retention-days=14 \
  --daily-schedule \
  --start-time=05:00

gcloud compute disks add-resource-policies <DISK_NAME> \
  --zone=<ZONE> \
  --resource-policies=<POLICY_NAME>
```
