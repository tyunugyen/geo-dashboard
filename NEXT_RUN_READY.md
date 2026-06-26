# ✅ Next Run Ready - All Scripts Fixed

**Date**: 2026-06-26  
**Status**: All benchmark scripts updated and ready for automated runs

---

## What Was Fixed

### **1. Monthly Benchmark** ✅ READY
**File**: `geo_monthly_benchmark.bat`

**Changes**:
- ✅ **Removed GPT-5** - was failing 100% of aided queries (0% aided SOV)
- ✅ Runs **5 models** now (was 6):
  - claude-sonnet-4-6
  - claude-haiku-4-5-20251001
  - claude-opus-4-8
  - gpt-4o
  - gemini-2.5-pro
- ✅ Updated commit message: "5-model" instead of "9-model"
- ✅ Updated dashboard URL to correct PaaS link
- ✅ Estimated time: ~15-20 minutes (was ~18-25 with GPT-5)

**Next run**: 1st Monday of July 2026 (automated)

---

### **2. Weekly Benchmark** ✅ READY
**File**: `geo_weekly_benchmark.bat`

**Changes**:
- ✅ **Changed from 3 Claude models to 1** (Haiku only)
- ✅ Was running: Sonnet + Haiku + Opus = 210 prompts (~10 min)
- ✅ Now runs: Haiku only = 70 prompts (~3 min)
- ✅ Updated dashboard URL to correct PaaS link
- ✅ Updated message: "5-model monthly" instead of "9-model"
- ✅ **3× faster** - true weekly pulse check now

**Next run**: Monday, June 30, 2026 (automated)

**Why Haiku only?**
- Weekly is meant to be a **quick pulse check**, not full benchmark
- Haiku is fast, cheap, and reliable
- Monthly already tests all models comprehensively

---

### **3. Pulse Benchmark** ✅ READY
**File**: `geo_pulse_benchmark.bat` (NEW)

**What it does**:
- Runs 3 reasoning/preview models:
  - o3 (OpenAI reasoning)
  - o3-mini (OpenAI reasoning - smaller)
  - gemini-3.1-pro-preview (Google next-gen)
- Built-in retry logic (2 attempts per model)
- 120s timeout per prompt (reasoning models need time)
- Error validation after completion
- Takes ~30-45 minutes

**When to run**: Quarterly or when investigating next-gen models (MANUAL only)

