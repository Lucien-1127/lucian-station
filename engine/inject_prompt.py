#!/usr/bin/env python3
"""
inject_prompt.py — 三層 Prompt Injection 生成器
PINNED:  Darwin 信號加權表（rendered from signal_weights.json）
ROLE:    role-matched PREFER/AVOID lesson 子集（tag 匹配）
RECENT:   WORKED/FAILED 完整 lesson（全任務共享）
THRESH:  threshold block（可選）

格式：輸出 Markdown 文字，直接注入 System Prompt / Role Block / Context
"""

import json
from pathlib import Path
from typing import Optional

# 預設 injection 容量上限（token 估算）
CAPS = {
    "pinned": 600,   # PINNED tier 最大 tokens
    "role": 800,     # ROLE-MATCHED 最大 tokens
    "recent": 1200,  # RECENT 最大 tokens
}

# 資料檔案路徑
def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"

OUTCOMES_FILE = _data_dir() / "outcome_records.jsonl"
LESSONS_FILE = _data_dir() / "lessons.jsonl"
WEIGHTS_FILE = _data_dir() / "signal_weights.jsonl"
THRESHOLDS_FILE = _data_dir() / "thresholds.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    """讀取 JSONL，回傳 list of dict。"""
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _render_bar(w: float) -> str:
    """將權重渲染為視覺化長條圖（0.5~2.0 → 0~10 格）。"""
    filled = int(round((w - 0.5) / 0.15)) if w >= 0.5 else 0
    filled = max(0, min(10, filled))
    return "█" * filled + "░" * (10 - filled)


def build_pinned_block(weights: dict) -> str:
    """建構 PINNED 層：Darwin 信號加權表。"""
    if not weights:
        return ""

    weights_data = weights.get("weights", {})
    if not weights_data:
        return ""

    lines = [
        "## 📊 Darwin 信號權重快照",
        "| 信號 | 權重 | 視覺化 |",
        "|------|------|--------|",
    ]
    for sig, data in weights_data.items():
        w = data.get("w", 1.0)
        bar = _render_bar(w)
        lines.append(f"| `{sig}` | `{w:.3f}` | `{bar}` |")

    lines.append("")
    return "\n".join(lines)


def build_role_block(
    lessons: list[dict],
    role: str = "default",
    tags: Optional[list[str]] = None,
    max_tokens: int = 800,
) -> str:
    """
    建構 ROLE-MATCHED 層：PREFER / AVOID 精華。
    依 task_type 或 tags 篩選，TRUNCATE 到 max_tokens。
    """
    if not lessons:
        return ""

    tags = tags or []
    # 優先匹配 role，再匹配 tags
    matched = []
    for lesson in lessons:
        lt = lesson.get("task_type", "")
        lt_tags = lesson.get("tags", [])
        if lt == role or any(t in lt_tags for t in tags):
            matched.append(lesson)

    # 取最新 5 筆
    matched = matched[-5:] if len(matched) > 5 else matched
    if not matched:
        return ""

    lines = ["## 🧭 角色匹配教訓", ""]
    for lesson in matched:
        pref = lesson.get("PREFER", [])
        avd = lesson.get("AVOID", [])
        if pref:
            lines.append("### ✅ PREFER")
            for p in pref:
                lines.append(f"- {p}")
        if avd:
            lines.append("### ❌ AVOID")
            for a in avd:
                lines.append(f"- {a}")
        lines.append("")

    content = "\n".join(lines)
    # TRUNCATE 到 max_tokens（粗估：每個中文字 = 2 chars / 0.5 token）
    char_limit = int(max_tokens * 2)
    if len(content) > char_limit:
        content = content[:char_limit] + "\n... (已截斷)"
    return content


def build_recent_block(
    lessons: list[dict],
    max_tokens: int = 1200,
) -> str:
    """
    建構 RECENT 層：最近 N 筆 WORKED / FAILED 完整 lesson。
    """
    if not lessons:
        return ""

    # 取最新 3 筆（同時有 WORKED 或 FAILED 的 lesson）
    recent = [l for l in lessons[-10:] if l.get("WORKED") or l.get("FAILED")][-3:]

    lines = ["## 📎 最近案例", ""]
    for lesson in recent:
        worked = lesson.get("WORKED", [])
        failed = lesson.get("FAILED", [])
        if worked:
            lines.append("### ✅ WORKED")
            for w in worked:
                lines.append(f"- {w}")
        if failed:
            lines.append("### ❌ FAILED")
            for f in failed:
                lines.append(f"- {f}")
        lines.append("")

    content = "\n".join(lines)
    char_limit = int(max_tokens * 2)
    if len(content) > char_limit:
        content = content[:char_limit] + "\n... (已截斷)"
    return content


def build_thresholds_block(thresholds: dict) -> str:
    """建構 Threshold block（可選）。"""
    if not thresholds:
        return ""

    th = thresholds.get("thresholds", {})
    if not th:
        return ""

    lines = ["## 🎯 目標閾值", ""]
    for sig, data in th.items():
        t = data.get("threshold", 0.5)
        lines.append(f"- `{sig}`: {t:.2f}")

    return "\n".join(lines)


def build_injection(
    role: str = "default",
    tags: Optional[list[str]] = None,
    caps: Optional[dict] = None,
    weights: Optional[dict] = None,
    thresholds: Optional[dict] = None,
    lessons: Optional[list[dict]] = None,
) -> str:
    """
    主要產出函式。組裝三層 injection 文字。
    """
    tags = tags or []
    caps = caps or CAPS
    lessons = lessons or _read_jsonl(LESSONS_FILE)
    weights = weights or _read_jsonl(WEIGHTS_FILE)
    thresholds = thresholds or _read_jsonl(THRESHOLDS_FILE)

    # 若 weights/thresholds 是 list（從 JSONL 讀，取最新一筆記錄）
    if isinstance(weights, list):
        weights = (weights[-1] if weights else {}) or {}
    if isinstance(thresholds, list):
        thresholds = (thresholds[-1] if thresholds else {}) or {}

    parts = []

    # PINNED: Darwin weights（永久固定，最優先）
    pw = build_pinned_block(weights or {})
    if pw:
        parts.append(pw)

    # ROLE-MATCHED: PREFER/AVOID（每次不同 role 動態更換）
    rb = build_role_block(lessons, role, tags, caps["role"])
    if rb:
        parts.append(rb)

    # RECENT: WORKED/FAILED（全任務共享，最後）
    recent = build_recent_block(lessons, caps["recent"])
    if recent:
        parts.append(recent)

    # Thresholds block（可選）
    tb = build_thresholds_block(thresholds or {})
    if tb:
        parts.append(tb)

    return "\n\n".join(parts) if parts else ""


if __name__ == "__main__":
    import sys
    # 測試
    injection = build_injection(role="general")
    print(injection)
    print(f"\n[total: {len(injection)} chars / ~{len(injection)//4} tokens]")