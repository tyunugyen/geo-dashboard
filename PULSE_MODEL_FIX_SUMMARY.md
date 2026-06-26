# Pulse Model Data Quality Fix — Summary

**Date**: 2026-06-26  
**Issue**: Incomplete pulse model benchmarks showing as baseline (28.6% aided SOV from 5/7 failed prompts)

---

## ✅ What Was Fixed

### 1. **Removed Incomplete Data from Dashboard**
- ❌ **Removed**: o3 and Gemini 3.1 Pro Preview from `PULSE_MODELS`
- ✅ **Reason**: 5/7 aided prompts failed with `[ERROR: empty response from API]`
- ✅ **Result**: Dashboard no longer shows inaccurate 28.6% baseline

### 2. **Added Data Quality Check Function**
```python
def check_benchmark_quality(csv_path, model_name):
    """Detect incomplete benchmarks (>30% error rate) and return warning."""
```
- Automatically detects high error rates (>30% threshold)
- Returns warning message: "⚠️ Incomplete data — rerun with timeout=120s, retry=3x"
- Integrated into `build_model_sov()` to flag pulse models

### 3. **Auto-Skip Incomplete Pulse Models**
- If benchmark has >30% errors → skip from pulse list
- Dashboard only shows **verified complete data**
- No false baselines shown to user

---

## 📊 Root Cause Analysis

### Why 28.6% Aided SOV Was Wrong

**o3 (OpenAI Reasoning Model)**:
- ✅ 2/7 aided prompts succeeded (H1, P5)
- ❌ 5/7 prompts failed with API errors
- 📉 Result: 2/7 = 28.6% (not a real SOV)

**Gemini 3.1 Pro Preview**:
- ✅ 2/7 aided prompts succeeded (H1, H5)
- ❌ 5/7 prompts failed with API errors
- 📉 Result: 2/7 = 28.6% (not a real SOV)

### Actual Issue
- ⚠️ **API failures**, not model quality
- ⚠️ **Incomplete benchmark** — can't compare to standard models (7/7 success)
- ⚠️ **False negative** — models might mention GoDaddy in those 5 failed prompts

---

## 🔄 How to Re-Enable Pulse Models

When you're ready to re-run pulse benchmarks with proper error handling:

### 1. **Update Benchmark Script** (geo_benchmark_multi_model.py)
Add these fixes for reasoning models:

```python
# Longer timeout for reasoning models (o3 thinks 30-60s per prompt)
timeout = 120  # Was 30s

# Retry logic (3 attempts with exponential backoff)
for attempt in range(3):
    try:
        response = call_api(prompt, timeout=timeout)
        if response:
            break
    except Exception as e:
        if attempt < 2:
            sleep(10 ** attempt)  # 1s, 10s backoff
        else:
            log_error()

# Rate limit handling (pause between prompts)
time.sleep(10)  # 10s between prompts for preview models
```

### 2. **Run Pulse Benchmarks**
```bash
python geo_benchmark_multi_model.py --model o3 --timeout 120 --retry 3
python geo_benchmark_multi_model.py --model gemini-3.1-pro-preview --timeout 120 --retry 3
```

### 3. **Verify Complete Data**
Check CSV for errors:
```bash
grep -i "ERROR" benchmarks/geo_multi_o3_*.csv | wc -l
# Should be 0 or close to 0
```

### 4. **Re-enable in generate_session_json.py**
Uncomment pulse models in `PULSE_MODELS` array (lines 90-112):
```python
PULSE_MODELS = [
    {
        "name": "o3",
        "why": "OpenAI reasoning model — track next-gen behavior",
        "unaided": "0%",
        "aided": "100%",  # Replace with actual from complete benchmark
        "status": "success",
        "u_color": "red",
        "a_color": "green",
        "trigger": "Reasoning model behavior baseline"
    },
    # ... same for Gemini 3.1
]
```

### 5. **Regenerate Dashboard**
```bash
python generate_session_json.py --monthly
git add public/data/session.json
git commit -m "Add verified pulse model benchmarks"
git push
```

---

## 📋 Monthly Benchmark Status

**Current monthly benchmark models** (geo_monthly_benchmark.bat):
- ✅ claude-sonnet-4-6
- ✅ claude-haiku-4-5-20251001
- ✅ claude-opus-4-8
- ✅ gpt-4o
- ✅ gpt-5
- ✅ gemini-2.5-pro

**NOT automated** (manual only):
- ❌ o3 (reasoning model — requires special handling)
- ❌ o3-mini
- ❌ gemini-3.1-pro-preview (preview API)

**Recommendation**: Keep pulse models as **quarterly manual benchmarks** with proper timeout/retry config, not weekly automated.

---

## ✅ Summary

| Before | After |
|--------|-------|
| Dashboard showed 28.6% pulse model SOV | Pulse models hidden (incomplete data) |
| No validation of benchmark quality | Auto-detects >30% error rate |
| Inaccurate baseline shown to user | Only complete verified data shown |
| Hardcoded incomplete values | Clear instructions to re-enable |

**Result**: Dashboard now only shows **accurate, complete benchmarks**. Pulse models will return when properly benchmarked with retry/timeout handling.

---

## 📁 Files Modified

1. `generate_session_json.py`:
   - Lines 90-135: Commented out incomplete PULSE_MODELS
   - Lines 137-160: Added `check_benchmark_quality()` function
   - Lines 288-310: Integrated quality check into `build_model_sov()`
   - Line 24: Added `import pandas as pd`

2. `public/data/session.json`:
   - Regenerated with empty pulse models array
   - Timestamp: 2026-06-26 15:07

---

## 🎯 Next Steps

**When ready to benchmark pulse models again:**
1. Add timeout/retry logic to benchmark script
2. Run manual pulse benchmarks
3. Verify 0% error rate
4. Uncomment PULSE_MODELS in generate_session_json.py
5. Update with actual complete SOV data
6. Regenerate session.json

**For now**: Dashboard shows only **verified complete data** ✅
