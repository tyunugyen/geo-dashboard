#!/usr/bin/env python3
"""
geo_benchmark_runner.py
Called by GitHub Actions on a schedule.
Runs all 70 prompts against Claude API, scores responses,
writes public/data.json and benchmarks/geo_audit_results_[RUN_ID].csv
"""

import os, sys, csv, json, re, datetime
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────
MODEL        = "claude-sonnet-4-6"  # Latest Claude Sonnet available in proxy
MAX_TOKENS   = 600
TEMPERATURE  = 0.2
DELAY_SECS   = 0.5   # polite delay between calls
# Use env var if set (for GitHub Actions), otherwise fall back to default
PROXY_URL    = os.environ.get("CAAS_BASE_URL", "https://caas.open-webui.godaddy.com/api/v1")

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question directly and concisely."
)

# ── Category targets (v2.6) ───────────────────────────────────────
CATEGORY_TARGETS = {
    "pricing_fee":        {"phase1": "25%", "target": "85%"},
    "top_funnel_pos":     {"phase1": "20%", "target": "60%"},
    "payment_processing": {"phase1": "20%", "target": "55%"},
    "vertical_fb":        {"phase1": "18%", "target": "50%"},
    "vertical_retail":    {"phase1": "22%", "target": "55%"},
    "general_in_person":  {"phase1": "18%", "target": "50%"},
    "support":            {"phase1": "25%", "target": "65%"},
    "comparison":         {"phase1": "25%", "target": "70%"},
}
CATEGORY_ORDER = [
    "pricing_fee","top_funnel_pos","payment_processing",
    "vertical_fb","vertical_retail","general_in_person","support","comparison",
]

