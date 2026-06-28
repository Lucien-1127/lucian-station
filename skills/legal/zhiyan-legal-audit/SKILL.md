---
name: zhiyan-legal-audit
description: 智研AI法律工作站 (zhiyan-legal) 程式碼審查、測試補強、架構改進 SOP
version: 1.3.0
author: Lucian
platforms: [linux]
---

# zhiyan-legal 程式碼審查與架構改進 SOP

## 前置條件

```bash
cd ~/zhiyan-legal
source .venv/bin/activate
PYTHONPATH=src python -m pytest tests/ -v   # 先跑 baseline
```

## 新增：自動化檢索與建庫工作流 SOP (2026-06-28 更新)

在執行 `zhiyan-legal` 相關任務時，強制實施以下自動化閉環流程：

1. **API 分流策略**：
   - 委派任務前，必須在 `config.yaml` 的 `agents_config` 中配置該子代理的專屬金鑰池 (`api_keys`)。
   - 避免使用全域輪替池，以防單一任務限速拖累系統其他環節。

2. **資料建置閉環 (Ingestion Loop)**：
   - 原始資料：僅處理 UTF-8 JSON 純文字檔 (繞過 PDF/掃描檔)。
   - 資料結構：SQLite FTS5 (精確軌) + 本機向量 ChromaDB (語意軌)。
   - 儲存策略：將資料庫拆分為「唯讀歷史卷」與「動態寫入卷」，以適配雲端 API 的增量同步 (Chunked Upload)。

3. **審計觸發器 (Audit Trigger)**：
   - 所有 Legal Writer 輸出必須通過 `Citation Verification`：回溯 SQLite 原始內容驗證，未達標則觸發 `BLOCKED`，禁止顯示草稿。

4. **Self-Healing 錯誤處理**：
   - 發生 429/401 時，系統自動觸發 Failover 鏈 (DeepSeek -> Gemini)。
   - 禁止宣稱成功，任務失敗時必須寫入 `TODO.json` 以供後續重啟自動接手。

### 檢查清單

| 優先 | 項目 | 檢查點 |
|------|------|--------|
| 🔴 P1 | router.py | KEYWORD_MAP 有無 key 衝突？單字關鍵字（告/殺/查）有無邊界保護？新 task 有無對應觸發詞？ |
| 🔴 P1 | pyproject.toml | build-backend 是否為 `setuptools.build_meta`？ |
| 🔴 P1 | loader.py | compose() 中 missing 變數是否被使用？ |
| 🟡 P2 | runner.py | API 呼叫有無 try/except？token 估算是否統一用 count_tokens()？有無 validate_output()？ |
| 🟡 P2 | setup.sh | cd 路徑是否指向專案根目錄？ |
| 🟡 P3 | src/zhiyan_legal/ | 有無 __init__.py / __main__.py？ |
| 🟡 P3 | 根目錄 | 有無殘留空檔案（如 =1.0.0）？ |

### 修正 SOP

1. 開 branch：`git checkout -b fix/issue-description`
2. 逐一修正（每個問題獨立 commit）
3. 跑測試確認不壞既有案例
4. 補充對應測試案例（先寫 test 再修 code → TDD 精神）
5. merge 到 main → push

## 二、測試補強標準

### 測試覆蓋目標

| 模組 | 最低測試數 | 關鍵測試點 |
|------|-----------|-----------|
| router.py | 20+ | 各 task 路由、SAFETY/LITIGATION 優先、邊界保護 edge case、重疊關鍵字優先序、預設 fallback、新 task 觸發 |
| loader.py | 10+ | frontmatter 剝離、compose 串接、missing 警告、截斷精確長度、空檔案、count_tokens 估算、parse_frontmatter、simulation_mode |
| manifest.py | 24+ | Layer dataclass、CORE_LAYERS 完整性、TASK_LAYERS 任務覆蓋、resolve_doc、get_load_order 排序/去重/預設/fallback、真實檔案存在驗證 |

### 邊界保護測試（router.py）

