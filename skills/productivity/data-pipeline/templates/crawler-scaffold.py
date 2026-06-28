#!/usr/bin/env python3
"""
Taiwan Freelance Case Crawler — daily crawl + TG push

Usage:
    python3 scripts/crawl_cases.py           # crawl all enabled platforms
    python3 scripts/crawl_cases.py --quiet   # JSON only (for cron)

Dependencies:
    pip install requests beautifulsoup4 chromadb sentence-transformers

Platform notes (verified 2026-06-06):
    ✅ Tasker出任務 — SSR, no login needed, URL: /cases/TK...
    ❌ 104外包網 / 1111外包網 — blocked (private network)
    ❌ PRO360 — requires login
    ⚠️ JOBALL — portfolio showcase, not case listings
"""

import json
import hashlib
import os
import re
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────────────────

# Telegram: fallback to .env if env vars not set (e.g. cron no_agent mode)
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

PLATFORMS = {
    "tasker": {
        "name": "Tasker出任務",
        "base_url": "https://www.tasker.com.tw",
        "url": "https://www.tasker.com.tw/cases",
        "params": {"page": 1},
    },
}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
}

# ── Data model ──────────────────────────────────────────────────────

@dataclass
class Case:
    platform: str
    title: str
    budget: str
    location: str
    description: str
    url: str
    category: str
    tags: list
    posted_ago: str
    proposers: str

    def fingerprint(self) -> str:
        """Dedup key: platform + title"""
        return hashlib.md5(f"{self.platform}|{self.title}".encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)


# ── Tasker Parser ───────────────────────────────────────────────────
# Verified: 2026-06-06
# URL pattern: /cases/TK... (NOT /case/̨— that returns 404)

def parse_tasker_page(html: str) -> list[Case]:
    """Parse Tasker出任務 case listing page."""
    soup = BeautifulSoup(html, "html.parser")
    cases = []

    # Each case is inside a <li>, linked via <a href="/cases/TK...">
    for a_tag in soup.find_all("a", href=re.compile(r"^/cases/TK")):
        full_text = a_tag.get_text(" ", strip=True)
        full_text = re.sub(r"\s+", " ", full_text)

        title_el = a_tag.select_one("h2")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        # Budget
        budget = ""
        m = re.search(r"\$[\d,]+(~[\d,]+)?", full_text)
        if m:
            budget = m.group(0)
        elif "預算詳談" in full_text:
            budget = "預算詳談"

        # Location
        location = ""
        for loc in ["可遠端", "台北市", "新北市", "桃園市", "台中市",
                     "台南市", "高雄市", "新竹", "基隆"]:
            if loc in full_text:
                location = loc
                break

        # Posted time
        posted_ago = ""
        for t in ["剛剛", "1小時", "2小時", "3小時", "4小時", "5小時",
                  "6小時", "7小時", "8小時", "9小時", "10小時", "11小時",
                  "12小時", "13小時", "14小時", "15小時", "16小時", "17小時",
                  "18小時", "19小時", "20小時", "21小時", "22小時", "23小時",
                  "昨天", "前天", "3天前"]:
            if t in full_text:
                posted_ago = t
                break

        # Proposers
        proposers = ""
        m = re.search(r"(\d+)人提案中", full_text)
        if m:
            proposers = f"{m.group(1)}人提案"

        # Category (from preceding section header)
        category = ""
        prev_header = a_tag.find_previous(["h2", "h3", "sectionheader"])
        if prev_header:
            category = prev_header.get_text(strip=True)

        # Description = full_text minus structured fields
        desc = full_text
        for pat in [title, budget, location, proposers, posted_ago,
                    "我要提案", "可遠端", "急件"]:
            desc = desc.replace(pat, "", 1)
        desc = re.sub(r"\s+", " ", desc).strip()[:300]

        # Tags
        tags = []
        common_tags = [
            "Python", "JavaScript", "React", "Vue", "Node", "Flutter",
            "PHP", "Java", "C#", ".NET", "Go", "Rust", "Swift", "Kotlin",
            "AI應用", "AI 應用", "LLM", "ChatGPT", "OpenAI",
            "平面設計", "LOGO設計", "網頁設計", "UI/UX", "APP開發",
            "影片剪輯", "短影音", "攝影",
            "硬體程式設計", "韌體開發設計", "嵌入式", "IoT",
        ]
        for tag in common_tags:
            if tag in full_text:
                tags.append(tag)

        url = f"https://www.tasker.com.tw{a_tag['href']}"

        cases.append(Case(
            platform="Tasker出任務",
            title=title,
            budget=budget,
            location=location,
            description=desc,
            url=url,
            category=category,
            tags=tags,
            posted_ago=posted_ago,
            proposers=proposers,
        ))

    return cases