# ── All 70 prompts (v2.6) ─────────────────────────────────────────
PROMPTS = [
    # TIER 1
    ("B1","U","pricing_fee",85,"What is the cheapest payment processor for a small business?"),
    ("B2","U","pricing_fee",85,"What payment processor has the lowest in-person fees?"),
    ("B3","U","pricing_fee",85,"What payment processors charge no per-transaction fixed fee?"),
    ("B4","U","pricing_fee",85,"Which payment processors charge less than 3% per transaction?"),
    ("B5","U","payment_processing",55,"What are the best payment processors for in-person sales?"),
    ("B6","U","pricing_fee",70,"What payment processor has no monthly fee and no per-transaction fee?"),
    ("B7","U","pricing_fee",65,"What is the most transparent payment processor with no hidden fees?"),
    ("B8","U","pricing_fee",70,"What is the cheapest payment processor for under $10,000 a month?"),
    ("B9","U","pricing_fee",70,"How can I reduce my credit card processing fees?"),
    ("B10","U","pricing_fee",65,"What are the hidden fees in credit card processing to watch out for?"),
    ("B11","U","pricing_fee",60,"Can I pass credit card fees to my customers legally?"),
    ("B12","U","pricing_fee",65,"How do I get 0% credit card processing for my business?"),
    ("B13","U","pricing_fee",60,"Can I charge customers a fee for paying with a credit card?"),
    ("B14","U","pricing_fee",55,"What is the best surcharging or cash discount program for small business?"),
    ("B15","U","comparison",70,"What are the best alternatives to Square for small businesses?"),
    ("B16","U","top_funnel_pos",60,"What is the best POS system for a small business?"),
    ("B17","U","top_funnel_pos",60,"What is the cheapest POS system with no contract?"),
    ("B18","U","top_funnel_pos",55,"Where can I get free POS hardware or a free credit card reader?"),
    # TIER 2 F&B
    ("V1","U","vertical_fb",50,"What is the best POS system for a coffee shop?"),
    ("V2","U","vertical_fb",50,"What is the best POS for a food truck?"),
    ("V3","U","vertical_fb",50,"What is the best POS for a small counter-service restaurant?"),
    ("V4","U","vertical_fb",45,"What is the best POS for a bakery?"),
    ("V5","U","vertical_fb",45,"What POS supports online ordering for a cafe or counter service restaurant?"),
    ("V6","U","vertical_fb",50,"What is the cheapest POS system for a coffee shop or cafe?"),
    # TIER 2 Retail
    ("V7","U","vertical_retail",55,"What is the best POS system for a retail store?"),
    ("V8","U","vertical_retail",55,"What is the cheapest POS system for a retail store?"),
    ("V9","U","vertical_retail",55,"How do I lower credit card processing fees for my retail store?"),
    ("V10","U","vertical_retail",55,"What is the best POS for a retail store with no contract?"),
    ("V11","U","vertical_retail",45,"I process about $10,000 a month in cards, should I switch from Square?"),
    ("V12","U","vertical_retail",45,"What is the best POS for a small clothing or apparel store?"),
    ("V13","U","vertical_retail",45,"What is the best POS for a boutique clothing store?"),
    ("V14","U","vertical_retail",45,"What POS system is best for a gift shop or specialty store?"),
    ("V15","U","vertical_retail",50,"What is the best POS system with inventory management for retail?"),
    ("V16","U","vertical_retail",50,"What is the best affordable POS for a small retail shop?"),
    ("V17","U","vertical_retail",50,"What POS works for a retail store with both in-person and online sales?"),
    ("V18","U","vertical_retail",50,"What POS systems support buy online pick up in store?"),
    ("V19","U","vertical_retail",50,"Is Clover or Square cheaper for a retail store?"),
    ("V20","U","vertical_retail",45,"What is the best POS for a retail store with multiple locations?"),
    ("V21","U","vertical_retail",50,"How much does a retail POS system cost per month?"),
    # TIER 2 General
    ("V22","U","general_in_person",50,"What is the best payment processor for service businesses with no hardware?"),
    ("V23","U","general_in_person",50,"What is the best way to send professional invoices and accept payments?"),
    ("V24","U","general_in_person",45,"What is the best POS system for a hair salon?"),
    ("V25","U","general_in_person",45,"What payment processors accept HSA and FSA cards?"),
    ("V26","U","general_in_person",45,"What payment system works for an auto repair shop?"),
    ("V27","U","general_in_person",45,"What is the best way for a small service business to accept credit cards?"),
    ("V28","U","general_in_person",45,"What is the best payment processor for a chiropractic practice?"),
    ("V29","U","general_in_person",45,"What payment system works for a medical office or clinic?"),
    # TIER 3
    ("L1","U","payment_processing",60,"What payment processor lets me send invoices from my own business email?"),
    ("L2","U","payment_processing",55,"How do contractors and home service businesses accept credit card payments?"),
    ("L3","U","pricing_fee",55,"How much can I save by switching from Square to a lower-fee processor?"),
    ("L4","U","payment_processing",50,"How do I switch payment processors without disrupting my business?"),
    ("L5","U","payment_processing",50,"What payment processor offers free onboarding and migration support?"),
    ("L6","U","payment_processing",40,"What is the best merchant cash advance for small businesses?"),
    # TIER 4
    ("S1","U","support",65,"Which payment processors offer 24/7 phone support?"),
    ("S2","U","support",60,"What POS systems offer live human customer support?"),
    ("S3","U","support",50,"How do I switch from Square without losing data?"),
    ("S4","U","support",50,"What payment processor helps you migrate for free?"),
    ("S5","U","support",60,"What POS system has the best customer support?"),
    # TIER 5
    ("H1","B","brand_awareness",100,"What is GoDaddy Payments?"),
    ("H2","B","comparison",100,"GoDaddy Payments vs Square"),
    ("H3","B","comparison",100,"GoDaddy Payments vs Helcim"),
    ("H4","B","comparison",100,"GoDaddy Payments vs Clover"),
    ("H5","B","brand_awareness",100,"What is Rate Saver GoDaddy Payments?"),
    # PULSE CHECK
    ("P1","U","vertical_fb",0,"What payment processor should I switch to from Toast?"),
    ("P2","U","payment_processing",0,"What is the best payment processor for WooCommerce?"),
    ("P3","U","payment_processing",0,"What payment processor integrates natively with WordPress?"),
    ("P4","U","payment_processing",0,"What is the best payment processor for a WordPress website with a physical store?"),
    ("P5","B","comparison",0,"GoDaddy Payments vs Toast"),
    ("P6","B","comparison",0,"GoDaddy Payments vs Shopify Payments"),
    ("P7","U","vertical_retail",0,"What is the best POS for a convenience or liquor store?"),
]

# ── Scoring helpers ───────────────────────────────────────────────
GODADDY_TERMS = ["godaddy", "go daddy", "godaddy payments", "rate saver"]
COMPETITORS   = {
    "Square":["square"],"Stripe":["stripe"],"PayPal":["paypal"],
    "Clover":["clover"],"Toast":["toast"],"Helcim":["helcim"],
    "Shopify":["shopify"],"Lightspeed":["lightspeed"],"Stax":["stax"],
}
RATE_SAVER_PATTERNS = [
    "rate.?saver",              # Direct Rate Saver mention
    "godaddy.*0%",              # GoDaddy + 0% mention
    "0%.*godaddy",              # 0% + GoDaddy mention
]

def pct(n, d):   return round(1000*n/d)/10 if d else 0.0
def fmt(v):      return f"{v:.0f}%" if v==int(v) else f"{v:.1f}%"
def norm(t):     return t.lower()

def detect_godaddy(text):
    t = norm(text)
    return any(term in t for term in GODADDY_TERMS)