```python
# 告：報告中不觸發 LITIGATION
def test_boundary_ga_not_in_report():
    assert route("幫我寫一份報告") != "LITIGATION"

# 告：獨立使用或複合詞應觸發
def test_boundary_ga_standalone():
    assert route("我要告他") == "LITIGATION"
def test_boundary_ga_in_beigao():
    assert route("被告主張無過失") == "LITIGATION"

# 殺：抹殺中不觸發 SAFETY
def test_boundary_sha_not_in_mosha():
    assert route("對方完全抹殺我的貢獻") != "SAFETY"
def test_boundary_sha_standalone():
    assert route("他威脅要殺我全家") == "SAFETY"

# 查：審查中由複合詞「審查」QC 優先匹配
def test_review_routes_to_qc():
    assert route("審查這個專案內的所有程式碼") == "QC"
def test_cha_standalone():
    assert route("幫我查一個法條") == "RESEARCH"
```

### SIMULATION 模式測試

```python
def test_simulation_hypothesis():
    assert route("假設某判決已作廢") == "SIMULATION"
def test_simulation_safety_overrides():
    assert route("假設我不想活了") == "SAFETY"
def test_simulation_litigation_overrides():
    assert route("假設我要提告") == "LITIGATION"
```

## 三、架構改進模式

### 關鍵字邊界保護
- `告` → 改用複合詞（告人/告他/被告/提告/告訴/控告），移除單字
- `殺` → 邊界保護：前後都是中文字時不匹配
- `查` → 不設邊界保護（中文常作獨立動詞），用複合詞（審查/調查）先匹配

### SIMULATION 模擬模式
```python
# KEYWORD_MAP 新增
"假設": "SIMULATION", "模擬": "SIMULATION",
"推演": "SIMULATION", "假定": "SIMULATION",
"如果": "SIMULATION",

# 路由優先序（route() 中）
# 1. SAFETY → 2. LITIGATION → 3. SIMULATION → 4. QC/RESEARCH/REPORT → 5. personas → 6. CONSULTANT

# describe_route() 新增
"SIMULATION": "🧪 模擬模式 (Simulation Mode)",

# CLI 新增 --simulate 參數
parser.add_argument("--simulate", action="store_true",
                    help="啟用模擬模式（接受假設前提推演）")

# compose() 傳入 simulation_mode 參數
system_prompt = compose(file_paths, simulation_mode=sim_mode)
```

### frontmatter 時態標記（loader.py）
```python
def parse_frontmatter(text: str) -> Tuple[str, Dict[str, Any]]:
    """解析 YAML frontmatter，提取 status/as_of_date/version/title。"""
    # 支援 frontmatter 格式：
    # ---
    # status: active | draft | deprecated
    # as_of_date: YYYY-MM-DD
    # version: semver
    # ---

# compose() 自動為有 frontmatter 的文件產生時態標頭
# ✅ status: active | as of 2026-06-01
# ⚠️ status: deprecated
# 📝 status: draft
```

### API Provider 模型更新（2026/06 市場現況）
```python
# 已退役模型
GPT-4o        → 2026/2 退役 → gpt-5.1
deepseek-chat → 2026/7 棄用 → deepseek/deepseek-v4-flash
gemini-2.5    → 已舊        → gemini-3-flash-preview
claude-sonnet-4 → 已舊     → claude-sonnet-4.6
mimo-v2.5 (小米) → 已無聲量 → minimax-m3

# 更新位置
.env.example, README.md (中英雙語表), scripts/setup.sh, src/zhiyan_legal/runner.py (MODEL_DEFAULT)
```

### logging 標準化
```python
import logging
logger = logging.getLogger("zhiyan_legal")
# CLI 加入 --verbose 開啟 DEBUG 層級
```

### 輸出校驗（簡化版 DeepThink）
```python
from .runner import validate_output

# run_llm() 回傳前自動校驗
content = response.choices[0].message.content or ""
return validate_output(content, task)

# 各 task 校驗 pattern（在 _TASK_VALIDATION 中定義）：
# QC:         條款/缺失/風險 → 應指出具體條款與風險點
# LITIGATION: 原告/被告/攻防 → 應涵蓋雙方立場
# REPORT:     摘要/結論/建議 → 應有摘要→分析→結論
# RESEARCH:   依據/判決/見解 → 應附法規或判決依據
# CONSULTANT: 方案/比較/利弊 → 應比較不同選項
# SAFETY:     協助/資源/專線 → 應提供求助資源
# SIMULATION: 假設/模擬/⚠   → 應標示免責聲明

# 未達門檻時 append 警語（不刪不改原始內容）
# 門檻：max(1, len(patterns) // 3) 個 pattern 匹配
```

