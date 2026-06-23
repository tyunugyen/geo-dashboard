const http   = require('http');
const fs     = require('fs');
const path   = require('path');
const https  = require('https');

const PORT      = process.env.PORT || 3000;
const PUBLIC    = path.join(__dirname, 'public');
const DATA_JSON = path.join(PUBLIC, 'data.json');

// ── jsonstorage.net persistence (optional, free, no account needed) ──
//
// ONE-TIME SETUP (2 minutes):
//   1. Run this in your terminal once:
//      curl -s -X POST https://api.jsonstorage.net/v1/json \
//        -H "Content-Type: application/json" \
//        -d @public/data.json
//
//   2. You'll get back something like:
//      {"uri":"https://api.jsonstorage.net/v1/json/abc123/xyz789"}
//
//   3. Your STORAGE_ID is the last two parts: "abc123/xyz789"
//
//   4. In GoDaddy PaaS → Settings → Secrets, add:
//      STORAGE_ID = abc123/xyz789
//
// After that: every CSV upload saves permanently, survives restarts/redeploys.
// Without STORAGE_ID set: falls back to local data.json only.

const STORAGE_ID      = process.env.STORAGE_ID || '';
const STORAGE_BASE    = 'api.jsonstorage.net';
const STORAGE_ENABLED = !!STORAGE_ID;

function storageRequest(method, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const options = {
      hostname: STORAGE_BASE,
      path:     `/v1/json/${STORAGE_ID}`,
      method,
      headers: {
        'Content-Type':  'application/json',
        'Accept':        'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
      },
    };
    const req = https.request(options, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(Buffer.concat(chunks).toString()) }); }
        catch { resolve({ status: res.statusCode, body: {} }); }
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

async function loadFromStorage() {
  if (!STORAGE_ENABLED) return false;
  try {
    const r = await storageRequest('GET');
    if (r.status !== 200) { console.warn('[storage] GET failed:', r.status); return false; }
    const content = JSON.stringify(r.body, null, 2);
    fs.writeFileSync(DATA_JSON, content, 'utf-8');
    console.log(`[storage] loaded data.json — run: ${r.body?.meta?.run_id || 'unknown'}`);
    return true;
  } catch (e) {
    console.warn('[storage] load error:', e.message); return false;
  }
}

async function saveToStorage(data) {
  if (!STORAGE_ENABLED) return false;
  try {
    const r = await storageRequest('PUT', data);
    if (r.status !== 200) { console.warn('[storage] PUT failed:', r.status); return false; }
    console.log('[storage] data.json saved to jsonstorage.net');
    return true;
  } catch (e) {
    console.warn('[storage] save error:', e.message); return false;
  }
}

// ── MIME map ──────────────────────────────────────────────────────
const MIME = {
  '.html': 'text/html', '.json': 'application/json',
  '.js':   'text/javascript', '.css': 'text/css', '.csv': 'text/csv',
};

// ── Category config ───────────────────────────────────────────────
const CATEGORY_TARGETS = {
  pricing_fee:        { phase1: '25%', target: '85%' },
  top_funnel_pos:     { phase1: '20%', target: '60%' },
  payment_processing: { phase1: '20%', target: '55%' },
  vertical_fb:        { phase1: '18%', target: '50%' },
  vertical_retail:    { phase1: '22%', target: '55%' },
  general_in_person:  { phase1: '18%', target: '50%' },
  support:            { phase1: '25%', target: '65%' },
  comparison:         { phase1: '25%', target: '70%' },
};
const CATEGORY_ORDER = [
  'pricing_fee','top_funnel_pos','payment_processing',
  'vertical_fb','vertical_retail','general_in_person','support','comparison',
];

// ── CSV helpers ───────────────────────────────────────────────────
function splitLine(line) {
  const r=[]; let cur='', inQ=false;
  for (const c of line) {
    if (c==='"'){inQ=!inQ;}
    else if(c===','&&!inQ){r.push(cur);cur='';}
    else{cur+=c;}
  }
  r.push(cur); return r;
}
function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const headers = splitLine(lines[0]);
  return lines.slice(1).filter(l=>l.trim()).map(l => {
    const vals=splitLine(l), row={};
    headers.forEach((h,j)=>{ row[h.trim()]=(vals[j]||'').trim(); });
    return row;
  });
}

