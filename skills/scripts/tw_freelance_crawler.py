#!/home/hsieh89t_gmail_com/.hermes/scripts/.venv/bin/python3
"""
台灣 AI 接案市場爬蟲 + 統計分析 + LLM 週報

Platforms:
  - Tasker出任務 (tasker.com.tw)  → 完整案件詳情
  - 小任務 (task.tw)              → 列表資料

Modes:
  --daily   (default) 爬新案 + 推播 TG
  --weekly            產出完整 AI 接案市場週報 (LLM)
  --stats             僅輸出統計 JSON

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_HOME_CHANNEL (from ~/.hermes/.env)
     OPENROUTER_API_KEY (for LLM weekly report)
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────────────────

DB_PATH = os.path.expanduser("~/.hermes/scripts/tw_freelance.db")
CRAWL_INTERVAL_SEC = 2
MAX_PAGES_TASKER = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

# TG credentials
TG_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_HOME_CHANNEL", "")
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k == "TELEGRAM_BOT_TOKEN" and not TG_BOT_TOKEN:
                        TG_BOT_TOKEN = v
                    elif k == "TELEGRAM_HOME_CHANNEL" and not TG_CHAT_ID:
                        TG_CHAT_ID = v

# LLM API
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_KEY:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k == "OPENROUTER_API_KEY":
                        OPENROUTER_KEY = v

LLM_MODEL = "deepseek/deepseek-v4-flash"
LLM_BASE_URL = "https://openrouter.ai/api/v1"

# AI keywords
AI_KEYWORDS = [
    "AI", "ai", "人工智慧", "機器學習", "深度學習", "LLM", "大語言模型",
    "ChatGPT", "OpenAI", "Claude", "Gemini", "LangChain", "RAG",
    "prompt", "stable diffusion", "StableDiffusion",
    "computer vision", "影像辨識", "自然語言", "NLP", "自動化",
    "n8n", "Make", "Zapier", "API串接", "爬蟲", "crawler",
    "pytorch", "tensorflow", "huggingface",
    "fine-tune", "微調", "embedding", "vector", "向量",
    "資料分析", "data analysis", "data science",
    "Python", "Node.js", "JavaScript", "React", "Vue",
    "全端", "full stack", "Flutter", "React Native",
    "IoT", "ESP32", "STM32", "Arduino", "嵌入式", "firmware",
    "APP開發", "iOS", "Android",
]

# ── Data Models ─────────────────────────────────────────────────────

@dataclass
class Case:
    platform: str
    title: str
    budget: str = ""
    location: str = ""
    description: str = ""
    url: str = ""
    category: str = ""
    tags: list = field(default_factory=list)
    proposers: str = ""
    posted_ago: str = ""
    posted_date: str = ""
    crawled_at: str = ""

    def fingerprint(self) -> str:
        raw = f"{self.platform}|{self.title}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def is_ai_related(self) -> bool:
        text = f"{self.title} {self.description} {' '.join(self.tags)}".lower()
        for kw in AI_KEYWORDS:
            if kw.lower() in text:
                return True
        return False

    def budget_numeric(self) -> Optional[float]:
        """Extract numeric budget value (low end)."""
        m = re.search(r"\$([\d,]+)", self.budget)
        if m:
            return float(m.group(1).replace(",", ""))
        return None

    def ai_category(self) -> str:
        """Classify AI case into subcategory."""
        t = f"{self.title} {self.description}".lower()
        if any(x in t for x in ["圖像", "影像", "stable diffusion", "midjourney", "dall-e", "圖生成"]):
            return "AI 圖像生成"
        if any(x in t for x in ["文案", "內容", "寫作", "文章", "翻譯"]):
            return "AI 文案/內容"
        if any(x in t for x in ["自動化", "n8n", "make", "zapier", "workflow", "流程"]):
            return "自動化流程"
        if any(x in t for x in ["chatbot", "chatbot", "bot", "客服", "對話"]):
            return "AI 對話/客服"
        if any(x in t for x in ["資料分析", "data分析", "數據", "分析", "dashboard"]):
            return "AI 數據分析"
        if any(x in t for x in ["剪輯", "影片", "短影音", "短視頻", "視頻"]):
            return "AI 影音"
        if any(x in t for x in ["LLM", "RAG", "langchain", "vector", "embedding",
                                 "微調", "fine", "fine-tune", "訓練"]):
            return "LLM/RAG"
        return "其他 AI"


# ── Database ────────────────────────────────────────────────────────

class SeenDB:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        # Create fresh table if not exists
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS seen (
                fingerprint TEXT PRIMARY KEY,
                title TEXT,
                platform TEXT,
                crawled_at TEXT
            );
        """)
        # Add columns that might be missing (old schema)
        for col, col_type in [("category", "TEXT DEFAULT ''"),
                              ("budget", "TEXT DEFAULT ''"),
                              ("budget_num", "REAL DEFAULT NULL"),
                              ("is_ai", "INTEGER DEFAULT 0"),
                              ("ai_category", "TEXT DEFAULT ''"),
                              ("tags", "TEXT DEFAULT ''")]:
            try:
                self.conn.execute(f"ALTER TABLE seen ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # column already exists
        self.conn.commit()

    def is_seen(self, fp: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM seen WHERE fingerprint=?", (fp,))
        return cur.fetchone() is not None

    def mark_seen(self, case: Case):
        budget_num = case.budget_numeric()
        self.conn.execute(
            """INSERT OR IGNORE INTO seen
               (fingerprint, title, platform, category, budget, budget_num,
                is_ai, ai_category, tags, crawled_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (case.fingerprint(), case.title[:200], case.platform,
             case.category[:50], case.budget[:50], budget_num,
             1 if case.is_ai_related() else 0,
             case.ai_category() if case.is_ai_related() else "",
             ",".join(case.tags)[:200],
             case.crawled_at or datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def cleanup(self, days: int = 60):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        self.conn.execute("DELETE FROM seen WHERE crawled_at < ?", (cutoff,))
        self.conn.commit()

    def total_seen(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM seen")
        return cur.fetchone()[0]

    def get_weekly_stats(self, days: int = 7) -> dict:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            "SELECT * FROM seen WHERE crawled_at >= ?", (cutoff,)
        ).fetchall()

        total = len(rows)
        ai_total = sum(1 for r in rows if r["is_ai"])
        by_platform = Counter(r["platform"] for r in rows)
        by_ai_cat = Counter(r["ai_category"] for r in rows if r["is_ai"])

        budgets = sorted(r["budget_num"] for r in rows if r["budget_num"] is not None)

        prev_cutoff = (datetime.now(timezone.utc) - timedelta(days=days * 2)).isoformat()
        prev_rows = self.conn.execute(
            "SELECT COUNT(*) as c FROM seen WHERE crawled_at >= ? AND crawled_at < ?",
            (prev_cutoff, cutoff),
        ).fetchone()
        prev_total = prev_rows["c"] if prev_rows else 0

        return {
            "period_days": days,
            "total_cases": total,
            "prev_period_total": prev_total,
            "change_pct": round(((total - prev_total) / max(prev_total, 1)) * 100, 1),
            "ai_cases": ai_total,
            "ai_pct": round((ai_total / max(total, 1)) * 100, 1),
            "by_platform": dict(by_platform.most_common()),
            "by_ai_category": dict(by_ai_cat.most_common()),
            "budgets": {
                "count": len(budgets),
                "min": budgets[0] if budgets else None,
                "max": budgets[-1] if budgets else None,
                "median": budgets[len(budgets) // 2] if budgets else None,
                "avg": round(sum(budgets) / len(budgets), 0) if budgets else None,
            } if budgets else None,
            "ai_keyword_cases": [r["title"] for r in rows if r["is_ai"]][:50],
        }


# ── Crawlers ────────────────────────────────────────────────────────

def crawl_tasker(page: int = 1) -> list[Case]:
    """Crawl Tasker出任務 cases page."""
    url = f"https://www.tasker.com.tw/cases?page={page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cases = []

    for a_tag in soup.find_all("a", href=re.compile(r"^/cases/TK")):
        href = a_tag.get("href", "")
        url = f"https://www.tasker.com.tw{href}"
        full_text = a_tag.get_text(" ", strip=True)
        full_text = re.sub(r"\s+", " ", full_text)

        h2 = a_tag.select_one("h2")
        title = h2.get_text(strip=True) if h2 else ""

        budget = ""
        m = re.search(r"\$[\d,]+(~[\d,]+)?", full_text)
        if m:
            budget = m.group(0)
        elif "預算詳談" in full_text:
            budget = "預算詳談"

        location = ""
        for loc in ["可遠端", "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市"]:
            if loc in full_text:
                location = loc
                break

        tags = []
        for tag in ["Python", "JavaScript", "React", "Vue", "Node.js", "Flutter",
                     "PHP", "Java", "C#", ".NET", "Go", "Swift", "Kotlin",
                     "AI應用", "AI 應用", "LLM", "ChatGPT", "OpenAI",
                     "平面設計", "LOGO設計", "UI/UX", "APP開發",
                     "影片剪輯", "短影音", "攝影",
                     "硬體程式設計", "韌體開發設計", "嵌入式", "IoT",
                     "ASP.Net", "ASP.NET", "C#", "SQL",
                     "行銷", "SEO", "文案", "翻譯"]:
            if tag in full_text:
                tags.append(tag)

        proposers = ""
        m = re.search(r"(\d+)人提案中", full_text)
        if m:
            proposers = f"{m.group(1)}人提案"

        posted_ago = ""
        for t in ["剛剛", "1小時", "2小時", "3小時", "4小時", "5小時",
                   "6小時", "7小時", "8小時", "9小時", "10小時",
                   "11小時", "12小時", "13小時", "14小時", "15小時",
                   "16小時", "17小時", "18小時", "19小時", "20小時",
                   "21小時", "22小時", "23小時",
                   "昨天", "前天", "3天前", "4天前", "5天前", "6天前", "7天前"]:
            if t in full_text:
                posted_ago = t
                break

        desc = full_text
        if title:
            desc = desc.replace(title, "", 1)
        for pat in [budget, location, proposers, posted_ago, "我要提案", "可遠端", "急件"]:
            desc = desc.replace(pat, "")
        desc = re.sub(r"\s+", " ", desc).strip()[:300]

        if title:
            cases.append(Case(
                platform="Tasker出任務",
                title=title,
                budget=budget,
                location=location,
                description=desc,
                url=url,
                tags=tags,
                proposers=proposers,
                posted_ago=posted_ago,
                crawled_at=datetime.now(timezone.utc).isoformat(),
            ))

    return cases


def crawl_tasktw(page: int = 1) -> list[Case]:
    """Crawl 小任務 task.tw list page."""
    url = "https://task.tw/list"
    if page > 1:
        # task.tw might use pagination via query params
        url = f"https://task.tw/list?page={page}"

    headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cases = []

    # task.tw uses list items (li) for tasks
    # Each task seems to be in a div with text content
    # Look for date/time patterns to identify task entries
    task_blocks = soup.find_all(lambda tag: (
        tag.name in ["div", "li"] and
        bool(re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", tag.get_text()))
    ))

    seen_titles = set()
    for block in task_blocks:
        text = block.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        # Extract title (first meaningful text before date)
        date_m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if not date_m:
            continue
        posted_date = date_m.group(1)

        # Title is text before the date
        title_end = text.find(posted_date)
        title = text[:title_end].strip()
        # Remove common noise
        for noise in ["已結案", "我要接任務", "擅長這個類型的任務嗎"]:
            title = title.replace(noise, "").strip()
        title = re.sub(r"\s+", " ", title).strip()

        if not title or title in seen_titles or len(title) < 3:
            continue
        seen_titles.add(title)

        # Category
        category = ""
        for cat_name in ["跑腿", "家教", "活動支援", "多媒體／設計相關", "文書", "其他"]:
            if cat_name in text:
                category = cat_name
                break

        # Tags
        tags = []
        for t_tag in ["急件", "個人可", "無經驗可", "需附作品", "需開立發票",
                       "長期合作", "單次任務", "小天使分享"]:
            if t_tag in text:
                tags.append(t_tag)

        # Check if it's AI-related
        ai = any(kw.lower() in text.lower() for kw in AI_KEYWORDS)

        # Budget (task.tw doesn't show budget on list page)
        budget = ""
        m = re.search(r"\$[\d,]+", text)
        if m:
            budget = m.group(0)

        if title:
            case = Case(
                platform="小任務",
                title=title,
                budget=budget,
                category=category,
                tags=tags,
                description=text[:200],
                posted_date=posted_date,
                url="https://task.tw/list",
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )
            cases.append(case)

    return cases


# ── Statistics ──────────────────────────────────────────────────────

def get_top_cases(stats: dict, n: int = 5) -> list[dict]:
    """Get top AI cases by budget for recommendations."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    db = SeenDB()
    rows = db.conn.execute(
        "SELECT title, platform, budget, budget_num, is_ai, ai_category, crawled_at "
        "FROM seen WHERE crawled_at >= ? AND is_ai = 1 AND budget_num IS NOT NULL "
        "ORDER BY budget_num DESC LIMIT ?",
        (cutoff, n),
    ).fetchall()

    results = []
    for r in rows:
        results.append({
            "title": r["title"],
            "platform": r["platform"],
            "budget": f"${r['budget_num']:,.0f}" if r["budget_num"] else "",
            "category": r["ai_category"],
        })
    return results


# ── LLM Weekly Report ──────────────────────────────────────────────

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via OpenRouter."""
    if not OPENROUTER_KEY:
        return "[LLM 不可用：無 API Key]"

    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 2048,
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM 錯誤: {e}]"


def generate_weekly_report(days: int = 7) -> str:
    """Generate full AI freelance market weekly report."""
    db = SeenDB()
    stats = db.get_weekly_stats(days=days)
    top_cases = get_top_cases(stats, n=10)

    # Build data payload for LLM
    data = {
        "period": f"過去 {days} 天",
        "stats": stats,
        "top_ai_cases": top_cases,
        "ai_case_titles": stats.get("ai_keyword_cases", [])[:30],
    }

    system_prompt = """你是一位專業的 AI 接案市場分析師。你的任務是根據提供的數據，產出一份結構化的「每週 AI 接案市場週報」。

請使用台灣繁體中文（正體中文），語氣專業但親切。請用數據說話，盡量帶出具體的數字、預算範圍、比例。

輸出格式必須嚴格遵循以下結構：

**1. 本週 AI 接案市場概況**
   - AI 相關案件總數（與上週比較）
   - 主要來源平台
   - 案件類型分布

**2. 熱門 AI 應用需求排名**（Top 5）
   附上簡短解釋

**3. 預算水平分析**
   - 低、中、高案件分布
   - 最高預算的案件類型

**4. 新興趨勢與機會**
   - 本週新出現的 AI 應用方向
   - 值得關注的市場信號

**5. 本週推薦關注案件**
   列出 3 件最值得關注的案件"""

    user_prompt = f"""以下是本週台灣接案平台的爬蟲數據，請根據這些數據產出週報：

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

請產出完整的週報（Markdown 格式）。"""

    report = call_llm(system_prompt, user_prompt)

    # Add header
    today = datetime.now().strftime("%Y/%m/%d")
    header = f"📊 *AI 接案市場週報* — {today}\n\n"
    return header + report


def _generate_briefing(data: dict) -> str:
    """Generate daily AI market briefing in Telegram-optimized format."""
    sys_prompt = """你是一位 AI 接案市場分析師。根據提供的數據，產出每日市場快訊。

硬規則：
1. 使用台灣繁體中文，技術術語保留英文（LLM、RAG、prompt 等）
2. 預算統一用 NT$; 找不到寫「資料不足」
3. 禁用 Markdown 表格、程式碼區塊、深度縮排（Telegram 顯示會亂）
4. emoji 限視覺區隔用途，每段 1-3 個
5. 連結必須基於真實 URL，不要編造
6. 找不到的欄位寫「資料不足」
7. 投案分析用客觀第三人稱
8. 如果數據不足（案件太少），誠實反映並說明

輸出格式嚴格如下，直接填內容：

━━━━━━━━━━━━━
🎯 今日 AI 接案快訊
📆 {today} · 第{week}週 · {weekday}
━━━━━━━━━━━━━

🔥 熱門案件 Top 5

1️⃣ {title}
💰 {budget} · 🏢 {platform}
⏱ {posted_ago} · 🏷 {tags}
🔗 {url}

2️⃣ ...

━━━━━━━━━━━━━

📊 市場結構

🧩 案件類型
・{type}:{pct}%
・...

💰 預算分布
・低預算 <1 萬:{n} 筆
・中預算 1-5 萬:{n} 筆
・高預算 5-10 萬:{n} 筆
・企業級 >10 萬:{n} 筆

📈 市場熱度
今日約 {n} 筆 · vs 本週平均 {熱絡/持平/冷清}

━━━━━━━━━━━━━

🔑 今日熱門關鍵詞

1. {keyword}({n}筆)
2. ...

━━━━━━━━━━━━━

✨ 新興需求

🆕 {trend}
📝 {explanation}

━━━━━━━━━━━━━

💡 重點推案

🎯 {case}
💬 {analysis}
🔗 {url}

━━━━━━━━━━━━━

📌 明日觀察
・{observation}

━━━━━━━━━━━━━"""

    user_prompt = f"""以下是本日爬蟲數據，請產出每日 AI 接案快訊：

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

請直接產出完整 Telegram 格式內容（無須額外說明）。"""

    report = call_llm(sys_prompt, user_prompt)
    today = data.get("today", datetime.now().strftime("%Y/%m/%d"))
    return report


# ── Telegram ────────────────────────────────────────────────────────

def send_tg(text: str, silent: bool = False) -> bool:
    """Send message via Telegram."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return False

    chunks = []
    while len(text) > 4000:
        split_at = text.rfind("\n", 0, 4000)
        if split_at < 0:
            split_at = 4000
        chunks.append(text[:split_at])
        text = text[split_at:].strip()
    if text:
        chunks.append(text)

    ok = True
    for chunk in chunks:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": TG_CHAT_ID,
                    "text": chunk,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                    "disable_notification": silent,
                },
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                pass  # silent fail
            time.sleep(0.5)
        except Exception:
            ok = False
    return ok


def format_daily_push(new_cases: list[Case]):
    """Format daily new cases push."""
    ai_cases = [c for c in new_cases if c.is_ai_related()]

    lines = []

    if ai_cases:
        lines.append(f"🤖 *AI 相關新案*（{len(ai_cases)} 筆）\n")
        for c in ai_cases[:6]:
            parts = [f"[{c.title}]({c.url})"]
            if c.budget:
                parts.append(c.budget)
            if c.posted_ago:
                parts.append(c.posted_ago)
            lines.append(f"• {' — '.join(parts)}")
            tag = c.ai_category()
            if tag:
                lines.append(f"  `{tag}`")
        if len(ai_cases) > 6:
            lines.append(f"\n... 還有 {len(ai_cases) - 6} 筆")
        lines.append("")

    if new_cases:
        lines.append(f"📋 *全部新案*（{len(new_cases)} 筆）\n")
        for c in new_cases[:10]:
            parts = [f"[{c.title}]({c.url})"]
            if c.budget:
                parts.append(c.budget)
            if c.posted_ago:
                parts.append(c.posted_ago)
            lines.append(f"• {' — '.join(parts)}")
        if len(new_cases) > 10:
            lines.append(f"\n... 還有 {len(new_cases) - 10} 筆")

    ts = datetime.now().strftime("%m/%d %H:%M")
    ai_count = sum(1 for c in new_cases if c.is_ai_related())
    lines.append(f"\n🕐 {ts} | AI {ai_count}/{len(new_cases)} 筆")
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="台灣 AI 接案市場分析")
    parser.add_argument("--daily", action="store_true", help="每日爬蟲+推播(預設)")
    parser.add_argument("--weekly", action="store_true", help="週報模式")
    parser.add_argument("--briefing", action="store_true", help="每日快訊模式(TG格式)")
    parser.add_argument("--stats", action="store_true", help="僅輸出統計")
    parser.add_argument("--days", "-d", type=int, default=7, help="統計天數")
    parser.add_argument("--pages", "-p", type=int, default=MAX_PAGES_TASKER, help="爬取頁數")
    parser.add_argument("--no-tg", action="store_true", help="不推TG")
    parser.add_argument("--quiet", "-q", action="store_true", help="純JSON輸出")
    args = parser.parse_args()

    mode = "briefing" if args.briefing else "weekly" if args.weekly else "stats" if args.stats else "daily"

    db = SeenDB()
    db.cleanup(days=60)

    # ── Daily briefing ──
    if mode == "briefing":
        if not args.quiet:
            print("📋 生成每日 AI 接案快訊...", file=sys.stderr)
        # Crawl latest data
        all_cases = []
        for page in range(1, min(args.pages, 2)):
            for c in crawl_tasker(page):
                if not db.is_seen(c.fingerprint()):
                    db.mark_seen(c)
                all_cases.append(c)
            time.sleep(CRAWL_INTERVAL_SEC)
        for c in crawl_tasktw():
            if not db.is_seen(c.fingerprint()):
                db.mark_seen(c)
            all_cases.append(c)

        # Get weekly stats for context
        stats = db.get_weekly_stats(days=args.days)

        # Build data payload for LLM briefing
        ai_cases_7d = db.conn.execute(
            "SELECT title, platform, budget, budget_num, ai_category, tags, crawled_at "
            "FROM seen WHERE crawled_at >= ? AND is_ai = 1 "
            "ORDER BY crawled_at DESC LIMIT 30",
            ((datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat(),)
        ).fetchall()

        briefing_data = {
            "today": datetime.now().strftime("%Y/%m/%d %A"),
            "week_number": datetime.now().isocalendar()[1],
            "stats": stats,
            "ai_cases_7d": [dict(r) for r in ai_cases_7d],
        }

        report = _generate_briefing(briefing_data)
        if args.no_tg:
            print(report)
        else:
            ok = send_tg(report, silent=False)
            if not args.quiet:
                print(f"✅ TG 快訊推送: {'成功' if ok else '失敗'}", file=sys.stderr)
            if not ok:
                print(report)
        return

    # ── Stats only ──
    if mode == "stats":
        stats = db.get_weekly_stats(days=args.days)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    # ── Weekly report ──
    if mode == "weekly":
        if not args.quiet:
            print("📊 生成 AI 接案市場週報...")
        report = generate_weekly_report(days=args.days)
        if args.no_tg:
            print(report)
        else:
            ok = send_tg(report, silent=False)
            if not args.quiet:
                print(f"✅ TG 週報推送: {'成功' if ok else '失敗'}")
            if not ok:
                print(report)
        return

    # ── Daily crawl ──
    all_new: list[Case] = []

    # Tasker
    for page in range(1, args.pages + 1):
        if not args.quiet:
            print(f"🔍 [Tasker] 第 {page} 頁...", end=" ", flush=True)
        try:
            cases = crawl_tasker(page)
            new_count = 0
            for c in cases:
                if not db.is_seen(c.fingerprint()):
                    db.mark_seen(c)
                    all_new.append(c)
                    new_count += 1
            if not args.quiet:
                print(f"{len(cases)} 案, {new_count} 新")
            time.sleep(CRAWL_INTERVAL_SEC)
        except Exception as e:
            if not args.quiet:
                print(f"❌ {e}", file=sys.stderr)

    # 小任務
    if not args.quiet:
        print(f"🔍 [小任務] 爬取中...", end=" ", flush=True)
    try:
        cases = crawl_tasktw(page=1)
        new_count = 0
        for c in cases:
            if not db.is_seen(c.fingerprint()):
                db.mark_seen(c)
                all_new.append(c)
                new_count += 1
        if not args.quiet:
            print(f"{len(cases)} 案, {new_count} 新")
        time.sleep(CRAWL_INTERVAL_SEC)
    except Exception as e:
        if not args.quiet:
            print(f"❌ {e}", file=sys.stderr)

    ai_new = [c for c in all_new if c.is_ai_related()]

    summary = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "new_cases": len(all_new),
        "ai_cases": len(ai_new),
        "platforms": sorted(set(c.platform for c in all_new)),
        "db_total": db.total_seen(),
        "tg_sent": False,
    }

    # TG Push
    if not args.no_tg and all_new:
        msg = format_daily_push(all_new)
        tg_ok = send_tg(msg, silent=False)
        summary["tg_sent"] = tg_ok
        if not args.quiet:
            print(f"📨 TG 推送: {'✅' if tg_ok else '❌'}")

    if not args.quiet:
        print(f"\n📊 新 {len(all_new)} | AI {len(ai_new)} | DB {db.total_seen()}")
        if ai_new:
            cats = Counter(c.ai_category() for c in ai_new)
            print(f"   分類: {dict(cats.most_common(5))}")

    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()