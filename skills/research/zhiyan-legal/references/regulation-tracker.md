# regulation_tracker — 法規異動自動追蹤引擎

> 移植自 [ksliao0314/law-tracker](https://github.com/ksliao0314/law-tracker)（MIT License）
> Node.js → Python 重寫，整合進智研 AI 法律工作站

---

## 資料庫結構（data/regulation_tracker.db）

```sql
-- 追蹤中的法規
CREATE TABLE tracked_regulations (
    pcode TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT DEFAULT '',
    baseline_version TEXT,       -- 上次確認的版本日期 (YYYYMMDD)
    baseline_date TEXT,           -- 設定 baseline 的日期
    frequency_days INTEGER DEFAULT 7,
    last_checked_at TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

-- 查核歷史
CREATE TABLE check_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pcode TEXT NOT NULL,
    checked_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    old_version TEXT,
    new_version TEXT,
    status TEXT NOT NULL,         -- unchanged / changed / newly_tracked / missing
    summary_json TEXT,
    FOREIGN KEY (pcode) REFERENCES tracked_regulations(pcode)
);

-- 法規索引快取（每日更新）
CREATE TABLE moj_cache (
    key TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
```

## 條文快取（data/articles/<pcode>.json）

```json
{
  "20220504": {
    "1": "為防制毒品危害，維護國民身心健康，制定本條例。",
    "2": "本條例所稱毒品，指具有成癮性、濫用性…"
  },
  "_oldver": {
    "1": "...",
    "2": "..."
  }
}
```

- 版本鍵 = YYYYMMDD（修正日期），取自 moj.gov.tw API 的 `LawModifiedDate`
- `_oldver` = 從 LawOldVer 網頁抓取的歷史版本
- 保留最近 8 個版本

## API 端點

| 端點 | 格式 | 說明 |
|------|------|------|
| `law.moj.gov.tw/api/Ch/Law/JSON` | ZIP → JSON | 法律完整索引（含條文） |
| `law.moj.gov.tw/api/Ch/Order/JSON` | ZIP → JSON | 命令完整索引（含條文） |
| `law.moj.gov.tw/LawClass/LawOldVer.aspx?pcode=X0000` | HTML | 歷史條文（備援） |

ZIP 結構：內含單一 JSON 檔案（UTF-8 BOM），陣列格式，每筆含 `LawURL`、`LawName`、`LawLevel`、`LawModifiedDate`、`LawArticles`、`LawHistories`。

## LCS 逐字元比對

`diff_articles()`: 比對新舊條文，分類為 modified/add/remove
`lcs_diff()`: 單一條文內的字元級差異

LCS 演算法：O(n*m) DP，字元級。文字總長 > 6000 時退回全文級別比對（不逐字）。

Word 輸出格式：
- 三欄表格：修正條文（新）| 現行條文（舊）| 備註
- 新增文字：紅底線（RGB #C0392B）
- 刪除文字：紅刪除線（RGB #C0392B）

## 整合要點

1. **cron 排程**：`0 9 * * *`，執行 `python3 scripts/regulation_check.py`
2. **🕊️ 通知原則**：無異動時不發任何訊息，只有偵測到法規異動才推播通知。cron 任務的 prompt 應檢查 exit code：0=安靜，1=主動通知，2=回報錯誤
3. **同步時機**：每日首次查核前自動下載；同一天不重複
4. **試算模式**：`check_one(pcode, official=False)` 測試比對但不更新 baseline
5. **路徑設定**：資料目錄預設 `data/`（專案根目錄下），可透過 `data_dir` 參數指定

### 套用新法規到追蹤清單

```bash
# 加入單一法規
python3 -m src.zhiyan_legal.regulation_tracker add --pcode C0000008 --frequency 7

# 加入所有預設法規
python3 -m src.zhiyan_legal.regulation_tracker track-all-default
```

### 產出 Word 對照表

```bash
# 單一法規（自動匯出到 data/exports/）
python3 -m src.zhiyan_legal.regulation_tracker diff --pcode C0000008

# 指定匯出路徑
python3 -m src.zhiyan_legal.regulation_tracker diff --pcode C0000008 --output ./對照表.docx

# 批次產出所有有異動的法規
python3 -m src.zhiyan_legal.regulation_tracker diff-all
```

## 錯誤恢復

| 錯誤情境 | 行為 |
|---------|------|
| moj.gov.tw API 500 | 沿用前一日快取索引 |
| LawOldVer 網頁無法連線 | 僅輸出當前版本條文（無舊版比對） |
| 條文快取檔案損毀 | 跳過該法規，下次 sync 重新建立 |
| 同一天 sync 多次 | 只下載一次（fresh date 檢查） |

## FastAPI Web API（regulation_api.py）

法規異動監控有 REST API 後端，用 FastAPI 包裝。所有端點回傳 JSON，自帶 Swagger UI。

### 啟動方式

```bash
# 開發模式（auto-reload）
cd ~/zhiyan-legal
PYTHONPATH=src uvicorn zhiyan_legal.regulation_api:app --host 127.0.0.1 --port 7850 --reload

# 生產模式（systemd 常駐）
sudo systemctl start zhiyan-api

# 快速腳本（有 crontab @reboot 時自動跑）
~/zhiyan-legal/scripts/start_api.sh
```

⚠️ uvicorn 在 Hermes venv 下，systemd 路徑必須指定 venv python，不可用 `/home/hsieh89t_gmail_com/.local/bin/uvicorn`（之前踩過 203/EXEC 坑）。

### API 端點一覽

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/status` | 系統狀態 |
| POST | `/api/sync?force=true` | 手動同步法規索引 |
| POST | `/api/check?official=true` | 執行查核所有追蹤法規 |
| GET | `/api/tracked` | 列出所有追蹤法規 |
| POST | `/api/tracked/add?pcode=...&frequency=7` | 加入追蹤法規 |
| DELETE | `/api/tracked/{pcode}` | 移除法規追蹤 |
| GET | `/api/history?days=7` | 查核歷史 |
| GET | `/api/search?keyword=毒品` | 搜尋法規名稱（關鍵字需 URL 編碼） |
| GET | `/api/diff/{pcode}?format=json` | 新舊條文對照（json 或 docx） |
| GET | `/api/diff/all` | 批次產出 Word 對照表 |

Swagger UI 在 `http://localhost:7850/docs`。

### 注意事項

- 搜尋端點中文關鍵字需 URL 編碼，否則 uvicorn 回 Invalid HTTP request received
- diff JSON 格式摘要化（保留前 300 字元）；`format=docx` 下載完整 Word
- 首次請求 lazy-load 索引快取，約需 1-2 秒

### systemd 常駐

```ini
[Unit]
Description=法規異動監控 API
After=network-online.target
[Service]
Type=simple
User=hsieh89t_gmail_com
WorkingDirectory=/home/hsieh89t_gmail_com/zhiyan-legal
Environment=PYTHONPATH=/home/hsieh89t_gmail_com/zhiyan-legal/src
ExecStart=/home/hsieh89t_gmail_com/.hermes/hermes-agent/venv/bin/python3 -m uvicorn zhiyan_legal.regulation_api:app --host 127.0.0.1 --port 7850
Restart=on-failure
RestartSec=5
```

```bash
sudo systemctl enable --now zhiyan-api  # 開機自啟
journalctl -u zhiyan-api -f             # 看 log
```

### Caddy 反向代理

Caddyfile 在 `~/zhiyan-legal/Caddyfile`。部署方式：

```bash
sudo cp ~/zhiyan-legal/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

**本機模式**（無 HTTPS）：
```
127.0.0.1 {
    reverse_proxy 127.0.0.1:7850
}
```

**Tailscale 模式**（手機可用，加密通道免設定）：
```
http://100.68.234.34:80 {
    reverse_proxy 127.0.0.1:7850
}
```
手機開瀏覽器連 `http://100.68.234.34/docs` 即可用 Swagger UI。

