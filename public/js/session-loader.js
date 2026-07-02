// session-loader.js — shared fetch + render engine for all dashboard tabs
// All tabs call: loadSession().then(s => renderTab(s))

const SESSION_URL = './data/session.json';

// ── Core loader ───────────────────────────────────────────────────
async function loadSession() {
  try {
    const sessionRes = await fetch(SESSION_URL + '?v=' + Date.now());
    const session = await sessionRes.json();
    return session;
  } catch(e) {
    console.error('Session load failed:', e);
    return null;
  }
}

// ── Header bar (runs on every tab) ───────────────────────────────
function renderHeader(s) {
  const m = s.meta || {};
  const u = s.sov_dashboard?.unaided_sov?.value || s.kpis?.unaided_sov?.value || '~0%';

  // Update header badges
  document.querySelectorAll('[data-last-updated]').forEach(el =>
    el.textContent = m.last_updated || '—');

  document.querySelectorAll('[data-run-type]').forEach(el => {
    if (m.run_type === 'weekly') {
      el.textContent = 'Weekly pulse';
      el.className = 'badge';
    } else if (m.run_type === 'monthly') {
      el.textContent = 'Full benchmark';
      el.className = 'badge badge-success';
    }
  });

  document.querySelectorAll('[data-unaided-sov]').forEach(el =>
    el.textContent = 'Unaided SOV ' + u);

  // Last updated bar
  document.querySelectorAll('[data-lu-date]').forEach(el =>
    el.textContent = m.last_updated || '—');

  document.querySelectorAll('[data-lu-run]').forEach(el =>
    el.textContent = m.run_id || '—');

  document.querySelectorAll('[data-lu-details]').forEach(el => {
    if (m.run_type === 'weekly') {
      el.textContent = `${m.model_name || 'Claude'} · ${m.prompt_count || 70} prompts`;
    } else if (m.run_type === 'monthly') {
      el.textContent = `${m.model_count || 9} models · ${m.prompt_count || 70} prompts`;
    }
  });

  // Show last full benchmark on weekly pages
  document.querySelectorAll('[data-last-benchmark]').forEach(el => {
    if (m.run_type === 'weekly' && m.last_full_benchmark) {
      el.style.display = 'inline';
      el.innerHTML = ` · &nbsp; Last full benchmark: <strong>${m.last_full_benchmark}</strong>`;
    } else {
      el.style.display = 'none';
    }
  });
}

// ── SOV KPI cards (Overview + Report) ────────────────────────────
function renderSOVCards(s) {
  const d = s.sov_dashboard || {};
  set('kpi-unaided',     d.unaided_sov?.value  || '~0%');
  set('kpi-aided',       d.aided_sov?.value    || '~100%');
  set('kpi-rate-saver',  d.rate_saver_sov?.value || '0%');
  set('kpi-citation',    d.citation_rank?.value || 'Unranked');
}

// ── Category grid (Overview) ──────────────────────────────────────
function renderCategories(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const cats = s.categories || [];
  el.innerHTML = cats.map(c => `
    <div class="cat-cell cat-cell-${c.cell || c.status || 'red'}" title="${c.name}">
      <div class="cat-name">${c.name.replace(/_/g,' ')}</div>
      <div class="cat-sov ${c.cell || c.color || 'red'}">${c.sov}</div>
      <div class="cat-target">→ ${c.target}</div>
    </div>`).join('');
}

// ── Competitor bars (Overview) ────────────────────────────────────
function renderCompetitors(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const comps = s.competitors || [];
  el.innerHTML = comps.map(c => `
    <div class="comp-row${c.godaddy ? ' comp-godaddy' : ''}">
      <div class="comp-name">${c.name}</div>
      <div class="comp-bar-wrap">
        <div class="comp-bar-fill" style="width:${c.sov}%;background:${c.bar}"></div>
      </div>
      <div class="comp-pct">${c.display}</div>
      <div class="comp-label">${c.label}</div>
    </div>`).join('');
}

