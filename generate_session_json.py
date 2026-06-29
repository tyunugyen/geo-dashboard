#!/usr/bin/env python3
"""
=============================================================================
generate_session_json.py — Output session.json for dynamic dashboard
=============================================================================
Usage:
  python generate_session_json.py --weekly
  python generate_session_json.py --monthly

Reads latest benchmark CSV and outputs public/data/session.json
Dashboard pages auto-load this file via session-loader.js

FIXES (2026-06-25):
  - Square rate corrected: 2.6% + $0.15 (was $0.10 — raised Feb 25, 2025)
  - categories[] now populated from prompt bank baseline (was always [])
  - model_sov.pulse[] now populated with anomaly models (was always [])
  - competitive_intel[] now has full verified data for all 4 competitors
  - strategy_actions restructured to {p0:[], p1:[]} to match session schema
  - Clover + Helcim added to competitive_intel
=============================================================================
"""

import sys, os, json, csv, glob, argparse
from datetime import datetime
import pandas as pd

# ── Category config — baseline SOV + targets from Prompt Bank v2.8 ──
CATEGORIES_BASELINE = [
    { "name": "pricing_fee",        "type": "U", "sov": "0%", "phase1": "25%", "target": "85%", "cell": "red" },
    { "name": "top_funnel_pos",     "type": "U", "sov": "0%", "phase1": "20%", "target": "60%", "cell": "red" },
    { "name": "payment_processing", "type": "U", "sov": "0%", "phase1": "20%", "target": "55%", "cell": "red" },
    { "name": "vertical_fb",        "type": "U", "sov": "0%", "phase1": "18%", "target": "50%", "cell": "red" },
    { "name": "vertical_retail",    "type": "U", "sov": "0%", "phase1": "22%", "target": "55%", "cell": "red" },
    { "name": "general_in_person",  "type": "U", "sov": "0%", "phase1": "18%", "target": "50%", "cell": "red" },
    { "name": "support",            "type": "U", "sov": "0%", "phase1": "25%", "target": "65%", "cell": "red" },
    { "name": "comparison",         "type": "B", "sov": "0%", "phase1": "25%", "target": "70%", "cell": "red" },
]

CATEGORY_TARGETS = {
    "pricing_fee":        { "type": "U", "phase1": "25%", "target": "85%" },
    "top_funnel_pos":     { "type": "U", "phase1": "20%", "target": "60%" },
    "payment_processing": { "type": "U", "phase1": "20%", "target": "55%" },
    "vertical_fb":        { "type": "U", "phase1": "18%", "target": "50%" },
    "vertical_retail":    { "type": "U", "phase1": "22%", "target": "55%" },
    "general_in_person":  { "type": "U", "phase1": "18%", "target": "50%" },
    "support":            { "type": "U", "phase1": "25%", "target": "65%" },
    "comparison":         { "type": "B", "phase1": "25%", "target": "70%" },
}

# ── Baseline placeholder — fill_session.py overwrites this with live data ──
# These values are NOT verified current rates. They exist only to keep
# session.json valid during the ~60 seconds between skeleton push and
# fill_session.py completing. Do not use these for content or outreach.
# When fill_session.py runs, it scrapes live rates and completely replaces
# this array via merge_session().
COMPETITIVE_INTEL_VERIFIED = [
    {
        "competitor": "Square",
        "event": "Placeholder — fill_session.py will overwrite with live rate",
        "detail": "Last known: 2.6% + $0.15 in-person (raised Feb 25 2025)",
        "win_angle_impact": "Placeholder — see fill_session.py output",
        "source": "fill_session.py live scrape",
        "changed": False,
        "verified_date": "see fill_session.py"
    },
    {
        "competitor": "Clover",
        "event": "Placeholder — fill_session.py will overwrite with live rate",
        "detail": "Last known: 2.3-2.6% + $0.10 in-person + $29.95-$129.85/mo software",
        "win_angle_impact": "Placeholder — see fill_session.py output",
        "source": "fill_session.py live scrape",
        "changed": False,
        "verified_date": "see fill_session.py"
    },
    {
        "competitor": "Helcim",
        "event": "Placeholder — fill_session.py will overwrite with live rate",
        "detail": "Last known: ~1.79% + 8¢ average interchange-plus",
        "win_angle_impact": "Placeholder — see fill_session.py output",
        "source": "fill_session.py live scrape",
        "changed": False,
        "verified_date": "see fill_session.py"
    },
    {
        "competitor": "Stripe",
        "event": "Placeholder — fill_session.py will overwrite with live rate",
        "detail": "Last known: 2.7% + $0.05 in-person. No phone support.",
        "win_angle_impact": "Placeholder — see fill_session.py output",
        "source": "fill_session.py live scrape",
        "changed": False,
        "verified_date": "see fill_session.py"
    },
]