**網域模式**（自動 Let's Encrypt TLS）：
```
law.你的網域.tw {
    reverse_proxy 127.0.0.1:7850
}
```

### 前端開發方向

目前只有 API 後端。未來可做 PWA：
- 儀表板：法規卡片（綠燈/黃燈/紅燈）
- 異動歷史時間軸
- 內嵌 diff viewer
- 手機桌面捷徑（PWA manifest + Service Worker）
- 推送通知

---

## 移植來源對照

| law-tracker (Node.js) | regulation_tracker (Python) |
|----------------------|-----------------------------|
| `server.mjs` (HTTP + scheduler) | 不用 — 由 Hermes cron 排程 |
| `server.mjs:refreshIndex()` | `RegulationTracker.sync_index()` |
| `server.mjs:buildDiff()` | `regulation_diff.build_diff_report()` |
| `server.mjs:lcsDiffS()` | `regulation_diff.lcs_diff()` |
| `server.mjs:asOfDate()` | `RegulationTracker._as_of_date()` |
| `server.mjs:parseMojZip()` | `_parse_moj_zip()` |
| `data/groups.json` | `regulation_tracker.db` (SQLite) |
| `data/articles/<pcode>.json` | 同左（格式相容） |
| `data/pcode_all.json` | 不用 — 直接下載完整索引 |
