# GEO Dashboard: Weekly vs Monthly - Recommendation

## Current Confusion

**What's wrong:**
- `data.json` labeled "Monthly" but contains weekly W27 data
- Dashboard says "weekly trends" + "monthly report" inconsistently
- Only showing Haiku (1 model) when last monthly had 9 models
- CTA says "view full monthly report" but there's no clear monthly baseline

## Recommended Two-Tier System

### Tier 1: **Monthly Official Benchmark** (Comprehensive)
**Purpose:** Official SOV number for stakeholders/leadership
**Cadence:** Once per month (first Monday of month)
**Models:** All 9 models (3 Claude + 4 OpenAI + 2 Gemini)
**Output:** 
- File: `benchmarks/geo_monthly_YYYY-MM.csv`
- Dashboard label: "Monthly Official"
- Full 9-model comparison table

**Script:** `geo_benchmark_multi_model.py --models all`

### Tier 2: **Weekly Pulse Check** (Efficient)
**Purpose:** Track week-over-week changes quickly
**Cadence:** Every Monday (automated via GitHub Actions)
**Models:** Claude Haiku only (fast, cheap)
**Output:**
- File: `benchmarks/geo_audit_results_YYYY-Www.csv`
- Dashboard label: "Weekly Pulse"
- Shows delta from last monthly baseline

**Script:** `geo_benchmark_runner.py` (already working!)

---

## Implementation Plan

### 1. Separate Data Files

```json
// public/data_monthly.json (official baseline)
{
  "meta": {
    "label": "Monthly Official",
    "period": "June 2026",
    "run_id": "2026-06-W26",
    "models": "9 models: Claude (3), GPT (4), Gemini (2)"
  },
  "kpis": { ... }
}

// public/data_weekly.json (pulse check)
{
  "meta": {
    "label": "Weekly Pulse",
    "period": "Week 27",
    "run_id": "2026-06-W27",
    "models": "Claude Haiku 4.5 only",
    "baseline": "2026-06-W26"  // reference to monthly
  },
  "kpis": { ... }
}
```

### 2. Dashboard Display

**Top section (Hero metrics):**
```
┌─────────────────────────────────────────────────────────┐
│ 📊 GoDaddy Payments GEO Dashboard                      │
│                                                         │
│ Monthly Official (June 2026): 0% Unaided / 100% Aided  │
│ Weekly Pulse (W27): 0% Unaided (↔ no change)          │
└─────────────────────────────────────────────────────────┘
```

**Section 1: Monthly Baseline (June W26)**
- 9-model comparison table
- "This is the official number"
- Full category breakdown

**Section 2: Weekly Pulse Check (W27, W28...)**
- Single line: "W27: 0% (↔ no change from baseline)"
- Trend chart showing weekly dots
- "Next monthly: July 1"

### 3. Workflow Changes

**Keep:** 
- Current weekly automation (Haiku, every Monday)
- Outputs to `geo_audit_results_YYYY-Www.csv`

**Add:**
- Monthly automation (first Monday of month)
- Runs `geo_benchmark_multi_model.py --models all`
- Outputs to `geo_monthly_YYYY-MM.csv`
- Updates `data_monthly.json`

**Update:**
- Weekly runner updates `data_weekly.json` (not `data.json`)
- Dashboard loads BOTH files and displays appropriately

### 4. CTA Clarity

**Before:**
```
"view full monthly report" → confusing, points where?
```

**After:**
```
┌─ Monthly Official ────────────────────────────────┐
│ June 2026 · 9 models · 630 data points           │
│                                                   │
│ [View Full Report] [Download CSV]                │
└───────────────────────────────────────────────────┘

┌─ Weekly Pulse ────────────────────────────────────┐
│ W27 · Haiku · 70 prompts · ↔ No change           │
│ W28 · Next run: July 6                           │
└───────────────────────────────────────────────────┘
```

---

## Summary

**The Fix:**
1. ✅ Keep weekly automation (working now!)
2. ✅ Add monthly automation (first Monday)
3. ✅ Separate `data_monthly.json` vs `data_weekly.json`
4. ✅ Dashboard shows BOTH with clear labels
5. ✅ User sees: "Official monthly baseline + weekly tracking"

**The Value:**
- Clear: Monthly = official, Weekly = pulse
- Efficient: Don't run 9 models every week (expensive)
- Actionable: See week-over-week changes quickly
- Scalable: Monthly can expand to more models

---

## Alternative: Simpler Approach

If two-tier is too complex:

**Option B: Weekly-Only with Historical**
- Run Haiku weekly (current)
- Every 4 weeks, run all 9 models
- Dashboard shows "Latest: W27 Haiku" + "Last Full: W26 (9 models)"
- Clearer than current, simpler than two files

**My recommendation: Go with Two-Tier** (Option A above)
