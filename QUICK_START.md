# GEO Dashboard - Quick Start

## ⚡ Test Right Now

```batch
cd C:\Users\tyunguyen\geo-dashboard
test_session_generation.bat
```

Browser opens → Check the dashboard!

---

## 🔄 Weekly Run (Every Monday)

```batch
geo_weekly_benchmark.bat
```

**Takes ~10 min**
- Runs 3 Claude models
- Updates session.json
- Dashboard shows "Weekly pulse"

---

## 📊 Monthly Run (1st of month)

```batch
geo_monthly_benchmark.bat
```

**Takes ~20 min**
- Runs 6 models (Claude + GPT + Gemini)
- Updates session.json
- Dashboard shows "Full benchmark"

---

## 🎯 What You'll See

### Weekly Dashboard:
```
🔵 Weekly pulse  |  Last updated: 2026-06-23 16:30  |  Unaided SOV ~0%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Last updated: 2026-06-23 16:30  ·  Run: 2026-06-W26  ·  Claude · 70 prompts
· Last full benchmark: June 2026
```

### Monthly Dashboard:
```
🟢 Full benchmark  |  Last updated: 2026-06-30 23:59  |  Unaided SOV ~0%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Last updated: 2026-06-30 23:59  ·  Run: June 2026  ·  9 models · 70 prompts
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `geo_weekly_benchmark.bat` | Run weekly (Claude only) |
| `geo_monthly_benchmark.bat` | Run monthly (9 models) |
| `generate_session_json.py` | Converts CSV → session.json |
| `public/data/session.json` | Dashboard data (auto-updates) |
| `public/index.html` | Main dashboard page |

---

## 🔧 Manual Commands

### Generate session.json manually:
```batch
# Weekly
python generate_session_json.py --weekly

# Monthly
python generate_session_json.py --monthly

# Specific CSV
python generate_session_json.py --weekly --csv benchmarks/geo_multi_claude-sonnet-4-6_2026-06-W26.csv
```

### View dashboard:
```
file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
```

---

## ✅ Checklist

- [ ] Run `test_session_generation.bat`
- [ ] Verify dashboard shows "Weekly pulse"
- [ ] Run `geo_weekly_benchmark.bat` (next Monday)
- [ ] Run `geo_monthly_benchmark.bat` (next month)

---

## 📚 More Info

- **Full details:** `INTEGRATION_COMPLETE.md`
- **Data structure:** `DASHBOARD_UPDATE_GUIDE.md`
- **Troubleshooting:** Check those docs!

---

## 🚨 Troubleshooting

### Dashboard shows old data?
Press `Ctrl + F5` to hard refresh

### CSV not found?
```batch
dir benchmarks\*.csv
```

### Script errors?
```batch
python --version
python generate_session_json.py --help
```

---

That's it! Your dashboard now auto-updates from CSV. 🎉
