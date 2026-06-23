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
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

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
        ym = run_id.split("-RUN")[0]
        y, m = ym.split("-")
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        period = f"{months[int(m)-1]} {y}"
    except Exception:
        pass

    u_col, _ = color_for(u_sov, "40%")
    a_col    = "#68d391" if a_sov >= 90 else "#f6e05e" if a_sov >= 70 else "#fc8181"
    r_col, _ = color_for(r_sov, "25%")
    return dict(
        run_id=run_id, period=period,
        u_sov=u_sov, a_sov=a_sov, r_sov=r_sov,
        u_col=u_col, a_col=a_col, r_col=r_col,
        categories=categories,
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
        "categories":  s["categories"],
        "competitors": existing.get("competitors", []),
    }
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
    ap.add_argument("csv_path",           help="geo_audit_results_[RUN_ID].csv")
    ap.add_argument("--repo",   default=".", help="Path to repo root (default: current dir)")
    ap.add_argument("--label",  default=None)
    ap.add_argument("--prior",  default=None, type=float)
    ap.add_argument("--dry-run", action="store_true", help="Update data.json but do not commit/push")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    data_json_path = os.path.join(repo, "public", "data.json")

    # Validate inputs
    if not os.path.exists(args.csv_path):
        print(f"ERROR: CSV not found: {args.csv_path}"); sys.exit(1)
    if not os.path.exists(data_json_path):
        print(f"ERROR: data.json not found at {data_json_path}"); sys.exit(1)

    # Score CSV
    print(f"\n  Reading:  {args.csv_path}")
    rows = load_csv(args.csv_path)
    if not rows:
        print("ERROR: CSV is empty"); sys.exit(1)
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
    shutil.copy2(args.csv_path, csv_dest)
    print(f"  Copied CSV to: benchmarks/{os.path.basename(args.csv_path)}")

    steps = [
        (["add", "public/data.json"],
         "Staging data.json"),
        (["add", "-f", f"benchmarks/{os.path.basename(args.csv_path)}"],
         "Staging CSV"),
        (["commit", "-m", commit_msg],     "Committing"),
        (["push"],                          "Pushing to GitHub → PaaS will redeploy"),
    ]
    for git_args, label in steps:
        print(f"  {label}...", end=" ", flush=True)
        ok = run_git(git_args, cwd=repo, dry_run=args.dry_run)
        print("✅" if ok else "❌")
        if not ok:
            print("\n  Push failed. Check git is set up: git remote -v")
            sys.exit(1)

    print(f"\n  ✅ Done. PaaS will redeploy in ~30 seconds.")
    print(f"  Dashboard: https://host.beta.godaddy.com/paas/projects/kz6jwep09q")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
