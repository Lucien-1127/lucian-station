#!/usr/bin/env python3
"""
apply_hard_track.py — Cooldowns + Blocklist 機械化寫入
寫入後 LLM 看不到，由 apply_hard_track.check() 在決策前呼叫。
不生成任何文字 lesson，純機械過濾。
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# 預設 cooldown 有效期（分鐘）
DEFAULT_COOLDOWN_MINUTES = 30

# 全域狀態檔案（與 self_learning_cycle.py 共用路徑）
def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"

STATE_FILE = _data_dir() / "hard_track.json"


def load_hard_track() -> dict:
    """讀取 Hard Track 狀態。"""
    if not STATE_FILE.exists():
        return {"cooldowns": {}, "blocklist": [], "version": "2.0"}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"cooldowns": {}, "blocklist": [], "version": "2.0"}


def save_hard_track(state: dict) -> None:
    """寫入 Hard Track 狀態。"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def is_blocked(entity: str) -> bool:
    """檢查 entity 是否在 blocklist。"""
    state = load_hard_track()
    return any(e.get("entity") == entity for e in state.get("blocklist", []))


def is_cooldown_active(entity: str) -> tuple[bool, Optional[str]]:
    """檢查 entity 是否在 cooldown 中。回傳 (is_active, reason)。"""
    state = load_hard_track()
    cooldowns = state.get("cooldowns", {})
    if entity not in cooldowns:
        return False, None
    entry = cooldowns[entity]
    until = datetime.fromisoformat(entry["until"])
    if datetime.now(timezone.utc) < until:
        return True, entry.get("reason")
    else:
        # cooldown 過期，移除
        del cooldowns[entity]
        save_hard_track(state)
        return False, None


def add_cooldown(entity: str, reason: str, minutes: int = DEFAULT_COOLDOWN_MINUTES) -> None:
    """新增 cooldown 條目。"""
    state = load_hard_track()
    state.setdefault("cooldowns", {})[entity] = {
        "until": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
        "reason": reason,
        "added_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_hard_track(state)


def add_blocklist(entity: str, reason: str) -> None:
    """新增 blocklist 條目（永久）。"""
    state = load_hard_track()
    existing = [e.get("entity") for e in state.get("blocklist", [])]
    if entity not in existing:
        state.setdefault("blocklist", []).append({
            "entity": entity,
            "reason": reason,
            "added_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    save_hard_track(state)


def remove_blocklist(entity: str) -> bool:
    """移除 blocklist 條目。回傳是否真的移除了。"""
    state = load_hard_track()
    before = len(state.get("blocklist", []))
    state["blocklist"] = [e for e in state.get("blocklist", []) if e.get("entity") != entity]
    removed = len(state.get("blocklist", [])) < before
    if removed:
        save_hard_track(state)
    return removed


def run_cycle(
    cooldowns: dict,
    blocklist: list,
    verbose: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    在每個 self_learning_cycle 執行時呼叫。
    清理過期 cooldowns，更新 blocklist。
    回傳：
      active_cooldowns: list[str]
      blocked_signals: list[str]
      expired: list[str]
    """
    if not dry_run:
        state = load_hard_track()
    else:
        state = {"cooldowns": cooldowns or {}, "blocklist": blocklist or []}

    now = datetime.now(timezone.utc)
    expired = []
    active = []
    still_blocked = []

    # 清理過期 cooldowns
    for entity, entry in list(state.get("cooldowns", {}).items()):
        until = datetime.fromisoformat(entry["until"])
        if now >= until:
            expired.append(entity)
            del state["cooldowns"][entity]
            if verbose:
                print(f"  [CLEAN] cooldown 過期: {entity}")

    # 檢查 blocklist
    for entry in state.get("blocklist", []):
        still_blocked.append(entry["entity"])

    if not dry_run:
        save_hard_track(state)

    return {
        "active_cooldowns": active,
        "blocked_signals": still_blocked,
        "expired": expired,
        "cooldowns": state.get("cooldowns", {}),
        "blocklist": state.get("blocklist", []),
    }


def check(entity: str) -> tuple[bool, str]:
    """
    在每個決策前呼叫。檢查 entity 是否被 Hard Track 攔截。
    回傳 (blocked: bool, reason: str)
    """
    blocked, reason = is_cooldown_active(entity)
    if blocked:
        return True, f"cooldown: {reason}"

    if is_blocked(entity):
        return True, "blocklist"

    return False, ""


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        entity = sys.argv[2] if len(sys.argv) > 2 else "test_entity"
        blocked, reason = check(entity)
        print(f"check('{entity}'): blocked={blocked}, reason={reason}")
    else:
        # 測試
        add_cooldown("test_signal", "示範原因", minutes=1)
        blocked, reason = check("test_signal")
        print(f"After add_cooldown: blocked={blocked}, reason={reason}")