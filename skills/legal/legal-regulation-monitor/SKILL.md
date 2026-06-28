---
name: legal-regulation-monitor
description: 法規異動全端監控 — 檢測引擎(baseline比對) + 新舊條文對照(LCS+Word) + REST API(FastAPI) + Flutter Android App
version: 2.0.0
author: Lucian
platforms: [linux]
---

# 法規異動自動監控

## 適用場景

- 專案需要自動追蹤特定法規的最新修正狀態
- 法規版本異動時自動通知（推播到 Telegram / Email）
- 定期產出修法異動報告
- 整合入法學 AI 系統做引用驗證

## 資料源

| 來源 | 端點 | 內容 |
|------|------|------|
| 全國法規資料庫·法律 | `https://law.moj.gov.tw/api/Ch/Law/JSON` | 法律完整索引 + 條文 |
| 全國法規資料庫·命令 | `https://law.moj.gov.tw/api/Ch/Order/JSON` | 命令完整索引 + 條文 |
| 歷史法規（舊版條文） | `https://law.moj.gov.tw/LawClass/LawOldVer.aspx?pcode={PCODE}` | 逐版條文全文 |
| 沿革頁面 | `https://law.moj.gov.tw/LawClass/LawHistory.aspx?pcode={PCODE}` | 修法沿革文字 |

註：Law + Order API 回傳的是 ZIP 壓縮檔，內含單一 JSON 檔案。

### 資料格式（API JSON）

ZIP 內的 JSON 陣列，每筆包含：
```
LawName       — 法規名稱
LawURL        — 含 pcode 參數的網址
LawLevel      — 「法律」或「命令」
LawCategory   — 類別
LawModifiedDate — 最新修正日期（YYYYMMDD 字串）
LawEffectiveDate — 施行日期
LawAbandonNote — 廢止註記（含「廢」字表示已廢止）
LawHistories  — 沿革文字（含中華民國曆日期）
LawArticles   — 條文陣列
```

## 核心演算法

### Baseline 版本比對

```
每次查核時：
  1. 下載最新索引（同一天不重複）
  2. 對每部追蹤法規：
     a. 讀取上次記錄的 baseline_version（YYYYMMDD）
     b. 查詢索引中當前 modifiedDate
     c. modifiedDate > baseline_version → 有異動
     d. 正式查核時更新 baseline_version
```

### As-of 日期計算

從 LawHistories（沿革）解析各版修正日期：

```
「中華民國一百零六年六月十四日」→ 20170614
```

解析步驟：
1. 正則提取「中華民國 X年 Y月 Z日」
2. 國字轉阿拉伯數字（一→1, 二→2, … 十/百/千 位數處理）
3. 民國年 + 1911 → 西元年
4. 所有版本日期升冪排序
5. 取 ≤ 目標日期的最大日期 = as-of 版本

退回機制：沿革解析不到時，退回到索引的 modifiedDate（若 ≤ 基準日）。

## 資料庫設計

```sql
-- 追蹤清單
CREATE TABLE tracked_regulations (
    pcode TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT DEFAULT '',
    baseline_version TEXT,       -- 上次確認的版本 YYYYMMDD
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
    status TEXT NOT NULL,        -- unchanged / changed / newly_tracked / missing / abolished
    summary_json TEXT
);

-- 索引快取（避免每日重複下載）
CREATE TABLE moj_cache (
    key TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
```

## 實施步驟

### 1. 建立核心引擎

Python 模組：`src/zhiyan_legal/regulation_tracker.py`

核心類別 `RegulationTracker` 提供：

| 方法 | 說明 |
|------|------|
| `sync_index(force=False)` | 下載或快取最新法規索引 |
| `add_tracking(pcode, name, frequency_days)` | 加入追蹤法規 |
| `remove_tracking(pcode)` | 移除法規追蹤 |
| `check_one(pcode, official=True)` | 查核單一法規 |
| `check_all(official=True)` | 查核所有追蹤法規 |
| `search_law(keyword)` | 依名稱搜尋法規 |
| `get_recent_changes(days)` | 近期異動紀錄 |
| `status_summary()` | 系統狀態摘要 |

### 2. 建立 cron 腳本

