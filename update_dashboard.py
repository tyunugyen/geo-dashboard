#!/usr/bin/env python3
"""
=============================================================================
update_dashboard.py  (GitHub-connected version)
=============================================================================
One command:  python update_dashboard.py geo_audit_results_2026-07-RUN-1.csv

What it does:
  1. Scores your benchmark CSV
  2. Updates public/data.json with new SOV metrics
  3. git commit + git push  →  GoDaddy PaaS auto-redeploys from GitHub

Requirements:
  - Git installed and configured on your machine
  - This script lives in the root of your geo-dashboard repo
  - GitHub repo connected to GoDaddy PaaS (one-time setup)

Options:
  --repo   PATH    Path to repo root        (default: current directory)
  --prior  FLOAT   Prior month unaided SOV%  (optional, for delta display)
  --label  TEXT    Header label e.g. "Month 2" (default: auto from run ID)
  --dry-run        Score and update data.json but do NOT commit or push
=============================================================================
"""

import sys, os, json, csv, argparse, subprocess, datetime

# ── Category config (mirrors server.js) ──────────────────────────
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
    "pricing_fee", "top_funnel_pos", "payment_processing",
    "vertical_fb", "vertical_retail", "general_in_person",
    "support", "comparison",
]

# ── Helpers ───────────────────────────────────────────────────────
def pct(n, d):   return round(1000 * n / d) / 10 if d else 0.0
def fmt(v):      return f"{v:.0f}%" if v == int(v) else f"{v:.1f}%"
def color_for(sov, p1_str):
    p1 = float(p1_str.strip("%")) or 20
    r  = sov / p1 if p1 else 0
    if r < 0.33: return "#fc8181", "red"
    if r < 0.80: return "#f6e05e", "yellow"
    return "#68d391", "green"

def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def score_comparison(rows, csv_filename=""):
    """Score a geo_multi_comparison_*.csv — builds multi-model SOV table."""
    import re

    def parse_pct(s):
        try: return float(str(s).strip("%"))
        except: return 0.0

    STATUS_COLOR = {"success": "#68d391", "partial": "#f6e05e", "anomaly": "#fc8181", "error": "#fc8181"}

    # Extract run_id from filename if available
    run_id  = "2026-06-W26"
    if csv_filename:
        match = re.search(r"(\d{4}-\d{2}-W\d{2})", csv_filename)
        if match:
            run_id = match.group(1)

    # Derive period from run_id
    if run_id:
        match = re.match(r"(\d{4})-(\d{2})-W(\d{2})", run_id)
        if match:
            year, month, week = match.groups()
            months = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
            period = f"{months[int(month)-1]} {year}"
        else:
            period = "June 2026"
    else:
        period  = "June 2026"

    run_date = ""
    model_sov = {}

    # Use minimum across all successful models for overall SOV (conservative estimate)
    u_sov, a_sov, r_sov = 0.0, 0.0, 0.0
    success_models = [r for r in rows if r.get("status","") == "success"]
    if success_models:
        u_sov = min(parse_pct(r.get("unaided_sov","0")) for r in success_models)
        a_sov = min(parse_pct(r.get("aided_sov","0")) for r in success_models)
        r_sov = min(parse_pct(r.get("rate_saver_sov","0")) for r in success_models)

    for r in rows:
        mid   = r.get("model_id", r.get("model_name","")).lower().replace("-","_").replace(".","_").replace(" ","_")
        mname = r.get("model_name", mid)
        aided = parse_pct(r.get("aided_sov","0"))
        a_color = "#68d391" if aided >= 90 else "#f6e05e" if aided >= 60 else "#fc8181"
        status = r.get("status","success")
        model_sov[mid] = {
            "name":    mname,
            "unaided": r.get("unaided_sov","0%"),
            "aided":   r.get("aided_sov","0%"),
            "rs":      r.get("rate_saver_sov","0%"),
            "status":  status,
            "note":    "",
            "u_color": "#fc8181",
            "a_color": a_color,
        }

    models_str = ", ".join(r.get("model_name","") for r in rows if r.get("model_name"))

    def fmt(v): return f"{v:.0f}%" if v == int(v) else f"{v:.1f}%"
    def color_for(sov, p1=40):
        r = sov/p1 if p1 else 0
        if r < 0.33: return "#fc8181","red"
        if r < 0.80: return "#f6e05e","yellow"
        return "#68d391","green"

    u_col,_ = color_for(u_sov)
    a_col   = "#68d391" if a_sov >= 90 else "#f6e05e" if a_sov >= 70 else "#fc8181"
    r_col,_ = color_for(r_sov, 25)

    # Build category list from existing data.json
    categories = []

    return dict(
        run_id=run_id, period=period, run_date=run_date,
        u_sov=u_sov, a_sov=a_sov, r_sov=r_sov,
        u_col=u_col, a_col=a_col, r_col=r_col,
        categories=categories, model_sov=model_sov,
        models_str=models_str, promptCount=70,
        u_count=63, a_count=7,
    )


