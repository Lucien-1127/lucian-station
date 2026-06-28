#!/usr/bin/env python3
"""
evolve_thresholds.py — 閾值自動演化
每 N 筆結果，根據贏家/輸家的 signal_snapshot 重新計算目標閾值，
nudge config 不超過 10%，防止單次 streak 翻轉策略。
冷啟動保護：sample_count < 20 時 skip。
"""

import json
import statistics
from pathlib import Path
from typing import Optional

SIGNALS = ["quality_score", "recency", "source_trust"]
DEFAULT_MIN_SAMPLES = 20
NUDGE_CAP = 0.10  # 單次最大調整幅度（10%）


def evolve_thresholds(
    outcomes: list[dict],
    current_thresholds: Optional[dict] = None,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> dict:
    """
    執行閾值演化。
    回傳：
      status: cold_start | no_change | updated
      new_thresholds: dict（只有 status=updated 時有值）
    """
    total = len(outcomes)
    if total < min_samples:
        return {"status": "cold_start", "sample_count": total}

    recent = outcomes[-30:]  # 滑動窗口
    wins = [r for r in recent if r.get("outcome_value", 0) > 0]
    losses = [r for r in recent if r.get("outcome_value", 0) <= 0]

    if not wins or not losses:
        return {"status": "insufficient_contrast"}

    # 計算各信號在 wins vs losses 的分佈差異
    new_thresholds = (current_thresholds or {}).copy()

    for sig in SIGNALS:
        win_vals = [r.get("signal_snapshot", {}).get(sig, 0.5) for r in wins]
        loss_vals = [r.get("signal_snapshot", {}).get(sig, 0.5) for r in losses]

        if len(win_vals) < 2 or len(loss_vals) < 2:
            continue

        # 目標閾值 = wins 的 25th percentile（低標）
        import statistics as stat
        win_25 = stat.quantiles(win_vals, n=4)[0] if len(win_vals) >= 4 else min(win_vals)

        if sig not in new_thresholds:
            new_thresholds[sig] = {"threshold": 0.5, "history": []}

        current_t = new_thresholds[sig]["threshold"]
        # Nudge cap：單次變化不超過 NUDGE_CAP
        max_delta = current_t * NUDGE_CAP
        delta = win_25 - current_t
        nudge = max(-max_delta, min(max_delta, delta))
        new_t = round(current_t + nudge, 4)
        new_t = max(0.1, min(0.9, new_t))

        new_thresholds[sig]["threshold"] = new_t
        new_thresholds[sig].setdefault("history", []).append({
            "at": total,
            "win_25": round(win_25, 4),
            "new_t": new_t,
        })

    changed = any(
        new_thresholds[sig]["threshold"] != (current_thresholds or {}).get(sig, {}).get("threshold", 0.5)
        for sig in SIGNALS
    )

    result = {
        "version": "2.0",
        "sample_count": total,
        "thresholds": new_thresholds,
    }

    return {"status": "updated", "new_thresholds": result} if changed else {"status": "no_change"}


if __name__ == "__main__":
    # 測試
    test_outcomes = [
        {"outcome_value": 0.8, "signal_snapshot": {"quality_score": 0.9, "recency": 0.7, "source_trust": 0.6}},
        {"outcome_value": -0.3, "signal_snapshot": {"quality_score": 0.3, "recency": 0.4, "source_trust": 0.5}},
    ] * 10
    result = evolve_thresholds(test_outcomes)
    print(json.dumps(result, ensure_ascii=False, indent=2))