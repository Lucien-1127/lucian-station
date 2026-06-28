#!/usr/bin/env python3
"""
derive_lesson.py — Template-Driven Lesson Derivation
LLM 只讀不寫：所有 lesson 由本 script 根據 outcome 模板生成。
冷啟動保護：低信心 outcome 直接 skip，不生成無意義 lesson。
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

# 信號清單（與 recalc_weights.py 同步）
SIGNALS = ["quality_score", "recency", "source_trust"]

# Template-driven lesson 生成 prompt（給 LLM 用的格式，不是 LLM 生成）
LESSON_TEMPLATES = {
    "WORKED": [
        "當 信號 Z 為 {z_value} 時，採取了 {action}，結果為 {outcome}。",
        "在 {context} 情境下，{approach} 方法有效。",
    ],
    "FAILED": [
        "當 {trigger} 時，嘗試 {approach} 導致 {failure_mode}。",
        "在 {context} 情境下，{method} 方法失效，因為 {reason}。",
    ],
}


def compute_signal_profile(outcome: dict) -> dict:
    """從 outcome 計算信號強度剖面。"""
    snapshot = outcome.get("signal_snapshot", {})
    result = {}
    for sig in SIGNALS:
        raw = snapshot.get(sig)
        if raw is None:
            # 沒有 snapshot 時，根據 outcome_value 推估
            ov = outcome.get("outcome_value", 0)
            if ov > 0:
                result[sig] = 0.7  # 預設正向 outcome 的基礎分
            else:
                result[sig] = 0.4
        else:
            result[sig] = float(raw)
    return result


def derive_single_outcome(outcome: dict, dry_run: bool = False) -> Optional[dict]:
    """
    對單筆 outcome 執行 template-driven lesson 衍生。
    回傳 lesson dict，或 None（跳過）。
    """
    outcome_value = outcome.get("outcome_value")
    if outcome_value is None:
        return None

    # 信心閾值：outcome_value 太小（趨近 0）時跳過
    if abs(outcome_value) < 0.1:
        return None  # 模糊結果，跳過

    # 計算信號剖面
    profile = compute_signal_profile(outcome)

    # 決定 lesson 類型
    is_positive = outcome_value > 0

    # Template-driven lesson 生成（不走 LLM，直接套模板）
    if is_positive:
        lesson_type = "WORKED"
        prefer, avoid = _build_worked(outcome, profile)
    else:
        lesson_type = "FAILED"
        prefer, avoid = _build_failed(outcome, profile)

    # 決定主要信號（影響最大的那個）
    main_signal = max(profile, key=profile.get)  # type: ignore[arg-type]

    lesson = {
        "id": str(uuid.uuid4()),
        "outcome_id": outcome.get("id", ""),
        "task_type": outcome.get("task_type", "general"),
        "PREFER": prefer,
        "AVOID": avoid,
        "WORKED": [f"{lesson_type} 案例"] if is_positive else [],
        "FAILED": [] if is_positive else [f"{lesson_type} 案例"],
        "confidence": min(1.0, abs(outcome_value)),
        "main_signal": main_signal,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": "2.0",
    }
    return lesson


def _build_worked(outcome: dict, profile: dict) -> tuple[list[str], list[str]]:
    """根據正向 outcome 生成 PREFER / AVOID。"""
    main_signal = max(profile, key=profile.get)  # type: ignore[arg-type]
    prefer = [
        f"當 {main_signal} 指標偏高時，維持當前策略",
        f"source_trust ≥ 0.8 時，信號可信度高，可直接採用",
    ]
    avoid = [
        f"避免在所有信號同時低迷時做高風險決策",
    ]
    return prefer, avoid


def _build_failed(outcome: dict, profile: dict) -> tuple[list[str], list[str]]:
    """根據負向 outcome 生成 PREFER / AVOID。"""
    main_signal = min(profile, key=profile.get)  # type: ignore[arg-type]
    prefer = [
        f"當 {main_signal} 指標偏低時，先暫緩決策，收集更多資料",
    ]
    avoid = [
        f"避免在 source_trust < 0.5 時盲目採用單一來源的資訊",
        f"避免在 recency 低的歷史資料上做長期判斷",
    ]
    return prefer, avoid


def derive_batch(outcomes: list[dict], dry_run: bool = False) -> list[dict]:
    """對多筆 outcomes 批次衍生 lessons。"""
    lessons = []
    for outcome in outcomes:
        lesson = derive_single_outcome(outcome, dry_run=dry_run)
        if lesson:
            lessons.append(lesson)
    return lessons


if __name__ == "__main__":
    import json
    from pathlib import Path
    test_outcome = {
        "id": "test-001",
        "outcome_value": 0.8,
        "task_type": "research",
        "signal_snapshot": {"quality_score": 0.9, "recency": 0.7, "source_trust": 0.6},
    }
    lesson = derive_single_outcome(test_outcome)
    print(json.dumps(lesson, ensure_ascii=False, indent=2))