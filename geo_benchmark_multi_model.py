#!/usr/bin/env python3
"""
geo_benchmark_multi_model.py
Runs GEO benchmark suite against multiple models (Claude, GPT, Gemini, etc.)
and compares results to identify which models mention GoDaddy Payments.

Usage:
    python geo_benchmark_multi_model.py                    # Run all models
    python geo_benchmark_multi_model.py --model gpt-4o     # Run specific model
    python geo_benchmark_multi_model.py --models claude openai  # Run specific groups
"""

import os, sys, csv, json, re, datetime, time, argparse
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────
# Use internal URL (works on VPN) - self-hosted runner has VPN access
PROXY_URL    = "https://caas-gocode-prod.caas-prod.prod.onkatana.net"
MAX_TOKENS   = 600
TEMPERATURE  = 0.2
DELAY_SECS   = 0.5   # polite delay between calls

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question directly and concisely."
)

# Model groups for benchmarking - 8 total: 5 primary + 3 pulse
# Primary = main monthly benchmark, Pulse = tracking signals
MODEL_GROUPS = {
    "primary": [
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6"},
        {"id": "claude-opus-4-8", "name": "Claude Opus 4.8"},
        {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
    ],
    "pulse": [
        {"id": "o3", "name": "o3"},
        {"id": "o3-mini", "name": "o3-mini"},
        {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro Preview"},
    ],
    # Legacy groups for backwards compatibility
    "claude": [
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6"},
        {"id": "claude-opus-4-8", "name": "Claude Opus 4.8"},
        {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
    ],
    "all": None,  # Will be computed from primary + pulse
}

# All models = primary + pulse (8 total)
ALL_MODELS = MODEL_GROUPS["primary"] + MODEL_GROUPS["pulse"]

# ── Category targets (v2.6) ───────────────────────────────────────────
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

# ── All 70 prompts (v2.6) ─────────────────────────────────────────────
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
    # TIER 5 (Branded - aided)
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

# ── Scoring helpers ───────────────────────────────────────────────────
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

# ── Run benchmark for a single model ──────────────────────────────────
def run_model_benchmark(model_info, api_key, verbose=True):
    """Run benchmark against a single model"""
    model_id = model_info["id"]
    model_name = model_info["name"]

    client = OpenAI(api_key=api_key, base_url=PROXY_URL, timeout=60.0)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-W%V")
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = []

    if verbose:
        print(f"\n{'='*60}")
        print(f"Model: {model_name} ({model_id})")
        print(f"Run ID: {run_id} | {len(PROMPTS)} prompts")
        print(f"{'='*60}")

    # Test connection
    if verbose:
        print("  Testing connection...", end=" ", flush=True)
    try:
        test = client.chat.completions.create(
            model=model_id, max_tokens=20, temperature=0,
            messages=[{"role":"user","content":"Say OK"}]
        )
        test_resp = test.choices[0].message.content if test.choices else ""
        if verbose:
            print(f"[OK] Connected")
    except Exception as e:
        if verbose:
            print(f"\n[FAIL] Connection FAILED: {e}")
        return None, f"Connection failed: {e}"

    # Run all prompts
    for i, (pid, ptype, pcat, ptgt, ptext) in enumerate(PROMPTS, 1):
        if verbose:
            print(f"  [{i:2}/{len(PROMPTS)}] {pid}: {ptext[:50]}...", end=" ", flush=True)

        try:
            msg = client.chat.completions.create(
                model=model_id,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user",  "content":ptext},
                ]
            )
            response = msg.choices[0].message.content if msg.choices else ""
            err = ""
        except Exception as e:
            response = ""
            err = f"[ERROR: {e}]"
            if verbose:
                print(f" ERROR: {e}")

        if not response and not err:
            err = "[ERROR: empty response from API]"

        # Detect GoDaddy mentions and other metrics
        gd = "Y" if detect_godaddy(response) else "N"
        rs = "Y" if detect_rate_saver(response) else "N"
        comps = detect_competitors(response)
        rate_acc = "Y" if (gd=="Y" and detect_rate_accurate(response)) else ("N" if gd=="Y" else "N/A")
        excerpt = (response[:300].replace("\n"," ") if response else err)

        rows.append({
            "run_id": run_id,
            "run_date": run_date,
            "model_id": model_id,
            "model_name": model_name,
            "prompt_id": pid,
            "type": ptype,
            "category": pcat,
            "target_sov": ptgt,
            "prompt_text": ptext,
            "godaddy_mentioned": gd,
            "rate_accurate": rate_acc,
            "rate_saver_mentioned": rs,
            "competitors_cited": comps,
            "response_excerpt": excerpt,
        })

        if verbose:
            if ptype == "B":
                status = "[OK] GD" if gd=="Y" else "[FAIL] No GD"
            else:
                status = "[OK] GD" if gd=="Y" else "-"
            print(status)

        time.sleep(DELAY_SECS)

    return rows, None

# ── Calculate summary stats ───────────────────────────────────────────
def calculate_summary(rows):
    """Calculate SOV and other metrics for a model's results"""
    unaided = [r for r in rows if r["type"]=="U"]
    aided = [r for r in rows if r["type"]=="B"]

    u_sov = pct(sum(1 for r in unaided if r["godaddy_mentioned"]=="Y"), len(unaided))
    a_sov = pct(sum(1 for r in aided if r["godaddy_mentioned"]=="Y"), len(aided))
    r_sov = pct(sum(1 for r in unaided if r["rate_saver_mentioned"]=="Y"), len(unaided))

    return {
        "unaided_sov": u_sov,
        "aided_sov": a_sov,
        "rate_saver_sov": r_sov,
        "total_prompts": len(rows),
        "unaided_prompts": len(unaided),
        "aided_prompts": len(aided),
        "unaided_hits": sum(1 for r in unaided if r["godaddy_mentioned"]=="Y"),
        "aided_hits": sum(1 for r in aided if r["godaddy_mentioned"]=="Y"),
    }

# ── Save results ──────────────────────────────────────────────────────
def save_results(all_results, run_id):
    """Save benchmark results to CSV files"""
    os.makedirs("benchmarks", exist_ok=True)

    # Save individual model results
    for model_id, data in all_results.items():
        if data["rows"]:
            model_safe = model_id.replace("/", "_").replace(":", "_")
            csv_path = f"benchmarks/geo_multi_{model_safe}_{run_id}.csv"

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data["rows"][0].keys())
                writer.writeheader()
                writer.writerows(data["rows"])

            print(f"  Saved: {csv_path}")

    # Save comparison summary - append if file exists, otherwise create with header
    summary_path = f"benchmarks/geo_multi_comparison_{run_id}.csv"
    file_exists = os.path.exists(summary_path)

    with open(summary_path, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "model_id", "model_name", "unaided_sov", "aided_sov",
            "rate_saver_sov", "unaided_hits", "unaided_prompts",
            "aided_hits", "aided_prompts", "status"
        ])

        # Only write header if creating new file
        if not file_exists:
            writer.writeheader()

        for model_id, data in all_results.items():
            if data["rows"]:
                summary = data["summary"]
                writer.writerow({
                    "model_id": model_id,
                    "model_name": data["model_name"],
                    "unaided_sov": f"{summary['unaided_sov']:.1f}%",
                    "aided_sov": f"{summary['aided_sov']:.1f}%",
                    "rate_saver_sov": f"{summary['rate_saver_sov']:.1f}%",
                    "unaided_hits": summary["unaided_hits"],
                    "unaided_prompts": summary["unaided_prompts"],
                    "aided_hits": summary["aided_hits"],
                    "aided_prompts": summary["aided_prompts"],
                    "status": "success" if data["error"] is None else data["error"]
                })

    print(f"\n  Comparison summary: {summary_path}")

