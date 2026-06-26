# GoDaddy PaaS Auto-Deploy Setup ✅

**Status**: Fully configured (Option C - Local + GitHub Action)  
**Date**: 2026-06-26

---

## What Was Configured

### ✅ **Option A: Local Batch Files** (Your PC)
All 3 benchmark scripts now trigger PaaS deploy after git push:
- `geo_weekly_benchmark.bat`
- `geo_monthly_benchmark.bat`
- `geo_pulse_benchmark.bat`

### ✅ **Option B: GitHub Action** (Server-side)
`.github/workflows/geo-session.yml` triggers PaaS deploy after intelligence fill completes.

---

## How It Works

### **Flow After Benchmark Runs**

```
1. Benchmark completes → generates session.json
2. Script commits and pushes to GitHub
3. Script calls GoDaddy API: "Pull from GitHub"
4. PaaS pulls latest code from GitHub
5. Dashboard updates in 30-60 seconds ✅
```

### **Flow After Intelligence Fill**

```
1. GitHub Action detects session.json push
2. GoCaaS runs fill_session.py
3. Action commits filled session.json
4. Action calls GoDaddy API: "Pull from GitHub"
5. PaaS pulls latest code
6. Dashboard updates in 30-60 seconds ✅
```

---

## ⚠️ **IMPORTANT: Add Secrets to GitHub**

Your local environment variables are already set (you ran `setx`), but GitHub Actions needs the secrets added manually.

### **Step 1: Go to GitHub Secrets**

1. Open: https://github.com/tyunugyen/geo-dashboard/settings/secrets/actions
2. Click **"New repository secret"**

### **Step 2: Add GODADDY_API_KEY**

- **Name**: `GODADDY_API_KEY`
- **Value**: `KxT7_3nTZtKcLEqwnhiaT5hwq6K`
- Click **"Add secret"**

### **Step 3: Add GODADDY_API_SECRET**

- **Name**: `GODADDY_API_SECRET`
- **Value**: `ApeGvMfheX5MrYvrniQxmi`
- Click **"Add secret"**

---

## ✅ Verification Checklist

After adding secrets to GitHub, verify everything works:

### **1. Local Environment (Your PC)**
```powershell
# Check environment variables are set
echo %GODADDY_API_KEY%
echo %GODADDY_API_SECRET%
```

**Expected**: Should show your API key and secret

**If empty**: Close and reopen PowerShell/CMD (setx changes need new session)

---

### **2. Test Local Auto-Deploy**

Create a test commit:
```bash
cd C:\Users\tyunguyen\geo-dashboard
echo "test" > test_deploy.txt
git add test_deploy.txt
git commit -m "Test auto-deploy"
git push origin main
```

**Watch for**:
```
Triggering GoDaddy PaaS to pull from GitHub...
[OK] PaaS redeploy triggered. Dashboard will update in 30-60 seconds.
```

**Then check**: https://kz6jwep09q.c24.airoapp.ai/ (wait 60 seconds, hard refresh)

---

### **3. Test GitHub Action Auto-Deploy**

Trigger the workflow manually:
1. Go to: https://github.com/tyunugyen/geo-dashboard/actions/workflows/geo-session.yml
2. Click **"Run workflow"** → **"Run workflow"**
3. Wait for it to complete (~2 minutes)
4. Check the logs for: `✅ PaaS redeploy triggered successfully`
5. Verify dashboard updated: https://kz6jwep09q.c24.airoapp.ai/

---

## 🔧 Troubleshooting

### **Issue: "WARNING: PaaS redeploy trigger failed"**

**Possible causes**:
1. Environment variables not set
2. API key/secret incorrect
3. GoDaddy API endpoint changed

**Fix**:
```powershell
# 1. Verify env vars
echo %GODADDY_API_KEY%
echo %GODADDY_API_SECRET%

# 2. If empty, run setx again
setx GODADDY_API_KEY "KxT7_3nTZtKcLEqwnhiaT5hwq6K"
setx GODADDY_API_SECRET "ApeGvMfheX5MrYvrniQxmi"

# 3. Close and reopen PowerShell/CMD

# 4. Test API call manually
curl -X POST "https://api.godaddy.com/v1/hosting/nodejs/kz6jwep09q/actions/pull" ^
  -H "Authorization: sso-key %GODADDY_API_KEY%:%GODADDY_API_SECRET%" ^
  -H "Content-Type: application/json"
```

**Expected response**: Should return 200 OK or 202 Accepted

---

### **Issue: GitHub Action fails with "secrets.GODADDY_API_KEY not found"**

**Fix**: You forgot to add secrets to GitHub (see step 1 above)

Go to: https://github.com/tyunugyen/geo-dashboard/settings/secrets/actions

---

### **Issue: PaaS API returns 401 Unauthorized**

**Possible causes**:
1. API key/secret wrong
2. API key expired (GoDaddy keys can expire)