```python
# scripts/regulation_check.py
tracker = RegulationTracker()
tracker.sync_index()
results = tracker.check_all()
if any(r.get("changed") for r in results):
    print(f"[法規異動] ⚠ 發現異動！")
    for r in [r for r in results if r.get("changed")]:
        print(f"  {r['name']} v{r['old_version']} → v{r['new_version']}")
    # 可附加連結：https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={PCODE}
else:
    print(f"[法規異動] ✓ 全部無異動")
```

### 3. 設定 Hermes cron

```bash
hermes cron create --schedule "0 9 * * *" \
  --name "法規異動每日查核" \
  --prompt "執行法規異動查核腳本，解析結果並推播。" \
  --toolsets terminal
```

## CLI 命令（內建）

```bash
python -m zhiyan_legal.regulation_tracker sync      # 同步索引
python -m zhiyan_legal.regulation_tracker check      # 執行查核
python -m zhiyan_legal.regulation_tracker list       # 列出追蹤法規
python -m zhiyan_legal.regulation_tracker status     # 系統狀態
python -m zhiyan_legal.regulation_tracker add --pcode C0000008 --name 毒品危害防制條例
python -m zhiyan_legal.regulation_tracker remove --pcode C0000008
python -m zhiyan_legal.regulation_tracker report --days 7
python -m zhiyan_legal.regulation_tracker track-all-default  # 一鍵追蹤常用法規
```

## 常見陷阱

### 🔴 ZIP 解析失敗
```python
# ❌ 錯：用了 os.fdopen(0, "rb")  
# ✅ 對：io.BytesIO(buf)
def _parse_moj_zip(buf: bytes) -> list[dict]:
    import io
    with zipfile.ZipFile(io.BytesIO(buf)) as zf:
        names = zf.namelist()
        json_name = next(n for n in names if n.endswith(".json"))
        data = json.loads(zf.read(json_name).decode("utf-8-sig"))
```

### 🔴 法規名稱子字串誤配
搜尋「民法」會誤配到「備選國民法官初選名冊製作及管理辦法」（因「民」+「法」分別出現在「國民」和「辦法」中）。

**解法**：搜尋時採精確→前綴→子字串三層優先序，且確保精確名稱在前。

### 🟡 Lazy loading 索引快取
`RegulationTracker.__init__` 不自動載入索引（節省啟動時間），但 `search_law()`、`law_meta()`、`status_summary()` 等方法需要時應自動載入。

```python
def _ensure_index_loaded(self):
    if not self._index:
        self._load_index_from_cache()
```

### 🟡 追蹤空索引即要求查核
`check_one()` 在 `law_meta()` 回傳 None 時，應回傳 `status: "missing"` 而非拋錯。

### 🟡 Python 3.11 型別註記
`str | None` 在 Python 3.11 是合法的，但 Pyright 可能報錯。改成 `Optional[str]` 更安全。

### 🔴 中文 URL 編碼
FastAPI 對原始 UTF-8 中文查詢參數會回傳 `Invalid HTTP request received`，必須編碼：
```dart
_get('/search?keyword=${Uri.encodeComponent(keyword)}');
```

## 新舊條文對照（regulation_diff）

### 檔案
`src/zhiyan_legal/regulation_diff.py`（~700 行）

### 功能

| 功能 | 說明 |
|------|------|
| `diff_articles(old_arts, new_arts)` | 逐條比對：「修正」「新增」「刪除」分類 |
| `lcs_diff(old_text, new_text)` | LCS 逐字元 diff，回傳 ops（`=`/`+`/`-`） |
| `build_diff_report(pcode, tracker)` | 完整報告：新/舊條文提取→比對→附修正說明 |
| `export_word(report, path)` | python-docx 三欄 Word（標楷體 18pt 標題、紅底線新增/紅刪除線刪除） |

### 條文提取策略

1. 本機快取優先（sync 時自動存 `data/articles/{pcode}.json`，保留 8 版）
2. LawOldVer 網頁備援（`col-no` + `col-data` div 解析）
3. 舊版僅一個版本時自動從 LawOldVer 爬歷史版

### CLI

```bash
python -m zhiyan_legal.regulation_tracker diff --pcode C0000008     # 顯示 + Word
python -m zhiyan_legal.regulation_tracker diff-all                   # 批次產出
```

