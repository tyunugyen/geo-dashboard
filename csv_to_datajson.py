#!/usr/bin/env python3
"""
=============================================================================
csv_to_datajson.py
Converts geo_audit_benchmark.py CSV output into the GEO Dashboard data.json
=============================================================================

WHAT IT DOES
------------
Reads geo_audit_results_[RUN_ID].csv (the benchmark output) and produces
public/data.json — the single file that drives the dashboard. After running
this, just refresh the dashboard. You never edit the HTML.

HOW TO RUN
----------
1. Run the benchmark first:
       python geo_audit_benchmark.py
   (produces geo_audit_results_2026-07-RUN-1.csv)

2. Run this converter:
       python csv_to_datajson.py geo_audit_results_2026-07-RUN-1.csv

   Optional flags:
       --out public/data.json     (where to write — default: ./data.json)
       --label "Month 2"          (header label — default: auto from run_id)
       --prior 0                  (prior month's unaided SOV % for delta — optional)

3. Copy the new data.json into your dashboard's public/ folder and refresh.

NOTES
-----
- Only UNAIDED (type=U) prompts count toward Unaided SOV — aided are separated.
- Competitor SOV and aggregator labels are NOT in the benchmark CSV, so the
  script PRESERVES whatever is already in your existing data.json for those.
  Pass --keep existing_data.json to carry them forward (recommended).
- Color thresholds: red <33% of target, yellow 33-80%, green >80%.
=============================================================================
"""

import csv
import json
import sys
import argparse
import datetime


# Category 9-month targets (from the GEO Prompt Bank). Used if CSV lacks target_sov.
# v2.6: two-phase targets — phase1 = 6-month gate, phase2 = 12-month gate (north-star)
CATEGORY_TARGETS = {
    "pricing_fee":        {"phase1": 25, "phase2": 85},
    "top_funnel_pos":     {"phase1": 20, "phase2": 60},
    "payment_processing": {"phase1": 20, "phase2": 55},
    "vertical_fb":        {"phase1": 18, "phase2": 50},
    "vertical_retail":    {"phase1": 22, "phase2": 55},
    "general_in_person":  {"phase1": 18, "phase2": 50},  # replaces vertical_salon + hardware
    "support":            {"phase1": 25, "phase2": 65},
    "comparison":         {"phase1": 25, "phase2": 70},
    "brand_awareness":    {"phase1": 100,"phase2": 100},
}

# Display order for category heatmap
# v2.6 order: hardware removed, vertical_salon → general_in_person
CATEGORY_ORDER = [
    "pricing_fee", "top_funnel_pos", "payment_processing", "vertical_fb",
    "vertical_retail", "general_in_person", "support", "comparison",
]


def color_for(pct, target):
    """Traffic-light color based on progress toward the 9-month target."""
    if target <= 0:
        return "#68d391", "green"
    ratio = pct / target
    if ratio < 0.33:
        return "#fc8181", "red"
    elif ratio < 0.80:
        return "#f6e05e", "yellow"
    return "#68d391", "green"


def pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_data(rows, label=None, prior=None, keep=None):
    # --- Run metadata (from first row) ---
    run_id = rows[0].get("run_id", "UNKNOWN-RUN") if rows else "UNKNOWN-RUN"
    # Derive a human period from run_id like 2026-07-RUN-1
    period = "Unknown"
    try:
        ym = run_id.split("-RUN")[0]            # 2026-07
        y, m = ym.split("-")
        period = datetime.date(int(y), int(m), 1).strftime("%B %Y")
    except Exception:
        pass
    if not label:
        label = "Baseline" if run_id.endswith("RUN-1") else "Monthly"

    # --- Split unaided vs aided ---
    unaided = [r for r in rows if r.get("type", "").strip().upper() == "U"]
    aided   = [r for r in rows if r.get("type", "").strip().upper() == "B"]

    def mentioned(r):
        return r.get("godaddy_mentioned", "").strip().upper() == "Y"

    unaided_sov = pct(sum(1 for r in unaided if mentioned(r)), len(unaided))
    aided_sov   = pct(sum(1 for r in aided   if mentioned(r)), len(aided))

    # Rate Saver cited (unaided prompts only)
    rs_cited = sum(1 for r in unaided
                   if r.get("rate_saver_mentioned", "").strip().upper() == "Y")
    rs_sov = pct(rs_cited, len(unaided))

    # --- KPIs ---
    u_color, _ = color_for(unaided_sov, 40)      # north-star target 40%
    a_color, _ = color_for(aided_sov, 100)
    rs_color, _ = color_for(rs_sov, 50)          # rate saver target 50%

    def kpi_val(v):
        return f"{v:.0f}%" if v == int(v) else f"{v}%"

    kpis = {
        "unaided_sov": {"value": kpi_val(unaided_sov), "fill": round(unaided_sov), "color": u_color},
        "aided_sov":   {"value": kpi_val(aided_sov),   "fill": round(aided_sov),   "color": a_color},
        # helcim_gap preserved from existing data unless you compute it elsewhere
        "helcim_gap":  (keep or {}).get("kpis", {}).get("helcim_gap",
                        {"value": "25pts", "fill": 0, "color": "#f6e05e"}),
        "tech_health": {"value": kpi_val(rs_sov), "fill": round(rs_sov), "color": rs_color},  # = Rate Saver Cited
    }

    # --- Categories ---
    cat_stats = {}
    for r in unaided:
        c = r.get("category", "").strip()
        if not c:
            continue
        cat_stats.setdefault(c, {"hit": 0, "total": 0, "target": 0})
        cat_stats[c]["total"] += 1
        if mentioned(r):
            cat_stats[c]["hit"] += 1
        try:
            # Use phase2 as the benchmark target (12-month gate = north-star)
            raw = r.get("target_sov", 0)
            cat_stats[c]["target"] = int(float(raw)) if raw else CATEGORY_TARGETS.get(c, {}).get("phase2", 50)
        except Exception:
            cat_stats[c]["target"] = CATEGORY_TARGETS.get(c, {}).get("phase2", 50)

    categories = []
    ordered = [c for c in CATEGORY_ORDER if c in cat_stats] + \
              [c for c in cat_stats if c not in CATEGORY_ORDER]
    for c in ordered:
        s = cat_stats[c]
        sov = pct(s["hit"], s["total"])
        tgt_info = CATEGORY_TARGETS.get(c, {"phase1": 20, "phase2": 50})
        tgt_p1 = tgt_info.get("phase1", 20) if isinstance(tgt_info, dict) else tgt_info
        tgt_p2 = s["target"] or (tgt_info.get("phase2", 50) if isinstance(tgt_info, dict) else tgt_info)
        _, cell = color_for(sov, tgt_p1)  # color vs phase1 gate (6-month milestone)
        categories.append({
            "name": c,
            "sov": f"{sov:.0f}%" if sov == int(sov) else f"{sov}%",
            "phase1": f"{tgt_p1}%",
            "target": f"{tgt_p2}%",
            "cell": cell,
        })

    # --- Competitors + aggregator labels: preserved from existing data.json ---
    competitors = (keep or {}).get("competitors", [])

    data = {
        "meta": {
            "label": label,
            "period": period,
            "run_id": run_id,
            "sources": "Claude (verified) + Citation + Community",
        },
        "kpis": kpis,
        "categories": categories,
        "competitors": competitors,
    }

    # Delta note if prior provided
    if prior is not None:
        delta = round(unaided_sov - float(prior), 1)
        data["meta"]["unaided_delta"] = f"{'+' if delta >= 0 else ''}{delta}pts vs prior"

    return data, {
        "unaided_sov": unaided_sov, "aided_sov": aided_sov,
        "rate_saver": rs_sov, "categories": len(categories),
        "unaided_prompts": len(unaided), "aided_prompts": len(aided),
    }


def main():
    ap = argparse.ArgumentParser(description="Convert benchmark CSV to dashboard data.json")
    ap.add_argument("csv_path", help="geo_audit_results_[RUN_ID].csv")
    ap.add_argument("--out", default="data.json", help="output path (default: data.json)")
    ap.add_argument("--label", default=None, help="header label e.g. 'Month 2'")
    ap.add_argument("--prior", default=None, help="prior month unaided SOV %% for delta")
    ap.add_argument("--keep", default=None,
                    help="existing data.json to preserve competitors/aggregator labels")
    args = ap.parse_args()

    rows = load_rows(args.csv_path)
    if not rows:
        print("ERROR: CSV is empty.")
        sys.exit(1)

    keep = None
    if args.keep:
        try:
            with open(args.keep, encoding="utf-8") as f:
                keep = json.load(f)
            print(f"Preserving competitors + labels from {args.keep}")
        except Exception as e:
            print(f"WARNING: could not read --keep file ({e}). Competitors will be empty.")

    data, summary = build_data(rows, label=args.label, prior=args.prior, keep=keep)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 60)
    print("  data.json generated")
    print("=" * 60)
    print(f"  Run ID          : {data['meta']['run_id']}")
    print(f"  Period          : {data['meta']['period']}")
    print(f"  Unaided SOV     : {summary['unaided_sov']}%  ({summary['unaided_prompts']} prompts)")
    print(f"  Aided SOV       : {summary['aided_sov']}%  ({summary['aided_prompts']} prompts)")
    print(f"  Rate Saver cited: {summary['rate_saver']}%")
    print(f"  Categories      : {summary['categories']}")
    if not data["competitors"]:
        print("  ⚠️  Competitors empty — re-run with --keep public/data.json to preserve them.")
    print(f"\n  Written to: {args.out}")
    print("  Next: copy into dashboard public/ folder and refresh.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
