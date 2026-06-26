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
      el.innerHTML = `&nbsp;·&nbsp; Last full benchmark: <strong>${m.last_full_benchmark}</strong>`;
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
function renderModelTables(s) {
  const primary = s.model_sov?.primary || [];
  const pulse   = s.model_sov?.pulse   || [];

  const primaryEl = document.getElementById('primary-model-rows');
  if (primaryEl) primaryEl.innerHTML = primary.map(m => `
    <tr>
      <td>${m.name}</td>
      <td>${m.why}</td>
      <td class="${m.u_color || 'red'}">${m.unaided}</td>
      <td class="${m.a_color}">${m.aided}</td>
      <td>${statusBadge(m.status)}</td>
    </tr>`).join('');

  const pulseEl = document.getElementById('pulse-model-rows');
  if (pulseEl) pulseEl.innerHTML = pulse.map(m => `
    <tr>
      <td>${m.name}</td>
      <td>${m.why}</td>
      <td class="${m.u_color || 'red'}">${m.unaided}</td>
      <td class="${m.a_color}">${m.aided}</td>
      <td>${m.trigger || '—'}</td>
    </tr>`).join('');
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
      <h4>🔥 P0 — Citations &amp; Content</h4>
      ${renderActions(p0, 'P0') || '<p>No P0 actions this session.</p>'}
    </div>
    <div class="p1-section">
      <h4>🔶 P1 — Community &amp; Vertical Content</h4>
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

// ── Trends Chart ──────────────────────────────────────────────────────
function renderTrendsChart(trends) {
  const canvas = document.getElementById('trendsChart');
  const note = document.getElementById('trends-note');

  if (!canvas) return;

  if (!trends || trends.length === 0) {
    if (note) note.textContent = 'No historical data yet. Trends will appear after multiple weekly runs.';
    return;
  }

  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  // Chart dimensions
  const padding = { top: 20, right: 40, bottom: 30, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Find max value for Y-axis (at least 10 for visibility)
  const maxSov = Math.max(10,
    ...trends.map(t => Math.max(t.unaided_sov || 0, t.aided_sov || 0, t.rate_saver_sov || 0))
  );

  // Draw grid lines
  ctx.strokeStyle = '#2d3748';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(padding.left + chartWidth, y);
    ctx.stroke();

    // Y-axis labels
    const value = Math.round(maxSov * (1 - i / 4));
    ctx.fillStyle = '#718096';
    ctx.font = '10px -apple-system, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(value + '%', padding.left - 10, y + 4);
  }

  // Draw lines
  const drawLine = (data, color) => {
    if (data.length === 0) return;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((point, i) => {
      const x = padding.left + (chartWidth / (trends.length - 1)) * i;
      const y = padding.top + chartHeight - (point.value / maxSov * chartHeight);

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw points
    ctx.fillStyle = color;
    data.forEach((point, i) => {
      const x = padding.left + (chartWidth / (trends.length - 1)) * i;
      const y = padding.top + chartHeight - (point.value / maxSov * chartHeight);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });
  };

  // Prepare data series
  const unaidedData = trends.map(t => ({ value: t.unaided_sov || 0 }));
  const aidedData = trends.map(t => ({ value: t.aided_sov || 0 }));
  const rateSaverData = trends.map(t => ({ value: t.rate_saver_sov || 0 }));

  // Draw lines (order matters for layering)
  drawLine(aidedData, '#68d391');      // Green - Aided
  drawLine(rateSaverData, '#90cdf4'); // Blue - Rate Saver
  drawLine(unaidedData, '#fc8181');   // Red - Unaided (on top)

  // X-axis labels
  ctx.fillStyle = '#718096';
  ctx.font = '10px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  trends.forEach((t, i) => {
    const x = padding.left + (chartWidth / (trends.length - 1)) * i;
    const label = t.run_id.replace('2026-06-', 'W');
    ctx.fillText(label, x, height - 10);
  });

  // Update note
  if (note) {
    note.textContent = `Tracking ${trends.length} week${trends.length > 1 ? 's' : ''} of data`;
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
      // Render trends chart if on index page
      if (document.getElementById('trendsChart')) {
        renderTrendsChart(session.trends || []);
      }
      // Each page calls its own render functions after this
      if (typeof renderPage === 'function') {
        renderPage(session);
      }
    }
  });
});