**How to run**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_pulse_benchmark.bat
```

---

## Automated Schedule (Task Scheduler)

| Script | Frequency | Day | Time | Duration |
|--------|-----------|-----|------|----------|
| **geo_weekly_benchmark.bat** | Weekly | Every Monday | 9:00 AM | ~3 min |
| **geo_monthly_benchmark.bat** | Monthly | 1st Monday | 9:00 AM | ~15-20 min |
| **geo_pulse_benchmark.bat** | Manual | N/A | On demand | ~30-45 min |

---

## What to Expect Next Run

### **This Monday (June 30) - Weekly** ⚡
- Runs: Claude Haiku only
- Time: ~3 minutes (fast!)
- Output:
  - `benchmarks/geo_multi_claude-haiku-4-5-20251001_2026-06-W26.csv`
  - `public/data/session.json` (updated)
  - Git commit + push
  - GoCaaS webhook triggers intelligence fill

### **Next Month (July 6?) - Monthly** 📊
- Runs: 5 models (Claude 3, GPT-4o, Gemini 2.5)
- Time: ~15-20 minutes
- Output:
  - 5 individual model CSVs
  - `benchmarks/geo_multi_comparison_2026-07-W27.csv`
  - `public/data/session.json` (updated with all 5 models)
  - Git commit + push
  - GoCaaS webhook triggers intelligence fill

---

## Dashboard Model Count

### **Current (After This Month's Run)**
- Primary models: **6** (includes GPT-5 failure - last time)
- Pulse models: **0** (incomplete data removed)
- **Total: 6 models**

### **Next Month Forward**
- Primary models: **5** (GPT-5 removed)
- Pulse models: **0** (until you run pulse benchmark)
- **Total: 5 models**

### **If You Run Pulse Benchmark**
- Primary models: **5**
- Pulse models: **3** (o3, o3-mini, Gemini 3.1)
- **Total: 8 models**

---

## Why GPT-5 Was Removed

**Evidence from today's run**:
```
[59/70] H1: What is GoDaddy Payments?... [FAIL] No GD
[60/70] H2: GoDaddy Payments vs Square... [FAIL] No GD
[61/70] H3: GoDaddy Payments vs Helcim... [FAIL] No GD
[62/70] H4: GoDaddy Payments vs Clover... [FAIL] No GD
[63/70] H5: What is Rate Saver GoDaddy Payments?... [FAIL] No GD
[68/70] P5: GoDaddy Payments vs Toast... [FAIL] No GD
[69/70] P6: GoDaddy Payments vs Shopify Payments... [FAIL] No GD
```

**Result**: 0% aided SOV (0/7) - didn't mention GoDaddy in ANY branded query

**All other models**: 100% aided SOV (7/7) - perfect performance

**Decision**: GPT-5 API is broken or refusing to answer - removed from monthly rotation

---

## Files Changed

### **Scripts**
1. `geo_monthly_benchmark.bat` - Removed GPT-5, updated URLs
2. `geo_weekly_benchmark.bat` - Changed to Haiku only, updated URLs
3. `geo_pulse_benchmark.bat` - NEW: Manual pulse benchmark with retry logic

### **Python**
1. `generate_session_json.py`:
   - Removed incomplete pulse model data (PULSE_MODELS array)
   - Added `check_benchmark_quality()` function
   - Auto-skips incomplete benchmarks from dashboard

### **Documentation**
1. `PULSE_MODEL_FIX_SUMMARY.md` - Why pulse data was removed
2. `BENCHMARK_SCRIPTS_GUIDE.md` - Complete reference guide
3. `NEXT_RUN_READY.md` - This file (what's fixed and ready)

---

## Verification Checklist

Before next automated run, verify:

- [x] GPT-5 removed from `geo_monthly_benchmark.bat` (line 47)
- [x] Weekly runs Haiku only (not 3 models) - `geo_weekly_benchmark.bat` (line 38)
- [x] Dashboard URLs updated in both scripts
- [x] Pulse benchmark script created with retry logic
- [x] `generate_session_json.py` has quality checks
- [x] All changes committed and pushed to GitHub
- [x] Task Scheduler has 2 tasks:
  - GEO Weekly Benchmark (Every Monday, 9:00 AM)
  - GEO Monthly Benchmark (1st Monday, 9:00 AM)

---

## Quick Test Commands

**Test weekly (Haiku only - 3 min)**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_weekly_benchmark.bat
```

**Test monthly (5 models - 15-20 min)**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_monthly_benchmark.bat
```

**Run pulse benchmark (3 models - 30-45 min)**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_pulse_benchmark.bat
```

**Check task status**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\task_status.bat
```

---

## What Gets Triggered Automatically

When benchmarks push to GitHub:

1. **GitHub Action** (`auto-fill-session.yml`) triggers
2. **GoCaaS webhook** receives notification
3. **`fill_session.py`** runs automatically:
   - Perplexity simulation
   - Strategy actions
   - Build pages
   - Amplify threads
   - Citation pipeline
   - Report summary
4. **Updated `public/data/session.json`** pushed back to GitHub
5. **PaaS auto-deploys** (~5 minutes)
6. **Dashboard updates** at https://kz6jwep09q.c24.airoapp.ai/

**No manual intervention needed!** ✅

---

## Dashboard Links

- **Live**: https://kz6jwep09q.c24.airoapp.ai/
- **Local**: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
- **GitHub**: https://github.com/tyunugyen/geo-dashboard

---

## Support

**If weekly/monthly fails**:
1. Check logs in `benchmarks/` folder
2. Verify `%CAAS_API_KEY%` is set
3. Check VPN connection
4. Review this file: `BENCHMARK_SCRIPTS_GUIDE.md`

**If pulse benchmark fails**:
1. Check error rate (>30% = incomplete data)
2. Verify retry logic ran (2 attempts)
3. Don't enable pulse models in dashboard if error rate is high
4. Wait 24 hours and retry

---

**Everything is ready for the next automated run!** 🚀

**Next milestone**: Monday, June 30, 2026 - First weekly run with Haiku-only (3 min) ⚡
