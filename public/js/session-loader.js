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
      el.innerHTML = ` ·   Last full benchmark: ${m.last_full_benchmark}`;
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
    <a href="prompts.html#${c.name}" class="cat-cell cat-cell-${c.cell}">
      <div class="cat-name">${c.name.replace(/_/g,' ')}</div>
      <div class="cat-sov ${c.cell}">${c.sov}</div>
      <div class="cat-target">→ ${c.target}</div>
    </a>`).join('');
}

// ── Competitor bars (Overview) ────────────────────────────────────
function renderCompetitors(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const comps = s.competitors || [];
  el.innerHTML = comps.map(c => `
    <div class="comp-row">
      <div class="comp-name" style="color:${c.godaddy?'#fc8181':'#e2e8f0'}">${c.name}</div>
      <div class="comp-bar-wrap">
        <div class="comp-bar-fill" style="width:${c.sov}%;background:${c.bar};min-width:${c.sov>0?'2px':'0'}"></div>
      </div>
      <div class="comp-pct">${c.display}</div>
      <div class="comp-label">${c.label}</div>
    </div>`).join('');
}

// ── Model tables (Overview + Report) ─────────────────────────────
function renderModelTables(s) {
  const primary = s.model_sov?.primary || [];
  const pulse   = s.model_sov?.pulse   || [];

  const DEFAULT_PRIMARY = [
    {name:'Claude Haiku 4.5',  why:'Weekly pulse check',                     unaided:'—', aided:'—', status:'pending', u_color:'red', a_color:'green'},
    {name:'Claude Sonnet 4.6', why:'Full benchmark primary',                  unaided:'—', aided:'—', status:'pending', u_color:'red', a_color:'green'},
    {name:'GPT-4o',            why:'Largest consumer install base',           unaided:'—', aided:'—', status:'pending', u_color:'red', a_color:'green'},
    {name:'o3',                why:'OpenAI reasoning — growing merchant use', unaided:'—', aided:'—', status:'pending', u_color:'red', a_color:'green'},
    {name:'Gemini 2.5 Pro',    why:'Google search integration — high reach',  unaided:'—', aided:'—', status:'pending', u_color:'red', a_color:'green'},
  ];
  const DEFAULT_PULSE = [
    {name:'Gemini 2.5 Flash',       why:'Promoted to stable — behaviour consolidating', unaided:'—', aided:'—', status:'tracking', u_color:'red', a_color:'green'},
    {name:'o3-mini',                why:'OpenAI reasoning — usage pattern emerging',    unaided:'—', aided:'—', status:'tracking', u_color:'red', a_color:'green'},
    {name:'Gemini 3.1 Pro Preview', why:'Next-gen Gemini — monitor for anomalies',     unaided:'—', aided:'—', status:'tracking', u_color:'red', a_color:'yellow'},
  ];
  var LSKEY = 'geo-model-cache-v1';
  try {
    var cached = JSON.parse(localStorage.getItem(LSKEY) || '{}');
    primary.concat(pulse).forEach(function(m) {
      if (m.unaided !== '—' && m.unaided !== undefined) cached[m.name] = {unaided:m.unaided, aided:m.aided, u_color:m.u_color, a_color:m.a_color};
    });
    localStorage.setItem(LSKEY, JSON.stringify(cached));
  } catch(e) { var cached = {}; }
  function padModels(live, defaults) {
    var names = live.map(function(m){return m.name;});
    var out = live.slice();
    defaults.forEach(function(d){
      if (names.indexOf(d.name) === -1) {
        var merged = Object.assign({}, d);
        if (cached[d.name]) { merged.unaided=cached[d.name].unaided; merged.aided=cached[d.name].aided; merged.u_color=cached[d.name].u_color||d.u_color; merged.a_color=cached[d.name].a_color||d.a_color; merged.status='cached'; merged.notes='Last benchmark data'; }
        out.push(merged);
      }
    });
    return out;
  }
  var primaryAll = padModels(primary, DEFAULT_PRIMARY);
  var pulseAll   = padModels(pulse,   DEFAULT_PULSE);
  const COLOR_MAP = {'red':'#fc8181','yellow':'#f6e05e','green':'#68d391','blue':'#90cdf4'};

  function primaryRow(m) {
    const isHaiku = (m.name || '').toLowerCase().includes('haiku');
    const freq = isHaiku
      ? '<span class="tag-green" style="font-size:9px;">WEEKLY</span><span class="tag-blue" style="font-size:9px;margin-left:2px;">MONTHLY</span>'
      : '<span class="tag-blue" style="font-size:9px;">MONTHLY</span>';
    const uColor = COLOR_MAP[m.u_color] || m.u_color || '#fc8181';
    const aColor = COLOR_MAP[m.a_color] || m.a_color || '#68d391';
    var note = m.notes || m.why || '';
    if (m.status === 'partial') { note = '⚠️ ' + note; }
    else if (m.status === 'error') { note = '❌ ' + note; }
    return '<tr>'
      + '<td style="font-weight:600;">' + m.name + '</td>'
      + '<td>' + freq + '</td>'
      + '<td style="text-align:right;color:' + uColor + ';font-weight:700;">' + m.unaided + '</td>'
      + '<td style="text-align:right;color:' + aColor + ';font-weight:700;">' + m.aided + '</td>'
      + '<td>' + statusBadge(m.status) + '</td>'
      + '<td style="color:#718096;font-size:11px;">' + note + '</td>'
      + '</tr>';
  }
  function pulseRow(m) {
    const freq = '<span class="tag-blue" style="font-size:9px;">WEEKLY</span>';
    const uColor = COLOR_MAP[m.u_color] || m.u_color || '#4a5568';
    const aColor = COLOR_MAP[m.a_color] || m.a_color || '#4a5568';
    var note = m.notes || m.why || '';
    if (m.trigger) note = (note ? note + ' — ' : '') + m.trigger;
    if (m.status === 'partial') note = '⚠️ ' + note;
    return '<tr>'
      + '<td style="font-weight:600;">' + m.name + '</td>'
      + '<td>' + freq + '</td>'
      + '<td style="text-align:right;color:' + uColor + ';font-weight:700;">' + m.unaided + '</td>'
      + '<td style="text-align:right;color:' + aColor + ';font-weight:700;">' + m.aided + '</td>'
      + '<td>' + statusBadge(m.status) + '</td>'
      + '<td style="color:#718096;font-size:11px;">' + note + '</td>'
      + '</tr>';
  }

  const primaryEl = document.getElementById('primary-model-rows');
  if (primaryEl) primaryEl.innerHTML = primaryAll.map(primaryRow).join('');

  const pulseEl = document.getElementById('pulse-model-rows');
  if (pulseEl) pulseEl.innerHTML = pulseAll.map(pulseRow).join('');

  const reportEl = document.getElementById('report-ai-platform-rows');
  if (reportEl) {
    var rows = '';
    primaryAll.forEach(function(m) {
      const uColor = COLOR_MAP[m.u_color] || m.u_color || '#fc8181';
      const aColor = COLOR_MAP[m.a_color] || m.a_color || '#68d391';
      const noteText = m.status === 'partial'
        ? 'Partial run — ' + m.aided + ' aided SOV (' + (m.aided_failures_count || '?') + '/' + (m.aided_total || 7) + ' prompts completed)'
        : (m.aided === '100%' ? 'All aided prompts successful' : (m.notes || 'Baseline established'));
      rows += '<tr>'
        + '<td>' + m.name + '</td>'
        + '<td>Primary</td>'
        + '<td style="color:' + uColor + ';font-weight:700;">' + m.unaided + '</td>'
        + '<td style="color:' + aColor + ';font-weight:700;">' + m.aided + '</td>'
        + '<td>' + statusBadge(m.status) + '</td>'
        + '<td style="color:#718096;font-size:11px;">' + noteText + '</td>'
        + '</tr>';
    });
    pulseAll.forEach(function(m) {
      const uColor = COLOR_MAP[m.u_color] || m.u_color || '#4a5568';
      const aColor = COLOR_MAP[m.a_color] || m.a_color || '#4a5568';
      var noteText = m.status === 'partial'
        ? 'Partial run — ' + m.aided + ' aided SOV. Not a GoDaddy recognition issue.'
        : (m.notes || m.why || 'Directional signal only');
      rows += '<tr>'
        + '<td>' + m.name + '</td>'
        + '<td>Pulse</td>'
        + '<td style="color:' + uColor + ';font-weight:700;">' + m.unaided + '</td>'
        + '<td style="color:' + aColor + ';font-weight:700;">' + m.aided + '</td>'
        + '<td>' + statusBadge(m.status) + '</td>'
        + '<td style="color:#718096;font-size:11px;">' + noteText + '</td>'
        + '</tr>';
    });
    reportEl.innerHTML = rows;
  }
}

// ── Perplexity simulation table ───────────────────────────────────
function renderPerplexity(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.perplexity_simulation || [];
  el.innerHTML = rows.map(r => `
    <tr>
      <td>${r.cluster}</td>
      <td>${r.cited.join(', ')}</td>
      <td>${r.godaddy ? '✅ Present' : '❌'}</td>
      <td style="font-size:11px;color:#a0aec0;">${r.action}</td>
    </tr>`).join('');
}

// ── Competitive intel ─────────────────────────────────────────────
var CI_FALLBACK = {
  'Square': {ip:'2.6% + $0.15', ol:'2.9% + $0.30', src:'Square.com Jul 2026'},
  'Stripe': {ip:'2.7% + $0.05', ol:'2.9% + $0.30', src:'Stripe.com Jul 2026'},
  'Clover': {ip:'2.3–2.6% + $0.10', ol:'3.5% + $0.10', src:'Merchant Maverick Jul 2026'},
  'Helcim': {ip:'~1.93% + $0.08', ol:'~2.43% + $0.25', src:'Helcim.com Jul 2026'},
};
function renderCompetitiveIntel(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.competitive_intel || [];
  if (!rows.length) { el.innerHTML = 'No competitive intel this session.'; return; }
  el.innerHTML = rows.map(function(r) {
    var fb = CI_FALLBACK[r.competitor] || {};
    var ip = r.in_person_rate || fb.ip || '—';
    var ol = r.online_rate    || fb.ol || '—';
    var src = r.source        || fb.src || '';
    var chg = r.changed ? '⚠️ Changed' : '✅ No change';
    return '<div style="margin-bottom:10px;padding:8px 0;border-bottom:1px solid #1e2436;">'
      + '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
      + '<span style="font-weight:600;">' + r.competitor + '</span><span style="font-size:11px;">' + chg + '</span>'
      + '</div>'
      + '<div style="font-size:11px;color:#a0aec0;">'
      + '<span style="color:#718096;">In-Person</span> ' + ip + ' &nbsp;·&nbsp; '
      + '<span style="color:#718096;">Online</span> ' + ol
      + '</div>'
      + '<div style="font-size:10px;color:#4a5568;margin-top:2px;">Source: ' + src + '</div>'
      + '</div>';
  }).join('');
}

// ── Strategy actions ──────────────────────────────────────────────
function renderStrategyActions(s) {
  const actionsEl = document.getElementById('strategy-actions');
  if (!actionsEl) return;
  const actions = s.strategy_actions || {};
  const p0 = Array.isArray(actions) ? actions.filter(a => a.priority === 'P0') : (actions.p0 || []);
  const p1 = Array.isArray(actions) ? actions.filter(a => a.priority === 'P1') : (actions.p1 || []);
  const renderActions = (items, tier) => items.map((a, i) => `
    <tr>
      <td class="col-pri"><span class="priority-badge ${tier.toLowerCase()}">${tier}</span><div style="font-size:10px;color:#718096;margin-top:4px;">#${a.rank || i+1}</div></td>
      <td class="col-action"><div style="font-weight:600;color:#e2e8f0;margin-bottom:3px;">${a.action}</div>
        <div style="font-size:10px;color:#718096;">Root cause: ${a.root_cause} · Owner: ${a.owner}</div>
        <div style="font-size:10px;color:#4a5568;">⏱ ${a.window}</div>
        ${a.blocked_by && a.blocked_by !== 'None' ? `<div style="font-size:10px;color:#f6ad55;">Blocked by: ${a.blocked_by}</div>` : ''}
      </td>
      <td><span class="priority-badge ${tier.toLowerCase()}">${tier}</span></td>
    </tr>`).join('');
  actionsEl.innerHTML = `
    <div class="action-section">
      <div class="action-section-title p0-title">🔴 P0 — Citations &amp; Content</div>
      <table class="action-tbl"><thead><tr><th class="col-pri">Priority</th><th class="col-action">Action</th><th>Tier</th></tr></thead>
      <tbody>${renderActions(p0, 'P0') || '<tr><td colspan="3" style="color:#4a5568;">No P0 actions this session.</td></tr>'}</tbody></table>
    </div>
    <div class="action-section">
      <div class="action-section-title p1-title">🟡 P1 — Community &amp; Vertical Content</div>
      <table class="action-tbl"><thead><tr><th class="col-pri">Priority</th><th class="col-action">Action</th><th>Tier</th></tr></thead>
      <tbody>${renderActions(p1, 'P1') || '<tr><td colspan="3" style="color:#4a5568;">No P1 actions this session.</td></tr>'}</tbody></table>
    </div>`;
}

// ── BUILD pages ───────────────────────────────────────────────────
function renderBuildPages(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const pages = s.build_pages || [];
  el.innerHTML = pages.map(p => `
    <div class="card" style="margin-bottom:16px;">
      <div style="display:flex;gap:8px;margin-bottom:10px;align-items:center;">
        <span class="priority-badge ${p.priority.toLowerCase()}">${p.priority}</span>
        <span style="font-size:11px;color:#718096;">${p.brief_id}</span>
        <span style="font-size:11px;color:${p.crawl_phase2==='pending'?'#f6ad55':'#68d391'};">${p.crawl_phase2 === 'pending' ? '⏳ Awaiting CRAWL Phase 2' : '✅ ' + p.crawl_phase2}</span>
      </div>
      <div style="font-size:14px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">${p.h1}</div>
      <div style="font-size:11px;color:#718096;margin-bottom:6px;">Cluster: ${p.query_cluster.join(', ')} · Competitor: ${p.competitor}</div>
      <div style="font-size:11px;color:#a0aec0;margin-bottom:8px;">Win angle: ${p.win_angle}</div>
      ${p.claim_flags?.length ? `<div style="background:#2d1f00;border-left:3px solid #ed8936;padding:8px 12px;margin-bottom:8px;font-size:11px;">${p.claim_flags.map(f => `<div>⚠️ ${f.field}: ${f.note}</div>`).join('')}</div>` : ''}
      <div style="font-size:11px;color:#fc8181;margin-bottom:8px;">❌ Not best for: ${p.not_best_for}</div>
      <details><summary>FAQ (${p.faq?.length || 0} questions)</summary>
        ${(p.faq || []).map(q => `<div style="margin:8px 0;"><div style="font-weight:600;font-size:12px;">${q.q}</div><div style="font-size:11px;color:#a0aec0;margin-top:2px;">${q.a}</div></div>`).join('')}
      </details>
      ${p.footnotes?.length ? `<div style="margin-top:8px;font-size:10px;color:#4a5568;">${p.footnotes.map((f,i) => `<div>¹ ${f}</div>`).join('')}</div>` : ''}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid #2d3748;font-size:10px;color:#4a5568;">
        Meta title: ${p.meta_title}<br>Meta desc: ${p.meta_description}<br>Canonical: ${p.canonical}
      </div>
    </div>`).join('');
}

// ── AMPLIFY threads ───────────────────────────────────────────────
function renderAmplifyThreads(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const threads = s.amplify_threads || [];
  el.innerHTML = threads.map(t => `
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex;gap:8px;margin-bottom:8px;align-items:center;flex-wrap:wrap;">
        <span class="tag-blue">${t.priority_score}/10</span>
        <span style="font-size:11px;color:#a0aec0;">${t.platform} · ${t.community}</span>
        <span style="font-size:11px;color:#718096;">${t.date}</span>
        <span class="tag-${t.approved?'green':'yellow'}">${t.approved ? '✅ Approved' : '⏳ Awaiting review'}</span>
      </div>
      <div style="font-weight:600;margin-bottom:4px;">"${t.thread}"</div>
      <div style="font-size:11px;color:#718096;margin-bottom:8px;">Cluster: ${t.cluster.join(', ')}</div>
      ${t.claim_flags?.length ? `<div style="background:#2d1f00;border-left:3px solid #ed8936;padding:6px 10px;margin-bottom:8px;font-size:11px;">${t.claim_flags.map(f => `<div>⚠️ ${f.claim}: ${f.claim_status}</div>`).join('')}</div>` : ''}
      <details><summary>View draft response</summary>
        <div style="margin-top:8px;font-size:12px;line-height:1.5;color:#cbd5e0;">${t.draft}</div>
        <div style="margin-top:6px;font-size:11px;color:#718096;">📢 ${t.disclosure}</div>
      </details>
    </div>`).join('');
}

// ── AMPLIFY outcomes ──────────────────────────────────────────────
function renderAmplifyOutcomes(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const outcomes = s.amplify_outcomes || [];
  if (!outcomes.length) { el.innerHTML = '<div style="color:#4a5568;font-size:12px;">No replies posted yet.</div>'; return; }
  el.innerHTML = outcomes.map(o => `
    <tr><td>${o.date}</td><td>${o.thread}</td><td>${o.platform}</td>
    <td><a href="${o.url||'#'}" class="ext-link">View</a></td>
    <td>${o.outcome}</td><td style="color:#718096;font-size:11px;">${o.notes||''}</td></tr>`).join('');
}

// ── CITE pipeline ─────────────────────────────────────────────────
function renderCitePipeline(s, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const rows = s.cite_pipeline || [];
  el.innerHTML = rows.map(r => `
    <tr>
      <td>${r.publisher}</td><td style="color:#718096;font-size:11px;">${r.section}</td>
      <td>${statusIcon(r.status)} ${r.status}</td>
      <td><span class="priority-badge ${(r.priority||'').toLowerCase()}">${r.priority}</span></td>
      <td style="font-size:11px;">${r.best_for_label}</td>
      <td style="font-size:11px;color:${r.blocked_by&&r.blocked_by!=='None'?'#f6ad55':'#4a5568'};">${r.blocked_by || 'None'}</td>
      <td style="font-size:11px;color:#68d391;">${r.est_sov_impact}</td>
      <td style="font-size:11px;color:#718096;">${r.last_contact || '—'}</td>
      <td style="font-size:11px;color:#a0aec0;">${r.response || '—'}</td>
    </tr>`).join('');
}

// ── REPORT sections ───────────────────────────────────────────────
function renderReport(s) {
  const r = s.report_summary || {};
  set('report-constraint', r.binding_constraint || '—');
  const winsEl = document.getElementById('report-wins');
  if (winsEl) winsEl.innerHTML = (r.top_wins || []).map(w => `
    <div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #1e2436;">
      <div style="color:#68d391;font-size:18px;flex-shrink:0;">✅</div>
      <div><div style="font-weight:600;margin-bottom:3px;">${w.win}</div>
      <div style="font-size:11px;color:#718096;">Agent: ${w.agent} · ${w.impact}</div></div>
    </div>`).join('');
  const gapsEl = document.getElementById('report-gaps');
  if (gapsEl) gapsEl.innerHTML = (r.top_gaps || []).map(g => `
    <div style="padding:10px 0;border-bottom:1px solid #1e2436;">
      <div style="display:flex;gap:8px;margin-bottom:4px;"><span class="priority-badge ${(g.priority||'').toLowerCase()}">${g.priority}</span><span style="font-weight:600;">${g.gap}</span></div>
      <div style="font-size:11px;color:#718096;">Root cause: ${g.root_cause} · Action: ${g.action} · Window: ${g.window}</div>
    </div>`).join('');
  const liEl = document.getElementById('report-leading-indicators');
  if (liEl) liEl.innerHTML = (r.leading_indicators || []).map(i => `
    <div class="indicator-row">
      <span class="indicator-label">${i.indicator}</span>
      <span style="font-size:12px;color:#a0aec0;flex:1;text-align:right;margin-right:12px;">${i.value}</span>
      <span>${trafficLight(i.status)}</span>
    </div>`).join('');
  const ldEl = document.getElementById('report-leadership-decisions');
  if (ldEl) ldEl.innerHTML = (r.leadership_decisions || []).map(d => `
    <div style="padding:10px 0;border-bottom:1px solid #1e2436;">
      <div style="font-weight:600;margin-bottom:4px;">${d.decision}</div>
      <div style="font-size:11px;color:#718096;">Owner: ${d.owner} · Deadline: ${d.deadline}</div>
      <div style="font-size:11px;color:#fc8181;margin-top:3px;">${d.consequence}</div>
    </div>`).join('');
  const nmEl = document.getElementById('report-next-priority');
  if (nmEl) nmEl.innerHTML = (r.next_month_priority || []).map(n => `
    <tr><td><span class="priority-badge p0">#${n.priority}</span></td>
    <td style="font-weight:600;">${n.action}</td>
    <td style="font-size:11px;color:#718096;">${n.agent}</td>
    <td style="font-size:11px;color:#68d391;">${n.sov_impact}</td>
    <td style="font-size:11px;color:#4a5568;">${n.window}</td></tr>`).join('');
  set('report-confidence', r.data_confidence || '—');
  set('report-methodology', r.methodology_note || '—');
}

// ── Trends Chart ──────────────────────────────────────────────────
// FIX: Use trends.weekly first (contains all runs including weekly-only W31),
//      fall back to trends.monthly only if weekly is absent.
function renderTrendsChart(trends) {
  const canvas = document.getElementById('trendsChart');
  const note = document.getElementById('trends-note');
  if (!canvas) return;

  // ── FIX 1: Prefer weekly over monthly so W31 shows up ────────────
  var dataPoints = [];
  if (trends && typeof trends === 'object' && !Array.isArray(trends)) {
    dataPoints = trends.weekly || trends.monthly || [];
  } else if (Array.isArray(trends)) {
    dataPoints = trends;
  }

  var MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
                     'Jul','Aug','Sep','Oct','Nov','Dec'];

  var today = new Date();
  var currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);

  var sixMoBackMonth = today.getMonth() - 5;
  var sixMoBackYear  = today.getFullYear();
  if (sixMoBackMonth < 0) { sixMoBackMonth += 12; sixMoBackYear -= 1; }
  var sixMonthsAgo = new Date(sixMoBackYear, sixMoBackMonth, 1);

  var dataMonths = [];
  dataPoints.forEach(function(p) {
    var rid = p.run_id || '';
    var parts = rid.split('-');
    if (parts.length >= 2) {
      var yr = parseInt(parts[0]);
      var mo = parseInt(parts[1]) - 1;
      if (!isNaN(yr) && !isNaN(mo)) {
        var dm = new Date(yr, mo, 1);
        if (dm >= sixMonthsAgo) dataMonths.push(dm);
      }
    }
  });

  var windowStart = dataMonths.length > 0
    ? dataMonths.reduce(function(a, b) { return a < b ? a : b; })
    : currentMonth;

  var endMo = windowStart.getMonth() + 5;
  var endYr = windowStart.getFullYear();
  if (endMo > 11) { endMo -= 12; endYr += 1; }
  var windowEnd = new Date(endYr, endMo, 1);

  function getMonday(d) {
    var day = d.getDay();
    var diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.getFullYear(), d.getMonth(), diff);
  }

  var slotDate = getMonday(windowStart);
  var windowEndLastDay = new Date(windowEnd.getFullYear(), windowEnd.getMonth() + 1, 0);

  var slots = [];
  var d = new Date(slotDate);
  while (d <= windowEndLastDay) {
    var jan4 = new Date(d.getFullYear(), 0, 4);
    var w1 = new Date(jan4);
    w1.setDate(jan4.getDate() - jan4.getDay() + 1);
    var weekNum = Math.floor((d - w1) / (7 * 86400000)) + 1;
    slots.push({
      date: new Date(d), weekNum: weekNum, label: 'WK' + weekNum,
      month: MONTH_NAMES[d.getMonth()], monthIdx: d.getMonth(),
      isMonthStart: d.getDate() <= 7,
      unaided: null, aided: null, rateSaver: null, hasData: false
    });
    d.setDate(d.getDate() + 7);
  }

  dataPoints.forEach(function(p) {
    var wMatch = (p.run_id || '').match(/W([0-9]+)$/);
    if (!wMatch) return;
    var wn = parseInt(wMatch[1]);
    for (var si = 0; si < slots.length; si++) {
      if (slots[si].weekNum === wn) {
        slots[si].unaided   = parseFloat(p.unaided_sov)    || 0;
        slots[si].aided     = parseFloat(p.aided_sov)      || 0;
        slots[si].rateSaver = parseFloat(p.rate_saver_sov) || 0;
        slots[si].hasData = true;
        break;
      }
    }
  });

  var dataCount = slots.filter(function(s) { return s.hasData; }).length;
  var NUM_SLOTS = slots.length;
  if (NUM_SLOTS < 2) NUM_SLOTS = 2;

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

  [100, 75, 50, 25, 0].forEach(function(pct) {
    var y = padT + chartH - (pct / 100) * chartH;
    ctx.strokeStyle = '#2d3748'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillStyle = '#718096'; ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(pct + '%', padL - 6, y + 4);
  });

  function slotX(i) { return padL + (chartW / (NUM_SLOTS - 1)) * i; }

  slots.forEach(function(s, i) {
    ctx.strokeStyle = '#2d3748'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(slotX(i), H - padB + 2); ctx.lineTo(slotX(i), H - padB + 5); ctx.stroke();
  });

  slots.forEach(function(s, i) {
    if (s.isMonthStart) return;
    if (i % 2 !== 0) return;
    ctx.fillStyle = '#4a5568'; ctx.font = '9px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText(s.label, slotX(i), H - padB + 16);
  });

  var labeledMonths = new Set();
  slots.forEach(function(s, i) {
    if (!s.isMonthStart) return;
    var x = slotX(i);
    labeledMonths.add(s.monthIdx + '_' + s.date.getFullYear());
    ctx.strokeStyle = '#2d4a8a'; ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, H - padB + 2); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(x, H - padB + 2); ctx.lineTo(x, H - padB + 8); ctx.stroke();
    ctx.fillStyle = '#90cdf4'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText(s.month, x, H - padB + 30);
  });

  if (slots.length > 0) {
    var lastSlot = slots[slots.length - 1];
    var lastMonthKey = lastSlot.monthIdx + '_' + lastSlot.date.getFullYear();
    if (!labeledMonths.has(lastMonthKey)) {
      var x = slotX(slots.length - 1);
      ctx.strokeStyle = '#2d4a8a'; ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, H - padB + 2); ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(x, H - padB + 2); ctx.lineTo(x, H - padB + 8); ctx.stroke();
      ctx.fillStyle = '#90cdf4'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center';
      ctx.fillText(lastSlot.month, x, H - padB + 30);
    }
  }

  var METRICS = [
    { key: 'unaided',   color: '#dc2626' },
    { key: 'aided',     color: '#fbbf24' },
    { key: 'rateSaver', color: '#90cdf4' }
  ];
  METRICS.forEach(function(metric) {
    ctx.strokeStyle = metric.color; ctx.lineWidth = 2; ctx.setLineDash([]);
    var started = false;
    ctx.beginPath();
    slots.forEach(function(s, i) {
      if (!s.hasData) return;
      var x = slotX(i); var y = padT + chartH - (s[metric.key] / 100) * chartH;
      started ? ctx.lineTo(x, y) : (ctx.moveTo(x, y), started = true);
    });
    if (started) ctx.stroke();
    slots.forEach(function(s, i) {
      if (!s.hasData) return;
      var x = slotX(i); var y = padT + chartH - (s[metric.key] / 100) * chartH;
      ctx.fillStyle = metric.color;
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#161b28'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.stroke();
    });
  });

  if (note) {
    var startLabel = MONTH_NAMES[windowStart.getMonth()] + ' ' + windowStart.getFullYear();
    var endLabel   = MONTH_NAMES[windowEnd.getMonth()]   + ' ' + windowEnd.getFullYear();
    note.textContent = dataCount === 0
      ? 'No data yet · ' + startLabel + ' → ' + endLabel
      : dataCount + ' week' + (dataCount !== 1 ? 's' : '') + ' of data · ' + startLabel + ' → ' + endLabel;
  }
}

// ── Branded Search Status ─────────────────────────────────────────
function renderBrandedSearchStatus(s) {
  var brandedList = document.getElementById('branded-issues-list');
  if (!brandedList) return;
  var primary = (s.model_sov && s.model_sov.primary) ? s.model_sov.primary : [];
  var pulse   = (s.model_sov && s.model_sov.pulse)   ? s.model_sov.pulse   : [];
  var allModels = primary.concat(pulse);
  var hardFailures = [], partialRuns = [], brandedIssues = [];
  allModels.forEach(function(m) {
    var aidedPct = parseFloat((m.aided || '0').replace('%', ''));
    if (m.status === 'success' && aidedPct < 100) hardFailures.push(m);
    if (m.status === 'partial') partialRuns.push(m);
    if (m.branded_failures && m.branded_failures.length > 0) brandedIssues.push(m);
  });
  var html = '';
  hardFailures.concat(brandedIssues.filter(function(m) { return hardFailures.indexOf(m) === -1; })).forEach(function(m) {
    html += '<div class="indicator-row"><span class="priority-badge p0">P0</span>'
      + '<div class="indicator-label">' + m.name + ': <span style="color:#fc8181;">Failed to identify GoDaddy on branded prompts — aided SOV ' + m.aided + '</span></div>'
      + '<div class="indicator-status red">❌ ISSUE</div></div>';
  });
  partialRuns.forEach(function(m) {
    var aidedPct = parseFloat((m.aided || '0').replace('%', ''));
    var totalPrompts = m.aided_total || 7;
    var completedPrompts = m.aided_completed || Math.round(aidedPct / 100 * totalPrompts);
    html += '<div class="indicator-row"><span style="font-size:16px;">⚠️</span>'
      + '<div class="indicator-label">' + m.name + ': Partial run — ' + completedPrompts + '/' + totalPrompts + ' prompts. Aided SOV ' + m.aided + ' reflects partial data. Not a GoDaddy recognition issue.</div>'
      + '<div class="indicator-status yellow">⚠️ Partial data</div></div>';
  });
  if (html === '') {
    html = '<div class="indicator-row">'
      + '<span class="priority-badge p0" style="background:#0a2d1a;border-color:#22543d;color:#68d391;">OK</span>'
      + '<div class="indicator-label">All models correctly identify GoDaddy Payments when explicitly searched</div>'
      + '<div class="indicator-status green">✅ No issues detected</div></div>';
  }
  brandedList.innerHTML = html;
}

// ── Helpers ───────────────────────────────────────────────────────
function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function statusBadge(s) {
  const map = { success:'✅ Normal', partial:'⚠️ Partial', error:'❌ Error', pending:'⏳ Pending', tracking:'📡 Tracking', cached:'💾 Cached' };
  return map[s] || s || '—';
}
function statusIcon(s) {
  const map = { absent:'❌', present:'✅', review:'⚠️', defend:'🛡️', outreach_in_progress:'📤', active:'✅', active_needs_update:'⚠️', not_started:'⏸️', needs_update:'⚠️' };
  return map[s] || '—';
}
function trafficLight(s) {
  return s==='green' ? '🟢' : s==='red' ? '🔴' : '🟡';
}

// ── Init on page load ─────────────────────────────────────────────
// FIX 2: Use readyState check instead of only DOMContentLoaded listener.
// When the script is at the bottom of <body>, DOMContentLoaded may have
// already fired by the time the listener is registered — causing the
// header to never update. This pattern handles both cases.
function _geoDashboardInit() {
  loadSession().then(function(session) {
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
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _geoDashboardInit);
} else {
  _geoDashboardInit();
}