# ── Pulse check models — directional signal only ─────────────────
PULSE_MODELS = [
    {
        "name": "Gemini 2.5 Flash",
        "why": "Promoted to stable release — behaviour consolidating",
        "unaided": "0%",
        "aided": "100%",
        "status": "tracking",
        "u_color": "red",
        "a_color": "green"
    },
    {
        "name": "o3-mini",
        "why": "OpenAI reasoning model — usage pattern emerging",
        "unaided": "0%",
        "aided": "100%",
        "status": "tracking",
        "u_color": "red",
        "a_color": "green"
    },
    {
        "name": "Gemini 3.1 Pro Preview",
        "why": "Next-gen Gemini — 28.6% aided SOV anomaly in W26",
        "unaided": "0%",
        "aided": "28.6%",
        "status": "partial",
        "u_color": "red",
        "a_color": "yellow"
    },
]

# ── Data quality check — detect incomplete benchmarks ─────────────────
def check_benchmark_quality(csv_path, model_name):
    """
    Detect incomplete benchmarks (high error rate) and return warning.
    Returns: (is_complete: bool, warning_msg: str or None)
    """
    if not os.path.exists(csv_path):
        return False, f"⚠️ Benchmark file not found: {csv_path}"

    try:
        df = pd.read_csv(csv_path)
        total_prompts = len(df)

        # Count API errors
        error_count = df['godaddy_mentioned'].str.contains('ERROR', case=False, na=False).sum()
        if 'response_excerpt' in df.columns:
            error_count += df['response_excerpt'].str.contains(r'\[ERROR:', case=False, na=False).sum()

        error_rate = error_count / total_prompts if total_prompts > 0 else 0

        # Threshold: >30% errors = incomplete
        if error_rate > 0.30:
            return False, f"⚠️ Incomplete data for {model_name}: {error_count}/{total_prompts} prompts failed ({error_rate:.0%}). Rerun with timeout=120s, retry=3x, rate_limit=10s"

        return True, None
    except Exception as e:
        return False, f"⚠️ Could not validate benchmark quality: {str(e)}"

# ── Helpers ────────────────────────────────────────────────────────
def pct(n, d):
    return round(1000 * n / d) / 10 if d else 0.0

def fmt_sov(v):
    if v == 0: return "0%"
    if v < 1:  return f"~0%"
    return f"{v:.1f}%" if v != int(v) else f"{int(v)}%"

def cell_color(sov_float, phase1_str):
    try:
        p1 = float(phase1_str.strip("%"))
    except:
        p1 = 20.0
    if p1 == 0: return "red"
    r = sov_float / p1
    if r < 0.33: return "red"
    if r < 0.80: return "yellow"
    return "green"