### API 層深度優化模式（FastAPI 後端）

當需要對 `backend/main.py` + `backend/engine.py` 進行 API 層優化時，遵循以下五步模式：

#### 第一步：多層審計

| 層級 | 審計重點 | 典型發現 |
|------|---------|---------|
| Hermes Provider | fallback 鏈、credential pool、delegation model | 缺 OpenRouter fallback、delegation 用 Gemini |
| SaaS API (backend/) | sync vs async、connection pooling、retry、middleware | OpenAI() 每次建立、無 retry、無 rate limit |
| Regulation API (src/...) | singleton pattern、timeout、cache 位置 | tracker 全區域變數、cache 在 /tmp |
| Judicial API (judicial_api.py) | MCP timeout、retry、cleanup | 無 timeout、無 retry、lazy init 無 cleanup |

#### 第二步：engine.py 非同步改造模式

```python
from httpx import AsyncClient, Limits
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI

# 1. 連接池
_CONN_POOL = Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=30.0)

# 2. 自訂例外階層
class EngineError(Exception): pass
class LLMTimeoutError(EngineError): pass
class LLMConnectionError(EngineError): pass
class LLMRateLimitError(EngineError): pass
class LLMResponseError(EngineError): pass

# 3. Retry 裝飾器（指數退避 ×3）
@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((
           httpx.TimeoutException, httpx.ConnectError,
           httpx.RemoteProtocolError, httpx.HTTPStatusError)),
       reraise=True)

# 4. Lifespan 管理
async def startup(self):
    self._http_client = AsyncClient(base_url=..., timeout=..., limits=_CONN_POOL)
    self._async_openai = AsyncOpenAI(..., http_client=self._http_client)
    
async def shutdown(self):
    await self._http_client.aclose()
```

#### 第三步：main.py Middleware Stack 模式

從左到右逐一疊加，每層只做一件事：

```
1. Rate limit handler    → slowapi.Limiter (預設 30/min, 可 ZHIYAN_RATE_LIMIT 覆寫)
2. CORS                 → env 可控 (ZHIYAN_CORS_ORIGINS), 生產限特定 domain
3. TrustedHost          → env 可控 (ZHIYAN_TRUSTED_HOSTS), 生產才開
4. Request ID           → X-Request-ID header + X-Processing-Time-ms
5. Slow request warn    → >10s 打 warning log
6. Structured errors    → 統一 ErrorResponse schema (error/detail/request_id)
```

Request ID middleware 實作（最關鍵的一層）：
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content=ErrorResponse(
            error="internal_error", detail="伺服器內部錯誤", request_id=rid
        ).model_dump())
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = rid
    response.headers["X-Processing-Time-ms"] = str(round(elapsed * 1000, 1))
    if elapsed > 10:
        logger.warning("[%s] 慢請求: %.1fs", rid, elapsed)
    return response
```

#### 第四步：相依注入（取代全域變數）

```python
# main.py — FastAPI lifespan 管理引擎生命週期
_engine: ZhiyanEngine | None = None

def get_engine() -> ZhiyanEngine:
    assert _engine is not None
    return _engine

@asynccontextmanager
async def lifespan(app):
    _engine = ZhiyanEngine(config=EngineConfig())
    await _engine.startup()
    yield
    await _engine.shutdown()

# route 中
@app.post("/api/chat")
async def chat(request: Request, body: ChatRequest):
    engine = get_engine()
    result = await engine.query_async(...)
```

#### 第五步：整合測試驗證

```bash
# 啟動 server
uvicorn main:app --host 127.0.0.1 --port 8000

# 測試所有 endpoints
curl http://127.0.0.1:8000/api/status          # 狀態
curl -X POST http://127.0.0.1:8000/api/chat \   # LLM 呼叫
  -H "Content-Type: application/json" \
  -d '{"message":"test","max_tokens":50}'
curl -X POST http://127.0.0.1:8000/api/reload   # 重新載入

# 驗證 header
curl -sI http://127.0.0.1:8000/api/status | grep -i x-request-id

