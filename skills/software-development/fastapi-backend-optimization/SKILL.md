---
name: fastapi-backend-optimization
description: FastAPI 後端優化模式 — async engine、connection pool、retry、middleware stack、rate limiting、request ID tracing
version: 1.0.0
author: Lucien
---

# FastAPI 後端優化

將 LLM API 後端從同步阻塞重構為 async-first、有彈性、可觀測的服務。

## 觸發條件

- 現有 FastAPI 後端使用同步模型（`OpenAI()` client 每次建立、無 retry、無 timeout）
- LLM API 呼叫偶發 503/429 沒有 retry 機制
- 後端無 rate limiting、無 request ID 追蹤
- 需要 graceful startup/shutdown

## 核心模式

### 層 1 — Async Engine（httpx + tenacity）

```
v1 (同步, 阻塞)              v2 (async, 連接池)
┌─────────────────┐         ┌──────────────────────┐
│ OpenAI() 每次建立│   →     │ AsyncOpenAI + httpx   │
│ 無 retry         │   →     │ tenacity ×3 exp backoff│
│ 無 timeout       │   →     │ asyncio.timeout(Ns)   │
│ Exception→500    │   →     │ 6 種自訂例外          │
│ 無法 graceful    │   →     │ startup()/shutdown()  │
└─────────────────┘         └──────────────────────┘
```

**關鍵實作**：

```python
import httpx
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Connection pool
_LIMITS = httpx.Limits(
    max_keepalive_connections=5,
    max_connections=10,
    keepalive_expiry=30.0,
)

# Retry decorator
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((
        httpx.TimeoutException, httpx.ConnectError,
        httpx.RemoteProtocolError, httpx.HTTPStatusError,
    )),
    reraise=True,
)

# Lifespan-aware resource management
async def startup(self):
    self._http_client = httpx.AsyncClient(
        base_url=api_base,
        timeout=httpx.Timeout(60.0),
        limits=_LIMITS,
    )
    self._async_client = AsyncOpenAI(
        base_url=api_base, api_key=api_key,
        http_client=self._http_client,
    )

async def shutdown(self):
    if self._http_client:
        await self._http_client.aclose()
```

### 例外階層

```python
class EngineError(Exception):      # 基礎例外
class LLMConnectionError(EngineError):  # 連線失敗
class LLMTimeoutError(EngineError):     # 逾時
class LLMRateLimitError(EngineError):   # 429
class LLMResponseError(EngineError):    # 回傳異常
```

### 層 2 — Middleware Stack

| Middleware | 用途 | 關鍵參數 |
|-----------|------|---------|
| Request ID | 每請求唯一追蹤 ID | `uuid.uuid4().hex[:12]` |
| Rate Limiting (slowapi) | 防濫用 | `30/minute` 預設 |
| CORS | 跨域 | 可透過 env 控制 |
| TrustedHost | 生產安全 | 可選 |
| 慢請求警告 | >10s 自動 WARN | logging |
| 統一錯誤回應 | 所有例外→結構化 JSON | ErrorResponse schema |

### FastAPI Lifespan 相依注入

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = ZhiyanEngine(config=EngineConfig())
    await engine.startup()
    app.state.engine = engine
    yield
    await engine.shutdown()
```

取代全域變數 `engine = ZhiyanEngine()` — 可測試、可管理生命週期。

## 檔案結構

```python
backend/
├── engine.py        # Async LLM engine (httpx pool + retry + exception hierarchy)
├── main.py          # FastAPI app (middleware stack + lifespan + routes)
└── requirements.txt # fastapi, uvicorn, openai, httpx, tenacity, slowapi, python-dotenv
```

## 實戰陷阱

| 陷阱 | 症狀 | 解法 |
|------|------|------|
| `.env` 沒載入 | API key missing at startup | main.py 頂層加 `load_dotenv()`，engine.py 也加（獨立使用時） |
| API key 藏在 Hermes profile .env | `_get_api_key()` 找不到 key | 加入自動 .env 發現：`~/.hermes/profiles/*/.env` → `~/.hermes/.env` → `cwd/.env`，用 `os.environ.setdefault()` 避免覆蓋既有值 |
| Port conflict | address already in use | `lsof -ti:PORT \| xargs kill -9` 清乾淨再啟動 |
| slowapi type hint 報錯 | LSP 說找不到 slowapi | 已裝在 venv 但 pyright 沒指向 venv — runtime 沒問題 |
| HEAD request 回 404 | FastAPI 預設不支援 HEAD | 可忽略，或手動加 `@app.head()` |

## 環境變數

| 變數 | 預設值 | 用途 |
|------|--------|------|
| ZHIYAN_API_KEY | (auto-discover) | API key（支援 DEEPSEEK_API_KEY 等 fallback） |
| ZHIYAN_API_BASE_URL | https://api.deepseek.com/v1 | API base URL |
| ZHIYAN_MODEL | deepseek-chat | 預設模型 |
| ZHIYAN_RATE_LIMIT | 30/minute | Rate limit |
| ZHIYAN_CORS_ORIGINS | * | CORS 允許來源 |
| ZHIYAN_TRUSTED_HOSTS | (空=關閉) | Trusted hosts |
| APP_PORT | 8000 | 服務埠 |
| APP_WORKERS | 1 | uvicorn workers 數 |

## 驗證方法

```bash
# 啟動
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000

# 測試
curl http://127.0.0.1:8000/api/status
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "回一個字：OK", "max_tokens": 50}'

# 檢查 request ID header
curl -sI http://127.0.0.1:8000/api/status | grep x-request-id
```

## 參考文件

| 檔案 | 用途 |
|------|------|
| `references/prompt-optimization-committee.md` | 多模型委員會架構 — 用 async pipeline 做 prompt 品質審查 |