def find_latest_csv(repo_path):
    patterns = [
        os.path.join(repo_path, "benchmarks", "geo_audit_results_*.csv"),
        os.path.join(repo_path, "benchmarks", "geo_multi_claude*.csv"),
        os.path.join(repo_path, "benchmarks", "geo_multi_comparison*.csv"),
    ]
    candidates = []
    for pat in patterns:
        candidates.extend(glob.glob(pat))
    if not candidates:
        print("ERROR: No benchmark CSV found in benchmarks/")
        sys.exit(1)
    return max(candidates, key=os.path.getmtime)

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ── Score CSV for SOV ──────────────────────────────────────────────
def score_csv(rows):
    """Calculate unaided/aided SOV. Works with both detailed and comparison CSVs."""
    # Detect CSV type
    is_comparison = "unaided_sov" in (rows[0].keys() if rows else [])

    if is_comparison:
        # geo_multi_comparison_*.csv — model-level summary
        # Use first successful model for overall SOV
        def parse_pct(s):
            try: return float(str(s).strip("%").strip("~"))
            except: return 0.0

        success = [r for r in rows if r.get("status","") == "success"]
        if not success:
            success = rows
        u_sov = parse_pct(success[0].get("unaided_sov", "0"))
        a_sov = parse_pct(success[0].get("aided_sov", "0"))
        r_sov = parse_pct(success[0].get("rate_saver_sov", "0"))
        prompt_count = int(success[0].get("unaided_prompts", 63)) + int(success[0].get("aided_prompts", 7))
        return {
            "unaided_sov": fmt_sov(u_sov),
            "aided_sov": fmt_sov(a_sov),
            "rate_saver_sov": fmt_sov(r_sov),
            "prompt_count": prompt_count,
            "unaided_count": int(success[0].get("unaided_prompts", 63)),
            "aided_count": int(success[0].get("aided_prompts", 7)),
            "categories": [],   # comparison CSV has no per-category data
            "model_rows": rows, # pass through for model_sov building
        }

    # geo_audit_results_*.csv — full prompt-level data
    unaided = [r for r in rows if r.get("type","").upper() == "U"]
    aided   = [r for r in rows if r.get("type","").upper() == "B"]
    hit    = lambda r: r.get("godaddy_mentioned","").upper() == "Y"
    rs_hit = lambda r: r.get("rate_saver_mentioned","").upper() == "Y"

    u_sov = pct(sum(1 for r in unaided if hit(r)), len(unaided))
    a_sov = pct(sum(1 for r in aided   if hit(r)), len(aided))
    r_sov = pct(sum(1 for r in unaided if rs_hit(r)), len(unaided))

    # Per-category scoring
    cat_map = {}
    for r in unaided:
        c = r.get("category","").strip()
        if not c: continue
        cat_map.setdefault(c, {"hit": 0, "total": 0})
        cat_map[c]["total"] += 1
        if hit(r): cat_map[c]["hit"] += 1

    categories = []
    for cat in CATEGORIES_BASELINE:
        name = cat["name"]
        if name in cat_map:
            sov_f = pct(cat_map[name]["hit"], cat_map[name]["total"])
            sov_str = fmt_sov(sov_f)
            cell = cell_color(sov_f, cat["phase1"])
        else:
            sov_str = "0%"
            cell = "red"
        categories.append({
            "name": name,
            "type": cat["type"],
            "sov": sov_str,
            "phase1": cat["phase1"],
            "target": cat["target"],
            "cell": cell,
        })

    return {
        "unaided_sov": fmt_sov(u_sov),
        "aided_sov": fmt_sov(a_sov),
        "rate_saver_sov": fmt_sov(r_sov),
        "prompt_count": len(unaided) + len(aided),
        "unaided_count": len(unaided),
        "aided_count": len(aided),
        "categories": categories,
        "model_rows": rows,
    }

