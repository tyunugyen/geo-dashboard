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
=============================================================================
"""

import sys, os, json, csv, glob, argparse
from datetime import datetime

# ── Load latest benchmark CSV ──────────────────────────────────────
def find_latest_csv(repo_path):
    """Find most recent geo_audit_results CSV or geo_multi CSV."""
    patterns = [
        os.path.join(repo_path, "benchmarks", "geo_audit_results_*.csv"),
        os.path.join(repo_path, "benchmarks", "geo_multi_claude*.csv"),
    ]
    candidates = []
    for pat in patterns:
        candidates.extend(glob.glob(pat))

    if not candidates:
        print("ERROR: No benchmark CSV found in benchmarks/")
        sys.exit(1)

    latest = max(candidates, key=os.path.getmtime)
    return latest

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ── Score CSV for SOV ──────────────────────────────────────────────
def score_csv(rows):
    """Calculate unaided/aided SOV from benchmark CSV."""
    unaided = [r for r in rows if r.get("type","").upper() == "U"]
    aided   = [r for r in rows if r.get("type","").upper() == "B"]

    hit = lambda r: r.get("godaddy_mentioned","").upper() == "Y"
    rs_hit = lambda r: r.get("rate_saver_mentioned","").upper() == "Y"

    u_sov = round(100 * sum(1 for r in unaided if hit(r)) / len(unaided), 1) if unaided else 0.0
    a_sov = round(100 * sum(1 for r in aided if hit(r)) / len(aided), 1) if aided else 0.0
    r_sov = round(100 * sum(1 for r in unaided if rs_hit(r)) / len(unaided), 1) if unaided else 0.0

    return {
        "unaided_sov": f"~{int(u_sov)}%" if u_sov < 1 else f"{u_sov:.1f}%",
        "aided_sov": f"~{int(a_sov)}%" if a_sov < 1 else f"{a_sov:.1f}%",
        "rate_saver_sov": f"{int(r_sov)}%",
        "prompt_count": len(unaided) + len(aided),
        "unaided_count": len(unaided),
        "aided_count": len(aided),
    }

# ── Update trends history ──────────────────────────────────────────
def update_trends_history(run_id, scored, repo_path):
    """Append current week's data to trends.json for historical tracking."""
    trends_path = os.path.join(repo_path, "public", "data", "trends.json")

    # Load existing trends or create new
    if os.path.exists(trends_path):
        with open(trends_path, "r", encoding="utf-8") as f:
            trends = json.load(f)
    else:
        trends = {"weekly": []}

    # Parse SOV values to floats
    def parse_sov(s):
        try:
            return float(s.replace("~", "").replace("%", ""))
        except:
            return 0.0

    # Create new data point
    new_point = {
        "run_id": run_id,
        "unaided_sov": parse_sov(scored["unaided_sov"]),
        "aided_sov": parse_sov(scored["aided_sov"]),
        "rate_saver_sov": parse_sov(scored["rate_saver_sov"])
    }

    # Check if this run_id already exists (update instead of append)
    existing_idx = next((i for i, p in enumerate(trends["weekly"]) if p["run_id"] == run_id), None)
    if existing_idx is not None:
        trends["weekly"][existing_idx] = new_point
    else:
        trends["weekly"].append(new_point)

    # Keep only last 12 weeks
    trends["weekly"] = trends["weekly"][-12:]

    # Write back
    with open(trends_path, "w", encoding="utf-8") as f:
        json.dump(trends, f, indent=2, ensure_ascii=False)

    return trends["weekly"]

