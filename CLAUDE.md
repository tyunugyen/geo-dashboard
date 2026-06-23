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
│   ├── action-amplify.html
│   ├── action-cite.html
│   └── data.json       # Dashboard data — updated monthly via CSV upload
└── csv_to_datajson.py  # Optional: local Python converter
```

## Monthly update workflow
```bash
python update_dashboard.py geo_audit_results_YYYY-MM-RUN-1.csv
# → scores CSV → updates public/data.json → git commit → git push → auto-redeploys
```

## Environment variables (set in PaaS Settings → Secrets)
- `PORT` — provided automatically by the platform
- `STORAGE_ID` — optional jsonstorage.net ID for extra persistence
