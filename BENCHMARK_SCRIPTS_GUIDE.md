# GEO Benchmark Scripts — Quick Reference

## 📁 Available Scripts

### 1. **geo_weekly_benchmark.bat** ⚡ Weekly Pulse Check
**When to run**: Every Monday (automated via Task Scheduler)  
**Models**: Claude Haiku (primary model only)  
**Time**: ~3-5 minutes  
**Purpose**: Quick weekly health check

```bash
.\geo_weekly_benchmark.bat
```

**What it does**:
1. Runs 70 prompts with Claude Haiku
2. Generates session.json
3. Commits and pushes to GitHub
4. GoCaaS webhook triggers intelligence fill

---

### 2. **geo_monthly_benchmark.bat** 📊 Full Monthly Benchmark
**When to run**: 1st Monday of each month (automated via Task Scheduler)  
**Models**: 5 production models
- claude-sonnet-4-6
- claude-haiku-4-5-20251001
- claude-opus-4-8
- gpt-4o
- gemini-2.5-pro

**Time**: ~15-20 minutes  
**Purpose**: Full competitive baseline across all major models

```bash
.\geo_monthly_benchmark.bat
```

**What it does**:
1. Runs 70 prompts × 5 models = 350 prompts
2. Generates comparison CSV
3. Updates session.json with full model table
4. Commits and pushes
5. GoCaaS webhook triggers intelligence fill

**Note**: GPT-5 removed (June 2026) due to persistent API errors.

---

### 3. **geo_pulse_benchmark.bat** 🔬 Pulse Models (Manual)
**When to run**: Quarterly or when investigating next-gen models  
**Models**: 3 reasoning/preview models
- o3 (OpenAI reasoning)
- o3-mini (OpenAI reasoning - smaller)
- gemini-3.1-pro-preview (Google next-gen)

**Time**: ~30-45 minutes (these models are SLOW)  
**Purpose**: Track next-gen reasoning model behavior

```bash
.\geo_pulse_benchmark.bat
```

**What it does**:
1. Runs 70 prompts × 3 models with retry logic
2. 120s timeout per prompt (reasoning models need time to think)
3. Auto-retries failed models once
4. Validates error rate
5. Commits CSVs to GitHub
6. **Does NOT regenerate session.json** (you do this manually after validation)

**After running**:
1. Check error rate in CSVs:
   ```bash
   findstr /I "ERROR" benchmarks\geo_multi_o3_*.csv
   findstr /I "ERROR" benchmarks\geo_multi_o3-mini_*.csv
   findstr /I "ERROR" benchmarks\geo_multi_gemini-3.1-pro-preview_*.csv
   ```

2. If error rate < 10%:
   - ✅ Uncomment PULSE_MODELS in `generate_session_json.py` (lines 90-112)
   - ✅ Update with actual SOV percentages from CSVs
   - ✅ Run: `python generate_session_json.py --monthly`
   - ✅ Commit and push

3. If error rate > 30%:
   - ❌ Don't enable in dashboard
   - ❌ Check CAAS_API_KEY and VPN
   - ❌ Consider adding more retry logic to benchmark script

---

## 🗓️ Automated Schedule

| Script | Frequency | Day | Time |
|--------|-----------|-----|------|
| geo_weekly_benchmark.bat | Weekly | Every Monday | 9:00 AM |
| geo_monthly_benchmark.bat | Monthly | 1st Monday | 9:00 AM |
| geo_pulse_benchmark.bat | Manual | N/A | Run when needed |

**Set up via Windows Task Scheduler**:
```bash
.\setup_scheduled_tasks.bat
```

---

## 🛠️ Troubleshooting

### Weekly/Monthly Fails
1. Check `CAAS_API_KEY` environment variable:
   ```bash
   echo %CAAS_API_KEY%
   ```
2. Check VPN connection
3. Check logs in `benchmarks/` folder

### Pulse Benchmark High Error Rate
**Common causes**:
- **Timeout too short**: Reasoning models need 60-120s per prompt
- **Rate limiting**: API throttling preview models
- **Model availability**: Preview models may be unstable

**Solutions**:
1. Already includes retry logic (2 attempts)
2. Already includes 120s timeout
3. If still fails, wait 24 hours and retry

