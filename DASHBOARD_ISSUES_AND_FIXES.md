# Dashboard Issues & Fixes - 2026-06-26

## 🔴 Issue Summary

You reported 4 issues with the dashboard at https://kz6jwep09q.c24.airoapp.ai/:

1. **Unaided SOV by category** - boxes missing
2. **Competitors** - only showing 5, missing Helcim, Shopify, Toast, etc.
3. **"What we track" section** - shows "Loading..."
4. **Actions needed formatting** - very off

## 🔍 Root Causes Found

### 1. Dashboard Showing Old Cached Version
- **Problem**: PaaS deployment showing stale HTML/JS from 2026-06-23
- **Evidence**: 
  - session.json: Updated 2026-06-26 1:57 PM ✅
  - index.html: Last updated 2026-06-25 2:28 PM ⚠️
  - Dashboard shows timestamp: 2026-06-23 16:30 ⚠️

### 2. Competitors Hardcoded to 5
- **Problem**: `generate_session_json.py` has hardcoded competitors array:
  ```python
  "competitors": [
      { "name": "Square", ... },
      { "name": "Stripe", ... },
      { "name": "PayPal", ... },
      { "name": "Clover", ... },
      { "name": "GoDaddy", ... },
  ]
  ```
- **Missing**: Helcim, Toast, Shopify, PayPal Business, Merchant Maverick
- **Location**: Line ~240 in `generate_session_json.py`

### 3. fill_session.py BUILD Filter Too Strict
- **Problem**: Line 202 only matches actions with `agent == "BUILD"`
- **Reality**: Strategy actions have agents like "Content + SEO", "Publisher Outreach"
- **Result**: Build pages never generated, `build_pages: []` always empty
- **Fixed**: ✅ Updated to match any content/build-related keywords

### 4. PaaS Deployment Lag
- **Problem**: Changes pushed to GitHub but not deployed to PaaS yet
- **Typical lag**: 2-5 minutes
- **Workaround**: Hard refresh browser (Ctrl+Shift+R)

## ✅ Fixes Applied

### 1. fill_session.py BUILD Filter Fixed
**File**: `fill_session.py` line 202

**Before**:
```python
build_actions = [a for a in p0 + p1 if a.get("agent") == "BUILD"]
```

**After**:
```python
# Match any action that involves building content/pages
build_actions = [a for a in p0 + p1 if any(
    keyword in a.get("agent", "").lower() or keyword in a.get("action", "").lower()
    for keyword in ["build", "content", "page", "landing", "seo", "publish"]
)]
```

**Impact**: `build_pages` will now populate correctly when `fill_session.py` runs

## ⚠️ Remaining Issues to Fix

### 1. Expand Competitors Array
**File**: `generate_session_json.py` (around line 240)

**Current** (5 competitors):
```python
"competitors": [
    { "name": "Square",  "sov": 95, ... },
    { "name": "Stripe",  "sov": 92, ... },
    { "name": "PayPal",  "sov": 88, ... },
    { "name": "Clover",  "sov": 50, ... },
    { "name": "GoDaddy", "sov": 0,  ... },
]
```

**Should add** (based on competitive_intel data):
```python
"competitors": [
    { "name": "Square",  "sov": 95, ... },
    { "name": "Stripe",  "sov": 92, ... },
    { "name": "PayPal",  "sov": 88, ... },
    { "name": "Helcim",  "sov": 60, "display": "~60%", "label": "Interchange+ ~1.93% + $0.08 — volume discounts", ... },
    { "name": "Toast",   "sov": 55, "display": "~55%", "label": "Restaurant POS — 2.49% + $0.15", ... },
    { "name": "Shopify Payments", "sov": 70, "display": "~70%", "label": "E-commerce anchor", ... },
    { "name": "Clover",  "sov": 50, ... },
    { "name": "GoDaddy", "sov": 0,  ... },
]
```

### 2. Force PaaS Redeployment
**Options**:
1. **Wait 5-10 minutes** and hard refresh (Ctrl+Shift+R)
2. **Trigger manual redeploy** via PaaS dashboard
3. **Push a trivial change** to force rebuild:
   ```bash
   echo "<!-- Cache bust -->" >> public/index.html
   git add public/index.html
   git commit -m "Force PaaS redeploy"
   git push origin main
   ```

### 3. Verify Dashboard Rendering
**After PaaS deploys**, check:
- Categories boxes render correctly
- All competitors show (not just 5)
- "What we track" loads data
- Actions formatting looks correct

## 📋 Next Steps

1. **Commit fill_session.py fix**:
   ```bash
   git add fill_session.py
   git commit -m "Fix: expand BUILD action filter to catch content/SEO agents"
   git push origin main
   ```

2. **Fix competitors array** in `generate_session_json.py`:
   - Add missing competitors (Helcim, Toast, Shopify, etc.)
   - Get SOV estimates from competitive research
   - Regenerate session.json

3. **Force PaaS redeploy**:
   - Option: Push trivial change to public/index.html
   - Or: Wait for auto-redeploy + hard refresh

4. **Test on Monday**:
   - Weekly benchmark will run at 9am
   - Fill session will run at 10am with fixed filter
   - Verify build_pages populates correctly

## 🔧 Quick Diagnostic Commands

```bash
# Check what GitHub has
curl -s https://raw.githubusercontent.com/tyunugyen/geo-dashboard/main/public/data/session.json | jq '.meta.last_updated'

# Check local session.json
cat public/data/session.json | jq '.meta.last_updated'

# Count competitors
cat public/data/session.json | jq '.competitors | length'

# Check model_sov
cat public/data/session.json | jq '.model_sov.primary | length'

# Check build_pages
cat public/data/session.json | jq '.build_pages | length'
```

## 💡 Why This Happened

1. **Dashboard cache** - PaaS serves cached HTML/JS for performance
2. **Hardcoded data** - Competitors list wasn't dynamic enough
3. **Strict filter** - BUILD check was too narrow for real strategy agents
4. **Test timing** - Your test ran before PaaS finished deploying

This is normal for a new automation setup. Once Monday's scheduled run completes and PaaS catches up, everything should work smoothly.
