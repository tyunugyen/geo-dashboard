# GEO Dashboard Automation — Standard Operating Procedure

**Last Updated:** 2026-06-26  
**Owner:** Tom Yu-Nguyen  
**Dashboard:** https://geo-dashboard-pi-three.vercel.app/

---

## Overview

The GEO (Generative Engine Optimization) Dashboard tracks GoDaddy Payments' Share of Voice (SOV) across AI models. This SOP documents the weekly and monthly automation workflows.

**What We Track:**
- **Primary Models (5)**: Claude Sonnet 4.6, Claude Haiku 4.5, Claude Opus 4.8, GPT-4o, Gemini 2.5 Pro
- **Pulse Models (3)**: Gemini 2.5 Flash, o3-mini, Gemini 3.1 Pro Preview

---

## Weekly Automation

### Schedule
- **Frequency:** Every Monday
- **Duration:** ~3 minutes
- **Model:** Claude Haiku 4.5 only (primary pulse check)

### Execution Methods

#### Option 1: Manual Run (Recommended)
```batch
cd C:\Users\tyunguyen\geo-dashboard
geo_weekly_benchmark.bat
```

#### Option 2: Windows Task Scheduler
- **Task Name:** "GEO Weekly Benchmark"
- **Trigger:** Every Monday at 9:00 AM
- **Action:** Run `geo_weekly_benchmark.bat`
- **Location:** `C:\Users\tyunguyen\geo-dashboard\`

### What It Does

1. **Validates Environment**
   - Checks Python installation
   - Verifies `CAAS_API_KEY` environment variable
   - Confirms network connectivity to CaaS proxy

2. **Runs Benchmark**
   - Executes 70 prompts (63 unaided + 7 aided) via Claude Haiku 4.5
   - Uses GoCode CaaS proxy: `https://caas-gocode-prod.caas-prod.prod.onkatana.net`
   - Saves results to: `benchmarks/geo_multi_claude-haiku-4-5-20251001_YYYY-MM-WXX.csv`

3. **Generates Dashboard Data**
   - Runs `generate_session_json.py --weekly`
   - Creates/updates `public/data/session.json`
   - Updates `public/data/trends.json` (weekly array)

4. **Pushes to GitHub**
   - Commits benchmark CSV + session.json
   - Pushes to `main` branch
   - Commit message: `"GEO benchmark: W2026-XX | Unaided SOV X% | Weekly pulse check"`

5. **Auto-Deploy (Automated)**
   - **Vercel:** Auto-deploys on push to main (~30 seconds)
   - Dashboard updates automatically at https://geo-dashboard-pi-three.vercel.app/

6. **Intelligence Layer Fill (Automated)**
   - GitHub Action `geo-session.yml` triggers on `session.json` push
   - Runs `fill_session.py` via Claude API to populate:
     - `competitive_intel[]` — competitor rate verification
     - `report_summary.binding_constraint` — analysis
     - `strategy_actions.p0/p1[]` — recommended actions
   - Self-hosted runner required (VPN access to CaaS)
   - Commits updated session.json with tag `[geo-bot]`

### Output Files
```
benchmarks/geo_multi_claude-haiku-4-5-20251001_2026-06-W26.csv
public/data/session.json
public/data/trends.json (weekly array updated)
```

### Success Criteria
- ✅ CSV saved with 70 rows (header + 70 prompts)
- ✅ session.json `meta.run_type` = "weekly"
- ✅ Git push successful
- ✅ Vercel deployment shows updated run_id
- ✅ GitHub Action completes intelligence fill

---

## Monthly Automation

### Schedule
- **Frequency:** 1st of each month
- **Duration:** ~15-20 minutes
- **Models:** All 5 primary models

### Execution Methods

#### Option 1: Manual Run (Recommended)
```batch
cd C:\Users\tyunguyen\geo-dashboard
geo_monthly_benchmark.bat
```

