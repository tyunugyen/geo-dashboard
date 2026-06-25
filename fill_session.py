#!/usr/bin/env python3
"""
=============================================================================
fill_session.py — Claude API intelligence layer for GEO dashboard
=============================================================================
Called by GitHub Actions after generate_session_json.py writes the skeleton.
Reads public/data/session.json, calls Claude API to fill all empty arrays,
writes the completed session.json back.

Usage:
  python fill_session.py
  python fill_session.py --dry-run   # prints output without writing

Requires:
  pip install anthropic
  Environment variable: CAAS_API_KEY
=============================================================================
"""

import os, sys, json, argparse
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────
SESSION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "public", "data", "session.json"
)

# GoDaddy CaaS uses the standard Anthropic SDK but with a custom base URL
# If your CAAS_API_KEY works with the standard Anthropic API, use as-is.
# If it requires a custom endpoint, set CAAS_BASE_URL env var.
CAAS_BASE_URL = os.environ.get("CAAS_BASE_URL", None)
MODEL = "claude-sonnet-4-5-20251001"

# ── Load session skeleton ───────────────────────────────────────────
def load_session(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ── Build the prompt ────────────────────────────────────────────────
def build_prompt(session):
    run_type   = session["meta"].get("run_type", "weekly")
    run_id     = session["meta"].get("run_id", "UNKNOWN")
    unaided    = session["sov_dashboard"]["unaided_sov"]["value"]
    aided      = session["sov_dashboard"]["aided_sov"]["value"]
    rs_sov     = session["sov_dashboard"]["rate_saver_sov"]["value"]
    last_bench = session["meta"].get("last_full_benchmark", "June 2026")

    return f"""You are the GEO Intelligence Agent for GoDaddy Payments.

You are running a {run_type.upper()} GEO session for run {run_id}.

CURRENT SOV DATA (from benchmark CSV):
- Unaided SOV: {unaided} (GoDaddy mentioned without being named — north-star metric)
- Aided SOV: {aided} (GoDaddy mentioned when named)
- Rate Saver SOV: {rs_sov}
- Last full 9-model benchmark: {last_bench}

FULL SESSION SKELETON (what the BAT script produced):
{json.dumps(session, indent=2)}

YOUR JOB:
Fill every empty array in the session.json with real intelligence.
Return ONLY a valid JSON object — the complete filled session.json.
No explanation, no markdown, no code blocks. Just the raw JSON.

FILL THESE ARRAYS:

1. perplexity_simulation[] 
   - Simulate what Perplexity cites for each query cluster from the GEO Prompt Bank
   - Key clusters: cheapest processor, pass fees to customers, best alternatives to Square,
     24/7 support, best POS for coffee shop, GoDaddy brand search, Rate Saver unprompted
   - For each: cluster name, prompt_ids (from B/V/S/H tiers), cited sources, godaddy bool, action

2. competitive_intel[]
   - Use these VERIFIED rates (confirmed 2026-06-25):
     Square: 2.6% + $0.15 in-person (raised Feb 25 2025). Online: 3.3% + $0.30
     Clover: 2.3-2.6% + $0.10 direct. Monthly software $29.95-$129.85
     Helcim: interchange-plus ~1.93% + $0.08. NerdWallet label: Best for volume discounts
     Stripe: 2.7% + $0.05 in-person. 2.9% + $0.30 online. No phone support
   - For each: competitor, event, detail, win_angle_impact, source, changed bool, verified_date

3. strategy_actions {{p0:[], p1:[]}}
   - P0: highest priority actions based on 0% unaided SOV
   - P1: supporting actions
   - For each: rank, action, agent, root_cause, owner, window, priority_score, blocked_by, auto_accepted

4. build_pages[]
   - Auto-accept ALL gap flags from strategy_actions — no user confirmation needed
   - Produce full page drafts for every P0 and P1 BUILD action
   - For each page: brief_id, priority, auto_accepted:true, h1 (merchant language),
     query_cluster[], competitor, win_angle, status:"draft_complete",
     crawl_phase2:"pending", claim_flags[], meta_title, meta_description,
     canonical, not_best_for, footnotes[], faq[] (min 7 questions in merchant voice)

5. amplify_threads[]
   - Top 3 highest-priority Reddit/community threads for this week
   - Focus on: fee switching, surcharging/Rate Saver, Clover contract escape
   - For each: id, priority_score, thread, platform, community, date, cluster[],
     draft_status:"ready_for_review", claim_flags[], draft (full response text),
     disclosure, approved:false, posted:false, outcome:""

6. cite_pipeline[]
   - Current status for all 6 priority publishers
   - NerdWallet (x2), Forbes Advisor, Wise, Business.com, TechRadar
   - For each: publisher, section, status, priority, best_for_label,
     blocked_by, est_sov_impact, last_contact, response, outreach_channel

7. report_summary (complete — not skeleton)
   - binding_constraint: one sentence, leads with unaided SOV
   - top_wins[]: 3 wins with agent attribution and impact
   - top_gaps[]: 3 gaps with priority, root_cause, action, window
   - leading_indicators[]: 6 indicators with value and red/yellow/green status
   - leadership_decisions[]: decisions blocked waiting for leadership
   - leadership_decisions_carryover[]: prior month decisions not yet resolved
   - next_month_priority[]: P0/P1/P2 actions with agent, sov_impact, window
   - data_confidence: string
   - methodology_note: string

RULES:
- H1s must use MERCHANT language (how merchants ask) not GoDaddy marketing language
  WRONG: "GoDaddy Payments Rate Saver — Zero Processing Fees"
  RIGHT: "How to Reduce Your Credit Card Processing Fees to 0%"
- FAQ questions must be in merchant voice ("Can I...", "How do I...", "What happens if...")
- claim_status: "verify_needed" for any rate or product spec that needs Registry confirmation
- Do NOT invent Registry IDs — use claim_status: "verify_needed" and describe what needs checking
- Unaided SOV and Aided SOV must NEVER be blended — they measure different things
- All Gap Flags are AUTO-ACCEPTED — trigger BUILD immediately, no user confirmation
- If {"run_type": "weekly"}: fill amplify_threads, competitive_intel, cite_pipeline status,
  build_pages for any new gap flags, partial report_summary
- If {"run_type": "monthly"}: fill everything completely including full executive report_summary
- Square rate is 2.6% + $0.15 (NOT $0.10 — that was the old rate)
- GoDaddy in-person rate (POS Plus): 2.3% + $0
- Rate Saver: 0% credit, 1.9% + $0 debit in-person. NOT available in CT, MA, PR or ecommerce

Return ONLY the complete JSON object. No other text."""

# ── Call Claude API ─────────────────────────────────────────────────
def call_claude(prompt, api_key, base_url=None):
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**kwargs)

    print("  Calling Claude API...")
    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ── Parse response ──────────────────────────────────────────────────
