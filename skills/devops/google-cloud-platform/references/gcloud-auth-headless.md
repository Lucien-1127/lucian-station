# GCP 帳號認證 — 無頭 VM 完整流程

## 背景

VM 上預設只有 Compute Engine 服務帳號（如 `*-compute@developer.gserviceaccount.com`），無法做需要使用者 OAuth token 的操作（Cloud Workstations 等）。需連結個人 Google 帳號。

## 完整流程（已驗證可行）

### 步驟 1：啟動背景 PTY

```bash
terminal(command="gcloud auth login --no-browser", background=true, pty=true, timeout=300)
```

### 步驟 2：回答 Y

```python
process(action="submit", data="Y", session_id="...")
```

### 步驟 3：擷取 remote-bootstrap URL 參數

從 process 輸出中取得 `state` 和 `code_challenge`，用 Python 構造瀏覽器可用的 OAuth URL：

```python
from urllib.parse import urlencode
params = {
    'response_type': 'code',
    'client_id': '32555940559.apps.googleusercontent.com',
    'redirect_uri': 'http://localhost:8085/',        # 必須用 HTTP
    'scope': 'openid https://www.googleapis.com/auth/userinfo.email ...',
    'state': '<從 remote-bootstrap 擷取>',
    'access_type': 'offline',
    'code_challenge': '<從 remote-bootstrap 擷取>',
    'code_challenge_method': 'S256',
}
url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
```

### 步驟 4：用戶在手機瀏覽器完成登入

用戶打開 URL → 登入 → 會被重導向到 `http://localhost:8085/?state=...&code=...`（手機無法載入，但網址列有 code）。

### 步驟 5：餵回應 URL 給 gcloud

```python
process(action="submit", 
        data="https://localhost:8085/?state=...&code=4/0Ad...",
        session_id="...")
```

成功輸出：`You are now logged in as [user@gmail.com].`

## 🔴 關鍵陷阱：HTTP vs HTTPS

**問題**：Google OAuth 只接受 `http://localhost:8085/` 作為 redirect_uri（此 client 未註冊 HTTPS localhost）。但 gcloud 本地 parse 回應 URL 時強制檢查 HTTPS，報 `(insecure_transport) OAuth 2 MUST utilize https.`。

**唯一解法**：OAuth URL 用 `http://` redirect_uri（讓 Google 接受），但回應 URL 餵給 gcloud 時**前綴改 `https://`**（讓 gcloud parse 通過）。gcloud 在 token exchange 階段會用正確的 `http://` redirect_uri。

| OAuth URL redirect_uri | 回應 URL 前綴 | 結果 |
|------------------------|-------------|------|
| `http://localhost:8085/` | `http://` | ❌ gcloud 報 `insecure_transport` |
| `https://localhost:8085/` | `https://` | ❌ Google 報 `redirect_uri_mismatch` |
| `http://localhost:8085/` | `https://` | ✅ 唯一成功路徑 |

## ⚠️ URL Scope 編碼

Safari 會誤解 scope 參數中的 `+` 和 `:`。必須用 `urllib.parse.urlencode` 正確編碼（`https%3A%2F%2F...`）。

## 驗證

```bash
gcloud auth list                    # 確認 hsieh89t@gmail.com 為 ACTIVE
gcloud projects get-iam-policy ...  # 確認 roles/owner 權限
```
