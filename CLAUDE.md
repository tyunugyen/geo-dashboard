# CLAUDE.md — GEO Visibility Dashboard

This is a Node.js dashboard deployed on GoDaddy Node.js Hosting.

## Start command
```
npm start  →  node server.js
```

## Structure
```
geo-dashboard/
├── server.js           # Express-style HTTP server with POST /upload endpoint
├── package.json        # start: node server.js, build: echo build
├── public/
│   ├── index.html      # Main dashboard (Overview)
│   ├── prompts.html    # All 70 prompts by tier
│   ├── aggregators.html
│   ├── roadmap.html
│   ├── action-build.html
│   ├── action-amplify.html  # AMPLIFY + weekly monitoring workflow
│   ├── action-cite.html
│   ├── report.html          # Monthly executive report (NEW)
│   ├── maintenance.html     # Weekly + monthly actions guide (NEW)
│   └── data.json       # Dashboard data — updated monthly via CSV upload
└── update_dashboard.py # Score CSV + update data.json + git push
```

## Monthly update workflow (automated via .bat)
```bash
# Automated — runs via Windows Task Scheduler:
geo_monthly_benchmark.bat
# → runs 70 prompts × 3 models → scores CSV → updates data.json → git push → redeploys

# Manual fallback:
python update_dashboard.py geo_audit_results_YYYY-MM-RUN-1.csv
```

## Weekly workflow (manual — see public/maintenance.html)
```
Every Monday:
1. Open Claude → run "Weekly GEO" task
2. Search Reddit for active payment/POS threads
3. Score threads → post approved replies with disclosure
4. Log outcomes in action-amplify.html outcome tracking table
```

## Monthly Claude session
```
Open Claude → say: "Run monthly GEO session."
Claude auto-pulls GEO Prompt Bank note (7db9a2e8) + ICP snapshot note.
Runs AUDIT → STRATEGY → BUILD/CITE/AMPLIFY workflow.
```

## Pages added in v2
- report.html      — Executive GEO Report (auto-populates from data.json)
- maintenance.html — Weekly + monthly actions, Claude prompts, file map

## Environment variables (set in PaaS Settings → Secrets)
- `PORT`       — provided automatically by the platform
- `STORAGE_ID` — optional jsonstorage.net ID for extra persistence
