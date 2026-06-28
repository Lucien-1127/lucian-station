# MCP Taiwan Legal DB 整合紀錄（已驗證 2026-06-28）

## 背景
zhiyan-legal 原使用官方司法院 API（data.judicial.gov.tw），需帳密、限時 00:00–06:00、回傳 7 天前資料。
2026-06 以 mcp-taiwan-legal-db 取代。

## 安裝
```bash
pip install mcp-taiwan-legal-db
python3 -m playwright install chromium  # F5 WAF fallback
```

## ⚠️ API 簽章已驗證（文件落後於實際套件）

> 2026-06-28 實測修正：套件文件（pip show mcp-taiwan-legal-db）與實際 API 不符，以下為親測正確的簽章。

### judicial_api.py 公開函式 vs 底層實作

| 公開函式 | 底層方法 | 正確參數 |
|---------|---------|---------|
| `search_judgments(keyword=, case_type=)` | `_jud_search.search()` | 8 參數（見下方） |
| `get_judgment(jid=)` | `_jud_doc.get_by_jid(jid)` | 只接受 `jid=` |
| `get_judgment(url=)` | `_jud_doc.get_by_url(url)` | 只接受 `url=` |
| `query_regulation(law_name=, article_no=)` | `_reg_client.resolve_pcode()` + `_reg_client.get_article()` | resolve_pcode 是 sync |

**search_judgments 完整參數（已驗證）**：
```python
search_judgments(
    keyword="",      # 搜尋關鍵字
    court="",        # 法院名稱
    case_type="",    # 民事/刑事/行政
    year_from=0,
    year_to=0,
    case_word="",    # 案件類型（如 "簡上"）
    case_number="",
    main_text="",
)  # 回傳 {"success": bool, "total_count": int, "results": [...]}
```

**results 每筆欄位**：
```python
{"jid": "TPDV,114,簡上,409,20260624,1", "title": None,
 "court": "臺灣臺北地方法院", "date": "115-06-24",
 "case_id": "114年度簡上字第409號", "cause": "損害賠償"}
```

**get_judgment 回傳欄位（已驗證）**：
```python
{"success": True, "cached": "http_data_aspx",
 "court": "臺灣臺北地方法院", "date": "115-06-24",
 "judges": ["楊承軒", "陳冠中", "陳裕元"],
 "parties": {"上訴人": ["羅秋足", "宋秀珍"]},
 "cause": "損害賠償",
 "facts": "...（5872-16794 字豐富事實）...",
 "reasoning": "...",
 "cited_statutes": ["民法第184條", "民法第767條"],
 "cited_cases": ["最高法院95年度台上字第310號"],
 "full_text": "裁決字號：..."}  # 可能為空（WAF 阻）但 facts 豐富
```

**JID 格式**：`{法院代碼},{民國年},{案件類型},{編號},{西元月日},{流水號}`
- `TPDV`=臺北地院、`TPHV`=臺灣高等法院、`KSHV`=高雄高分院、`TNHV`=臺南高分院
- 流水號：`1`=第一審，`2`=第二審以此類推

**Quota Guard**：
- 429 Rate Limit → 標記 `FAILED`，禁止宣稱成功
- `full_text` 為空但 `facts` 有內容 → WAF 阻擋全文，不影響主要使用

## 常見錯誤與修復（2026-06-28 實測）

| 錯誤 | 原因 | 修復 |
|------|------|------|
| `TypeError: RegulationClient.__init__() takes 2 positional arguments but 3` | 多了 `_waf` 參數 | `_reg_client = RegulationClient(_cache)` |
| `AttributeError: 'JudgmentDocClient' object has no attribute 'get'` | 文件寫 `.get()` | 改用 `.get_by_jid(jid=)` |
| `TypeError: get_by_jid() got an unexpected keyword argument 'url'` | 同時傳 `jid` 和 `url` | 分支：`if jid: get_by_jid(jid=)` |
| `AttributeError: 'RegulationClient' object has no attribute 'query'` | 文件寫 `.query()` | 用 `resolve_pcode()` + `get_article()` |
| `TypeError: object str can't be used in 'await'` | `resolve_pcode` 是 sync 但用了 await | 移除 await |

## 正確工作流程（⚠️ 鐵律，2026-06-28 新增）

```
法律問題輸入
    ↓
Step 1：MCP search_judgments + get_judgment（雙軌 RAG + 全國法規驗證）
    ↓
Step 2：若法條引用 → query_regulation（resolve_pcode + get_article）
    ↓
Step 3：CITATION 強制引用（法規名+條號+JID 三元素齊備）
    ↓
產出（含風險燈號 🔴🟡🟢 + 信心標記）
```

> ❌ **錯誤**：直接用 curl/瀏覽器搜外部網站（繞過 MCP）
> ✅ **正確**：先 MCP+RAG，不足才派子代理至 law.moj.gov.tw

## 特點
- 免帳密，爬 judgment.judicial.gov.tw 公開頁面
- 無時間限制，白天也能查
- 即時資料
- 支援 httpx 快速查 + Playwright F5 WAF fallback
- 結果快取 30 天

## 整合點
- src/zhiyan_legal/judicial_api.py — 主要模組（2026-06-28 修復 4 個 API bug）
- tests/test_judicial_api.py — 測試（parse_case_number + build_jid）
- docs/80_技術參考/api_differences.md — 官方 API vs MCP 差異對比筆記

## 生效狀態（2026-06-28）
- ✅ 舊 `judicial_api.py` 官方 API 客戶端已刪除
- ✅ judicial_api.py API 簽章已修復（4 個 bug）
- ✅ 成功查得 4 個真實案例（JID: TPDV/KSHV/TPHV/TNHV）
- ✅ facts 欄位豐富（5872-16794 字），可直接用於案例寫作
- 🔌 六組 GCP MCP Server 同時上線（BigQuery/Storage/Run/Logging/Compute/ResourceManager）