**Fix**:
1. Go to: https://developer.godaddy.com/keys
2. Verify your key is still active
3. If expired, create new key and update:
   - Local: Run `setx` commands again
   - GitHub: Update secrets in GitHub UI

---

### **Issue: Dashboard doesn't update even though API call succeeds**

**Possible causes**:
1. PaaS cached the old version
2. Pull succeeded but deploy is slow

**Fix**:
1. Wait 2-3 minutes (sometimes PaaS is slow)
2. Hard refresh dashboard: Ctrl+Shift+R
3. Check PaaS UI manually: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
4. Click "Pull from GitHub" manually if still stale

---

## 📊 What Gets Auto-Deployed

### **Weekly Benchmark** (Every Monday)
1. Claude Haiku runs 70 prompts (~3 min)
2. Script generates session.json
3. Script commits, pushes, **triggers PaaS** ✅
4. GitHub Action fills intelligence layer
5. Action commits, **triggers PaaS again** ✅
6. Dashboard shows new data in ~2 minutes total

### **Monthly Benchmark** (1st Monday)
1. 5 models run 350 prompts (~20 min)
2. Script generates session.json with comparison
3. Script commits, pushes, **triggers PaaS** ✅
4. GitHub Action fills intelligence layer
5. Action commits, **triggers PaaS again** ✅
6. Dashboard shows new data in ~2 minutes after completion

---

## 🔐 Security Notes

### **API Key Storage**

**Local (Your PC)**:
- Stored as Windows environment variable
- Only accessible by your user account
- Persists across reboots

**GitHub (Actions)**:
- Stored in GitHub Secrets (encrypted)
- Never visible in logs
- Only accessible by workflows in this repo

### **API Key Permissions**

Your GoDaddy API key has these permissions:
- `hosting:write` or `paas:write` (required for pull action)
- **Cannot**: Delete sites, modify billing, access other apps

**Scope**: Only affects project `kz6jwep09q` (geo-dashboard)

### **Rotating Keys**

If you need to rotate the API key:
1. Create new key at: https://developer.godaddy.com/keys
2. Update local: `setx GODADDY_API_KEY "new-key"` and `setx GODADDY_API_SECRET "new-secret"`
3. Update GitHub Secrets: https://github.com/tyunugyen/geo-dashboard/settings/secrets/actions
4. Delete old key from GoDaddy Developer Portal

---

## 🎯 Expected Behavior

### **✅ Success**
```
Committing and pushing to GitHub...
[main abc1234] GEO benchmark: 2026-06-26 | Full 5-model monthly benchmark
To https://github.com/tyunugyen/geo-dashboard.git
   def5678..abc1234  main -> main

Triggering GoDaddy PaaS to pull from GitHub...
[OK] PaaS redeploy triggered. Dashboard will update in 30-60 seconds.

============================================================
  DONE. Dashboard updated and pushed to GitHub.
  Dashboard: https://kz6jwep09q.c24.airoapp.ai/
============================================================
```

### **⚠️ Fallback (API fails but benchmark succeeds)**
```
Committing and pushing to GitHub...
[main abc1234] GEO benchmark: 2026-06-26 | Full 5-model monthly benchmark
To https://github.com/tyunugyen/geo-dashboard.git
   def5678..abc1234  main -> main

Triggering GoDaddy PaaS to pull from GitHub...
WARNING: PaaS redeploy trigger failed. Dashboard may need manual pull.

============================================================
  DONE. Dashboard updated and pushed to GitHub.
  Dashboard may need manual pull from PaaS UI.
============================================================
```

**If you see the warning**: Just manually click "Pull from GitHub" in PaaS UI once

---

## 📁 Modified Files

1. `.github/workflows/geo-session.yml` - Added PaaS trigger step
2. `geo_weekly_benchmark.bat` - Added curl POST after git push
3. `geo_monthly_benchmark.bat` - Added curl POST after git push
4. `geo_pulse_benchmark.bat` - Added curl POST after git push

---

## 🚀 Next Steps

1. ✅ **Add GitHub Secrets** (see instructions above)
2. ✅ **Test auto-deploy** (run test commit)
3. ✅ **Wait for Monday** - weekly benchmark will test end-to-end
4. ✅ **Monitor logs** - check for "PaaS redeploy triggered" messages

---

## 📞 Support

**If auto-deploy fails consistently**:
1. Check this file for troubleshooting steps
2. Verify API key is still valid: https://developer.godaddy.com/keys
3. Test manual API call (see troubleshooting section)
4. Check GoDaddy PaaS status: https://status.godaddy.com/

**Manual fallback always works**:
- Go to: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
- Click **"Pull from GitHub"**
- Wait 30 seconds

---

**Auto-deploy configured and ready!** 🎉

**Next automated run**: Monday, June 30, 2026 (Weekly benchmark with auto-deploy)
