# Answers to All 4 Questions

## Q1: Does the weekly automation capture Perplexity/source data from GoCaaS?

**Answer: ❌ NO**

**Why:**
- GoCaaS returns plain Claude API responses (training data only)
- No web search capability
- No citations or source URLs
- All `source_path` fields show "N/A — not mentioned" or "Training data"
- All `cited_urls` fields are empty

**This is expected behavior** - Claude API doesn't include Perplexity-style web search.

---

## Q2: Why doesn't Sonnet work?

**Answer: It worked 3 days ago, may be temporarily unavailable**

**Evidence:**
- ✅ June 26 (W26): Sonnet ran successfully (0% SOV but completed)
- ❌ June 29 (W27): Returns "500 Internal server error"

**Possible causes:**
1. Model temporarily disabled on GoCaaS
2. Model ID changed
3. Capacity/rate limit issues

**Action taken:**
Created `test_sonnet.py` to test multiple Sonnet model IDs:
- claude-sonnet-4-6
- claude-sonnet-4.6
- claude-sonnet-4-5
- claude-3-5-sonnet-20241022
- claude-3-5-sonnet-latest

Run this to diagnose: `python test_sonnet.py`

---

## Q3: Dashboard weekly/monthly confusion - what's your recommendation?

**Answer: Implement Two-Tier System**

### Current Confusion:
- Says "Weekly SOV Trends" AND "view full monthly report"
- `data.json` labeled "Monthly" but has weekly W27 data
- Only 1 model (Haiku) shown when last monthly had 9 models
- Mixed messaging about what's being tracked

### Recommended Solution: **Two-Tier System**

| Tier | Cadence | Models | Purpose | Output |
|------|---------|--------|---------|--------|
| **Monthly Official** | 1st Monday | 8 models (5 primary + 3 pulse) | Official SOV for stakeholders | `data_monthly.json` |
| **Weekly Pulse** | Every Monday | Haiku only | Track week-over-week changes | `data_weekly.json` |

**Benefits:**
- ✅ Clear distinction between official vs pulse
- ✅ Cost-efficient (don't run 8 models weekly)
- ✅ Fast tracking (weekly Haiku shows trends)
- ✅ Comprehensive (monthly has full comparison)

**Implementation:**
1. Separate data files (`data_monthly.json` + `data_weekly.json`)
2. Dashboard displays both with clear labels
3. Weekly automation (working!) updates weekly file
4. Add monthly automation for first Monday

See `DASHBOARD_RECOMMENDATION.md` for full details.

---

## Q4: Why does the site say "9 models" when we changed to 8?

**Answer: ✅ FIXED**

**The Problem:**
- Dashboard showed "9 models" everywhere
- Multi-model script still had GPT-5 and other removed models
- You changed to 8-model structure but code wasn't updated

**The Fix (just committed):**

**8-Model Structure:**

**Primary (5):**
1. Claude Sonnet 4.6
2. Claude Opus 4.8
3. Claude Haiku 4.5
4. GPT-4o
5. Gemini 2.5 Pro

**Pulse (3):**
6. o3
7. o3-mini
8. Gemini 3.1 Pro Preview

**Changes Made:**
- ✅ Removed GPT-5, Gemini Flash, research models
- ✅ Reorganized `MODEL_GROUPS` to `primary` / `pulse`
- ✅ Changed default from `--models claude` to `--models primary`
- ✅ Updated all "9 models" text to "8 models" in HTML
- ✅ `ALL_MODELS` now = 8 total

**Usage:**
```bash
python geo_benchmark_multi_model.py --models primary  # 5 models (default)
python geo_benchmark_multi_model.py --models pulse    # 3 models  
python geo_benchmark_multi_model.py --models all      # 8 models (5+3)
```

---

## Next Steps

1. **Test Sonnet:** Run `python test_sonnet.py` to diagnose why it's failing
2. **Dashboard:** Decide on two-tier system vs simpler alternative
3. **Monthly automation:** Set up first-Monday full benchmark run (8 models)

---

## Summary

| # | Question | Status | Action |
|---|----------|--------|--------|
| 1 | Perplexity data? | ❌ No (expected) | None needed |
| 2 | Sonnet 500 error? | 🔍 Investigating | Run test_sonnet.py |
| 3 | Dashboard confusion? | 📋 Recommendation ready | Review DASHBOARD_RECOMMENDATION.md |
| 4 | 9 vs 8 models? | ✅ Fixed | Commit 8628ba5 |
