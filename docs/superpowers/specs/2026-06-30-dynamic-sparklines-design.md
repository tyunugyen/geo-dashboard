# Dynamic Sparkline Bars Design

**Date:** 2026-06-30  
**Status:** Approved  
**Author:** Claude Code

## Overview

Make the 4 sparkline bars in each top-line metric box dynamic to show the last 4 weeks of actual data from the `trends.weekly` array in `session.json`.

Currently, the bars are hardcoded static HTML. This change will make them reflect real weekly trend data, showing whatever weeks are available (padding with zeros for missing weeks).

## Goals

- Display historical trend data visually in the 4 metric cards
- Use existing `trends.weekly` data already loaded from `session.json`
- Show 1-4 weeks of data, padding earlier weeks with zero values if fewer than 4 weeks exist
- Maintain existing visual styling (gray bars for history, blue bar for current)

## Data Flow

### Data Source
- Use `trends.weekly` array from the already-loaded `session.json`
- Each entry contains:
  - `run_id`: Week identifier (e.g., "2026-06-W27")
  - `unaided_sov`: Unaided share of voice percentage
  - `aided_sov`: Aided share of voice percentage
  - `rate_saver_sov`: Rate Saver citation percentage

### 4-Week Window Logic
1. Extract last 4 entries from `trends.weekly` (most recent = rightmost bar)
2. If fewer than 4 weeks exist, pad the beginning with zero values
3. Example with 2 weeks of data: `[{sov: 0}, {sov: 0}, {week1_data}, {week2_data}]`

### Metric Mapping
- **Card 1 (Unaided SOV)**: Use `unaided_sov` from trends
- **Card 2 (Aided SOV)**: Use `aided_sov` from trends
- **Card 3 (Citation Rank)**: Keep static bars (no numeric trend data)
- **Card 4 (Rate Saver Cited)**: Use `rate_saver_sov` from trends

## Bar Height Calculation

### Normalization Formula
- Heights are calculated relative to the maximum value in the 4-week window
- Minimum bar height: **3px** (for visibility, even when value is 0)
- Maximum bar height: **36px** (container height from CSS `.pf-spark`)
- Formula: `height = 3 + (value / maxValue) * 33` if maxValue > 0, else 3px

### Visual Styling
- **Bars 1-3** (historical): Gray background (`#2d3748`)
- **Bar 4** (current): Blue background (`#3182ce`) with class `now`
- All bars retain rounded top corners from existing CSS (`.pf-bar` styling)

## Implementation

### JavaScript Function

**Function Signature:**
```javascript
function buildSparkline(trendsWeekly, metricKey)
```

**Parameters:**
- `trendsWeekly`: Array of weekly trend objects from `session.json`
- `metricKey`: String - metric name to extract (`'unaided_sov'`, `'aided_sov'`, `'rate_saver_sov'`)

**Algorithm:**
1. Extract last 4 weeks from `trendsWeekly` array
2. If fewer than 4 entries, pad start with `{[metricKey]: 0}` objects
3. Extract metric values: `values = weeks.map(w => w[metricKey] || 0)`
4. Calculate max: `maxValue = Math.max(...values, 0.01)` (avoid division by zero)
5. Calculate heights: `heights = values.map(v => 3 + (v / maxValue) * 33)`
6. Generate HTML for 4 bars:
   - First 3 bars: `<div class="pf-bar" style="height: Xpx"></div>`
   - Last bar: `<div class="pf-bar now" style="height: Xpx"></div>`
7. Return HTML string wrapped in container: `<div class="pf-spark">...</div>`

**Return Value:**
HTML string containing the complete sparkline markup

### Integration Points

**DOM Modification:**
Add unique IDs to each metric card's sparkline container in `index.html`:
- Card 1: `<div class="pf-spark" id="spark-unaided">...</div>`
- Card 2: `<div class="pf-spark" id="spark-aided">...</div>`
- Card 3: `<div class="pf-spark" id="spark-citation">...</div>` (unchanged, static)
- Card 4: `<div class="pf-spark" id="spark-ratesaver">...</div>`

**JavaScript Calls:**
In the existing `fetch('/data/session.json')` callback, after loading data:
```javascript
if (d.trends && d.trends.weekly) {
  document.getElementById('spark-unaided').outerHTML = buildSparkline(d.trends.weekly, 'unaided_sov');
  document.getElementById('spark-aided').outerHTML = buildSparkline(d.trends.weekly, 'aided_sov');
  document.getElementById('spark-ratesaver').outerHTML = buildSparkline(d.trends.weekly, 'rate_saver_sov');
}
```

### Error Handling

**Missing Data:**
- If `trends.weekly` is undefined or empty: generate 4 bars at minimum height (3px)
- If individual metric value is null/undefined: treat as 0
- If metricKey doesn't exist in trend object: treat as 0

**Graceful Degradation:**
- Dashboard never breaks due to missing trend data
- Falls back to showing flat baseline bars (all 3px) when no data available
- Ensures visual consistency even with incomplete data

## Files Modified

1. **`public/index.html`** (HTML changes):
   - Add IDs to 3 sparkline containers: `spark-unaided`, `spark-aided`, `spark-ratesaver`
   
2. **`public/index.html`** (JavaScript changes):
   - Add `buildSparkline()` function
   - Add 3 calls to update sparklines in the session.json load callback

## Testing Checklist

- [ ] Verify bars display correctly with 2 weeks of data (current state)
- [ ] Verify bars display correctly with 4+ weeks of data (future state)
- [ ] Verify bars display correctly with 0 weeks of data (all zeros)
- [ ] Verify bar heights scale proportionally to values
- [ ] Verify current week bar has blue color and `now` class
- [ ] Verify historical bars have gray color
- [ ] Verify Citation Rank card keeps static bars (unchanged)
- [ ] Verify no JavaScript errors in browser console
- [ ] Verify dashboard loads and renders without breaking

## Future Enhancements (Out of Scope)

- Add hover tooltips showing exact SOV percentage per week
- Add week labels (W25, W26, W27, W28) below bars
- Animate bar height transitions when data updates
- Add trend indicators (↑↓ arrows) based on week-over-week change

## Assumptions

- `session.json` format remains stable with `trends.weekly` array
- Weekly data continues to be generated by `fill_session.py`
- `trends.weekly` array is sorted chronologically (oldest first)
- Dashboard loads `session.json` exactly once per page load