def score(rows):
    unaided = [r for r in rows if r.get("type","").upper() == "U"]
    aided   = [r for r in rows if r.get("type","").upper() == "B"]
    hit     = lambda r: r.get("godaddy_mentioned","").upper() == "Y"
    rs_hit  = lambda r: r.get("rate_saver_mentioned","").upper() == "Y"

    u_sov = pct(sum(1 for r in unaided if hit(r)), len(unaided))
    a_sov = pct(sum(1 for r in aided   if hit(r)), len(aided))
    r_sov = pct(sum(1 for r in unaided if rs_hit(r)), len(unaided))

    cat_map = {}
    for r in unaided:
        c = r.get("category","").strip()
        if not c: continue
        cat_map.setdefault(c, {"hit": 0, "total": 0})
        cat_map[c]["total"] += 1
        if hit(r): cat_map[c]["hit"] += 1

    ordered = [c for c in CATEGORY_ORDER if c in cat_map] +               [c for c in cat_map if c not in CATEGORY_ORDER]
    categories = []
    for c in ordered:
        s    = cat_map[c]
        sov  = pct(s["hit"], s["total"])
        tgt  = CATEGORY_TARGETS.get(c, {"phase1": "20%", "target": "50%"})
        col, cell = color_for(sov, tgt["phase1"])
        categories.append({
            "name": c, "sov": fmt(sov),
            "phase1": tgt["phase1"], "target": tgt["target"],
            "cell": cell,
        })

    run_id = rows[0].get("run_id", "UNKNOWN") if rows else "UNKNOWN"
    period = "Unknown"
    try:
        # Handle both formats: "2026-06-RUN-1" and "2026-06-W26"
        parts = run_id.split("-")
        y, m = parts[0], parts[1]
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        period = f"{months[int(m)-1]} {y}"
    except Exception:
        pass

    u_col, _ = color_for(u_sov, "40%")
    a_col    = "#68d391" if a_sov >= 90 else "#f6e05e" if a_sov >= 70 else "#fc8181"
    r_col, _ = color_for(r_sov, "25%")

    # Per-model SOV (from multi-model CSV — uses 'model' or 'model_name' column)
    model_sov = {}
    model_col = "model_name" if rows and "model_name" in rows[0] else "model"
    models_seen = list(dict.fromkeys(r.get(model_col, "") for r in rows if r.get(model_col)))
    for mname in models_seen:
        mrows = [r for r in unaided if r.get(model_col, "") == mname]
        if not mrows: continue
        m_sov = pct(sum(1 for r in mrows if hit(r)), len(mrows))
        m_col, _ = color_for(m_sov, "40%")
        ml = mname.lower()
        key = ("claude"  if "claude"  in ml else
               "chatgpt" if any(x in ml for x in ["gpt","openai"]) else
               "gemini"  if "gemini"  in ml else
               ml.replace(" ","_").replace("-","_"))
        model_sov[key] = {"value": fmt(m_sov), "color": m_col}

    # Models string for meta
    models_str = ", ".join(models_seen) if models_seen else "Claude Sonnet 4.6, Claude Haiku 4.5, GPT-4o, Gemini 2.5 Pro"

    return dict(
        run_id=run_id, period=period,
        u_sov=u_sov, a_sov=a_sov, r_sov=r_sov,
        u_col=u_col, a_col=a_col, r_col=r_col,
        categories=categories, model_sov=model_sov, models_str=models_str,
        u_count=len(unaided), a_count=len(aided),
    )

