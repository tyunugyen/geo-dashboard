# Check PaaS Deployment Settings

## Step 1: Open PaaS Dashboard
1. Go to: https://host.beta.godaddy.com/paas/
2. Find your project: **kz6jwep09q** or search "geo-dashboard"
3. Click on it

## Step 2: Check Auto-Deploy Settings

### Look for "Deployments" or "Settings" Tab
Check these settings:

**Auto-Deploy**:
- ☑️ **Enabled** = No button clicks needed, auto-deploys on push
- ☐ **Disabled** = You must click "Deploy" or "Publish" manually

**Branch**:
- Should be set to: `main`
- Confirms it's watching the right branch

**Build Command** (if shown):
- Usually blank for static sites
- Or something like: `npm run build` or `build.sh`

**Deploy Directory**:
- Should be: `public` or `.` (root)
- This tells PaaS which folder to serve

## Step 3: Check Recent Deployments

Look for a "Deployments" or "History" section:
- Should show recent deploys with timestamps
- Check if your latest commits appear
- Look for:
  - `92bdbbb` - "Fix dashboard rendering issues" (~10 min ago)
  - `11b1e1b` - "Fix 'What we track' Loading issue" (~5 min ago)

## Step 4: Preview vs Live (If Applicable)

Some PaaS have two environments:

### Preview Environment
- URL: Something like `preview-kz6jwep09q.c24.airoapp.ai`
- Auto-updates on every push
- For testing before going live

### Live/Production Environment  
- URL: `kz6jwep09q.c24.airoapp.ai`
- May require clicking "Publish to Live" button
- Or auto-syncs from preview after X minutes

**Check which URL you're using:**
```
Your dashboard: https://kz6jwep09q.c24.airoapp.ai/
```

If this is "preview" - auto-updates on push ✅
If this is "live" - check if "Publish to Live" button exists

---

## What to Do Based on What You See

### Scenario A: Auto-Deploy is ON ✅
**What you see**: 
- Auto-deploy toggle is checked/enabled
- Recent deployments show your commits

**What to do**:
- ✅ Nothing! Just wait 5 minutes
- ✅ Hard refresh: Ctrl+Shift+R
- ✅ Dashboard updates automatically

### Scenario B: Manual Deploy Required ⚠️
**What you see**:
- Auto-deploy is OFF
- "Deploy Now" or "Publish" button visible
- Recent deployments list is empty

**What to do**:
- ❌ Click "Deploy Now" or "Trigger Deploy" button
- ⏱️ Wait for build to complete (status shows)
- ✅ Then hard refresh dashboard

### Scenario C: Preview → Live Flow 🔄
**What you see**:
- Two URLs: preview and live
- "Publish to Live" button exists
- You're viewing the "live" URL

**What to do**:
- Preview auto-updates (check it first)
- If preview looks good, click "Publish to Live"
- Wait for publish to complete
- Hard refresh live URL

---

## Quick Test: Is Auto-Deploy Working?

Run this to see if PaaS deployed your latest changes:

```powershell
# Check latest commit on GitHub
cd C:\Users\tyunguyen\geo-dashboard
git log -1 --oneline

# Check what PaaS has (wait 5 min after push first)
curl -s https://kz6jwep09q.c24.airoapp.ai/data/session.json | findstr "last_updated"

# Compare - should match
cat public/data/session.json | findstr "last_updated"
```

If they match → auto-deploy is working ✅
If PaaS is behind → you need to click deploy button ⚠️

---

## Most Common Setup (Your Likely Case)

Based on the fact that we verified sync earlier and PaaS had your data:

**Your PaaS is probably**:
- ✅ Auto-deploy enabled
- ✅ Watching `main` branch
- ✅ Serving `public` folder
- ✅ Updates automatically on push

**So you just need to**:
1. Wait 5 minutes after `git push`
2. Hard refresh: Ctrl+Shift+R
3. That's it!

---

## If Unsure, Take a Screenshot

If you're not sure which scenario you have:
1. Open PaaS dashboard
2. Take a screenshot of the main page
3. Share it and I can tell you exactly what to do

Or just wait 5 minutes and hard refresh - if it works, you had auto-deploy all along! 🎯