# 驗證 rate limit
for i in {1..35}; do curl -s -o /dev/null -w "HTTP %{http_code}\\n" http://127.0.0.1:8000/api/status; done
```

#### 關鍵陷阱

| 陷阱 | 症狀 | 解法 |
|------|------|------|
| 🔴 FastAPI lifespan 中 engine startup 失敗 | Server 啟動後馬上關閉 | `load_dotenv()` 必須在 import engine 前執行 |
| 🟡 OpenAI client 不接受 httpx 自訂 pool | `MaxRetryError` / 連線失敗 | AsyncOpenAI 的 `http_client` 參數只接受 `httpx.AsyncClient`，不接受 `httpx.Client` |
| 🟡 tenacity retry 與 asyncio.timeout 衝突 | retry 重試次數不符預期 | asyncio.timeout 在外層，retry 在內層 |
| 🟡 slowapi Limiter 需掛在 `app.state` | `AttributeError: 'FastAPI' object has no attribute 'limiter'` | `app.state.limiter = limiter` + `app.add_exception_handler(RateLimitExceeded, ...)` |
| 🟡 uvicorn workers >1 時 port 衝突 | `address already in use` | 舊 process 未清乾淨：`lsof -ti:8000 \| xargs kill -9` |
| 🟡 dotenv 載入後 api_key 仍為空 | 未設 `load_dotenv()` 在 module 層級 | 在 engine.py 和 main.py 最頂端 import 後立即 `load_dotenv()` |

---

### CLI 輸出格式（--output json）
```bash
python -m zhiyan_legal "查法條" --output json
# 輸出：{"query": "...", "task": "RESEARCH", "task_description": "...", "documents_loaded": 8, "token_estimate": 2345, "response": "..."}
```

### 檔案存在驗證（manifest.py）
CORE_LAYERS 和 TASK_LAYERS 中所有參考的檔案在 docs/ 下應真實存在：
```python
def test_core_layer_files_exist(self):
    for layer in CORE_LAYERS:
        for fname in layer.files:
            path = os.path.join(DOCS_DIR, layer.path, fname)
            assert os.path.exists(path), f"Missing: {layer.path}/{fname}"

def test_task_layer_files_exist(self):
    for task, layers in TASK_LAYERS.items():
        for layer in layers:
            for fname in layer.files:
                path = os.path.join(DOCS_DIR, layer.path, fname)
                assert os.path.exists(path), f"Missing: {task}/{layer.path}/{fname}"