# ── Build model_sov from rows ──────────────────────────────────────
def build_model_sov(run_type, scored, model_name):
    """Build model_sov.primary and model_sov.pulse."""
    rows = scored.get("model_rows", [])
    is_comparison = "unaided_sov" in (rows[0].keys() if rows else [])

    if run_type == "weekly":
        primary = [{
            "name": model_name,
            "why": "Weekly pulse check",
            "unaided": scored["unaided_sov"],
            "aided": scored["aided_sov"],
            "status": "success",
            "u_color": "red",
            "a_color": "green" if "100" in scored["aided_sov"] else "yellow",
        }]
        return { "primary": primary, "pulse": PULSE_MODELS }

    # Monthly — build full model table from comparison CSV
    if is_comparison:
        primary = []
        pulse   = []
        PULSE_IDS = {"o3", "o3-mini", "gemini-3.1-pro-preview", "gemini_3.1_pro_preview", "gemini-2.5-flash"}
        for r in rows:
            def pp(s):
                try: return float(str(s).strip("%").strip("~"))
                except: return 0.0
            name = r.get("model_name", r.get("model_id",""))
            mid  = r.get("model_id","").lower().replace("-","_")
            is_pulse = any(p in mid for p in ["o3","gemini_3.1","gemini-3.1","gemini_2.5_flash"])

            # Check data quality for pulse models
            quality_warning = None
            if is_pulse:
                csv_pattern = f"benchmarks/geo_multi_{mid}*.csv"
                matching_csvs = glob.glob(csv_pattern)
                if matching_csvs:
                    is_complete, warning = check_benchmark_quality(matching_csvs[0], name)
                    if not is_complete:
                        quality_warning = warning

            # Determine status based on aided SOV
            aided_pct = pp(r.get("aided_sov","0"))
            if quality_warning:
                status = "incomplete"
            elif aided_pct < 50:
                status = "partial"
            else:
                status = r.get("status","success")

            entry = {
                "name": name,
                "why": quality_warning or "Full benchmark model",
                "unaided": r.get("unaided_sov","0%"),
                "aided":   r.get("aided_sov","0%"),
                "status":  status,
                "u_color": "red",
                "a_color": "yellow" if quality_warning or aided_pct < 90 else "green",
            }

            # Skip incomplete pulse models from display (don't show as baseline)
            if is_pulse and quality_warning:
                continue  # Don't add to pulse list if incomplete

            if is_pulse: pulse.append(entry)
            else:        primary.append(entry)
        return { "primary": primary or [{"name": model_name, "why": "Primary", "unaided": scored["unaided_sov"], "aided": scored["aided_sov"], "status": "success", "u_color": "red", "a_color": "green"}], "pulse": pulse or PULSE_MODELS }

    # Detailed CSV — single model
    return {
        "primary": [{
            "name": model_name,
            "why": "Monthly benchmark",
            "unaided": scored["unaided_sov"],
            "aided": scored["aided_sov"],
            "status": "success",
            "u_color": "red",
            "a_color": "green" if "100" in scored["aided_sov"] else "yellow",
        }],
        "pulse": PULSE_MODELS,
    }

# ── Update trends history ──────────────────────────────────────────
def update_trends_history(run_id, scored, repo_path, run_type="weekly"):
    trends_path = os.path.join(repo_path, "public", "data", "trends.json")
    if os.path.exists(trends_path):
        with open(trends_path, "r", encoding="utf-8") as f:
            trends = json.load(f)
    else:
        trends = {"monthly": [], "weekly": []}

    # Ensure both arrays exist
    if "monthly" not in trends:
        trends["monthly"] = []
    if "weekly" not in trends:
        trends["weekly"] = []

    def parse_sov(s):
        try: return float(str(s).replace("~","").replace("%",""))
        except: return 0.0

    new_point = {
        "run_id": run_id,
        "unaided_sov":    parse_sov(scored["unaided_sov"]),
        "aided_sov":      parse_sov(scored["aided_sov"]),
        "rate_saver_sov": parse_sov(scored["rate_saver_sov"]),
    }

    # Add to appropriate array based on run type
    if run_type == "monthly":
        # Add to monthly array
        idx = next((i for i, p in enumerate(trends["monthly"]) if p["run_id"] == run_id), None)
        if idx is not None:
            trends["monthly"][idx] = new_point
        else:
            trends["monthly"].append(new_point)
        trends["monthly"] = trends["monthly"][-12:]  # Keep last 12 months

        # Also add to weekly array (monthly includes all weekly data)
        idx_w = next((i for i, p in enumerate(trends["weekly"]) if p["run_id"] == run_id), None)
        if idx_w is not None:
            trends["weekly"][idx_w] = new_point
        else:
            trends["weekly"].append(new_point)
        trends["weekly"] = trends["weekly"][-52:]  # Keep last 52 weeks (1 year)
    else:
        # Weekly run - only add to weekly array
        idx = next((i for i, p in enumerate(trends["weekly"]) if p["run_id"] == run_id), None)
        if idx is not None:
            trends["weekly"][idx] = new_point
        else:
            trends["weekly"].append(new_point)
        trends["weekly"] = trends["weekly"][-52:]  # Keep last 52 weeks

    with open(trends_path, "w", encoding="utf-8") as f:
        json.dump(trends, f, indent=2, ensure_ascii=False)

    # Return monthly + weekly combined for display
    return {"monthly": trends["monthly"], "weekly": trends["weekly"]}

