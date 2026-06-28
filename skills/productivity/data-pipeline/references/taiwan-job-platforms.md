# Taiwan Freelance/Case Platforms — Crawlability & DOM Structure

> Last updated: 2026-06-06
> Source: manual inspection via Hermes browser tools + web_extract

---

## 1. Tasker出任務 (tasker.com.tw) — ✅ 可爬

**案件列表 URL:** `https://www.tasker.com.tw/cases`
**類型:** SSR (伺服器端渲染) — 直接用 requests + BeautifulSoup

### URL 參數
| 參數 | 說明 | 範例 |
|------|------|------|
| `page` | 分頁 | `?page=1`, `?page=2` |
| `selected_tags` | 標籤 ID | `229` = 系統分析與設計 |

### DOM 結構 (2026-06-06 驗證)

```python
# ⚠️ 關鍵 URL 模式：/cases/TK... 不是 /case/ (後者會 404)
# 每個案件是一個 <a href="/cases/TKxxxxxxxxxxxx">
case_links = soup.find_all("a", href=re.compile(r"^/cases/TK"))

# 卡片內結構:
link.select_one("h2")                        # 標題 (唯一的 h2)
re.search(r"\$[\d,]+", text)                 # 預算 (如 $1,000)
re.search(r"可遠端|台北|桃園|台中|高雄|台南", text)  # 地點
link.find_previous(["h2","h3","sectionheader"])  # 分類標籤
re.search(r"(\d+)人提案中", text)             # 提案人數
re.search(r"\d+小時|昨天|前天", text)          # 刊登時間
```

### 注意事項 & 陷阱
- 需偽裝 User-Agent: `Mozilla/5.0 ... Chrome/120.0.0.0`
- 不需 Cookie/登入即可瀏覽案件列表
- 請求間隔建議 ≥3 秒
- 案件約 1420+ 筆 (2026-06-06 觀察)
- **404 陷阱:** `/search?category=ai` → 404，不要用此路徑
- 新案件時間標示為「X小時前/昨天/前天」，無精確時間戳
- 有些案件無明確預算（顯示「預算詳談」）

---

## 2. JOBALL (joball.tw) — ⚠️ 非案件平台

**URL:** `https://joball.tw/`
**類型:** 作品集/專家展示平台

頁面主要內容:
- **最新作品** — 專家上傳的作品展示 (LOGO設計、海報設計等)
- **最近活躍的專家** — 自由工作者個人頁面
- **無案件發包列表** — 沒有像 Tasker 的「我要接案」案件列表

**爬蟲價值:** 低 — 沒有結構化的接案案件資料。

---

## 3. 104外包網 (case.104.com.tw) — 🚫 阻擋

**URL:** `https://case.104.com.tw/`
**狀態:** 被封鎖 — 瀏覽工具回報 `Blocked: private or internal network address`

**替代方案:**
- 104 的 job search (`www.104.com.tw/jobs/search/`) 可爬，但那是正職工作而非接案
- 不建議作為爬蟲目標

---

## 4. PRO360達人網 (pro360.com.tw) — 🚫 需登入

**URL:** `https://www.pro360.com.tw/proposals/`
**狀態:** 404
**原因:** 提案列表需要登入後才能瀏覽，或該路徑已改

**不建議作為爬蟲目標**

---

## 5. 1111外包網 (case.1111.com.tw) — 🚫 阻擋

**URL:** `https://case.1111.com.tw/`
**狀態:** 被封鎖

---

## 6. 小任務 (task.tw) — ✅ 可爬（部分資料）

**URL:** `https://task.tw/list`
**類型:** 混合 — SSR 基礎內容 + JS 路由，無個案專屬連結

### DOM 結構

```python
# 每行任務是一個 <div> 或 <li> 包含時間戳
task_blocks = soup.find_all(lambda tag: (
    tag.name in ["div", "li"] and
    bool(re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", tag.get_text()))
))

# 各欄位
re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)  # 日期
# 標題 = 日期前的文字
# 分類 = 跑腿/家教/活動支援/多媒體/文書/其他（出現在文字中）
# 標籤 = 急件/個人可/無經驗可/需附作品/長期合作/單次任務
```

### 限制
- ❌ **無個案專屬連結** — SPA 路由，無法直接訪問單一案件
- ❌ **無預算資訊** — 列表頁不顯示金額
- ✅ 有精確時間戳（`2026-06-06 18:39:46`）
- ✅ 有分類標籤
- 約 400+ 頁資料（2026-06-06 觀察）

## 推薦爬蟲策略

| 優先 | 平台 | 建議 | 說明 |
|------|------|------|------|
| 🥇 | **Tasker出任務** | ✅ 強烈推薦 | SSR，免登入，案件分類完整，每日更新 |
| 🥈 | **小任務** | ✅ 補充 | 有時間戳+分類，無連結/預算 |
| ❌ | JOBALL / PRO360 / 104外包 / 1111外包 | ❌ 跳過 | 需登入或非案件平台 |
