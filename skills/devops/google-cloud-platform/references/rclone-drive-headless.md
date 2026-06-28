# rclone Google Drive 無頭 VM 認證流程

## 概要

在無頭 VM（無瀏覽器）上將 rclone 連接到個人 Google Drive 的流程。
與 gcloud auth login --no-browser 的 remote-bootstrap 問題同類。

## 核心技巧

**rclone 啟動本地 server 監聽 127.0.0.1:53682 → 用戶手機打開 OAuth URL → 複製跳轉網址 → curl 餵給本地 server**

## 完整步驟

### 1. 安裝 rclone
```bash
curl -O https://downloads.rclone.org/rclone-current-linux-amd64.deb
sudo dpkg -i rclone-current-linux-amd64.deb
rm rclone-current-linux-amd64.deb
```

### 2. 啟動授權（背景 PTY）
```bash
# 背景 PTY 啟動（rclone 會在 127.0.0.1:53682 開本地 HTTP server）
terminal(command="rclone authorize \"drive\"", background=true, pty=true, notify_on_complete=true)
```

### 3. 從 process output 提取 state
```bash
# poll 看 output，找到 state 參數
process(action="poll", session_id="...")
# → http://127.0.0.1:53682/auth?state=E91abPaI-nB5wGmuTfs0HA
```

### 4. 生成 OAuth URL 給用戶
```python
from urllib.parse import urlencode
params = {
    'client_id': '202264815644.apps.googleusercontent.com',  # rclone 預設
    'redirect_uri': 'http://127.0.0.1:53682/',
    'response_type': 'code',
    'scope': 'https://www.googleapis.com/auth/drive',
    'state': '<從 rclone 提取的 state>',
    'access_type': 'offline',
    'prompt': 'consent',
}
print('https://accounts.google.com/o/oauth2/auth?' + urlencode(params))
```

### 5. 用戶在手機打開 URL → 登入 Google → 跳轉到 127.0.0.1:53682（失敗）
- 用戶複製跳轉失敗的完整網址（含 `?state=...&code=4/0Ad...`）
- 貼回來

### 6. curl 給 rclone 本地 server
```bash
curl -s "http://127.0.0.1:53682/?state=...&code=4/0Ad..."
# → 回傳 <h1>Success!</h1>
```

### 7. 建立 config
```ini
[gdrive]
type = drive
scope = drive
token = {"access_token":"...","token_type":"Bearer","refresh_token":"1//0eS...","expiry":"2026-06-27T11:39:29Z"}
```

### 8. 寫入 ~/.config/rclone/rclone.conf
```bash
# 直接 write_file 或
rclone config create gdrive drive token='<JSON>'
```

### 9. 驗證
```bash
rclone lsd gdrive:
# → 列出 Google Drive 目錄結構
```

## 注意事項

- rclone 預設 client_id = `202264815644.apps.googleusercontent.com`
- 只能用 `http://127.0.0.1:53682/`（Google OAuth 不接受 HTTPS localhost）
- refresh_token 會自動續約，不需重複認證
- rclone v1.74+ 支援此流程

## 與 gcloud auth 的差異

| 項目 | gcloud auth | rclone authorize |
|------|------------|-----------------|
| 本地 server port | 8085 | 53682 |
| client_id | 32555940559 | 202264815644 |
| 餵 code 方式 | process submit | curl |
| HTTPS 包裝 | 需要（gcloud 強制檢查） | 不需要（rclone 接受 HTTP） |