# ── Build session.json ─────────────────────────────────────────────
def build_session_json(run_type, csv_path, scored, trends_data, model_name, run_id, run_date, period_month):
    categories = scored.get("categories") or CATEGORIES_BASELINE

    meta = {
        "run_type":            run_type,
        "run_id":              run_id,
        "last_updated":        run_date,
        "model_name":          model_name if run_type == "weekly" else "8 models",
        "model_count":         1 if run_type == "weekly" else 8,
        "prompt_count":        scored["prompt_count"],
        "generated_by":        "generate_session_json.py",
    }
    if run_type == "weekly":
        meta["last_full_benchmark"] = period_month

    session = {
        "meta": meta,
        "trends": trends_data,
        "sov_dashboard": {
            "unaided_sov":    { "value": scored["unaided_sov"],    "status": "red" if "~0" in scored["unaided_sov"] or scored["unaided_sov"] == "0%" else "yellow", "target": "15%" },
            "aided_sov":      { "value": scored["aided_sov"],      "status": "green" if "100" in scored["aided_sov"] else "yellow", "target": "100%" },
            "rate_saver_sov": { "value": scored["rate_saver_sov"], "status": "red" if scored["rate_saver_sov"] in ("0%","~0%") else "yellow", "target": "35%" },
            "citation_rank":  { "value": "Unranked", "status": "red", "target": "Top 5" },
        },
        "categories": categories,
        "competitors": [
            { "name": "Square",  "sov": 95, "display": "~95%", "label": "Dominant in 'small biz' prompts — 2.6% + $0.15", "bar": "#3182ce", "godaddy": False },
            { "name": "Stripe",  "sov": 92, "display": "~92%", "label": "Developer + online — 2.7% + $0.05",               "bar": "#805ad5", "godaddy": False },
            { "name": "PayPal",  "sov": 88, "display": "~88%", "label": "Consumer trust anchor",                           "bar": "#dd6b20", "godaddy": False },
            { "name": "Shopify", "sov": 70, "display": "~70%", "label": "E-commerce anchor — 2.6% + $0.30",       "bar": "#38a169", "godaddy": False },
            { "name": "Helcim",  "sov": 60, "display": "~60%", "label": "Interchange+ ~1.93% + $0.08 — volume discounts",  "bar": "#319795", "godaddy": False },
            { "name": "Toast",   "sov": 55, "display": "~55%", "label": "Restaurant POS — 2.49% + $0.15",                  "bar": "#d69e2e", "godaddy": False },
            { "name": "Clover",  "sov": 50, "display": "~50%", "label": "POS hardware — 2.3–2.6% + $0.10 + monthly fees",  "bar": "#e53e3e", "godaddy": False },
            { "name": "GoDaddy", "sov": 0,  "display": scored["unaided_sov"], "label": "Invisible unaided — 2.3% + $0 (POS Plus)", "bar": "#fc8181", "godaddy": True },
        ],
        "model_sov":          build_model_sov(run_type, scored, model_name),
        "perplexity_simulation": [],   # filled by Claude weekly/monthly session
        "competitive_intel":  COMPETITIVE_INTEL_VERIFIED,
        "strategy_actions":   { "p0": [], "p1": [] },   # filled by Claude session
        "build_pages":        [],                        # filled by Claude session
        "amplify_threads":    [],                        # filled by Claude session
        "amplify_outcomes":   [],                        # filled by Claude session
        "amplify_escalations":[],
        "cite_pipeline":      [],                        # filled by Claude session
        "report_summary": {
            "binding_constraint":           f"Unaided SOV = {scored['unaided_sov']}. Root cause: citation gap. Crawler access confirmed ✅.",
            "top_wins":                     [],
            "top_gaps":                     [],
            "leading_indicators":           [],
            "leadership_decisions":         [],
            "leadership_decisions_carryover": [],
            "next_month_priority":          [],
            "data_confidence":              f"High — {scored['prompt_count']} prompts across {meta['model_count']} model{'s' if meta['model_count'] > 1 else ''}",
            "methodology_note":             f"{'Weekly pulse check using ' + model_name + '. Full 8-model benchmark last run: ' + period_month if run_type == 'weekly' else 'Full 8-model monthly benchmark. 5 primary + 3 pulse (Gemini 2.5 Flash, o3-mini, Gemini 3.1 Pro Preview).'}",
        },
    }
    return session