def build_data_json(s, existing, label=None, prior=None):
    data = {
        "meta": {
            "label":               label or "Monthly",
            "period":              s["period"],
            "run_id":              s["run_id"],
            "sources":             "Benchmark CSV",
            "prompt_bank_version": existing.get("meta", {}).get("prompt_bank_version", "2.6"),
        },
        "kpis": {
            "unaided_sov": {"value": fmt(s["u_sov"]), "fill": round(s["u_sov"]), "color": s["u_col"]},
            "aided_sov":   {"value": fmt(s["a_sov"]), "fill": round(s["a_sov"]), "color": s["a_col"]},
            "helcim_gap":  existing.get("kpis", {}).get("helcim_gap",
                           {"value": "25pts", "fill": 0, "color": "#f6e05e"}),
            "tech_health": {"value": fmt(s["r_sov"]), "fill": round(s["r_sov"]), "color": s["r_col"]},
        },
        "categories":  s.get("categories") or existing.get("categories",[]),
        "competitors": existing.get("competitors", []),
        "model_sov":   s.get("model_sov", {}),
    }
    data["meta"]["models"]    = s.get("models_str", "Claude Sonnet 4.6, Claude Haiku 4.5, GPT-4o, Gemini 2.5 Pro")
    data["meta"]["sources"]   = s.get("models_str", "9-model benchmark") + " (GoCode proxy)"
    if s.get("run_date"): data["meta"]["run_date"] = s["run_date"]
    if s.get("promptCount"): data["meta"]["prompt_count"] = s["promptCount"]
    if prior is not None:
        delta = round(s["u_sov"] - float(prior), 1)
        data["meta"]["unaided_delta"] = f"{'+' if delta >= 0 else ''}{delta}pts vs prior"
    return data

def run_git(args, cwd, dry_run=False):
    cmd = ["git"] + args
    if dry_run:
        print(f"  [dry-run] would run: {' '.join(cmd)}")
        return True
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  git error: {result.stderr.strip()}")
        return False
    return True

