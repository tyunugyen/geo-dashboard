# How to Debug PaaS Dashboard Issues

## Step 1: Check What session.json PaaS is Serving

### Method A: Direct URL Check
Open your browser and go to:
```
https://kz6jwep09q.c24.airoapp.ai/data/session.json
```

This shows you EXACTLY what session.json PaaS has. Compare the `last_updated` field to your local one.

### Method B: Browser DevTools
1. Open dashboard: https://kz6jwep09q.c24.airoapp.ai/
2. Press **F12** (or right-click → Inspect)
3. Click **Network** tab
4. Press **Ctrl+R** to refresh
5. Look for `session.json` in the list
6. Click it → **Preview** tab shows the data
7. Check `meta.last_updated` - does it match your local file?

## Step 2: Check PaaS Deployment Settings

### Via PaaS Dashboard
1. Go to GoDaddy PaaS dashboard: https://host.beta.godaddy.com/paas/
2. Find your project: **kz6jwep09q**
3. Click **Settings** or **Configuration**
4. Look for:
   - **Git Repository**: Should be `https://github.com/tyunugyen/geo-dashboard`
   - **Branch**: Should be `main`
   - **Auto-deploy**: Should be enabled
   - **Build command**: Check if it's correct
   - **Deploy directory**: Should be `public` or `.`

### Check Recent Deployments
1. In PaaS dashboard, click **Deployments** tab
2. Look at recent deploy logs
3. Check:
   - When was the last successful deploy?
   - Did it pull the latest commit?
   - Are there any errors?

## Step 3: Compare Files

### Local vs GitHub
```powershell
# Your local file
cat public/data/session.json | findstr "last_updated"

# What's on GitHub
curl -s https://raw.githubusercontent.com/tyunugyen/geo-dashboard/main/public/data/session.json | findstr "last_updated"
```

### Local vs PaaS
```powershell
# Your local file
cat public/data/session.json | findstr "last_updated"

# What PaaS has
curl -s https://kz6jwep09q.c24.airoapp.ai/data/session.json | findstr "last_updated"
```

## Step 4: Force PaaS to Redeploy

### Method A: Via PaaS Dashboard
1. Go to PaaS dashboard
2. Click **Deployments**
3. Click **Redeploy** or **Trigger Deploy** button

### Method B: Via Git Push
```powershell
cd C:\Users\tyunguyen\geo-dashboard

# Make a trivial change to force rebuild
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "public/index.html" -Value "`n<!-- Deployed: $timestamp -->"

git add public/index.html
git commit -m "Force redeploy - cache bust"
git push origin main
```

Then wait 2-3 minutes and refresh dashboard.

## Step 5: Check if PaaS Has File Access

```powershell
# Test if PaaS can serve your files
curl -I https://kz6jwep09q.c24.airoapp.ai/data/session.json

# Should return "200 OK"
# If it returns "404 Not Found", PaaS doesn't have the file
```

## Common Issues & Solutions

### Issue 1: PaaS Shows 404 for session.json
**Problem**: File not deployed or wrong directory structure  
**Fix**: 
- Check PaaS deploy directory setting
- Make sure `public/data/session.json` is committed to git
- Redeploy

### Issue 2: PaaS Shows Old Data
**Problem**: Cached or not redeploying  
**Fix**:
- Clear browser cache (Ctrl+Shift+R)
- Force redeploy via PaaS dashboard
- Push trivial commit to trigger new deploy

### Issue 3: Auto-Deploy Not Working
**Problem**: PaaS not watching GitHub repo  
**Fix**:
- Check webhook settings in GitHub repo
- Reconnect PaaS to GitHub
- Manually trigger deploy

## Quick Diagnostic Script

Save this as `check_paas_sync.ps1`:

```powershell
Write-Host "=== PaaS Sync Checker ===" -ForegroundColor Cyan
Write-Host ""

# Local
$local = (Get-Content public/data/session.json | ConvertFrom-Json).meta.last_updated
Write-Host "Local session.json:  $local" -ForegroundColor Green

# GitHub
try {
    $github = (Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tyunugyen/geo-dashboard/main/public/data/session.json" -UseBasicParsing).Content | ConvertFrom-Json | Select-Object -ExpandProperty meta | Select-Object -ExpandProperty last_updated
    Write-Host "GitHub session.json: $github" -ForegroundColor Yellow
} catch {
    Write-Host "GitHub: ERROR - $_" -ForegroundColor Red
}

# PaaS
try {
    $paas = (Invoke-WebRequest -Uri "https://kz6jwep09q.c24.airoapp.ai/data/session.json" -UseBasicParsing).Content | ConvertFrom-Json | Select-Object -ExpandProperty meta | Select-Object -ExpandProperty last_updated
    Write-Host "PaaS session.json:   $paas" -ForegroundColor Magenta
} catch {
    Write-Host "PaaS: ERROR - $_" -ForegroundColor Red
}

Write-Host ""
if ($local -eq $github -and $github -eq $paas) {
    Write-Host "✓ ALL IN SYNC!" -ForegroundColor Green
} else {
    Write-Host "✗ OUT OF SYNC - PaaS needs to redeploy" -ForegroundColor Red
}
```

Run it:
```powershell
.\check_paas_sync.ps1
```
