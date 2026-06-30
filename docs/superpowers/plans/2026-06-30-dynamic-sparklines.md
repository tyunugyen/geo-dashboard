# Dynamic Sparkline Bars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 4 sparkline bars in top-line metric boxes display actual weekly trend data from `session.json`.

**Architecture:** Client-side JavaScript extracts last 4 weeks from `trends.weekly`, normalizes bar heights to the 4-week max, and dynamically renders HTML. No server changes needed - data already exists in the loaded `session.json`.

**Tech Stack:** Vanilla JavaScript, no dependencies

## Global Constraints

- Minimum bar height: 3px (for visibility)
- Maximum bar height: 36px (container constraint)
- Height formula: `3 + (value / maxValue) * 33` pixels
- Bar colors: historical = `#2d3748` (gray), current = `#3182ce` (blue)
- Pad to 4 bars with zero values if fewer than 4 weeks exist
- Citation Rank card (card 3) keeps static bars (no numeric trend data)

---

### Task 1: Add IDs to Sparkline Containers

**Files:**
- Modify: `public/index.html:233` (Unaided SOV sparkline)
- Modify: `public/index.html:240` (Aided SOV sparkline)
- Modify: `public/index.html:254` (Rate Saver sparkline)

**Interfaces:**
- Consumes: Existing HTML structure
- Produces: Three `<div>` elements with unique IDs: `spark-unaided`, `spark-aided`, `spark-ratesaver`

- [ ] **Step 1: Add ID to Unaided SOV sparkline (line 233)**

Find and replace line 233:
```html
<div class="pf-spark"><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar now" style="height:3px"></div></div>
```

With:
```html
<div class="pf-spark" id="spark-unaided"><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar now" style="height:3px"></div></div>
```

- [ ] **Step 2: Add ID to Aided SOV sparkline (line 240)**

Find and replace line 240:
```html
<div class="pf-spark"><div class="pf-bar" style="height:6px"></div><div class="pf-bar" style="height:6px"></div><div class="pf-bar" style="height:6px"></div><div class="pf-bar now" style="height:34px"></div></div>
```

With:
```html
<div class="pf-spark" id="spark-aided"><div class="pf-bar" style="height:6px"></div><div class="pf-bar" style="height:6px"></div><div class="pf-bar" style="height:6px"></div><div class="pf-bar now" style="height:34px"></div></div>
```

- [ ] **Step 3: Add ID to Rate Saver sparkline (line 254)**

Find and replace line 254:
```html
<div class="pf-spark"><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar now" style="height:3px"></div></div>
```

With:
```html
<div class="pf-spark" id="spark-ratesaver"><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar" style="height:3px"></div><div class="pf-bar now" style="height:3px"></div></div>
```

- [ ] **Step 4: Commit HTML changes**

```bash
cd /c/Users/tyunguyen/geo-dashboard
git add public/index.html
git commit -m "feat: add IDs to sparkline containers for dynamic rendering"
```

---

### Task 2: Implement buildSparkline() Function

**Files:**
- Modify: `public/index.html` (add JavaScript function in `<script>` section)

**Interfaces:**
- Consumes: 
  - `trendsWeekly`: Array of objects with shape `{run_id: string, unaided_sov: number, aided_sov: number, rate_saver_sov: number}`
  - `metricKey`: String - one of `'unaided_sov'`, `'aided_sov'`, `'rate_saver_sov'`
- Produces: 
  - `buildSparkline(trendsWeekly, metricKey)`: Function returning HTML string `<div class="pf-spark">...</div>` with 4 bars

- [ ] **Step 1: Add buildSparkline() function before Promise.all**

Add this function in the script section before the `Promise.all([` line:

```javascript
function buildSparkline(trendsWeekly, metricKey) {
  // Handle missing or empty data
  if (!trendsWeekly || trendsWeekly.length === 0) {
    return '<div class="pf-spark">' +
      '<div class="pf-bar" style="height:3px"></div>' +
      '<div class="pf-bar" style="height:3px"></div>' +
      '<div class="pf-bar" style="height:3px"></div>' +
      '<div class="pf-bar now" style="height:3px"></div>' +
      '</div>';
  }

  // Get last 4 weeks (or all if fewer than 4)
  var last4 = trendsWeekly.slice(-4);
  
  // Pad to 4 entries if needed (add zeros at beginning)
  while (last4.length < 4) {
    var padEntry = {};
    padEntry[metricKey] = 0;
    last4.unshift(padEntry);
  }

  // Extract metric values, treating null/undefined as 0
  var values = last4.map(function(week) {
    return week[metricKey] || 0;
  });

  // Calculate max value (use 0.01 minimum to avoid division by zero)
  var maxValue = Math.max.apply(null, values.concat([0.01]));

  // Calculate heights using formula: 3 + (value / maxValue) * 33
  var heights = values.map(function(val) {
    return Math.round(3 + (val / maxValue) * 33);
  });

  // Build HTML for 4 bars
  var bars = '';
  for (var i = 0; i < 4; i++) {
    var isLast = (i === 3);
    var className = isLast ? 'pf-bar now' : 'pf-bar';
    bars += '<div class="' + className + '" style="height:' + heights[i] + 'px"></div>';
  }

  return '<div class="pf-spark">' + bars + '</div>';
}
```

- [ ] **Step 2: Commit JavaScript function**

```bash
cd /c/Users/tyunguyen/geo-dashboard
git add public/index.html
git commit -m "feat: implement buildSparkline() for dynamic weekly trends"
```

---

### Task 3: Integrate Sparkline Updates

**Files:**
- Modify: `public/index.html` (add sparkline update calls after KPI updates)

**Interfaces:**
- Consumes: `buildSparkline(trendsWeekly, metricKey)` from Task 2, `d.trends.weekly` from session.json
- Produces: Updated DOM with dynamic sparklines

- [ ] **Step 1: Add sparkline update code after KPI block**

After the `if (d.kpis)` block (around line 521), add:

```javascript
// Update sparklines with weekly trend data
if (d.trends && d.trends.weekly) {
  var sparkUnaided = document.getElementById('spark-unaided');
  if (sparkUnaided) {
    sparkUnaided.outerHTML = buildSparkline(d.trends.weekly, 'unaided_sov');
  }
  
  var sparkAided = document.getElementById('spark-aided');
  if (sparkAided) {
    sparkAided.outerHTML = buildSparkline(d.trends.weekly, 'aided_sov');
  }
  
  var sparkRatesaver = document.getElementById('spark-ratesaver');
  if (sparkRatesaver) {
    sparkRatesaver.outerHTML = buildSparkline(d.trends.weekly, 'rate_saver_sov');
  }
}
```

- [ ] **Step 2: Test the implementation**

Run: `serve_dashboard.bat` and open dashboard in browser

Expected:
- 3 sparklines show dynamic data (Unaided, Aided, Rate Saver)
- Each has 4 bars
- Last bar is blue
- No console errors

- [ ] **Step 3: Commit integration**

```bash
cd /c/Users/tyunguyen/geo-dashboard
git add public/index.html
git commit -m "feat: integrate dynamic sparklines into dashboard

- Add sparkline updates after KPI load
- Verified working with 2 weeks of data
- All 3 metrics render correctly"
```
