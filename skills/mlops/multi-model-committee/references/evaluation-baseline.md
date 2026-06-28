# Committee Evaluation Baseline (v1)

## Clean Baseline (v1)

Established 2026-06-28 after Gemini 429 isolation + safety_unknown separation patch.

**Source**: `zhiyan-legal/results/committee_v1_baseline.json`

| Metric | Value | Notes |
|:-------|:------|:------|
| Total queries | 14 | 7 nonexistent_article + 4 fake_amendment + 3 fabricated_precedent |
| Models | 2 (agnes-k1, agnes-k2) | Gemini excluded due to quota exhaustion |
| Consensus rate | 57.1% (8/14) | Both models agreed on status |
| True divergence rate | 42.9% (6/14) | K1 vs K2 disagreed — this is the **first credible baseline** |
| Blind spot rate | 0.0% (0/14) | No case where both models failed simultaneously |
| K1 deleted hallucination | 1 case (Q007 §980) | §980 is active law (marriage age); K1 flagged it "deleted" |
| Safety_unknown count | 3 cases (Q009) | K2 correctly triggered safety filter for fabricated precedents |

## Regression Anchors

The v1 baseline defines acceptable ranges for automated regression testing:

```json
{
  "divergence_rate_range": [0.35, 0.50],
  "k1_precision_tracking": "pending",
  "safety_unknown_l3_trigger": 10,
  "note": "trigger L3 semantic development when safety_unknown >= 10 cases"
}
```

- **Divergence rate outside [35%, 50%]** — something fundamental changed (model update, normalization logic bug, test set drift)
- **safety_unknown >= 10** — enough signal to develop L3 semantic classification rules
- **K1 `deleted` verdict count** — track aggressive model risk; each `deleted` should trigger external verification via law.moj.gov.tw

## Known Divergence Points

These are the specific articles where K1 and K2 disagree. Use them as regression test cases.

| Q# | Article | K1 | K2 | Reality |
|:---|:--------|:---|:---|:--------|
| Q004 | — | unknown | (diverge) | — |
| Q007 | §980 | **deleted** ❌ | unknown ✅ | Active law (marriage age) |
| Q009 | §127, §490, §125 | unknown x3 | safety_unknown x3 | Fabricated precedents |
| Q011 | §10 | unknown | nonexistent | — |

## Model Profiles

### Agnes K1 (aggressive profile)
- **Strength**: Higher recall — more willing to classify
- **Risk**: `deleted` hallucination in Q007 §980 (active law misclassified)
- **Advice**: Independent `deleted` verdict counter needed; every `deleted` requires external verification

### Agnes K2 (conservative profile)
- **Strength**: Higher precision — correctly says `safety_unknown` when uncertain
- **Strength**: Did not hallucinate §980 status
- **Risk**: May overuse `unknown`, reducing actionable output
- **Advice**: `safety_unknown` is valuable signal — track separately from `unknown`

## Next Actions

| Condition | Action |
|:----------|:-------|
| safety_unknown >= 10 | Develop L3 semantic classification layer |
| New model added | Re-run full 14-query suite, compare divergence metrics |
| divergence rate outside [35%, 50%] | Investigate pipeline changes — normalize or mapper regression |
| Periodically (weekly) | Re-run suite to detect model drift (models may change over time without notice) |