// ── Model tables (Overview + Report) ─────────────────────────────
// FIX 2026-07: Added missing Frequency column (2nd <td>) to match 6-column <thead>
// BEFORE: 5 <td>s per row — Model | Why | Unaided | Aided | Status
// AFTER:  6 <td>s per row — Model | Frequency | Why | Unaided | Aided | Status
function renderModelTables(s) {
  const primary = s.model_sov?.primary || [];
  const pulse   = s.model_sov?.pulse   || [];
  const COLOR_MAP = {'red':'#fc8181','yellow':'#f6e05e','green':'#68d391','blue':'#90cdf4'};

  const primaryEl = document.getElementById('primary-model-rows');
  if (primaryEl) primaryEl.innerHTML = primary.map(m => {
    const isHaiku = (m.name || '').toLowerCase().includes('haiku');
    const freq = isHaiku
      ? '<span style="background:#f6ad55;color:#1a202c;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;margin-right:4px;">WEEKLY</span><span style="background:#2d4a8a;color:#90cdf4;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;">MONTHLY</span>'
      : '<span style="background:#2d4a8a;color:#90cdf4;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;">MONTHLY</span>';
    const uColor = COLOR_MAP[m.u_color] || m.u_color || '#fc8181';
    const aColor = COLOR_MAP[m.a_color] || m.a_color || '#68d391';
    return `<tr>
      <td><strong>${m.name}</strong></td>
      <td>${freq}</td>
      <td style="color:#a0aec0;font-size:11px;">${m.why}</td>
      <td><span class="model-tag tag-red" style="color:${uColor}">${m.unaided}</span></td>
      <td><span class="model-tag" style="background:#1a2744;color:${aColor};">${m.aided}</span></td>
      <td>${statusBadge(m.status)}</td>
    </tr>`;
  }).join('');

  const pulseEl = document.getElementById('pulse-model-rows');
  if (pulseEl) pulseEl.innerHTML = pulse.map(m => {
    const freq = '<span style="background:#f6ad55;color:#1a202c;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;">WEEKLY</span>';
    const uColor = COLOR_MAP[m.u_color] || m.u_color || '#4a5568';
    const aColor = COLOR_MAP[m.a_color] || m.a_color || '#4a5568';
    return `<tr>
      <td><strong>${m.name}</strong></td>
      <td>${freq}</td>
      <td style="color:#a0aec0;font-size:11px;">${m.why}</td>
      <td><span class="model-tag" style="background:#1a2744;color:${uColor};">${m.unaided}</span></td>
      <td><span class="model-tag" style="background:#1a2744;color:${aColor};">${m.aided}</span></td>
      <td>${statusBadge(m.status)}</td>
    </tr>`;
  }).join('');
}

// ── Perplexity simulation table (Overview + Report) ──────────────
function renderPerplexity(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.perplexity_simulation || [];
  el.innerHTML = rows.map(r => `
    <tr>
      <td>${r.cluster}</td>
      <td>${r.cited.join(', ')}</td>
      <td>${r.godaddy
        ? '<span class="tag-green">✅ Present</span>'
        : '<span class="tag-red">❌</span>'}</td>
      <td>${r.action}</td>
    </tr>`).join('');
}

// ── Competitive intel (Overview) ──────────────────────────────────
function renderCompetitiveIntel(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.competitive_intel || [];
  el.innerHTML = rows.map(r => `
    <div class="indicator-row">
      <span class="indicator-label"><strong>${r.competitor}</strong> — ${r.event}</span>
      <span class="indicator-status ${r.changed ? 'yellow' : 'blue'}">${r.changed ? '⚠️ Changed' : '✅ No change'}</span>
    </div>`).join('');
}