```

## 四、CHANGELOG 管理

每次 release 前更新 `CHANGELOG.md`，格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)：
- 🔴 Bug Fixes — P1 (Critical)
- 🟡 Improvements — P2 (High)
- 🟢 Features — P3 (Enhancement)
- 🧪 Testing — 測試新增/修正
- 附 commit index 與測試覆蓋里程碑

## 五、完整驗收

```bash
cd ~/zhiyan-legal
source .venv/bin/activate
PYTHONPATH=src python -m pytest tests/ -v
# 預期：122+ passed (2026/06 基準，持續成長)
```

## 六、Ablation 實驗執行方法

在 RAP 申請前需產出實測數據。以下為 zhiyan-legal 專用對照實驗 SOP。

### 實驗設計模式

n=50 題 × 2 條件（完整系統 vs 消融某層）
可擴展至 200 題 × 4 條件 × 3 複本（RAP 標準）

### 模型選擇（2026-06 最新）

**不要用 gemini-2.5 系列**（模型太舊）。優先選用 Gemini 3 系列：

| 模型 | 使用情境 | 輸入/M | 輸出/M | 成本/100 calls |
|------|---------|:------:|:------:|:--------------:|
| **3.1 flash-lite** | 最省錢、批次實驗、子代理高頻呼叫 | $0.25 | $1.50 | ~$0.06 |
| **3.5 flash** | 最佳性價比、即時對話、多模態 | $0.75 | $4.50 | ~$0.30 |
| **3.1 pro** | 深度推理、長文本分析（注意：API 上名稱可能已變） | 較貴 | 較貴 | 視用量 |

`gemini-3.1-flash-lite` 支援 system_instruction，經實測 50×2 experiment 零錯誤，
成本 $0.06/100 calls，原生引用率 88%（無需額外政策指引）。
如需更低成本可試 `gemini-3.1-flash-lite` 或等待 `gemini-3.1-flash-lite` 降價。

### Gemini Native API（重要）

AQ. 前綴的 Gemini key 不支援 OpenAI-compatible 端點（/v1beta/openai），
必須走原生 REST API：X-goog-api-key header，system_instruction 欄位與 contents 分開傳遞。

```python
data = {
    "system_instruction": {"parts": [{"text": system_prompt}]},
    "contents": [{"parts": [{"text": user_message}]}],
    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}
}
req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json", "X-goog-api-key": key},
    method="POST",
)
```

注意：3.5 flash 是思考模型，maxOutputTokens 需設足夠高（≥8192），
否則 output 會被 thinking tokens 吃光導致 FR=MAX_TOKENS 而無內容。

### 層級過濾

從 get_load_order() 回傳的 file_paths 中過濾特定文件：
- CITATION_POLICY → 消融 Citation Policy
- CORE_GATE → 消融 Fact Gate

### Fabrication 檢測 — ⚠️ 方法論核心陷阱

**Citation Rate ≠ Fabrication Rate。**

RQ1 問的是「不虛構引用政策能否減少捏造法條」，
但自動化檢查只能量到「是否有引用格式出現」。
一個模型可以在 88% 的回應中加上 [1][2] 格式，但那些條號全部是假的——反之亦然。

| 量到了什麼 | 沒量到什麼 | 影響 |
|-----------|-----------|------|
| 引用標記出現率（[1][2][T1]） | 那些條號是否真實存在於法規資料庫 | 完全無法回答 RQ1 |
| 信心標記出現率（✅/⚠️/❌） | 模型是否真的在低信心時中止 | 完全無法回答 RQ3 |

#### 正確的 Fabrication Rate 量測

1. 從回應中提取「法名稱 + 條號」對（正則比想像中難：模型常寫「依《勞動基準法》第9-1條」）
2. 對照本地 RAG DB（47K 條，law_name + article 欄位，格式為「第 X 條」）
3. 不可靠的條號→改用全國法規資料庫聯網驗證（law.moj.gov.tw，需正確 pcode）
4. 取 20% sample 人工覆核

常見陷阱：
- RAG DB 法條名稱用全稱（「中華民國刑法」「勞動基準法」），非簡稱
- RAG DB 條號格式含空格（「第 309 條」，非「309」）
- 模型回應用「XX法第YY條」但正則可能抓到周圍標點（如「：依XX法」）
- 聯網查 pcode 因法規類別不同（民法=B0000001、刑法=C0000001、勞動基準法=N0030001）

#### 自動化 heuristic（僅供快速掃描，不做結論用）

檢查 [T1] 引用標記、信心標記（✅/⚠️/❌）、條號密度。
僅為格式檢查，人工抽樣驗證（20% sample）仍為必要。

### 結果儲存

results/exp-{name}-{timestamp}/ 下存放 experiment_log.csv 與 summary.json。

### 2026-06-26 實戰發現（v3 更新）

- **Citation Policy 對 Gemini 引用行為邊際效應極低**（64% vs 66% 在 2.5，88% vs 88% 在 3.1）
- **Citation Policy 文件根本沒被模型遵循**：[T1] RAG 專用格式在 88 筆有引用回應中出現 0 次。模型只用自己的 [1][2] 通用格式，不理系統規定的引用格式。
- **信心標記（G0）由 CORE_GATE 控制，非 Citation Policy** — 兩條件皆為 0%，且跟有無政策無關
- **無政策時某些查詢反而產生更長回應**（模型自由發揮，不受格式壓縮）
- **Citation Rate ≠ Fabrication Rate** — 自動化格式檢查 64%/88% 引用標記，不等於引用內容真實性。初步人工驗證刑法309條、民法184條、勞基法9-1條皆為真實，但完整 fabrication rate 需配對 RAG DB 逐條驗證
- **Context caching 在 Gemini 自動啟用**，每次節省 ~15K tokens
- **總成本 $0.06-$0.08/100 calls** → 完整 RQ1（2400 calls）約 $1.44-$1.92
- **3.1 flash-lite 優於 2.5 flash-lite**：成本更低（$0.06 vs $0.08）、原生引用率更高（88% vs 64%）、且不被 Citation Policy 影響行為

### RQ 重新框架（2026-06-26 方法論審查後）

| 原始 RQ | 本次實驗的量測（錯誤） | 應用的量測（正確） |
|:---|:---|:---|
| RQ1：不虛構政策減少捏造？ | **Citation rate** — 僅檢查引用格式有無 | **Fabrication rate** — 比對 RAG DB + law.moj.gov.tw |
| RQ2：安全路由減少有害輸出？ | 有問題回應率（正確） | 需補充「危險問題」測試集 |
| RQ3：事實閘門改善校正？ | **信心標記率**（從未觸發=0%） | 邊界問題觸發率 +「待查」標記率 |
| — | Citation Policy 有無都 88% | Citation Policy 文件被忽略（[T1] 格式 0/88） |

→ 結論：Citation Policy 的邊際效應源自**模型本身已有足夠高的引用傾向**，
而非政策文件的約束力。應考慮消融 CORE_GATE 層作為下一步。

詳細實驗腳本與原始資料見 references/ablation-experiment.md。

## 七、RAP 申請支援

詳見 `references/rap-application.md`：
- OSF DOI 取得流程（最高優先）
- arXiv 預印本策略
- RESEARCH.md 內容標準
- 成功率因子分析

## 八、外部評測三級回覆流程

當收到第三方對 zhiyan-legal 的完整評測（含風險燈號、分數、改進建議）時，採用以下 **驗證→分級→行動** 流程，確保不盲目照單全收。

### 流程

```
接收評測
  │
  ▼