## REST API（regulation_api）

### 檔案
`src/zhiyan_legal/regulation_api.py`（FastAPI）

### 端點（Port 7850）

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/status` | 系統狀態（索引數、追蹤數、近 7 天異動） |
| GET | `/api/tracked` | 22 部追蹤法規清單（含燈號） |
| POST | `/api/tracked/add?pcode=&frequency=` | 加入追蹤 |
| DELETE | `/api/tracked/{pcode}` | 移除追蹤 |
| POST | `/api/check?official=true` | 執行查核 |
| POST | `/api/sync?force=false` | 同步索引 |
| GET | `/api/search?keyword=` | 搜尋法規（需 URL encode 中文） |
| GET | `/api/diff/{pcode}` | 新舊對照（JSON / docx） |
| GET | `/api/diff/all` | 批次產出 Word |
| GET | `/api/history?days=7` | 查核歷史 |

### 部署

```
systemd:       zhiyan-api.service（開機自啟、當掉重啟）
Python 路徑:   /home/.../.hermes/hermes-agent/venv/bin/python3
環境變數:      PYTHONPATH=src
```

### Caddy 反向代理（Tailscale 專用）

```
http://100.68.234.34:80 {
    reverse_proxy 127.0.0.1:7850
}
```

Android 端需 `network_security_config.xml` 允許 Tailscale IP 的 HTTP。

## Flutter Android App

### 檔案
`law_monitor_app/`（136 個檔案，6553 行 Dart）

### 架構

```
lib/
├── main.dart                  入口 + Material3 主題 + 路由
├── api/client.dart            API 客戶端 + 4 個 Model 類別
└── screens/
    ├── dashboard.dart          儀表板（法規清單 + 綠/黃/紅燈號 + 統計）
    ├── detail.dart             法規明細（diff 摘要 + 新舊對照卡片）
    ├── diff_viewer.dart        完整逐條對照檢視器
    ├── search.dart             關鍵字搜尋 + 一鍵加入追蹤
    └── settings.dart           API 網址設定 + 連線測試 + 關於資訊
```

### Build

```bash
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk
```

### 連線限制
- 需手機連 Tailscale 才能連 VM
- network_security_config.xml 白名單：`100.68.234.34`

## 整合指南（zhiyan-legal 專案）

### 檔案位置
```
zhiyan-legal/
├── src/zhiyan_legal/
│   ├── regulation_tracker.py    ← 核心引擎
│   ├── regulation_diff.py       ← 新舊對照 + Word 匯出
│   └── regulation_api.py        ← FastAPI REST 後端
├── scripts/
│   ├── regulation_check.py      ← cron 排程腳本
│   └── start_api.sh             ← API 啟動腳本
├── law_monitor_app/             ← Flutter Android App
├── data/
│   ├── regulation_tracker.db    ← SQLite 自動建立
│   ├── articles/*.json          ← 條文快取
│   └── exports/*.docx           ← Word 對照表
├── Caddyfile                     ← Tailscale 反向代理
└── docs/60_概念詞條/
    └── 法規現狀參考表.md        ← 更新引用標示
```

## 驗收檢查

```bash
# 1. 同步索引（首次下載 ~30MB，數秒）
python -m zhiyan_legal.regulation_tracker sync --force -v
# 預期：已同步索引：法律 1345 部、命令 10423 部，共 11768 筆

# 2. 加入追蹤
python -m zhiyan_legal.regulation_tracker add --pcode C0000008 --name 毒品危害防制條例 --frequency 7

# 3. 執行查核
python -m zhiyan_legal.regulation_tracker check
# 預期：首次納入 → 第二次起全部無異動

# 4. 查看狀態
python -m zhiyan_legal.regulation_tracker status

# 5. cron 腳本
python scripts/regulation_check.py
# 預期：exit code 0（無異動）或 1（有異動）

# 6. 一鍵追蹤預設法規
python -m zhiyan_legal.regulation_tracker track-all-default
```

## 參考檔案

- `references/law-tracker-api-spec.md` — 全國法規資料庫 API 規格細節
- `references/roc-date-parsing.md` — 中華民國曆 → 西元日期轉換實作