// ── Strategy actions (Overview) ───────────────────────────────────
function renderStrategyActions(s) {
  const actionsEl = document.getElementById('strategy-actions');
  if (!actionsEl) return;

  const actions = s.strategy_actions || {};
  const p0 = Array.isArray(actions) ? actions.filter(a => a.priority === 'P0') : (actions.p0 || []);
  const p1 = Array.isArray(actions) ? actions.filter(a => a.priority === 'P1') : (actions.p1 || []);

  const renderActions = (items, tier) => items.map((a, i) => `
    <div class="action-card action-${tier.toLowerCase()}">
      <div class="action-rank">${a.rank || i + 1}</div>
      <div class="action-body">
        <div class="action-title">${a.action}</div>
        <div class="action-meta">Root cause: ${a.root_cause} · Owner: ${a.owner}</div>
        <div class="action-window">⏱ ${a.window}</div>
        ${a.blocked_by && a.blocked_by !== 'None'
          ? `<div class="action-blocked">Blocked by: ${a.blocked_by}</div>` : ''}
      </div>
      <span class="badge-${tier.toLowerCase()}">${tier}</span>
    </div>`).join('');

  actionsEl.innerHTML = `
    <div class="p0-section">
      <h4>🔴 P0 — Citations &amp; Content</h4>
      ${renderActions(p0, 'P0') || '<p>No P0 actions this session.</p>'}
    </div>
    <div class="p1-section">
      <h4>🟡 P1 — Community &amp; Vertical Content</h4>
      ${renderActions(p1, 'P1') || '<p>No P1 actions this session.</p>'}
    </div>`;
}

// ── BUILD pages (BUILD tab) ───────────────────────────────────────
function renderBuildPages(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const pages = s.build_pages || [];
  el.innerHTML = pages.map(p => `
    <div class="build-card">
      <div class="build-header">
        <span class="priority-badge ${p.priority.toLowerCase()}">${p.priority}</span>
        <span class="build-id">${p.brief_id}</span>
        <span class="build-status">${p.crawl_phase2 === 'pending' ? '⏳ Awaiting CRAWL Phase 2' : '✅ ' + p.crawl_phase2}</span>
      </div>
      <h3 class="build-h1">${p.h1}</h3>
      <div class="build-meta">Cluster: ${p.query_cluster.join(', ')} · Competitor: ${p.competitor}</div>
      <div class="build-win-angle">Win angle: ${p.win_angle}</div>

      ${p.claim_flags?.length ? `
        <div class="claim-flags">
          ${p.claim_flags.map(f => `
            <div class="claim-flag">
              ⚠️ <strong>${f.field}:</strong> ${f.note}
            </div>`).join('')}
        </div>` : ''}

      <div class="build-not-best">❌ Not best for: ${p.not_best_for}</div>

      <details class="build-faq">
        <summary>FAQ (${p.faq?.length || 0} questions)</summary>
        ${(p.faq || []).map(q => `
          <div class="faq-item">
            <div class="faq-q">${q.q}</div>
            <div class="faq-a">${q.a}</div>
          </div>`).join('')}
      </details>

      ${p.footnotes?.length ? `
        <div class="build-footnotes">
          ${p.footnotes.map((f,i) => `<div>¹ ${f}</div>`).join('')}
        </div>` : ''}

      <div class="build-meta-tags">
        <div><strong>Meta title:</strong> ${p.meta_title}</div>
        <div><strong>Meta desc:</strong> ${p.meta_description}</div>
        <div><strong>Canonical:</strong> ${p.canonical}</div>
      </div>
    </div>`).join('');
}

