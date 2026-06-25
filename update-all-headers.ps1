# Update all HTML files to use dynamic session data
$files = @(
    "prompts.html",
    "aggregators.html",
    "action-build.html",
    "action-amplify.html",
    "action-cite.html",
    "roadmap.html",
    "report.html",
    "maintenance.html"
)

foreach ($file in $files) {
    $path = "C:\Users\tyunguyen\geo-dashboard\public\$file"
    Write-Host "Updating $file..."

    $content = Get-Content $path -Raw

    # Update header-right badges
    $content = $content -replace `
        '(<div class="header-right">\s*)<span class="badge">[^<]*</span>\s*<span class="badge"[^>]*>Last updated: [^<]*</span>\s*<span class="badge badge-warn">[^<]*</span>', `
        '$1<span class="badge" data-run-type>Weekly pulse</span>
    <span class="badge" style="background:#0a1a2d;border-color:#2d4a8a;color:#90cdf4;">Last updated: <span data-last-updated>2026-06-23 16:30</span></span>
    <span class="badge badge-warn" data-unaided-sov>Unaided SOV ~0%</span>'

    # Update last-updated-bar
    $content = $content -replace `
        '<div class="last-updated-bar"[^>]*>\s*<span>Last updated: <strong[^>]*>[^<]*</strong>\s*&nbsp;·&nbsp; Run: <span[^>]*>[^<]*</span>\s*&nbsp;·&nbsp; [^<]*\s*</span>\s*</div>', `
        '<div class="last-updated-bar" style="background:#0d1117; border-bottom:1px solid #2d3748; padding:6px 32px; display:flex; align-items:center; justify-content:space-between; font-size:11px; color:#4a5568;">
  <span>Last updated: <strong style="color:#718096;" data-lu-date>2026-06-23 16:30</strong>
    &nbsp;·&nbsp; Run: <span style="color:#4a5568;" data-lu-run>2026-06-W26</span>
    &nbsp;·&nbsp; <span data-lu-details>Claude · 70 prompts</span>
    <span data-last-benchmark style="display:none;"></span>
  </span>
</div>'

    # Add script tag before </body> if not already there
    if ($content -notmatch 'session-loader\.js') {
        $content = $content -replace '</body>', '<script src="./js/session-loader.js"></script>
</body>'
    }

    $content | Set-Content $path -NoNewline
    Write-Host "  ✓ $file updated"
}

Write-Host "`nAll files updated successfully!"