// ── Scoring ───────────────────────────────────────────────────────
const pct  = (n,d) => d ? Math.round(1000*n/d)/10 : 0;
const fmt  = v => (v===Math.round(v)?v.toFixed(0):v.toFixed(1))+'%';
function colorFor(sov, p1Str) {
  const p1=parseFloat(p1Str)||20, r=p1>0?sov/p1:0;
  if(r<0.33) return {color:'#fc8181',cell:'red'};
  if(r<0.80) return {color:'#f6e05e',cell:'yellow'};
  return {color:'#68d391',cell:'green'};
}
function periodFromRunId(id) {
  try {
    const [y,m]=id.split('-RUN')[0].split('-');
    const months=['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
    return `${months[parseInt(m,10)-1]} ${y}`;
  } catch { return 'Unknown'; }
}
function scoreCSV(rows) {
  const u=rows.filter(r=>(r.type||'').toUpperCase()==='U');
  const a=rows.filter(r=>(r.type||'').toUpperCase()==='B');
  const hit  = r=>(r.godaddy_mentioned||'').toUpperCase()==='Y';
  const rsHit= r=>(r.rate_saver_mentioned||'').toUpperCase()==='Y';
  const uSOV=pct(u.filter(hit).length,u.length);
  const aSOV=pct(a.filter(hit).length,a.length);
  const rSOV=pct(u.filter(rsHit).length,u.length);
  const catMap={};
  u.forEach(r=>{
    const c=(r.category||'').trim(); if(!c) return;
    if(!catMap[c])catMap[c]={hit:0,total:0};
    catMap[c].total++; if(hit(r))catMap[c].hit++;
  });
  const ordered=[...CATEGORY_ORDER.filter(c=>catMap[c]),
                 ...Object.keys(catMap).filter(c=>!CATEGORY_ORDER.includes(c))];
  const categories=ordered.map(c=>{
    const s=catMap[c],sov=pct(s.hit,s.total);
    const tgt=CATEGORY_TARGETS[c]||{phase1:'20%',target:'50%'};
    const cd=colorFor(sov,tgt.phase1);
    return{name:c,sov:fmt(sov),phase1:tgt.phase1,target:tgt.target,cell:cd.cell};
  });
  const runId=(rows[0]&&rows[0].run_id)||'UNKNOWN';
  const uC=colorFor(uSOV,'40%').color;
  const aC=aSOV>=90?'#68d391':aSOV>=70?'#f6e05e':'#fc8181';
  const rC=colorFor(rSOV,'25%').color;
  // Per-model SOV breakdown
  const modelSOV={};
  const modelsArr=[...new Set(rows.map(r=>r.model||'').filter(Boolean))];
  modelsArr.forEach(m=>{
    const mRows=u.filter(r=>r.model===m);
    if(!mRows.length) return;
    const mSOV=pct(mRows.filter(hit).length,mRows.length);
    const mCol=colorFor(mSOV,'40%').color;
    const key=m.toLowerCase().includes('claude')?'claude'
      :(m.toLowerCase().includes('gpt')||m.toLowerCase().includes('openai'))?'chatgpt'
      :m.toLowerCase().includes('perplexity')?'perplexity'
      :m.toLowerCase().replace(/[^a-z]/g,'_');
    modelSOV[key]={value:fmt(mSOV),color:mCol};
  });
  const models=modelsArr.join(', ')||'Claude, GPT-4o, Perplexity';
  const promptCount=new Set(rows.map(r=>r.prompt_id||'')).size||70;
  return{runId,period:periodFromRunId(runId),uSOV,aSOV,rSOV,
         categories,uC,aC,rC,modelSOV,models,promptCount};
}
function buildNewData(s, existing) {
  return {
    meta:{label:'Monthly',period:s.period,run_id:s.runId,sources:'Benchmark CSV upload',
          models:s.models||'Claude, GPT-4o, Perplexity',
          prompt_count:s.promptCount||70,
          prompt_bank_version:(existing.meta||{}).prompt_bank_version||'2.6'},
    kpis:{
      unaided_sov:{value:fmt(s.uSOV),fill:Math.round(s.uSOV),color:s.uC},
      aided_sov:  {value:fmt(s.aSOV),fill:Math.round(s.aSOV),color:s.aC},
      helcim_gap: (existing.kpis||{}).helcim_gap||{value:'25pts',fill:0,color:'#f6e05e'},
      tech_health:{value:fmt(s.rSOV),fill:Math.round(s.rSOV),color:s.rC},
    },
    categories:  s.categories,
    competitors: (existing.competitors||[]),
    model_sov:   s.modelSOV||{},
  };
}

// ── Body / multipart helpers ──────────────────────────────────────
const collectBody = req => new Promise((res,rej)=>{
  const c=[]; req.on('data',d=>c.push(d)); req.on('end',()=>res(Buffer.concat(c)));
  req.on('error',rej);
});
function extractCSV(body, boundary) {
  const delim='--'+boundary;
  for (const part of body.split(delim)) {
    if(part.includes('filename=')&&part.includes('.csv')){
      const sep='\r\n\r\n', idx=part.indexOf(sep);
      if(idx!==-1) return part.slice(idx+sep.length).replace(/\r\n--$/,'').trimEnd();
    }
  }
  return null;
}
const json200 = (res,d) => { res.writeHead(200,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'}); res.end(JSON.stringify(d)); };
const jsonErr  = (res,c,m) => { res.writeHead(c,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'}); res.end(JSON.stringify({error:m})); };

// ── HTTP server ───────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  const urlPath = req.url.split('?')[0];

  // POST /upload
  if (req.method==='POST' && urlPath==='/upload') {
    try {
      const rawBody = await collectBody(req);
      const bodyStr = rawBody.toString('utf-8');
      const ct      = req.headers['content-type']||'';
      let csvText   = null;
      if(ct.includes('multipart/form-data')){
        const m=ct.match(/boundary=([^\s;]+)/);
        if(!m) return jsonErr(res,400,'Missing boundary');
        csvText=extractCSV(bodyStr,m[1]);
      } else if(ct.includes('text/csv')||ct.includes('text/plain')){
        csvText=bodyStr;
      } else if(ct.includes('application/json')){
        try{csvText=JSON.parse(bodyStr).csv;}catch{}
      }
      if(!csvText) return jsonErr(res,400,'No CSV content found');
      const rows=parseCSV(csvText);
      if(!rows.length) return jsonErr(res,400,'CSV parsed to 0 rows');
      const missing=['type','category','godaddy_mentioned'].filter(k=>!(k in rows[0]));
      if(missing.length) return jsonErr(res,400,`Missing columns: ${missing.join(', ')}`);

      const scored  = scoreCSV(rows);
      let existing  = {};
      try{existing=JSON.parse(fs.readFileSync(DATA_JSON,'utf-8'));}catch{}
      const newData = buildNewData(scored,existing);
      const newJson = JSON.stringify(newData,null,2);

      // Atomic disk write
      const tmp=DATA_JSON+'.tmp';
      fs.writeFileSync(tmp,newJson,'utf-8');
      fs.renameSync(tmp,DATA_JSON);

      // Persist to jsonstorage.net
      const saved = await saveToStorage(newData);

      console.log(`[upload] ${scored.runId} unaided=${scored.uSOV}% storage=${saved}`);
      json200(res,{ok:true,runId:scored.runId,period:scored.period,
                   unaidedSOV:scored.uSOV,aidedSOV:scored.aSOV,rsSOV:scored.rSOV,
                   storageSaved:saved,data:newData,
                   message:`data.json updated — Unaided SOV: ${fmt(scored.uSOV)}`});
    } catch(e){
      console.error('[upload]',e); jsonErr(res,500,'Server error: '+e.message);
    }
    return;
  }

  // OPTIONS preflight
  if(req.method==='OPTIONS'){
    res.writeHead(204,{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,POST','Access-Control-Allow-Headers':'Content-Type'});
    res.end(); return;
  }

  // GET static files
  let sp=urlPath==='/'||urlPath===''?'/index.html':urlPath;
  const fp=path.join(PUBLIC,sp);
  if(!fp.startsWith(PUBLIC)){res.writeHead(403);res.end('Forbidden');return;}
  fs.readFile(fp,(err,data)=>{
    if(err){
      fs.readFile(path.join(PUBLIC,'index.html'),(e2,d2)=>{
        if(e2){res.writeHead(500);res.end('Error');return;}
        res.writeHead(200,{'Content-Type':'text/html'});res.end(d2);
      });return;
    }
    const ctype = MIME[path.extname(fp)] || 'application/octet-stream';
    const noCache = fp.endsWith('.html') || fp.endsWith('.json');
    const headers = {'Content-Type': ctype};
    if (noCache) {
      headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
      headers['Pragma'] = 'no-cache';
      headers['Expires'] = '0';
    }
    res.writeHead(200, headers);
    res.end(data);
  });
});

// ── Startup ───────────────────────────────────────────────────────
(async () => {
  if (STORAGE_ENABLED) {
    console.log(`[storage] jsonstorage.net persistence enabled (ID: ${STORAGE_ID})`);
    await loadFromStorage();
  } else {
    console.log('[storage] No STORAGE_ID set — using local data.json');
    console.log('          To enable persistence: see STORAGE_SETUP.md');
  }
  server.listen(PORT, () => {
    console.log(`GEO Dashboard running on http://localhost:${PORT}`);
    console.log(`Upload endpoint: POST http://localhost:${PORT}/upload`);
  });
})();
