#!/usr/bin/env python3
"""
self_learning_cycle.py — 育昇自學引擎 v2.0 觸發器

替換 lucian-station/skills/scripts/weekly_report.sh
負責驅動完整四階閉環：
  Phase 1: 收集 outcome records → data/outcome_records.jsonl
  Phase 2: 衍生 lesson（template-driven）
  Phase 3: 演化 Darwin 信號加權（冷啟動保護）
  Phase 4: 執行 Hard Track 檢查（cooldowns / blocklist）

使用方式：
  python3 self_learning_cycle.py                    # 完整執行
  python3 self_learning_cycle.py --phase 1         # 只做 Phase 1
  python3 self_learning_cycle.py --dry-run         # 模擬，不寫入
  python3 self_learning_cycle.py --verbose         # 詳細輸出
  python3 self_learning_cycle.py --help            # 顯示說明
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# 專案根目錄
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 資料層路徑
DATA_DIR = ROOT / "data"
SCHEMAS_DIR = ROOT / "schemas"
ENGINE_DIR = ROOT / "engine"

OUTCOMES_FILE = DATA_DIR / "outcome_records.jsonl"
LESSONS_FILE = DATA_DIR / "lessons.jsonl"
WEIGHTS_FILE = DATA_DIR / "signal_weights.jsonl"
THRESHOLDS_FILE = DATA_DIR / "thresholds.jsonl"
COOLDOWNS_FILE = DATA_DIR / "cooldowns.json"
BLOCKLIST_FILE = DATA_DIR / "blocklist.json"
LAST_CYCLE_FILE = DATA_DIR / ".last_cycle_ts"


# ── CLI 解析 ────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="育昇自學引擎 v2.0 — 觸發四階閉環",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python3 self_learning_cycle.py              # 完整執行
  python3 self_learning_cycle.py --phase 1    # 只收集 outcomes
  python3 self_learning_cycle.py --dry-run   # 模擬（不寫入）
  python3 self_learning_cycle.py --verbose    # 詳細輸出
  CRON: python3 self_learning_cycle.py >> ~/.hermes/logs/self_learning.log 2>&1
        """,
    )
    parser.add_argument(
        "--phase", "-p", type=int, choices=[1, 2, 3, 4],
        help="只執行指定 phase（1-4），預設執行全部",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="模擬執行，不寫入任何資料檔案",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="詳細輸出（包含每個步驟的具體行為）",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="安靜模式（只有結果摘要）",
    )
    parser.add_argument(
        "--min-samples", type=int, default=10,
        help="冷啟動保護閾值（default: 10，低於此值不演化 Darwin 權重）",
    )
    return parser.parse_args()


# ── 工具函式 ────────────────────────────────────────────


def load_jsonl(path: Path) -> list[dict]:
    """讀取 JSONL 檔案，回傳 list of dict。"""
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