// ── AMPLIFY threads (AMPLIFY tab) ─────────────────────────────────
function renderAmplifyThreads(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const threads = s.amplify_threads || [];
  el.innerHTML = threads.map(t => `
    <div class="amplify-card">
      <div class="amplify-header">
        <span class="priority-badge p${t.priority_score >= 8 ? '0' : t.priority_score >= 5 ? '1' : '2'}">${t.priority_score}/10</span>
        <span class="amplify-platform">${t.platform} · ${t.community}</span>
        <span class="amplify-date">${t.date}</span>
        <span class="amplify-status">${t.approved ? '✅ Approved' : '⏳ Awaiting review'}</span>
      </div>
      <div class="amplify-thread">"${t.thread}"</div>
      <div class="amplify-clusters">Cluster: ${t.cluster.join(', ')}</div>

      ${t.claim_flags?.length ? `
        <div class="claim-flags">
          ${t.claim_flags.map(f => `
            <div class="claim-flag">⚠️ <strong>${f.field}:</strong> ${f.note}</div>`
          ).join('')}
        </div>` : ''}

      <details class="amplify-draft">
        <summary>View draft response</summary>
        <pre class="draft-text">${t.draft}</pre>
        <div class="disclosure-box">📢 ${t.disclosure}</div>
      </details>

    </div>`).join('');
}

// ── AMPLIFY outcomes (AMPLIFY tab) ────────────────────────────────
function renderAmplifyOutcomes(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const outcomes = s.amplify_outcomes || [];
  if (!outcomes.length) {
    el.innerHTML = '<tr><td colspan="6">No replies posted yet.</td></tr>';
    return;
  }
  el.innerHTML = outcomes.map(o => `
    <tr>
      <td>${o.date}</td><td>${o.thread}</td><td>${o.platform}</td>
      <td><a href="${o.url}" target="_blank">View</a></td>
      <td>${o.outcome}</td><td>${o.notes}</td>
    </tr>`).join('');
}

// ── CITE pipeline (CITE tab) ──────────────────────────────────────
function renderCitePipeline(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.cite_pipeline || [];
  el.innerHTML = rows.map(r => `
    <tr class="cite-row cite-${r.status}">
      <td><strong>${r.publisher}</strong><br><small>${r.section}</small></td>
      <td>${statusIcon(r.status)} ${r.status}</td>
      <td>${r.priority}</td>
      <td>${r.best_for_label}</td>
      <td>${r.blocked_by || 'None'}</td>
      <td>${r.est_sov_impact}</td>
      <td>${r.last_contact || '—'}</td>
      <td>${r.response || '—'}</td>
    </tr>`).join('');
}

// ── REPORT sections ───────────────────────────────────────────────
function renderReport(s) {
  const r = s.report_summary || {};

  // Binding constraint banner
  set('report-constraint', r.binding_constraint || '—');

  // Top wins
  const winsEl = document.getElementById('report-wins');
  if (winsEl) winsEl.innerHTML = (r.top_wins || []).map(w => `
    <div class="win-card">
      <span class="tag-green">✅</span>
      <div><strong>${w.win}</strong><br><small>Agent: ${w.agent} · ${w.impact}</small></div>
    </div>`).join('');

  // Top gaps
  const gapsEl = document.getElementById('report-gaps');
  if (gapsEl) gapsEl.innerHTML = (r.top_gaps || []).map(g => `
    <div class="gap-card">
      <span class="priority-badge ${g.priority.toLowerCase()}">${g.priority}</span>
      <div><strong>${g.gap}</strong><br>
        <small>Root cause: ${g.root_cause} · Action: ${g.action} · Window: ${g.window}</small>
      </div>
    </div>`).join('');

  // Leading indicators
  const liEl = document.getElementById('report-leading-indicators');
  if (liEl) liEl.innerHTML = (r.leading_indicators || []).map(i => `
    <tr>
      <td>${i.indicator}</td>
      <td style="color:${i.status==='green'?'#68d391':i.status==='red'?'#fc8181':'#f6e05e'}">${i.value}</td>
      <td>${trafficLight(i.status)}</td>
    </tr>`).join('');

  // Leadership decisions
  const ldEl = document.getElementById('report-leadership-decisions');
  if (ldEl) ldEl.innerHTML = (r.leadership_decisions || []).map(d => `
    <tr>
      <td>${d.decision}</td>
      <td>${d.owner}</td>
      <td>${d.deadline}</td>
      <td>${d.consequence}</td>
    </tr>`).join('');

  // Next month priority
  const nmEl = document.getElementById('report-next-priority');
  if (nmEl) nmEl.innerHTML = (r.next_month_priority || []).map(n => `
    <tr>
      <td><span class="priority-badge ${n.priority.toLowerCase()}">${n.priority}</span></td>
      <td>${n.action}</td>
      <td>${n.agent}</td>
      <td>${n.sov_impact}</td>
      <td>${n.window}</td>
    </tr>`).join('');

  // Data confidence
  set('report-confidence', r.data_confidence || '—');
  set('report-methodology', r.methodology_note || '—');
}