一級：逐項對照事實
  ├── 讀 GitHub 現況（README topics、test count、CI、依賴、目錄結構）
  ├── 比對當地 repo（tests/、pyproject.toml、requirements.txt、.github/）
  └── 產出「評測主張 vs 實際狀態」對照表
  │
  ▼
二級：分級
  ├── ❌ 事實錯誤（topics 已設卻說無、test count 過時）
  ├── ✅ Valid（CI 真的缺、依賴真的漏、Flutter README 真的空）
  └── 🟡 正確但需花錢/時間（實驗數據、社群曝光）
  │
  ▼
三級：行動
  ├── ❌ 錯誤項：不用改，回報時標示
  ├── ✅ Valid 項：立即改（CI workflow、optional-deps、README 重寫）
  └── 🟡 待辦項：記錄在 CHANGELOG，排入 roadmap
  │
  ▼
報告：逐項回報「什麼對、什麼錯、做了什麼」
  └── 每項附 GitHub 連結證明已推送
```

### 典型驗證檢查點

| 評測主張 | 驗證方式 | 常見陷阱 |
|---------|---------|---------|
| topics 缺失 | 看 GitHub README 頂部 Topics 行 | 評測可能只看程式碼沒點進 GitHub |
| test count | `pytest tests/ -q \| tail -1` | 評測 snapshot 可能落後幾小時 |
| missing CI | `ls .github/workflows/`，再檢查 workflow 內容 | 可能只有 pages build；workflow 需含 `pytest tests/ -v` 和 `--dry-run` 驗證，見 `references/test-workflow.md` |
| deps 不完整 | 比對 `requirements.txt` vs 實際 import | python-docx/fastapi 常被遺漏，應放 `[project.optional-dependencies]`<br>用 `grep -r "^from pl" src/ --include="*.py"` 找漏網 |
| Flutter README 空 | 看 `law_monitor_app/README.md` | Flutter 預設樣板不算「有文件」 |
| 實驗數據缺 | 看 `RESEARCH.md` 有無 results/ | 與 planned experiment 不同 |

### 實戰教訓（2026-06-26 經驗）

- 評測說「116 tests」→ 實際已 **122**（幾小時內就變了）
- 評測說「topics 缺失」→ GitHub 頁面 **本來就有** 8 個 topics
- 評測說「依賴只有 2 個」→ valid，python-docx / fastapi 都未聲明
- 評測說「Flutter 文件空」→ valid，確實只剩 Flutter 樣板

→ 永遠先對照事實再決定行動，不信也不拒，只核實。

CI workflow 完整範本見 `references/test-workflow.md`。

## 九、多模型架構健康檢查（Architecture Health Check）

用提示詞優化委員會的 4 模型平行架構來審查**程式碼架構**（非提示詞/法律引用）。

### 觸發時機
- 大版本迭代前（v3.x → v4.x）
- 新增重大功能後
- 累積明顯技術債時

### 審查維度（4 模型 × 不同視角）

| 模型 | 角色 | 維度 |
|:-----|:-----|:-----|
| DeepSeek V4 Flash | 結構完整性 | 目錄健康度、import 依賴、重複模組、設定管理 |
| Gemini 3.5 Flash | 文件對齊 | 文件-程式碼落差、導航斷鏈、測試覆蓋 |
| Claude Sonnet 4 | 安全邊界 | 例外處理、API 防護、資源洩漏、安全缺口 |
| NVIDIA Nemotron 49B | 盲點偵測 | 隱含耦合、技術債、可維護性、水平擴展 |

### 執行步驟
1. **製作 Repo Profile** — 檔樹 + 行數 + 核心資料流 + 已知特徵
2. **設計 4 份審查提示詞** — 每模型一主題，統一 JSON schema `{"findings": [...]}`
3. **平行呼叫** — `asyncio.gather` 同時送 4 模型，temp=0.2
4. **彙整報告** — 依嚴重度分級 + 行動建議排序

### 實戰教訓
- **Gemini 有時回傳空白格式異常** — `asyncio.gather(return_exceptions=True)` 隔離
- **Reprofile 要夠厚** — 需附核心資料流圖、各檔案行數分佈
- **NVIDIA 最慢**（~49s）但盲點最關鍵 — 抓到了「雙路由隱含耦合」
- **結果保存** → `results/architecture_health_check.json`
- **不要用 prompt optimization pipeline** — 架構審查需自訂 review prompts + direct API calls

### 實測基準（2026-06-28）
```
Total: 28 findings | 🔴 3 Critical / 🟠 14 Major / 🔵 11 Minor
```

完整腳本參考專案根目錄 `run_arch_health_check.py`。

---

## 九.b CI 除錯模式：pytest 收集階段失敗

當 CI workflow 在 collecting 階段就中斷時，不要在 tests/ 下找原因，要找 src/ 中的 module-level import。

### 根因

pytest 在收集階段 import 測試檔案 → 觸發 import 被測模組 → 如果被測模組的 module-level import 失敗，整個收集就中斷。

### 典型觸發條件

| 情境 | 症狀 | 解法 |
|:----|:-----|:-----|
| 選用套件未裝 | ModuleNotFoundError | try/except ImportError 惰性載入 |
| 型別註記引用未定義名稱 | NameError | 用字串 forward ref |
| 模組級網路請求 | HTTPError 429 | 移到函式內部 |
| 舊模組被 disuse | ImportError | 更新 import 指向新位置 |

### 惰性載入範本

```python
_HAS_MCP = False
try:
    from mcp_server.server import JudicialSearchClient, CacheDB
    _HAS_MCP = True
