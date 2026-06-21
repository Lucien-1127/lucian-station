---
name: cli-to-web
description: 將現有 CLI / Python 引擎專案包裝為 FastAPI Web 服務的標準模式。保留原始碼、新增 Web 層、雙系統啟動腳本。
version: 1.0.0
author: Lucian
trigger: 使用者要求將現有 CLI 或 Python 專案做成網頁 App、將本地工具 SaaS 化、或說「像 XXX 網站一樣」
---

# CLI → Web Service 包裝模式

## 適用情境
- 現有 CLI 工具或 Python 引擎需要 Web UI
- 將 prompt-engineering / LLM 專案包裝為 SaaS 應用
- 保留既有文件與原始碼不動，新增 Web 層疊加

## 專案結構樣板

```
專案根目錄/
├── backend/
│   ├── main.py           ← FastAPI 應用主程式
│   ├── engine.py         ← 引擎封裝層（包裝原有核心邏輯）
│   ├── requirements.txt  ← Python 相依套件
│   ├── .env              ← API 金鑰與環境設定（gitignore）
│   └── .env.example      ← 設定範本（可 commit）
├── frontend/
│   ├── index.html        ← SPA 聊天 UI
│   ├── style.css         ← 主題樣式
│   └── app.js            ← 前端互動邏輯
├── docs/                 ← 保留原有文件（不動）
├── src/                  ← 保留原有原始碼（不動）
├── start.sh              ← WSL/Linux 啟動腳本
├── start.bat             ← Windows 啟動腳本
├── .gitignore
└── README.md
```

## 實作步驟

### Step 1: 建立目錄結構
```bash
mkdir -p 專案名/backend 專案名/frontend
cp -r 原專案/docs 原專案/src 新專案/
```

### Step 2: 引擎封裝層 (backend/engine.py)

建立一個 class 封裝原有核心邏輯：

```python
class AppEngine:
    def __init__(self):
        self._loaded = False
        self._prompt = None

    def load_docs(self) -> str:
        """載入所有規格文件，組合成 system prompt。"""
        # 依層級順序載入文件目錄
        load_order = ["10_核心層", "20_應用層", "30_模組層"]
        # 回傳組合後的提示詞

    def query(self, user_message: str, **kwargs) -> dict:
        """執行 LLM 查詢，回傳結構化結果。"""
        # 組合 messages = [system, history, user]
        # 呼叫 OpenAI 相容 API
        # 回傳 {"content": ..., "model": ..., "tokens_in": ..., "tokens_out": ..., "mode": ...}

    def reload(self):
        """強制重新載入文件。"""
        self._loaded = False

    def _detect_mode(self, text: str) -> str:
        """自動偵測輸入類型（如 legal / general）。"""
        KEYWORDS = {"legal": ["法", "條", "判決", ...]}
        match = sum(1 for kw in KEYWORDS.get("legal", []) if kw in text)
        return "legal" if match >= 1 else "general"
```

### Step 3: FastAPI 後端 (backend/main.py)

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="應用名稱", version="1.0.0")

# 生命週期 — 啟動時預載文件
@asynccontextmanager
async def lifespan(app):
    engine.load_docs()
    yield

# CORS — 開發時允許前端跨域
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# API 路由
@app.get("/api/status")     # 系統狀態
@app.post("/api/chat")      # 對話
@app.post("/api/reload")    # 重載文件

# 掛載靜態檔案（前端 SPA）
app.mount("/", StaticFiles(directory="前端路徑", html=True))
```

**Key design choices:**
- `asynccontextmanager lifespan` — 啟動時預載，不用 lazy load
- `CORS allow_origins=["*"]` — 開發用，上線後鎖定
- `StaticFiles(html=True)` — SPA 直接從同一個 port 服務
- `pydantic BaseModel` — 請求/回應型別驗證

### Step 4: 前端聊天 UI

**HTML 基本結構：**
```
側邊欄（品牌 + 導航） | 主內容區（頂欄 + 對話區 + 輸入區）
```

**關鍵功能：**
- `sendMessage()` — POST /api/chat，顯示載入動畫
- `addMessage(text, role, meta)` — 渲染使用者/AI 氣泡
- `newChat()` — 清空對話，回到歡迎畫面
- `handleKeydown(e)` — Enter 送出，Shift+Enter 換行
- `checkStatus()` — 啟動時檢查 API 連線

**專業 UI 要點：**
- 品牌色主色 + 金色點綴（法律/金融風格）
- 訊息氣泡區分使用者（淺灰）與 AI（白色+邊框）
- 建議問題快捷鍵（suggestion chips）
- 輸入框自動調整高度
- 行動版側邊欄收合
- 載入 overlay 防止重複送出
- API 中繼資料顯示（mode tag、tokens 用量）

### Step 5: 啟動腳本

**start.sh（WSL/Linux）：**
1. 檢查 `.env` 是否存在（無則提示但繼續）
2. 建立/啟用 Python venv
3. `pip install -r requirements.txt`
4. `source .env` 載入環境變數
5. `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

**start.bat（Windows）：**
1. 相同流程但用 `call .venv\Scripts\activate.bat`
2. 用 `for /f` 解析 .env 設定環境變數
3. 最終 `python -m uvicorn main:app ...`

## 陷阱

- **StaticFiles 順序很重要** — FastAPI 路由比對是順序的，API 路由要宣告在 `app.mount("/", ...)` 之前，否則 API 端點會被 static file handler 吃走
- **Pydantic Field 驗證** — 使用 `Field(min_length=1, max_length=10000)` 避免惡意輸入
- **venv 在 Windows/WSL 路徑不同** — `.venv/Scripts/python.exe` vs `.venv/bin/python`，腳本要分開寫
- **.env 載入方式** — Windows .bat 的 `for /f` 解析法無法處理含空格或引號的值，複雜 .env 建議用 python-dotenv 在 Python 內載入
- **reload 開發模式** — `--reload` 在 production 要關閉
- **前端 build** — 此模式適合無框架 SPA（vanilla HTML/CSS/JS），若用 React/Vue 需另加 build step

## 參考文件

- `references/build-order-example.md` — 完整實作案例：智研 SaaS 版（法律 AI CLI → Web App），含建置順序、API 回應結構範例

## 禁止事項
- ❌ 不要修改原專案的 docs/ 和 src/ 目錄中的檔案
- ❌ 不要將 .env（含 API 金鑰）提交到 version control
- ❌ 不要在 production 使用 --reload