### Git Push Fails
1. Check GitHub authentication
2. Check network connection
3. Manual push:
   ```bash
   cd C:\Users\tyunguyen\geo-dashboard
   git pull --rebase origin main
   git push origin main
   ```

---

## 📊 Model Categories

### Primary Models (Monthly + Weekly)
Production-ready models with stable APIs:
- Claude Sonnet 4.6
- Claude Haiku 4.5
- Claude Opus 4.8
- GPT-4o
- Gemini 2.5 Pro

**Error rate**: Usually < 1%

### Pulse Models (Quarterly Manual)
Next-gen reasoning/preview models:
- o3
- o3-mini
- Gemini 3.1 Pro Preview

**Error rate**: Can be 10-30% (unstable APIs)  
**Why track**: Early signal on next-gen model behavior

---

## 🎯 Quick Commands

**Run weekly benchmark now**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_weekly_benchmark.bat
```

**Run monthly benchmark now**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_monthly_benchmark.bat
```

**Run pulse benchmark (quarterly)**:
```bash
cd C:\Users\tyunguyen\geo-dashboard
.\geo_pulse_benchmark.bat
```

**Check last run status**:
```bash
git log --oneline -5
```

**View benchmark CSVs**:
```bash
dir benchmarks\geo_multi_*.csv
```

**Check for errors in latest run**:
```bash
findstr /I "ERROR" benchmarks\geo_multi_*_2026-06-*.csv
```

---

## 📈 What Gets Generated

### Weekly Run
- `benchmarks/geo_multi_claude-haiku-4-5-20251001_2026-06-W26.csv`
- `public/data/session.json` (updated)
- Git commit: "GEO benchmark: 2026-06-23 | Weekly pulse check"

### Monthly Run
- `benchmarks/geo_multi_claude-sonnet-4-6_2026-06-W26.csv`
- `benchmarks/geo_multi_claude-haiku-4-5-20251001_2026-06-W26.csv`
- `benchmarks/geo_multi_claude-opus-4-8_2026-06-W26.csv`
- `benchmarks/geo_multi_gpt-4o_2026-06-W26.csv`
- `benchmarks/geo_multi_gemini-2.5-pro_2026-06-W26.csv`
- `benchmarks/geo_multi_comparison_2026-06-W26.csv` (combined)
- `public/data/session.json` (updated with all models)
- Git commit: "GEO benchmark: 2026-06-26 | Full 5-model monthly benchmark"

### Pulse Run
- `benchmarks/geo_multi_o3_2026-06-W26.csv`
- `benchmarks/geo_multi_o3-mini_2026-06-W26.csv`
- `benchmarks/geo_multi_gemini-3.1-pro-preview_2026-06-W26.csv`
- Git commit: "GEO pulse benchmark: 2026-06-26 | o3, o3-mini, Gemini 3.1 Pro Preview"
- **Note**: session.json NOT auto-updated (you validate error rate first)

---

## ✅ Success Criteria

### Weekly/Monthly
- ✅ All models complete
- ✅ Error rate < 1%
- ✅ session.json updated
- ✅ Git push succeeds
- ✅ GoCaaS webhook triggers

### Pulse (Manual)
- ✅ At least 2/3 models complete
- ✅ Error rate < 30% for completed models
- ✅ CSVs committed to GitHub
- ⚠️ session.json updated ONLY after manual validation

---

## 🔗 Related Files

- **Scripts**: `geo_weekly_benchmark.bat`, `geo_monthly_benchmark.bat`, `geo_pulse_benchmark.bat`
- **Python**: `geo_benchmark_multi_model.py`, `generate_session_json.py`, `fill_session.py`
- **Data**: `public/data/session.json`, `benchmarks/*.csv`
- **Config**: `PULSE_MODEL_FIX_SUMMARY.md`, `.github/workflows/auto-fill-session.yml`
- **Setup**: `setup_scheduled_tasks.bat`, `task_status.bat`

---

**Last Updated**: 2026-06-26  
**Maintained By**: Tom Yu-Nguyen  
**Dashboard**: https://kz6jwep09q.c24.airoapp.ai/
