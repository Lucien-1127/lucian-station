#!/usr/bin/env python3
"""
recalc_weights.py — Darwin 信號加權演化
每 N 筆結果（recalcEvery=5）重新計算權重，boost top quartile ×1.05，decay bottom ×0.95。
冷啟動保護：sample_count < minSamples 時不回傳 new_weights。
需要同時有正負樣本才執行演化。
"""

import json
import statistics
from pathlib import Path
from typing import Optional

SIGNALS = ["quality_score", "recency", "source_trust"]
DEFAULT_MIN_SAMPLES = 10


def compute_lift(sig_values: list, winners_outcomes: list, losers_outcomes: list) -> float | None:
    """
    計算單一信號的 lift（win rate difference）。
    winners_outcomes/losers_outcomes 是 outcome_value 正負陣列。
    回傳 None 表示樣本不足。
    """
    wins = sum(1 for v in winners_outcomes if v > 0)
    losses = len(winners_outcomes) - wins
    total = wins + losses
    if total < 4:
        return None

    # 計算該信號高於平均時的 win rate
    avg_sig = statistics.mean(sig_values) if sig_values else 0
    high_sig_wins = sum(1 for v, s in zip(winners_outcomes, sig_values) if s > avg_sig and v > 0)
    high_sig_losses = sum(1 for v, s in zip(losers_outcomes, sig_values) if s > avg_sig and v <= 0)
    high_total = high_sig_wins + high_sig_losses
    if high_total < 2:
        return None

    win_rate = high_sig_wins / high_total
    base_rate = wins / total if total > 0 else 0.5
    lift = win_rate - base_rate
    return lift


def recalculate_signal_weights(
    outcomes: list[dict],
    current_weights: Optional[dict] = None,
    recalc_every: int = 5,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> dict:
    """
    執行 Darwin 信號加權演化。
    回傳 dict：
      status: cold_start | insufficient_contrast | no_signal_change | updated
      new_weights: dict（只有 status=updated 時有值）
    """
    total = len(outcomes)

    # 冷啟動保護
    if total < min_samples:
        return {"status": "cold_start", "sample_count": total, "min_samples": min_samples}

    # 每 recalc_every 筆才執行一次
    if total % recalc_every != 0:
        return {"status": "skipped", "reason": f"total={total} not divisible by recalc_every={recalc_every}"}

    # 分組
    recent = outcomes[-50:]  # 滑動窗口：只看最近 50 筆
    winners = [r["outcome_value"] for r in recent if r.get("outcome_value", 0) > 0]
    losers = [r["outcome_value"] for r in recent if r.get("outcome_value", 0) <= 0]

    if not winners or not losers:
        return {"status": "insufficient_contrast", "wins": len(winners), "losses": len(losers)}

    # 初始化權重
    if current_weights is None:
        current = {
            "version": "2.0",
            "sample_count": 0,
            "weights": {sig: {"w": 1.0, "history": []} for sig in SIGNALS},
        }
    else:
        current = current_weights

    new_weights = {sig: dict(data) for sig, data in current.get("weights", {}).items()}
    changed = False

    for sig in SIGNALS:
        sig_values = []
        sig_winners = []
        sig_losers = []
        for r in recent:
            val = r.get("signal_snapshot", {}).get(sig)
            if val is not None:
                sig_values.append(val)
                if r.get("outcome_value", 0) > 0:
                    sig_winners.append(val)
                else:
                    sig_losers.append(val)

        lift = compute_lift(sig_values, sig_winners, sig_losers)
        if lift is None:
            continue

        current_w = new_weights[sig]["w"]
        if lift > 0.05:
            new_w = round(current_w * 1.05, 4)
        elif lift < -0.05:
            new_w = round(current_w * 0.95, 4)
        else:
            new_w = current_w

        # clamp 到 [0.5, 2.0]
        new_w = max(0.5, min(2.0, new_w))
        new_weights[sig]["w"] = new_w

        # 記錄歷史
        history = new_weights[sig].setdefault("history", [])
        history.append({"at": len(outcomes), "lift": round(lift, 4), "w": new_w})
        if len(history) > 20:
            history[:] = history[-20:]

        if new_w != current_w:
            changed = True

    result = {
        "version": "2.0",
        "updated_at": "",
        "sample_count": total,
        "weights": new_weights,
    }

    if not changed:
        return {"status": "no_signal_change", "weights": new_weights}

    return {"status": "updated", "new_weights": result}


def load_weights(weights_path: Optional[Path] = None) -> dict:
    """讀取最新一筆記錄。"""
    if weights_path is None:
        weights_path = Path(__file__).resolve().parent.parent / "data" / "signal_weights.jsonl"
    if not weights_path.exists():
        return {
            "version": "2.0",
            "sample_count": 0,
            "weights": {sig: {"w": 1.0, "history": []} for sig in SIGNALS},
        }
    records = []
    with open(weights_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records[-1] if records else {
        "version": "2.0",
        "sample_count": 0,
        "weights": {sig: {"w": 1.0, "history": []} for sig in SIGNALS},
    }


if __name__ == "__main__":
    import json, sys
    test_outcomes = [
        {"outcome_value": 0.8, "signal_snapshot": {"quality_score": 0.9, "recency": 0.7, "source_trust": 0.6}},
        {"outcome_value": -0.3, "signal_snapshot": {"quality_score": 0.3, "recency": 0.4, "source_trust": 0.5}},
        {"outcome_value": 0.7, "signal_snapshot": {"quality_score": 0.8, "recency": 0.9, "source_trust": 0.7}},
        {"outcome_value": 0.6, "signal_snapshot": {"quality_score": 0.85, "recency": 0.6, "source_trust": 0.8}},
        {"outcome_value": -0.2, "signal_snapshot": {"quality_score": 0.4, "recency": 0.5, "source_trust": 0.4}},
        {"outcome_value": 0.9, "signal_snapshot": {"quality_score": 0.95, "recency": 0.8, "source_trust": 0.9}},
        {"outcome_value": -0.5, "signal_snapshot": {"quality_score": 0.2, "recency": 0.3, "source_trust": 0.3}},
        {"outcome_value": 0.75, "signal_snapshot": {"quality_score": 0.88, "recency": 0.7, "source_trust": 0.75}},
        {"outcome_value": 0.65, "signal_snapshot": {"quality_score": 0.82, "recency": 0.65, "source_trust": 0.7}},
        {"outcome_value": -0.4, "signal_snapshot": {"quality_score": 0.35, "recency": 0.45, "source_trust": 0.4}},
    ]
    current = load_weights()
    result = recalculate_signal_weights(test_outcomes, current)
    print(json.dumps(result, ensure_ascii=False, indent=2))