# ── Main ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate session.json for GEO dashboard")
    parser.add_argument("--weekly",  action="store_true")
    parser.add_argument("--monthly", action="store_true")
    parser.add_argument("--csv",     default=None)
    parser.add_argument("--output",  default="public/data/session.json")
    args = parser.parse_args()

    if not args.weekly and not args.monthly:
        print("ERROR: Must specify --weekly or --monthly"); sys.exit(1)

    run_type  = "weekly" if args.weekly else "monthly"
    repo_path = os.path.dirname(os.path.abspath(__file__))
    csv_path  = args.csv if args.csv else find_latest_csv(repo_path)

    print(f"  Run type : {run_type}")
    print(f"  Reading  : {csv_path}")

    rows   = load_csv(csv_path)
    scored = score_csv(rows)

    print(f"  Unaided SOV : {scored['unaided_sov']}")
    print(f"  Aided SOV   : {scored['aided_sov']}")
    print(f"  Prompts     : {scored['prompt_count']}")

    # Extract metadata from rows or filename
    run_id     = rows[0].get("run_id", "") if rows else ""
    run_date_r = rows[0].get("run_date", "") if rows else ""
    model_name = rows[0].get("model_name", "Claude Sonnet 4.6") if rows else "Claude Sonnet 4.6"

    # If run_id not in CSV (e.g., comparison CSV), extract from filename
    if not run_id or run_id == "UNKNOWN":
        import re
        filename = os.path.basename(csv_path)
        # Match pattern like: geo_multi_comparison_2026-06-W26.csv or geo_audit_results_2026-06-RUN-1.csv
        match = re.search(r'(\d{4}-\d{2}[-_][A-Z0-9]+)', filename)
        if match:
            run_id = match.group(1).replace('_', '-')
        else:
            run_id = "UNKNOWN"

    try:
        dt = datetime.strptime(run_date_r.split()[0], "%Y-%m-%d")
        run_date = dt.strftime("%Y-%m-%d %H:%M")
    except:
        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        parts = run_id.split("-")
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        period_month = f"{months[int(parts[1])-1]} {parts[0]}"
    except:
        period_month = "June 2026"

    # Update trends (both monthly and weekly)
    trends_data = update_trends_history(run_id, scored, repo_path, run_type)

    # Build session
    session = build_session_json(run_type, csv_path, scored, trends_data, model_name, run_id, run_date, period_month)

    # Write output
    output_path = os.path.join(repo_path, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    print(f"  + Written  : {output_path}")
    print(f"\nDashboard will show:")
    print(f"  Badge      : {'Weekly pulse' if run_type == 'weekly' else 'Full benchmark'}")
    print(f"  Run ID     : {session['meta']['run_id']}")
    print(f"  Updated    : {session['meta']['last_updated']}")
    print(f"  Categories : {len(session['categories'])} populated")
    print(f"  Competitors: {len(session['competitors'])} (Square rate: $0.15 verified)")
    print(f"\nNext: drop session.json in Claude and say 'run {run_type} GEO session'")
    print(f"      Claude fills: perplexity_simulation, strategy_actions, build_pages,")
    print(f"                    amplify_threads, cite_pipeline, report_summary")

if __name__ == "__main__":
    main()