except ImportError:
    logger.warning("mcp-server not installed")
_cache: "Optional[CacheDB]" = None

async def _ensure_init():
    if not _HAS_MCP:
        raise RuntimeError("請安裝 mcp-taiwan-legal-db")
```

### CI workflow 依賴管理

pyproject.toml 加依賴 ≠ CI 會自動裝。workflow 是直接 pip install，需同步更新。

```yaml
pip install openai>=1.0.0 python-dotenv>=1.0.0 tenacity>=8.0.0 httpx>=0.27.0
```

### 常見陷阱

- `比對` 同時存在 QC 和 RESEARCH → 後者覆蓋前者，QC 需改為 `核對比對`
- `告` 在「報告」中誤觸 LITIGATION → 改用複合詞（告人/告他/被告/提告/告訴/控告）
- `殺` 在「抹殺」中誤觸 SAFETY → 邊界保護（前後皆中文時不匹配）
- `查` **不要**加邊界保護 — 中文「查」常作獨立動詞（查資料/查法條），邊界保護會擋掉合法 RESEARCH 路由；改用複合詞（審查/調查）先匹配即可
- `build-backend` 勿用 `setuptools.backends._legacy:_Backend`（私有 API）
- `setup.sh` 執行 `cd "$SCRIPT_DIR"` 會跑到 scripts/，需改為 `cd "$PROJECT_ROOT"`
- Gmail 中文 locale → folder aliases 需設為 `[Gmail]/寄件備份` 等本地化名稱
- `himalaya template send` 在某些環境會報 `Could not determine home directory` → 需要用 `HOME=/home/... himalaya template send < file` 指定 HOME
