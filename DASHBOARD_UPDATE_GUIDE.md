# GEO Dashboard - Dynamic Update System

## Overview

The GEO dashboard now uses **dynamic data loading** from `session.json`. Your weekly automation script just needs to update one file, and all 9 HTML pages refresh automatically.

---

## How It Works

### 1. **Your Automation Outputs:**
```
public/
  data/
    session.json          ← YOU UPDATE THIS (weekly/monthly)
  js/
    session-loader.js     ← Loads and renders session.json
  *.html                  ← All pages auto-update from session.json
```

### 2. **Weekly vs Monthly Updates:**

#### **Weekly Pulse** (Claude only, 70 prompts):
```json
{
  "meta": {
    "run_type": "weekly",
    "run_id": "2026-06-W26",
    "last_updated": "2026-06-23 16:30",
    "model_name": "Claude Sonnet 4.6",
    "model_count": 1,
    "prompt_count": 70,
    "last_full_benchmark": "June 2026"
  }
}
```

**Displays as:**
- Header badge: "Weekly pulse" (blue)
- Last updated bar: "Last updated: 2026-06-23 16:30  ·  Run: 2026-06-W26  ·  Claude · 70 prompts"
- Shows: "Last full benchmark: June 2026" (for context)

#### **Monthly Benchmark** (9 models, 70+ prompts):
```json
{
  "meta": {
    "run_type": "monthly",
    "run_id": "June 2026",
    "last_updated": "2026-06-30 23:59",
    "model_name": "9 models",
    "model_count": 9,
    "prompt_count": 70
  }
}
```

**Displays as:**
- Header badge: "Full benchmark" (green)
- Last updated bar: "Last updated: 2026-06-30 23:59  ·  Run: June 2026  ·  9 models · 70 prompts"
- No "last full benchmark" footnote (this IS the benchmark)

---

## Your Automation Flow

### Weekly Run:
1. **CRAWL** → fetch live pages
2. **AUDIT** → parse CSV, calculate SOV
3. **AMPLIFY** → crawl Reddit/Quora/LinkedIn
4. **STRATEGY** → classify root causes, rank actions
5. **BUILD** → draft pages for accepted briefs
6. **CITE** → check aggregator pipeline
7. **REPORT** → write executive narrative
8. **UPDATE NOTES** → GEO Prompt Bank + Master File
9. **UPDATE CONFLUENCE** → Aggregator Tracker + Claim Registry
10. **PRODUCE OUTPUT**:
    ```bash
    # Update session.json with weekly structure
    cp output/weekly_session.json public/data/session.json
    
    # That's it! Dashboard auto-updates
    ```

### Monthly Run:
Same 10 steps, but:
- Use `"run_type": "monthly"` in session.json
- Include all 9 models in `model_sov` data
- Update `last_full_benchmark` timestamp for next month's weekly runs

---

## session.json Structure

### Required Fields:
```json
{
  "meta": {
    "run_type": "weekly|monthly",
    "run_id": "2026-06-W26 | June 2026",
    "last_updated": "2026-06-23 16:30",
    "model_name": "Claude Sonnet 4.6 | 9 models",
    "model_count": 1 | 9,
    "prompt_count": 70,
    "last_full_benchmark": "June 2026"  // Only for weekly
  },
  "sov_dashboard": {
    "unaided_sov": {"value": "~0%", "status": "red", "target": "15%"},
    "aided_sov": {"value": "~100%", "status": "green", "target": "100%"},
    "rate_saver_sov": {"value": "0%", "status": "red", "target": "35%"},
    "citation_rank": {"value": "Unranked", "status": "red", "target": "Top 5"}
  },
  "categories": [...],
  "competitors": [...],
  "model_sov": {"primary": [...], "pulse": [...]},
  "perplexity_simulation": [...],
  "competitive_intel": [...],
  "strategy_actions": [...],
  "build_pages": [...],
  "amplify_threads": [...],
  "amplify_outcomes": [...],
  "cite_pipeline": [...],
  "report_summary": {...}
}
```

### Full Template:
See `public/data/session.json` for the complete structure with all fields.

---

## Testing Locally

1. **Update session.json**:
   ```bash
   # Edit meta.run_type to "weekly" or "monthly"
   # Change meta.last_updated to current timestamp
   ```

2. **Open any HTML page**:
   ```bash
   # Open public/index.html in browser
   # Check header badges update
   # Check last-updated bar updates
   ```

3. **Verify dynamic loading**:
   - Header should show "Weekly pulse" or "Full benchmark"
   - Timestamp should match session.json
   - Prompt count should match session.json

---

## Deployment

### Your .bat script should:
```batch
@echo off
echo Running GEO automation...

REM 1-9: Your automation steps (CRAWL, AUDIT, etc.)
call run_automation.bat

REM 10: Update dashboard
echo Updating dashboard...
copy /Y output\session.json public\data\session.json

echo Dashboard updated! Visit: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
```

---

## Troubleshooting

### Dashboard shows old data:
- **Check**: `public/data/session.json` was updated
- **Fix**: Hard refresh browser (Ctrl+F5)

### "Weekly pulse" not showing:
- **Check**: `meta.run_type` is `"weekly"` in session.json
- **Fix**: Update session.json, refresh browser

### Script errors in console:
- **Check**: session.json is valid JSON
- **Fix**: Run through JSON validator: https://jsonlint.com/

---

## Files Modified

All HTML files now have:
1. **Dynamic data attributes** in header/badges
2. **Script tag**: `<script src="./js/session-loader.js"></script>`
3. **Auto-refresh** on page load from session.json

Updated files:
- ✅ index.html
- ✅ prompts.html
- ✅ aggregators.html
- ✅ action-build.html
- ✅ action-amplify.html
- ✅ action-cite.html
- ✅ roadmap.html
- ✅ report.html
- ✅ maintenance.html

---

## Next Steps

1. **Update your automation script** to output `session.json` in the correct format
2. **Test with a weekly run** (set `run_type: "weekly"`)
3. **Test with a monthly run** (set `run_type: "monthly"`)
4. **Verify all 9 pages** display correctly

Questions? Check `session-loader.js` for the rendering logic.
