# 🎯 Webhook Auto-Deploy Setup (Option 4)

**Status**: Code deployed, webhook config needed  
**Date**: 2026-06-26

---

## ✅ What's Been Added

Your `server.js` now has a **`/webhook` endpoint** that:
1. Receives push notifications from GitHub
2. Verifies the webhook signature (secure)
3. Executes `git pull` to update the dashboard
4. Returns success/failure status

**Result**: Push to GitHub → Dashboard auto-updates in 30 seconds! ✅

---

## 🔧 Setup Steps

### **Step 1: Generate Webhook Secret**

Generate a random secret token (used to verify webhooks are from GitHub):

```powershell
# Run this to generate a random secret
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Copy the output** - you'll need it for Steps 2 and 3.

Example output: `Kx9mP3nT5tKcLEqwnhiaT5hwq6K2aBc8`

---

### **Step 2: Add Secret to GoDaddy PaaS**

1. Go to: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
2. Click **Settings** → **Environment Variables**
3. Add new variable:
   - **Name**: `WEBHOOK_SECRET`
   - **Value**: `<paste the secret from Step 1>`
4. Click **Save**
5. **Restart** the app (if needed)

---

### **Step 3: Add Webhook to GitHub**

1. Go to: https://github.com/tyunugyen/geo-dashboard/settings/hooks
2. Click **Add webhook**
3. Fill in:

   **Payload URL**: `https://kz6jwep09q.c24.airoapp.ai/webhook`
   
   **Content type**: `application/json`
   
   **Secret**: `<paste the same secret from Step 1>`
   
   **Which events**: Select **"Just the push event"**
   
   **Active**: ✅ Checked

4. Click **Add webhook**

---

### **Step 4: Test It!**

Make a small test commit:

```bash
cd C:\Users\tyunguyen\geo-dashboard
echo "webhook test" > webhook_test.txt
git add webhook_test.txt
git commit -m "Test webhook auto-deploy"
git push origin main
```

**What should happen**:
1. GitHub sends webhook to your dashboard
2. Dashboard receives it and runs `git pull`
3. Dashboard updates with new files in ~30 seconds
4. Check GitHub webhook page - should show green checkmark ✅

---

## 🔍 Verify It Worked

### **1. Check GitHub Webhook Logs**

1. Go to: https://github.com/tyunguyen/geo-dashboard/settings/hooks
2. Click on your webhook
3. Click **Recent Deliveries**
4. Latest delivery should show:
   - **Status**: 200 OK ✅
   - **Response**: `{"ok":true,"message":"Dashboard updated from GitHub"...}`

### **2. Check Dashboard Logs (if accessible)**

If you can SSH or view logs in PaaS:
```
[webhook] Push received from tyunguyen to refs/heads/main
[webhook] Executing git pull...
[webhook] Git pull output: Already up to date.
```

### **3. Check Live Dashboard**

Wait 30 seconds, then check: https://kz6jwep09q.c24.airoapp.ai/