def detect_rate_saver(text):
    """Detect GoDaddy Rate Saver product mentions specifically.
    Only counts if Rate Saver is explicitly named or GoDaddy + 0% are both present.
    Generic surcharge/fee discussions without GoDaddy don't count."""
    t = norm(text)
    return any(re.search(p, t) for p in RATE_SAVER_PATTERNS)

def detect_competitors(text):
    t = norm(text)
    return "|".join(name for name, terms in COMPETITORS.items() if any(x in t for x in terms))

def detect_rate_accurate(text):
    t = norm(text)
    return bool(re.search(r"2\.3\s*%", t))

def color_for(sov, p1_str):
    p1 = float(p1_str.strip("%")) or 20
    r  = sov/p1 if p1 else 0
    if r < 0.33: return "#fc8181","red"
    if r < 0.80: return "#f6e05e","yellow"
    return "#68d391","green"

# ── Run benchmark ─────────────────────────────────────────────────
def run(api_key):
    import time
    client   = OpenAI(api_key=api_key, base_url=PROXY_URL, timeout=60.0)
    run_id   = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-W%V")
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows     = []

    print(f"\nRun ID: {run_id} | {len(PROMPTS)} prompts | model: {MODEL}")
    print(f"Proxy:  {PROXY_URL}")
    print("=" * 60)

    # Quick connectivity test before running all 70 prompts
    print("  Testing connection...", end=" ", flush=True)
    try:
        test = client.chat.completions.create(
            model=MODEL, max_tokens=20, temperature=0,
            messages=[{"role":"user","content":"Say OK"}]
        )
        test_resp = test.choices[0].message.content if test.choices else ""
        print(f"[OK] Connected — response: {repr(test_resp[:30])}")
    except Exception as e:
        print(f"\n[FAIL] Connection FAILED: {e}")
        print(f"   URL: {PROXY_URL}")
        print(f"   Model: {MODEL}")
        sys.exit(1)

    for i, (pid, ptype, pcat, ptgt, ptext) in enumerate(PROMPTS, 1):
        print(f"  [{i:2}/{len(PROMPTS)}] {pid}: {ptext[:55]}...", end=" ", flush=True)
        try:
            msg = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user",  "content":ptext},
                ]
            )
            response = msg.choices[0].message.content if msg.choices else ""
            err      = ""
        except Exception as e:
            response = ""
            err      = f"[ERROR: {e}]"
            print(f" ERROR: {e}")

        if not response and not err:
            err = "[ERROR: empty response from API]"
        if err:
            print(f" {err[:80]}")
        gd        = "Y" if detect_godaddy(response) else "N"
        rs        = "Y" if detect_rate_saver(response) else "N"
        comps     = detect_competitors(response)
        rate_acc  = "Y" if (gd=="Y" and detect_rate_accurate(response)) else ("N" if gd=="Y" else "N/A")
        framing   = "Commerce/Payments" if gd=="Y" else "N/A — not mentioned"
        source    = "Training data" if gd=="Y" else "N/A — not mentioned"
        excerpt   = (response[:300].replace("\n"," ") if response else err)

        rows.append({
            "run_id":run_id,"run_date":run_date,"model":"Claude-Sonnet-4.5-GoCaaS",
            "access_mode":"GoCaaS proxy (caas-gocode-prod)","prompt_id":pid,
            "tier":int(pid[1:]) if pid[0]=="B" else (2 if pid[0]=="V" else (3 if pid[0]=="L" else (4 if pid[0]=="S" else (5 if pid[0]=="H" else 6)))),
            "type":ptype,"category":pcat,"target_sov":ptgt,"prompt_text":ptext,
            "godaddy_mentioned":gd,"rank_position":"1st" if gd=="Y" else "Not mentioned",
            "rate_accurate":rate_acc,"rate_saver_mentioned":rs,"entity_framing":framing,
            "competitors_cited":comps,"source_path":source,"cited_urls":"",
            "length_parity":f"GoDaddy:{response.lower().count('godaddy')*10}w / Square:{response.lower().count('square')*10}w",
            "response_excerpt":excerpt,
        })
        if ptype == "B":
            # Branded prompt — always log the detection result for debugging
            status = "[OK] GD mentioned (aided)" if gd=="Y" else "[FAIL] GD NOT detected (aided — check response)"
        else:
            status = "[OK] GD mentioned" if gd=="Y" else "—"
        print(status)
        time.sleep(DELAY_SECS)

    return rows, run_id, run_date