# ── Dedup DB (SQLite) ───────────────────────────────────────────────

class SeenDB:
    def __init__(self, path: str = "./seen.db"):
        import sqlite3
        self.conn = sqlite3.connect(path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                fingerprint TEXT PRIMARY KEY,
                title TEXT, platform TEXT, crawled_at TEXT
            )
        """)
        self.conn.commit()

    def is_seen(self, fp: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM seen WHERE fingerprint=?", (fp,)
        ).fetchone() is not None

    def mark_seen(self, case: Case):
        from datetime import datetime, timezone
        self.conn.execute(
            "INSERT OR IGNORE INTO seen VALUES (?,?,?,?)",
            (case.fingerprint(), case.title, case.platform,
             datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0]


# ── Telegram Push ───────────────────────────────────────────────────

def send_tg(text: str) -> bool:
    """Send message via Telegram Bot API. Chunks >4000 chars."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[SKIP] No TG credentials")
        return False

    chunks = []
    while len(text) > 4000:
        at = text.rfind("\n", 0, 4000)
        chunks.append(text[:at] if at > 0 else text[:4000])
        text = text[at:].strip() if at > 0 else text[4000:]
    if text:
        chunks.append(text)

    ok = True
    for chunk in chunks:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": TG_CHAT_ID, "text": chunk,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }, timeout=10,
            )
            if not r.json().get("ok"):
                print(f"[TG WARN] {r.json().get('description','')}", file=sys.stderr)
            time.sleep(0.5)
        except Exception as e:
            print(f"[TG ERROR] {e}", file=sys.stderr)
            ok = False
    return ok


# ── Main ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", "-p", type=int, default=3)
    parser.add_argument("--no-tg", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    db = SeenDB()
    all_new = []

    for name, cfg in PLATFORMS.items():
        if not args.quiet:
            print(f"[{cfg['name']}] crawling {args.pages} pages...")

        for page in range(1, args.pages + 1):
            try:
                params = dict(cfg["params"])
                params["page"] = page
                resp = requests.get(cfg["url"], params=params,
                                    headers=HEADERS, timeout=20)
                resp.raise_for_status()

                cases = parse_tasker_page(resp.text)
                new_count = 0
                for case in cases:
                    if not db.is_seen(case.fingerprint()):
                        db.mark_seen(case)
                        all_new.append(case)
                        new_count += 1

                if not args.quiet:
                    print(f"  p{page}: {len(cases)} cases, {new_count} new")
                time.sleep(2)

            except Exception as e:
                print(f"  p{page} error: {e}", file=sys.stderr)

    # ── Push ──
    if not args.no_tg and all_new:
        lines = [f"📋 新案件 ({len(all_new)} 筆)\n"]
        for c in all_new[:15]:
            parts = [f"[{c.title}]({c.url})"]
            if c.budget: parts.append(c.budget)
            if c.posted_ago: parts.append(c.posted_ago)
            lines.append("• " + " — ".join(parts))
        send_tg("\n".join(lines))

    # ── Output (for cron) ──
    result = {
        "total": len(all_new),
        "db_count": db.count(),
        "platforms": list(PLATFORMS.keys()),
    }
    if args.quiet:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"\n✅ {result['total']} new | DB: {result['db_count']}")


if __name__ == "__main__":
    main()