def append_jsonl(path: Path, record: dict, dry_run: bool = False) -> None:
    """附加一筆記錄到 JSONL 檔案。"""
    if dry_run:
        print(f"  [DRY] 寫入 {path.name}: {record.get('id', '?')}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_json(path: Path, default: dict | list) -> dict | list:
    """讀取 JSON 檔案，失敗時回傳 default。"""
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_json(path: Path, data: dict | list, dry_run: bool = False) -> None:
    """寫入 JSON 檔案。"""
    if dry_run:
        print(f"  [DRY] 寫入 {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg: str, verbose: bool = False, quiet: bool = False) -> None:
    if quiet:
        return
    if verbose:
        print(f"  [INFO] {msg}")
    else:
        print(msg)


def section(title: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)


# ── Phase 1: 收集 Outcome Records ───────────────────────


def phase1_collect_outcomes(args: argparse.Namespace) -> list[dict]:
    """收集自上一輪以來的新 outcomes（目前從 stdin 讀取，未來可擴充鉤子）。"""
    section("Phase 1: 收集 Outcome Records")

    # 讀取現有資料筆數
    existing = load_jsonl(OUTCOMES_FILE)
    n_existing = len(existing)

    # 嘗試呼叫鉤子：從外部來源收集 outcomes
    # 目前實作：從 stdin 讀取一行 JSON（或跳過）
    collected = []
    import os
    if not os.isatty(sys.stdin.fileno()):
        # stdin 有資料，嘗試讀取
        try:
            raw = sys.stdin.read()
            if raw.strip():
                outcome = json.loads(raw.strip())
                collected.append(outcome)
                print(f"  從 stdin 收集到 1 筆記錄")
        except json.JSONDecodeError as e:
            print(f"  [WARN] stdin JSON 解析失敗：{e}，跳過")

    n_new = len(collected)

    if n_new > 0 and not args.dry_run:
        for r in collected:
            append_jsonl(OUTCOMES_FILE, r)

    total = n_existing + n_new
    print(f"  已累積 {total} 筆記錄（+ 新增 {n_new} 筆）")
    return collected


# ── Phase 2: 衍生 Lessons ────────────────────────────────


def phase2_derive_lessons(args: argparse.Namespace) -> list[dict]:
    """對每筆新 outcome 執行 template-driven lesson 衍生。"""
    section("Phase 2: 衍生 Lessons")

    outcomes = load_jsonl(OUTCOMES_FILE)
    existing_lessons = load_jsonl(LESSONS_FILE)
    existing_outcome_ids = {r.get("outcome_id") or r.get("id") for r in existing_lessons}

    # 只對新 outcomes 衍生 lesson
    new_outcomes = [o for o in outcomes if o.get("id") not in existing_outcome_ids]

    if not new_outcomes:
        print("  無新 outcome 需要處理")
        return []

    # 動態引入 engine 模組（避免頂層 import 失敗時影響啟動）
    sys.path.insert(0, str(ENGINE_DIR))
    try:
        from derive_lesson import derive_single_outcome
    except ImportError as e:
        print(f"  [WARN] 無法載入 derive_lesson：{e}，跳過 lesson 衍生")
        return []

    derived = []
    for outcome in new_outcomes:
        try:
            lesson = derive_single_outcome(outcome, dry_run=args.dry_run)
            if lesson:
                derived.append(lesson)
                if not args.dry_run:
                    append_jsonl(LESSONS_FILE, lesson)
                print(f"  衍生 lesson: {lesson.get('id', '?')} （outcome: {outcome.get('id', '?')}）")
        except Exception as e:
            print(f"  [WARN] 衍生失敗 outcome={outcome.get('id', '?')}：{e}")

    print(f"  共衍生 {len(derived)} 筆 lesson")
    return derived


# ── Phase 3: 演化 Darwin 信號加權 ───────────────────────


def phase3_evolve_weights(args: argparse.Namespace) -> dict | None:
    """執行 Darwin 信號加權演化（有冷啟動保護）。"""
    section("Phase 3: 演化 Darwin 信號加權")

    outcomes = load_jsonl(OUTCOMES_FILE)
    total = len(outcomes)

    if total < args.min_samples:
        print(f"  [SKIP] 冷啟動保護：樣本數 {total} < {args.min_samples}")
        print(f"         設定 --min-samples 0 可跳過此檢查")
        return None

    # 動態引入 engine 模組
    sys.path.insert(0, str(ENGINE_DIR))
    try:
        from recalc_weights import recalculate_signal_weights
    except ImportError as e:
        print(f"  [WARN] 無法載入 recalc_weights：{e}，跳過加權演化")
        return None

    # 讀取現有 weights
    existing_weights = load_jsonl(WEIGHTS_FILE)
    current_weights = existing_weights[-1] if existing_weights else None

    if not args.dry_run:
        result = recalculate_signal_weights(outcomes, current_weights)
    else:
        result = {"status": "dry_run", "action": "would_update_weights"}

    print(f"  狀態: {result.get('status')}")
    if result.get("status") == "cold_start":
        print(f"  [SKIP] 冷啟動保護（正負樣本不足）")
        return result

    if result.get("status") == "no_signal_change" and args.verbose:
        print(f"  [INFO] 信號無顯著變化，權重不更新")

    if result.get("new_weights"):
        new_weights = result["new_weights"]
        new_weights["updated_at"] = ts()
        if not args.dry_run:
            append_jsonl(WEIGHTS_FILE, new_weights)
        print(f"  權重已更新（version: {new_weights.get('version')}）")
        if args.verbose:
            for sig, wdata in new_weights.get("weights", {}).items():
                print(f"    {sig}: w={wdata.get('w', 1.0):.4f}")

    return result


# ── Phase 4: 執行 Hard Track ─────────────────────────────


def phase4_hard_track(args: argparse.Namespace) -> None:
    """執行 cooldowns 與 blocklist 檢查（純機械寫入）。"""
    section("Phase 4: 執行 Hard Track（Cooldowns / Blocklist）")

    sys.path.insert(0, str(ENGINE_DIR))
    try:
        from apply_hard_track import run_cycle
    except ImportError as e:
        print(f"  [WARN] 無法載入 apply_hard_track：{e}，跳過")
        return

    cooldowns = load_json(COOLDOWNS_FILE, {})
    blocklist = load_json(BLOCKLIST_FILE, [])

    result = run_cycle(cooldowns, blocklist, verbose=args.verbose, dry_run=args.dry_run)

    if not args.dry_run:
        save_json(COOLDOWNS_FILE, result.get("cooldowns", {}))
        save_json(BLOCKLIST_FILE, result.get("blocklist", []))

    active_cd = len(result.get("active_cooldowns", []))
    blocked = len(result.get("blocked_signals", []))
    print(f"  Cooldowns: {active_cd} 個作用中")
    print(f"  Blocklist: {blocked} 個信號被封鎖")
    if args.verbose and result.get("expired"):
        print(f"  已過期: {result['expired']} 筆")


# ── Phase 5: 更新觸發時間戳 ──────────────────────────────


def phase5_record_cycle(args: argparse.Namespace) -> None:
    """記錄本次 cycle 完成時間。"""
    if not args.dry_run:
        LAST_CYCLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_CYCLE_FILE.write_text(ts(), encoding="utf-8")
    print(f"  Cycle 完成時間已記錄: {ts()}")


# ── 主函式 ──────────────────────────────────────────────


def main() -> int:
    args = parse_args()

    if not args.quiet:
        print(f"""
╔══════════════════════════════════════════╗
║   育昇自學引擎 v2.0 — 自學觸發器           ║
║   {ts()}
║   Dry-run: {'ON' if args.dry_run else 'OFF'}
╚══════════════════════════════════════════╝
        """)

    # Phase 1: 收集
    if args.phase in (None, 1):
        phase1_collect_outcomes(args)

    # Phase 2: Lesson 衍生
    if args.phase in (None, 2):
        phase2_derive_lessons(args)

    # Phase 3: Darwin 演化
    if args.phase in (None, 3):
        phase3_evolve_weights(args)

    # Phase 4: Hard Track
    if args.phase in (None, 4):
        phase4_hard_track(args)

    # Phase 5: 記錄
    if args.phase is None:
        phase5_record_cycle(args)

    if not args.quiet:
        print(f"\n{'='*50}")
        print(f"  自學 Cycle 完成")
        print(f"  下次執行：建議 24 小時後（cron: daily）")
        print('='*50)

    return 0


if __name__ == "__main__":
    sys.exit(main())