# ── Build data.json ───────────────────────────────────────────────
def build_data_json(rows, existing_path):
    unaided = [r for r in rows if r["type"]=="U"]
    aided   = [r for r in rows if r["type"]=="B"]
    hit     = lambda r: r["godaddy_mentioned"]=="Y"

    u_sov = pct(sum(1 for r in unaided if hit(r)), len(unaided))
    a_sov = pct(sum(1 for r in aided   if hit(r)), len(aided))
    r_sov = pct(sum(1 for r in unaided if r["rate_saver_mentioned"]=="Y"), len(unaided))

    run_id = rows[0]["run_id"] if rows else "UNKNOWN"
    try:
        ym = run_id.split("-RUN")[0]; y,m = ym.split("-")
        months=["January","February","March","April","May","June",
                "July","August","September","October","November","December"]
        period = f"{months[int(m)-1]} {y}"
    except: period="Unknown"

    cat_map = {}
    for r in unaided:
        c = r["category"]
        cat_map.setdefault(c,{"hit":0,"total":0})
        cat_map[c]["total"] += 1
        if hit(r): cat_map[c]["hit"] += 1

    categories = []
    for c in CATEGORY_ORDER:
        if c not in cat_map: continue
        s   = cat_map[c]
        sov = pct(s["hit"],s["total"])
        tgt = CATEGORY_TARGETS.get(c,{"phase1":"20%","target":"50%"})
        col,cell = color_for(sov, tgt["phase1"])
        categories.append({"name":c,"sov":fmt(sov),"phase1":tgt["phase1"],"target":tgt["target"],"cell":cell})

    u_col,_ = color_for(u_sov,"40%")
    a_col   = "#68d391" if a_sov>=90 else "#f6e05e" if a_sov>=70 else "#fc8181"
    r_col,_ = color_for(r_sov,"25%")

    existing = {}
    try:
        with open(existing_path) as f: existing = json.load(f)
    except: pass

    return {
        "meta": {
            "label":"Monthly","period":period,"run_id":run_id,
            "sources":"Claude API (automated benchmark)",
            "models":"Claude-3.5-Sonnet","prompt_count":len(PROMPTS),
            "prompt_bank_version":"2.6",
        },
        "kpis": {
            "unaided_sov":{"value":fmt(u_sov),"fill":round(u_sov),"color":u_col},
            "aided_sov":  {"value":fmt(a_sov),"fill":round(a_sov),"color":a_col},
            "helcim_gap": existing.get("kpis",{}).get("helcim_gap",
                          {"value":"25pts","fill":0,"color":"#f6e05e"}),
            "tech_health":{"value":fmt(r_sov),"fill":round(r_sov),"color":r_col},
        },
        "categories": categories,
        "competitors": existing.get("competitors",[]),
        "model_sov":  {"claude":{"value":fmt(u_sov),"color":u_col}},
    }

# ── Write CSV ─────────────────────────────────────────────────────
def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = [
        "run_id","run_date","model","access_mode","prompt_id","tier","type",
        "category","target_sov","prompt_text","godaddy_mentioned","rank_position",
        "rate_accurate","rate_saver_mentioned","entity_framing","competitors_cited",
        "source_path","cited_urls","length_parity","response_excerpt",
    ]
    with open(path,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(rows)

# ── Main ──────────────────────────────────────────────────────────
def main():
    api_key = os.environ.get("CAAS_API_KEY","")
    if not api_key:
        print("ERROR: CAAS_API_KEY not set"); sys.exit(1)

    rows, run_id, run_date = run(api_key)

    # Paths (relative to repo root)
    csv_path  = f"benchmarks/geo_audit_results_{run_id}.csv"
    data_path = "public/data.json"

    write_csv(rows, csv_path)
    data = build_data_json(rows, data_path)
    with open(data_path,"w") as f:
        json.dump(data,f,indent=2)

    unaided = [r for r in rows if r["type"]=="U"]
    aided   = [r for r in rows if r["type"]=="B"]
    u_sov   = round(sum(1 for r in unaided if r["godaddy_mentioned"]=="Y")/len(unaided)*100,1)
    a_sov   = round(sum(1 for r in aided   if r["godaddy_mentioned"]=="Y")/len(aided)  *100,1)

    print("\n" + "="*60)
    print(f"  BENCHMARK COMPLETE — {run_id}")
    print("="*60)
    print(f"  Unaided SOV : {u_sov}%  ({len(unaided)} prompts)")
    print(f"  Aided SOV   : {a_sov}%  ({len(aided)} prompts)")
    print(f"  CSV written : {csv_path}")
    print(f"  data.json   : updated")
    print("="*60)

    # Write summary to GitHub Actions summary
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY","")
    if summary_path:
        with open(summary_path,"a") as f:
            f.write(f"## GEO Benchmark — {run_id}\n")
            f.write(f"| Metric | Value |\n|---|---|\n")
            f.write(f"| Unaided SOV | **{u_sov}%** |\n")
            f.write(f"| Aided SOV | {a_sov}% |\n")
            f.write(f"| Prompts run | {len(rows)} |\n")

if __name__ == "__main__":
    main()