#### Option 2: Windows Task Scheduler
- **Task Name:** "GEO Monthly Benchmark"
- **Trigger:** 1st of every month at 9:00 AM
- **Action:** Run `geo_monthly_benchmark.bat`
- **Location:** `C:\Users\tyunguyen\geo-dashboard\`

### What It Does

1. **Validates Environment** (same as weekly)

2. **Runs 5-Model Benchmark** (Sequential)
   ```
   1. Claude Sonnet 4.6    (~4 min)
   2. Claude Haiku 4.5     (~3 min)
   3. Claude Opus 4.8      (~5 min)
   4. GPT-4o              (~4 min)
   5. Gemini 2.5 Pro      (~4 min)
   ```
   - Each model runs 70 prompts independently
   - Creates separate CSV per model
   - Pulse models (Gemini Flash, o3-mini, Gemini 3.1) run separately (optional)

3. **Generates Comparison CSV**
   - Runs `analyze_results.py`
   - Creates `benchmarks/geo_multi_comparison_YYYY-MM-WXX.csv`
   - Contains model-level summary (unaided/aided SOV per model)

4. **Generates Dashboard Data**
   - Runs `generate_session_json.py --monthly`
   - Sets `meta.run_type` = "monthly"
   - Sets `meta.model_count` = 8
   - Updates trends for both monthly and weekly arrays

5. **Pushes to GitHub**
   - Commit message: `"GEO benchmark: YYYY-MM | Full 5-model monthly benchmark"`

6. **Auto-Deploy + Intelligence Fill** (same as weekly)

### Output Files
```
benchmarks/geo_multi_claude-sonnet-4-6_2026-06-W26.csv
benchmarks/geo_multi_claude-haiku-4-5-20251001_2026-06-W26.csv
benchmarks/geo_multi_claude-opus-4-8_2026-06-W26.csv
benchmarks/geo_multi_gpt-4o_2026-06-W26.csv
benchmarks/geo_multi_gemini-2.5-pro_2026-06-W26.csv
benchmarks/geo_multi_comparison_2026-06-W26.csv (summary)
public/data/session.json
public/data/trends.json (monthly + weekly arrays updated)
```

### Success Criteria
- ✅ 5 model CSVs saved (70 rows each)
- ✅ Comparison CSV saved with 5+ model rows
- ✅ session.json `meta.run_type` = "monthly"
- ✅ session.json `meta.model_count` = 8
- ✅ Git push successful
- ✅ Vercel deployment complete
- ✅ GitHub Action completes intelligence fill

---

## File Structure

```
geo-dashboard/
├── geo_weekly_benchmark.bat        # Weekly automation script
├── geo_monthly_benchmark.bat       # Monthly automation script
├── geo_benchmark_multi_model.py    # Core benchmark runner
├── generate_session_json.py        # Converts CSV → session.json
├── fill_session.py                 # Fills intelligence layer via Claude
├── analyze_results.py              # Generates comparison CSV
├── benchmarks/                     # Benchmark result CSVs
│   ├── geo_multi_<model>_<run_id>.csv
│   └── geo_multi_comparison_<run_id>.csv
├── public/
│   ├── index.html                  # Dashboard UI
│   ├── report.html                 # Monthly report page
│   └── data/
│       ├── session.json            # Live dashboard data
│       └── trends.json             # Historical trend data
└── .github/workflows/
    └── geo-session.yml             # Auto-fills intelligence layer
```

---

## Prerequisites

### Environment Variables
```batch
# Required: CaaS API Key for LLM access
setx CAAS_API_KEY "sk-your-key-here"

# Optional: For PaaS auto-deploy (deprecated, using Vercel now)
setx GODADDY_API_KEY "your-key"
setx GODADDY_API_SECRET "your-secret"
```

### Software Requirements
- **Python 3.13+** (in PATH)
- **Git** (in PATH)
- **openai** package: `pip install openai`
- **VPN:** Required for CaaS proxy access

### Network Access
- **CaaS Proxy:** `https://caas-gocode-prod.caas-prod.prod.onkatana.net`
- **GitHub:** Push access to `tyunugyen/geo-dashboard`
- **Vercel:** Auto-deploy configured for main branch

---

## GitHub Actions (Automated Intelligence Fill)

### Workflow: `geo-session.yml`

**Trigger:** Push to `public/data/session.json` on main branch

**Runs On:** Self-hosted runner (requires VPN for CaaS access)

**Steps:**
1. **Test CaaS Connectivity** — verifies runner can reach CaaS proxy
2. **Install Dependencies** — `pip install openai`
3. **Show Session Metadata** — logs run_type, run_id, timestamp
4. **Fill Session via Claude API** — runs `fill_session.py`
5. **Validate Output** — checks required fields populated
6. **Commit Completed Session** — pushes with `[geo-bot]` tag
7. **Trigger PaaS Redeploy** — (deprecated, Vercel auto-deploys)

**Output:** Updated `session.json` with:
- `competitive_intel[]` — verified competitor rates
- `report_summary.*` — AI-generated analysis
- `strategy_actions.*` — recommended actions
- `build_pages[]` — BUILD recommendations
- `amplify_threads[]` — AMPLIFY opportunities
- `cite_pipeline[]` — CITE actions

**Runtime:** ~2-3 minutes

---

## Troubleshooting

### Weekly/Monthly Script Fails

**"ERROR: CAAS_API_KEY is not set"**
```batch
setx CAAS_API_KEY "sk-your-key-here"
# Close and reopen terminal
```

**"ERROR: Python not found in PATH"**
```batch
# Add Python to PATH
set PATH=%PATH%;C:\Python313;C:\Python313\Scripts
# Or reinstall Python with "Add to PATH" checked
```