# ── Main ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GEO multi-model benchmark runner")
    parser.add_argument("--model", help="Run specific model by ID")
    parser.add_argument("--models", nargs="+", choices=["primary", "pulse", "claude", "all"],
                       default=["primary"], help="Run specific model groups: primary (5), pulse (3), all (8)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--fresh", action="store_true", help="Delete existing comparison CSV before starting (for first run)")
    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("CAAS_API_KEY")
    if not api_key:
        print("[FAIL] CAAS_API_KEY environment variable not set")
        sys.exit(1)

    # Determine which models to run
    if args.model:
        models_to_run = [m for m in ALL_MODELS if m["id"] == args.model]
        if not models_to_run:
            print(f"[FAIL] Model '{args.model}' not found")
            print(f"Available models: {', '.join(m['id'] for m in ALL_MODELS)}")
            sys.exit(1)
    else:
        if "all" in args.models:
            models_to_run = ALL_MODELS
        else:
            models_to_run = []
            for group in args.models:
                if group in MODEL_GROUPS and MODEL_GROUPS[group]:
                    models_to_run.extend(MODEL_GROUPS[group])
                else:
                    print(f"Warning: Unknown group '{group}', skipping")

    print(f"\n{'='*60}")
    print(f"GEO Multi-Model Benchmark Runner")
    print(f"{'='*60}")
    print(f"Running {len(models_to_run)} model(s): {', '.join(m['name'] for m in models_to_run)}")
    print(f"Total prompts per model: {len(PROMPTS)}")
    print(f"Proxy: {PROXY_URL}")

    # Run benchmarks
    all_results = {}
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-W%V")

    # If --fresh flag is set, delete existing comparison file for this run_id
    if args.fresh:
        summary_path = f"benchmarks/geo_multi_comparison_{run_id}.csv"
        if os.path.exists(summary_path):
            os.remove(summary_path)
            print(f"  Deleted existing comparison file: {summary_path}")

    for model_info in models_to_run:
        rows, error = run_model_benchmark(model_info, api_key, verbose=not args.quiet)

        if rows:
            summary = calculate_summary(rows)
            all_results[model_info["id"]] = {
                "model_name": model_info["name"],
                "rows": rows,
                "summary": summary,
                "error": error
            }

            if not args.quiet:
                print(f"\n  Results:")
                print(f"    Unaided SOV: {summary['unaided_sov']:.1f}% ({summary['unaided_hits']}/{summary['unaided_prompts']})")
                print(f"    Aided SOV: {summary['aided_sov']:.1f}% ({summary['aided_hits']}/{summary['aided_prompts']})")
                print(f"    Rate Saver mentions: {summary['rate_saver_sov']:.1f}%")
        else:
            all_results[model_info["id"]] = {
                "model_name": model_info["name"],
                "rows": [],
                "summary": {},
                "error": error
            }

    # Save all results
    print(f"\n{'='*60}")
    print("Saving results...")
    save_results(all_results, run_id)

    # Print comparison table
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"{'Model':<30} {'Unaided SOV':<15} {'Aided SOV':<15}")
    print(f"{'-'*60}")

    for model_id, data in all_results.items():
        if data["rows"]:
            s = data["summary"]
            print(f"{data['model_name']:<30} {s['unaided_sov']:>6.1f}% ({s['unaided_hits']:>2}/{s['unaided_prompts']:<2})  {s['aided_sov']:>6.1f}% ({s['aided_hits']:>1}/{s['aided_prompts']:<1})")
        else:
            print(f"{data['model_name']:<30} {'FAILED':<15} {data['error'][:30]}")

    print(f"\n{'='*60}")
    print(f"BENCHMARK COMPLETE - {run_id}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