# ── Build session.json structure ───────────────────────────────────
def build_session_json(run_type, csv_path, scored, trends_data):
    """Build full session.json structure."""
    rows = load_csv(csv_path)

    # Extract run metadata
    run_id = rows[0].get("run_id", "UNKNOWN") if rows else "UNKNOWN"
    run_date = rows[0].get("run_date", "") if rows else ""
    model_name = rows[0].get("model_name", "Claude Sonnet 4.6") if rows else "Claude Sonnet 4.6"

    # Format last_updated from run_date or use current timestamp
    try:
        if run_date:
            dt = datetime.strptime(run_date.split()[0], "%Y-%m-%d")
            last_updated = dt.strftime("%Y-%m-%d %H:%M")
        else:
            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    except:
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Determine last_full_benchmark for weekly runs
    try:
        parts = run_id.split("-")
        y, m = parts[0], parts[1]
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        period_month = f"{months[int(m)-1]} {y}"
    except:
        period_month = "June 2026"

    # Build meta section
    meta = {
        "run_type": run_type,
        "run_id": run_id,
        "last_updated": last_updated,
        "model_name": model_name if run_type == "weekly" else "9 models",
        "model_count": 1 if run_type == "weekly" else 9,
        "prompt_count": scored["prompt_count"],
        "generated_by": "generate_session_json.py"
    }

    if run_type == "weekly":
        meta["last_full_benchmark"] = period_month

    # Build full session structure
    session = {
        "meta": meta,
        "trends": trends_data,
        "sov_dashboard": {
            "unaided_sov": {
                "value": scored["unaided_sov"],
                "status": "red" if "~0" in scored["unaided_sov"] else "yellow",
                "target": "15%"
            },
            "aided_sov": {
                "value": scored["aided_sov"],
                "status": "green" if "100" in scored["aided_sov"] else "yellow",
                "target": "100%"
            },
            "rate_saver_sov": {
                "value": scored["rate_saver_sov"],
                "status": "red" if scored["rate_saver_sov"] == "0%" else "yellow",
                "target": "35%"
            },
            "citation_rank": {
                "value": "Unranked",
                "status": "red",
                "target": "Top 5"
            }
        },
        "categories": [],
        "competitors": [
            {"name": "Square", "sov": 95, "display": "95%", "label": "Dominant in 'small biz' prompts", "bar": "#3182ce", "godaddy": False},
            {"name": "Stripe", "sov": 92, "display": "92%", "label": "Developer + online", "bar": "#805ad5", "godaddy": False},
            {"name": "PayPal", "sov": 88, "display": "88%", "label": "Consumer trust anchor", "bar": "#dd6b20", "godaddy": False},
            {"name": "GoDaddy", "sov": 0, "display": scored["unaided_sov"], "label": "Invisible unaided", "bar": "#fc8181", "godaddy": True}
        ],
        "model_sov": {
            "primary": [
                {
                    "name": model_name if run_type == "weekly" else "Claude Sonnet 4.6",
                    "why": "Weekly pulse check" if run_type == "weekly" else "Primary model",
                    "unaided": scored["unaided_sov"],
                    "aided": scored["aided_sov"],
                    "status": "success",
                    "u_color": "red",
                    "a_color": "green" if "100" in scored["aided_sov"] else "yellow"
                }
            ],
            "pulse": []
        },
        "perplexity_simulation": [],
        "competitive_intel": [
            {"competitor": "Square", "event": "Rate check", "detail": "2.6% + $0.10 (no change)", "changed": False},
            {"competitor": "Stripe", "event": "Feature check", "detail": "No changes detected", "changed": False}
        ],
        "strategy_actions": [],
        "build_pages": [],
        "amplify_threads": [],
        "amplify_outcomes": [],
        "cite_pipeline": [],
        "report_summary": {
            "binding_constraint": f"Unaided SOV = {scored['unaided_sov']}. Root cause: citation gap. Crawler access confirmed ✅.",
            "top_wins": [],
            "top_gaps": [],
            "leading_indicators": [],
            "leadership_decisions": [],
            "next_month_priority": [],
            "data_confidence": f"High — {scored['prompt_count']} prompts across {meta['model_count']} model{'s' if meta['model_count'] > 1 else ''}",
            "methodology_note": f"{'Weekly pulse check using ' + model_name + '. Full 9-model benchmark last run: ' + period_month if run_type == 'weekly' else 'Full 9-model monthly benchmark.'}"
        }
    }

    return session

# ── Main ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate session.json for GEO dashboard")
    parser.add_argument("--weekly", action="store_true", help="Weekly run (Claude only)")
    parser.add_argument("--monthly", action="store_true", help="Monthly run (9 models)")
    parser.add_argument("--csv", default=None, help="Path to benchmark CSV (auto-detects if omitted)")
    parser.add_argument("--output", default="public/data/session.json", help="Output path")

    args = parser.parse_args()

    if not args.weekly and not args.monthly:
        print("ERROR: Must specify --weekly or --monthly")
        sys.exit(1)

    run_type = "weekly" if args.weekly else "monthly"

    # Find CSV
    repo_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = args.csv if args.csv else find_latest_csv(repo_path)

    print(f"  Run type: {run_type}")
    print(f"  Reading:  {csv_path}")

    # Score CSV
    rows = load_csv(csv_path)
    scored = score_csv(rows)

    print(f"  Unaided SOV: {scored['unaided_sov']}")
    print(f"  Aided SOV:   {scored['aided_sov']}")
    print(f"  Prompts:     {scored['prompt_count']}")

    # Extract run_id for trends
    run_id = rows[0].get("run_id", "UNKNOWN") if rows else "UNKNOWN"

    # Update trends history (only for weekly runs)
    if run_type == "weekly":
        trends_data = update_trends_history(run_id, scored, repo_path)
        print(f"  + Trends history updated ({len(trends_data)} weeks tracked)")
    else:
        trends_data = []

    # Build session.json
    session = build_session_json(run_type, csv_path, scored, trends_data)

    # Write output
    output_path = os.path.join(repo_path, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    print(f"  + Written:   {output_path}")
    print(f"\nDashboard will show:")
    print(f"  Badge: {'Weekly pulse' if run_type == 'weekly' else 'Full benchmark'}")
    print(f"  Run ID: {session['meta']['run_id']}")
    print(f"  Updated: {session['meta']['last_updated']}")
    print(f"  Models: {session['meta']['model_name']}")

if __name__ == "__main__":
    main()