def main():
    ap = argparse.ArgumentParser(description="Score benchmark CSV and push data.json to GitHub")
    ap.add_argument("csv_path", nargs="?", default=None,
                    help="geo_audit_results_[RUN_ID].csv (auto-detects latest if omitted)")
    ap.add_argument("--repo",   default=".", help="Path to repo root (default: current dir)")
    ap.add_argument("--label",  default=None)
    ap.add_argument("--prior",  default=None, type=float)
    ap.add_argument("--dry-run", action="store_true", help="Update data.json but do not commit/push")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    data_json_path = os.path.join(repo, "public", "data.json")

    # Auto-detect latest CSV if not specified
    if args.csv_path is None:
        import glob
        # Priority order: detailed results first, comparison summary last
        # geo_audit_results_* has full prompt-level data (type, category, godaddy_mentioned)
        # geo_multi_comparison_* is model-level summary only — NOT suitable for scoring
        priority_patterns = [
            os.path.join(repo, "benchmarks", "geo_audit_results_*.csv"),
            "geo_audit_results_*.csv",
            os.path.join(repo, "benchmarks", "geo_multi_*.csv"),
        ]
        candidates = []
        for pat in priority_patterns:
            matches = [f for f in glob.glob(pat) if "comparison" not in f]
            candidates.extend(matches)
        # Fall back to any CSV in benchmarks if nothing found above
        if not candidates:
            candidates = glob.glob(os.path.join(repo, "benchmarks", "*.csv"))
            candidates = [f for f in candidates if "comparison" not in f]
        if not candidates:
            print("ERROR: No detailed results CSV found.")
            print("Run geo_benchmark_runner.py or geo_benchmark_multi_model.py first.")
            print("Note: geo_multi_comparison_*.csv cannot be used — pass a detailed CSV explicitly.")
            sys.exit(1)
        args.csv_path = max(candidates, key=os.path.getmtime)
        print(f"  Auto-detected: {args.csv_path}")

    # Validate inputs
    if not os.path.exists(args.csv_path):
        print(f"ERROR: CSV not found: {args.csv_path}"); sys.exit(1)

    # Detect if this is a comparison summary CSV (geo_multi_comparison_*.csv)
    is_comparison = "comparison" in os.path.basename(args.csv_path)
    if is_comparison:
        print(f"  Detected: multi-model comparison CSV")
        print(f"  Will build model_sov table from all model rows")
    if not os.path.exists(data_json_path):
        print(f"ERROR: data.json not found at {data_json_path}"); sys.exit(1)

    # Score CSV
    print(f"\n  Reading:  {args.csv_path}")
    rows = load_csv(args.csv_path)
    if not rows:
        print("ERROR: CSV is empty"); sys.exit(1)

    if is_comparison:
        # Comparison CSV: model_id, model_name, unaided_sov, aided_sov, rate_saver_sov, status
        scored = score_comparison(rows, os.path.basename(args.csv_path))
    else:
        missing = [k for k in ["type","category","godaddy_mentioned"] if k not in rows[0]]
        if missing:
            print(f"ERROR: CSV missing columns: {', '.join(missing)}"); sys.exit(1)
        scored = score(rows)

    # Load existing data.json to preserve competitors
    with open(data_json_path) as f:
        existing = json.load(f)

    new_data = build_data_json(scored, existing, label=args.label, prior=args.prior)

    # Write data.json
    with open(data_json_path, "w") as f:
        json.dump(new_data, f, indent=2)
    print(f"  Updated:  {data_json_path}")

    # Update data_monthly.json (used by dashboard)
    data_monthly_path = os.path.join(repo, "public", "data_monthly.json")
    if os.path.exists(data_monthly_path):
        with open(data_monthly_path, encoding="utf-8-sig") as f:
            monthly = json.load(f)

        # Update main sections from new_data
        monthly["meta"] = new_data["meta"]
        monthly["kpis"] = new_data["kpis"]
        monthly["categories"] = new_data["categories"]
        if "model_sov" in new_data:
            monthly["model_sov"] = new_data["model_sov"]
        if "competitors" in new_data:
            monthly["competitors"] = new_data["competitors"]

        # Add new trend point
        if "trends" not in monthly:
            monthly["trends"] = {"monthly": [], "weekly": []}

        new_trend = {
            "run_id": scored["run_id"],
            "unaided_sov": scored["u_sov"],
            "aided_sov": scored["a_sov"],
            "rate_saver_sov": scored["r_sov"]
        }

        # Append to weekly trends (always)
        monthly["trends"]["weekly"].append(new_trend)

        # Append to monthly trends only if it's a monthly run (not a weekly pulse)
        if "monthly" in scored.get("label", "").lower() or scored["run_id"].endswith("W27"):
            monthly["trends"]["monthly"].append(new_trend)

        with open(data_monthly_path, "w", encoding="utf-8") as f:
            json.dump(monthly, f, indent=2, ensure_ascii=False)
        print(f"  Updated:  {data_monthly_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Run ID        : {scored['run_id']}")
    print(f"  Period        : {scored['period']}")
    print(f"  Unaided SOV   : {fmt(scored['u_sov'])}  ({scored['u_count']} prompts)")
    print(f"  Aided SOV     : {fmt(scored['a_sov'])}  ({scored['a_count']} prompts)")
    print(f"  Rate Saver    : {fmt(scored['r_sov'])}")
    if "unaided_delta" in new_data.get("meta", {}):
        print(f"  Delta         : {new_data['meta']['unaided_delta']}")

    if args.dry_run:
        print(f"\n  [dry-run] data.json updated — skipping git commit/push")
        print(f"{'='*60}\n")
        return

    # Git: stage, commit, push
    print(f"\n  Committing to git...")
    commit_msg = f"GEO benchmark: {scored['run_id']} | Unaided SOV {fmt(scored['u_sov'])} | {scored['u_count']} unaided prompts"

    # Copy CSV into repo under benchmarks/ for audit trail
    import shutil
    benchmarks_dir = os.path.join(repo, "benchmarks")
    os.makedirs(benchmarks_dir, exist_ok=True)
    csv_dest = os.path.join(benchmarks_dir, os.path.basename(args.csv_path))
    # Use read/write instead of shutil.copy2 to avoid Windows file lock errors
    if os.path.abspath(args.csv_path) != os.path.abspath(csv_dest):
        try:
            with open(args.csv_path, "r", encoding="utf-8") as src_f:
                content = src_f.read()
            with open(csv_dest, "w", encoding="utf-8") as dst_f:
                dst_f.write(content)
            print(f"  Copied CSV to: benchmarks/{os.path.basename(args.csv_path)}")
        except PermissionError:
            print(f"  ⚠️  CSV already in benchmarks/ (file in use) — skipping copy")
    else:
        print(f"  CSV already in benchmarks/ — no copy needed")

    steps = [
        (["add", "public/data.json"],
         "Staging data.json"),
        (["add", "public/data_monthly.json"],
         "Staging data_monthly.json"),
        (["add", "-f", f"benchmarks/{os.path.basename(args.csv_path)}"],
         "Staging CSV"),
        (["commit", "-m", commit_msg],     "Committing"),
        (["push", "origin", "main"],        "Pushing to GitHub - PaaS will redeploy"),
    ]
    for git_args, label in steps:
        print(f"  {label}...", end=" ", flush=True)
        ok = run_git(git_args, cwd=repo, dry_run=args.dry_run)
        print("[OK]" if ok else "[FAIL]")
        if not ok:
            print("\n  Push failed. Check git is set up: git remote -v")
            sys.exit(1)

    print(f"\n  [DONE] PaaS will redeploy in ~30 seconds.")
    print(f"  Dashboard: https://host.beta.godaddy.com/paas/projects/kz6jwep09q")
    print(f"{'='*60}\n")

    print(f"  Next: open Claude and say \"Run monthly GEO session.\" — I will pull context from Notes automatically.")

if __name__ == "__main__":
    main()