def parse_json_response(text):
    """Extract JSON from Claude response — handles any wrapping."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        try:
            return json.loads(inner)
        except json.JSONDecodeError:
            pass

    # Find first { and last }
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from Claude response")

# ── Merge: preserve skeleton fields, fill empty arrays ─────────────
def merge_session(skeleton, filled):
    """
    Merge filled intelligence into skeleton.
    Skeleton fields (meta, sov_dashboard, trends) are preserved as-is.
    Intelligence arrays are replaced with filled versions.
    """
    INTELLIGENCE_FIELDS = [
        "perplexity_simulation",
        "competitive_intel",
        "strategy_actions",
        "build_pages",
        "amplify_threads",
        "amplify_outcomes",
        "amplify_escalations",
        "cite_pipeline",
        "report_summary",
        "categories",
        "model_sov",
    ]

    result = dict(skeleton)  # start with skeleton

    for field in INTELLIGENCE_FIELDS:
        if field in filled:
            filled_val = filled[field]
            skeleton_val = skeleton.get(field)

            # Only replace if filled has actual content
            if field == "categories":
                # Only replace if filled has populated categories
                if filled_val and len(filled_val) > 0:
                    result[field] = filled_val
            elif field == "model_sov":
                # Merge primary/pulse separately
                if filled_val:
                    merged_model = dict(skeleton_val) if skeleton_val else {}
                    if filled_val.get("primary"):
                        merged_model["primary"] = filled_val["primary"]
                    if filled_val.get("pulse"):
                        merged_model["pulse"] = filled_val["pulse"]
                    result[field] = merged_model
            elif field == "strategy_actions":
                # Handle both flat list and {p0,p1} object
                if isinstance(filled_val, dict):
                    result[field] = filled_val
                elif isinstance(filled_val, list) and filled_val:
                    result[field] = {
                        "p0": [a for a in filled_val if a.get("priority") == "P0"],
                        "p1": [a for a in filled_val if a.get("priority") == "P1"],
                    }
            elif isinstance(filled_val, list) and filled_val:
                result[field] = filled_val
            elif isinstance(filled_val, dict) and filled_val:
                result[field] = filled_val

    # Always preserve skeleton metadata exactly
    result["meta"]          = skeleton["meta"]
    result["sov_dashboard"] = skeleton["sov_dashboard"]
    result["trends"]        = skeleton.get("trends", [])
    result["competitors"]   = filled.get("competitors") or skeleton.get("competitors", [])

    return result

# ── Main ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fill session.json intelligence layer via Claude API")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing")
    parser.add_argument("--session", default=SESSION_PATH, help="Path to session.json")
    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get("CAAS_API_KEY")
    if not api_key:
        print("ERROR: CAAS_API_KEY environment variable not set")
        sys.exit(1)

    base_url = os.environ.get("CAAS_BASE_URL", None)

    # Load skeleton
    if not os.path.exists(args.session):
        print(f"ERROR: session.json not found at {args.session}")
        sys.exit(1)

    print(f"  Loading: {args.session}")
    skeleton = load_session(args.session)
    run_type = skeleton["meta"].get("run_type", "weekly")
    run_id   = skeleton["meta"].get("run_id", "UNKNOWN")
    print(f"  Run type: {run_type} | Run ID: {run_id}")

    # Build prompt and call Claude
    prompt = build_prompt(skeleton)
    print(f"  Prompt length: {len(prompt):,} chars")

    raw_response = call_claude(prompt, api_key, base_url)
    print(f"  Response length: {len(raw_response):,} chars")

    # Parse response
    try:
        filled = parse_json_response(raw_response)
        print(f"  JSON parsed successfully")
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Raw response (first 500 chars):", raw_response[:500])
        sys.exit(1)

    # Merge skeleton + filled intelligence
    complete = merge_session(skeleton, filled)

    # Validate key fields
    checks = [
        ("build_pages",          lambda v: isinstance(v, list)),
        ("amplify_threads",      lambda v: isinstance(v, list)),
        ("cite_pipeline",        lambda v: isinstance(v, list)),
        ("perplexity_simulation",lambda v: isinstance(v, list)),
        ("competitive_intel",    lambda v: isinstance(v, list) and len(v) > 0),
        ("report_summary",       lambda v: isinstance(v, dict) and v.get("binding_constraint")),
    ]
    print("\n  Validation:")
    all_passed = True
    for field, check in checks:
        val = complete.get(field)
        passed = check(val)
        count  = len(val) if isinstance(val, list) else ("✓" if passed else "✗")
        print(f"    {'✅' if passed else '❌'} {field}: {count}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n  ⚠️  Some fields failed validation — check output before pushing")

    # Write or dry-run
    if args.dry_run:
        print("\n  [dry-run] Would write:")
        print(json.dumps(complete, indent=2)[:2000] + "\n  ...(truncated)")
    else:
        with open(args.session, "w", encoding="utf-8") as f:
            json.dump(complete, f, indent=2, ensure_ascii=False)
        print(f"\n  ✅ Written: {args.session}")
        print(f"  build_pages:  {len(complete.get('build_pages', []))}")
        print(f"  amplify:      {len(complete.get('amplify_threads', []))}")
        print(f"  cite_pipeline:{len(complete.get('cite_pipeline', []))}")
        print(f"  perplexity:   {len(complete.get('perplexity_simulation', []))}")

    print(f"\n  Next: git add public/data/session.json && git push")

if __name__ == "__main__":
    main()