// ── Trends Chart ─────────────────────────────────────────────────
// 6-month rolling window: 26 week slots, months on x-axis, WK ticks between
function renderTrendsChart(trends) {
  const canvas = document.getElementById('trendsChart');
  const note = document.getElementById('trends-note');
  if (!canvas) return;

  // Normalise input — handle {monthly:[...], weekly:[...]} or flat array
  let dataPoints = [];
  if (trends && typeof trends === 'object' && !Array.isArray(trends)) {
    dataPoints = trends.monthly || trends.weekly || [];
  } else if (Array.isArray(trends)) {
    dataPoints = trends;
  }

  // Build 26-slot skeleton (6 months back to today)
  function getISOWeek(d) {
    const jan4 = new Date(d.getFullYear(), 0, 4);
    const w1 = new Date(jan4);
    w1.setDate(jan4.getDate() - jan4.getDay() + 1);
    return Math.floor((d - w1) / (7 * 86400000)) + 1;
  }
  function getWeekStart(year, week) {
    const jan4 = new Date(year, 0, 4);
    const w1 = new Date(jan4);
    w1.setDate(jan4.getDate() - jan4.getDay() + 1);
    const d = new Date(w1);
    d.setDate(d.getDate() + (week - 1) * 7);
    return d;
  }

  const today = new Date();
  const currentWeek = getISOWeek(today);
  const currentYear = today.getFullYear();
  const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const NUM_SLOTS = 26;

  // slot 0 = 25 weeks ago, slot 25 = current week
  const slots = [];
  for (let i = 0; i < NUM_SLOTS; i++) {
    let wn = currentWeek - (NUM_SLOTS - 1) + i;
    let yr = currentYear;
    if (wn <= 0) { wn += 52; yr -= 1; }
    const ws = getWeekStart(yr, wn);
    slots.push({
      weekNum: wn, year: yr,
      label: 'WK' + wn,
      month: MONTH_NAMES[ws.getMonth()],
      isMonthStart: ws.getDate() <= 7,
      unaided: null, aided: null, rateSaver: null, hasData: false
    });
  }

  // Map actual data into slots by extracting week number from run_id
  // Handles formats: "2026-06-W26", "2026-07-W27", "W26", etc.
  dataPoints.forEach(function(p) {
    var rid = p.run_id || '';
    var wMatch = rid.match(/W([0-9]+)$/);
    if (!wMatch) return;
    var wn = parseInt(wMatch[1]);
    var slot = null;
    for (var si = 0; si < slots.length; si++) {
      if (slots[si].weekNum === wn) { slot = slots[si]; break; }
    }
    if (!slot) return;
    slot.unaided   = parseFloat(p.unaided_sov)    || 0;
    slot.aided     = parseFloat(p.aided_sov)      || 0;
    slot.rateSaver = parseFloat(p.rate_saver_sov) || 0;
    slot.hasData = true;
  });

  var dataCount = slots.filter(function(s) { return s.hasData; }).length;

  // Canvas setup
  canvas.width  = canvas.offsetWidth || 900;
  canvas.height = 210;
  canvas.style.display = 'block';
  var ctx = canvas.getContext('2d');
  var W = canvas.width, H = canvas.height;
  var padL = 52, padR = 24, padT = 28, padB = 56;
  var chartW = W - padL - padR;
  var chartH = H - padT - padB;

  ctx.fillStyle = '#161b28';
  ctx.fillRect(0, 0, W, H);

  // Y-axis grid lines + labels
  var yPcts = [100, 75, 50, 25, 0];
  yPcts.forEach(function(pct) {
    var y = padT + chartH - (pct / 100) * chartH;
    ctx.strokeStyle = '#2d3748'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillStyle = '#718096'; ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(pct + '%', padL - 6, y + 4);
  });

  // Slot X positions
  function slotX(i) { return padL + (chartW / (NUM_SLOTS - 1)) * i; }

  // Week tick marks (every slot, tiny gray)
  slots.forEach(function(s, i) {
    ctx.strokeStyle = '#2d3748'; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(slotX(i), H - padB + 2);
    ctx.lineTo(slotX(i), H - padB + 5);
    ctx.stroke();
  });

  // WK labels every 2 slots (small gray) — skip month-start slots
  slots.forEach(function(s, i) {
    if (s.isMonthStart) return;
    if (i % 2 !== 0) return;
    ctx.fillStyle = '#4a5568'; ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(s.label, slotX(i), H - padB + 16);
  });

  // Month labels (blue bold) + dashed vertical guide at month boundaries
  slots.forEach(function(s, i) {
    if (!s.isMonthStart) return;
    var x = slotX(i);
    // Dashed vertical guide
    ctx.strokeStyle = '#2d4a8a'; ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, H - padB + 2); ctx.stroke();
    ctx.setLineDash([]);
    // Tick
    ctx.beginPath(); ctx.moveTo(x, H - padB + 2); ctx.lineTo(x, H - padB + 8); ctx.stroke();
    // Month name
    ctx.fillStyle = '#90cdf4'; ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(s.month, x, H - padB + 30);
  });

  // Draw lines + dots for the 3 metrics
  var METRICS = [
    { key: 'unaided',   color: '#dc2626' },
    { key: 'aided',     color: '#fbbf24' },
    { key: 'rateSaver', color: '#90cdf4' }
  ];

  METRICS.forEach(function(metric) {
    // Line through data-bearing slots only
    ctx.strokeStyle = metric.color; ctx.lineWidth = 2; ctx.setLineDash([]);
    var started = false;
    ctx.beginPath();
    slots.forEach(function(s, i) {
      if (!s.hasData) return;
      var x = slotX(i);
      var y = padT + chartH - (s[metric.key] / 100) * chartH;
      if (!started) { ctx.moveTo(x, y); started = true; }
      else { ctx.lineTo(x, y); }
    });
    if (started) ctx.stroke();

    // Dots with dark ring on data slots
    slots.forEach(function(s, i) {
      if (!s.hasData) return;
      var x = slotX(i);
      var y = padT + chartH - (s[metric.key] / 100) * chartH;
      ctx.fillStyle = metric.color;
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#161b28'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.stroke();
    });
  });

  // Footer note
  if (note) {
    var first = null, last = null;
    slots.forEach(function(s) { if (s.hasData) { if (!first) first = s; last = s; } });
    note.textContent = dataCount === 0
      ? 'No data yet — run a benchmark to populate the chart'
      : dataCount + ' week' + (dataCount !== 1 ? 's' : '') + ' of data'
        + (first && last ? ' · ' + first.label + ' → ' + last.label : '');
  }
}

// ── Helpers ───────────────────────────────────────────────────────
function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function statusBadge(s) {
  const map = { success:'✅ Normal', partial:'⚠️ Partial', error:'❌ Error' };
  return map[s] || s;
}
function statusIcon(s) {
  const map = { absent:'❌', present:'✅', review:'⚠️', defend:'🛡️' };
  return map[s] || '—';
}
function trafficLight(s) {
  return s==='green' ? '🟢' : s==='red' ? '🔴' : '🟡';
}

// ── Init on page load ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadSession().then(session => {
    if (session) {
      renderHeader(session);
      if (document.getElementById('trendsChart')) {
        renderTrendsChart(session.trends || []);
      }
      if (typeof renderPage === 'function') {
        renderPage(session);
      }
    }
  });
});