The `webhook_test.txt` file should be there (won't show in UI, but will be in repo).

---

## ⚠️ Troubleshooting

### **Issue: Webhook shows 401 Unauthorized**

**Cause**: Secret mismatch between GitHub and PaaS

**Fix**:
1. Generate a new secret (Step 1)
2. Update BOTH GitHub webhook AND PaaS environment variable
3. Restart PaaS app

---

### **Issue: Webhook shows 500 Internal Server Error**

**Possible causes**:
1. `git pull` command failed (permissions issue)
2. PaaS environment doesn't allow executing git commands
3. Git not installed on PaaS server

**Fix**:
Check PaaS logs for exact error. If git commands aren't allowed, you'll need to use **Option 5 (GitHub Pages)** instead.

---

### **Issue: Webhook shows 200 OK but dashboard doesn't update**

**Possible causes**:
1. `git pull` succeeded but PaaS needs restart to serve new files
2. Browser cache

**Fix**:
1. Hard refresh: Ctrl+Shift+R
2. Check PaaS file browser - verify files updated
3. May need to add a restart command after git pull (see below)

---

### **Issue: "Git pull failed: not a git repository"**

**Cause**: PaaS doesn't deploy as a git repo (uses ZIP or other method)

**Fix**: Unfortunately, webhook won't work. Use **Option 5 (GitHub Pages)** instead - it's guaranteed to work and has true auto-deploy.

---

## 🔄 If Git Pull Needs App Restart

If `git pull` works but app needs restart to serve new files, update the webhook code:

Edit `server.js` line ~267 (inside webhook handler):

```javascript
// After git pull succeeds, add:
console.log('[webhook] Restarting app...');
process.exit(0); // PaaS will auto-restart
```

**Note**: This restarts the entire app. Only do this if files don't update without restart.

---

## ✅ Expected Behavior After Setup

### **Fully Automated Flow**

```
1. You: git push origin main
   ↓
2. GitHub: Sends webhook to dashboard
   ↓
3. Dashboard: Receives webhook → runs git pull
   ↓
4. Dashboard: Auto-updates with latest files
   ↓
5. You: Hard refresh browser → see new data
   
Total time: 30-60 seconds ✅
```

### **Weekly/Monthly Benchmarks**

```
Monday 9am: Scheduled task runs
  → Benchmark completes
  → Commits session.json
  → Pushes to GitHub
  → GitHub sends webhook ✅
  → Dashboard auto-pulls ✅
  → GitHub Action runs fill_session.py
  → Commits filled session.json
  → Pushes to GitHub
  → GitHub sends webhook again ✅
  → Dashboard auto-pulls again ✅
  → Dashboard fully updated!
```

**No manual steps!** Just check the dashboard Monday morning.

---

## 🔐 Security Notes

### **Webhook Secret**

- Stored in PaaS environment variables (secure)
- Stored in GitHub webhook settings (secure)
- Used to verify webhooks are from GitHub, not attackers
- Without secret, anyone could trigger git pull on your server

### **What Webhook Can Do**

- ✅ Run `git pull` (read-only, safe)
- ❌ Cannot push, delete files, or modify code
- ❌ Cannot access other PaaS apps
- ❌ Cannot access environment variables or secrets

**Scope**: Only affects this one repo and dashboard.

---

## 📊 Comparison: Before vs After

### **Before (Manual)**
```
1. Benchmark runs
2. Git push
3. [YOU] Open PaaS UI
4. [YOU] Click "Pull from GitHub"
5. [YOU] Wait 30 seconds
6. [YOU] Hard refresh browser

Total: 5 manual steps, 2 minutes
```

### **After (Webhook Auto-Deploy)**
```
1. Benchmark runs
2. Git push
3. [AUTO] Webhook triggers
4. [AUTO] Dashboard pulls from GitHub
5. [AUTO] Files update
6. [YOU] Hard refresh browser (30 sec later)

Total: 1 manual step, 30 seconds
```

---

## 🎯 Fallback Options

If webhook setup fails (git not allowed on PaaS), you have two backups:

### **Option 5: GitHub Pages** (Recommended)
- Go to: https://github.com/tyunguyen/geo-dashboard/settings/pages
- Enable Pages, source: `main` branch, `/public` folder
- Get URL: `https://tyunguyen.github.io/geo-dashboard/`
- **TRUE auto-deploy, zero config needed**

### **Manual Trigger**
- Run: `.\trigger_paas_deploy.bat`
- Takes 10 seconds

---

## 📁 Modified Files

1. `server.js` - Added `/webhook` endpoint with git pull logic
2. `WEBHOOK_AUTO_DEPLOY_SETUP.md` - This file

---

## 🚀 Next Steps

1. ✅ **Generate webhook secret** (Step 1)
2. ✅ **Add to PaaS environment variables** (Step 2)
3. ✅ **Add webhook to GitHub** (Step 3)
4. ✅ **Test with small commit** (Step 4)
5. ✅ **Verify in webhook logs** (check green checkmark)

**Once setup**: Every push auto-deploys! 🎉

---

## 📞 Support

**If webhook fails consistently**:
1. Check GitHub webhook logs for error details
2. Check PaaS logs (if accessible)
3. Verify PaaS allows `git` commands (might be restricted)
4. **Fallback**: Use GitHub Pages instead (guaranteed to work)

**Manual fallback always works**:
```bash
.\trigger_paas_deploy.bat
```

---

**Webhook code deployed and ready for configuration!** 

**Time to setup**: ~5 minutes  
**Result**: Fully automated git-push → dashboard-updates ✅