**"ERROR: Benchmark failed. Check CAAS_API_KEY and VPN."**
- ✅ Verify VPN connected (CaaS proxy requires internal network)
- ✅ Test API key: `curl -H "Authorization: Bearer $CAAS_API_KEY" https://caas-gocode-prod.caas-prod.prod.onkatana.net/health`
- ✅ Check proxy status in #caas-support Slack

### GitHub Action Fails

**"CaaS UNREACHABLE"**
- Self-hosted runner must have VPN access
- Check runner status: https://github.com/tyunugyen/geo-dashboard/settings/actions/runners
- Restart runner if offline

**"fill_session.py failed"**
- Check runner logs for API errors
- Verify `CAAS_API_KEY` secret set in repo settings
- Re-run workflow manually from Actions tab

### Dashboard Not Updating

**Vercel deployment stuck**
- Check: https://vercel.com/tyunugyens-projects/geo-dashboard/deployments
- Verify latest commit deployed
- Force redeploy from Vercel UI if needed

**Chart showing old data**
- Hard refresh: Ctrl+Shift+R (Chrome/Edge) or Cmd+Shift+R (Mac)
- Check `session.json` updated timestamp in browser DevTools → Network

---

## Data Format

### session.json Structure
```json
{
  "meta": {
    "run_type": "weekly|monthly",
    "run_id": "2026-06-W26",
    "last_updated": "2026-06-26 16:30",
    "model_name": "Claude Haiku 4.5" (weekly) | "8 models" (monthly),
    "model_count": 1 (weekly) | 8 (monthly),
    "prompt_count": 70
  },
  "trends": {
    "weekly": [{"run_id": "...", "unaided_sov": 0.0, "aided_sov": 100.0, "rate_saver_sov": 0.0}],
    "monthly": [...]
  },
  "sov_dashboard": {
    "unaided_sov": {"value": "0%", "status": "red", "target": "15%"},
    "aided_sov": {"value": "100%", "status": "green", "target": "100%"},
    ...
  },
  "model_sov": {
    "primary": [
      {"name": "Claude Sonnet 4.6", "unaided": "0%", "aided": "100%", "status": "success"},
      ...
    ],
    "pulse": [
      {"name": "Gemini 2.5 Flash", "unaided": "0%", "aided": "100%", "status": "success"},
      ...
    ]
  },
  "categories": [...],
  "competitors": [...],
  "competitive_intel": [...],  // Filled by GitHub Action
  "report_summary": {...}       // Filled by GitHub Action
}
```

### trends.json Structure
```json
{
  "weekly": [
    {"run_id": "2026-06-W26", "unaided_sov": 0.0, "aided_sov": 100.0, "rate_saver_sov": 0.0}
  ],
  "monthly": [
    {"run_id": "2026-06-W26", "unaided_sov": 0.0, "aided_sov": 100.0, "rate_saver_sov": 0.0}
  ]
}
```

---

## Maintenance

### Weekly Tasks
- ✅ Verify weekly benchmark completes each Monday
- ✅ Check GitHub Action completes intelligence fill
- ✅ Spot-check dashboard shows latest run_id

### Monthly Tasks
- ✅ Run full 5-model benchmark (1st of month)
- ✅ Review monthly report page: https://geo-dashboard-pi-three.vercel.app/report.html
- ✅ Verify trend chart shows 2+ data points

### Quarterly Tasks
- ✅ Review and update prompt bank (prompts.json)
- ✅ Audit competitor rates in competitive_intel
- ✅ Update target SOV percentages if strategy changes
- ✅ Archive old benchmark CSVs (keep last 6 months)

---

## Contacts

**Owner:** Tom Yu-Nguyen (tyunguyen@godaddy.com)  
**CaaS Support:** #caas-support Slack channel  
**GitHub Repo:** https://github.com/tyunugyen/geo-dashboard  
**Dashboard:** https://geo-dashboard-pi-three.vercel.app/

---

## Changelog

### 2026-06-26
- Migrated from GoDaddy PaaS to Vercel (auto-deploy on push)
- Updated model structure: 5 primary + 3 pulse = 8 models
- Removed GPT-5 from tracking (quality issues)
- Fixed trends chart rendering for single data points
- Added Gemini 3.1 Pro Preview status logic (partial vs success)

### 2026-06-25
- Removed GPT-5 from primary models
- Added Claude Opus 4.8 to primary models
- Moved Gemini 2.5 Flash to pulse models
- Fixed run_id extraction from comparison CSV filename

### 2026-06-23
- Initial automation setup
- Created weekly and monthly batch files
- Configured GitHub Actions for intelligence fill
- Deployed to Vercel
