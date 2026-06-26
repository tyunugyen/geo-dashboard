#!/usr/bin/env python3
"""
fill_session.py — GEO dashboard intelligence layer via CaaS proxy
Uses OpenAI SDK + GoDaddy CaaS proxy (same pattern as benchmark scripts)
Two-call strategy: avoids proxy timeout on large responses

Usage:
  python fill_session.py
  python fill_session.py --dry-run
"""

import os, sys, json, argparse
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────
PROXY_URL  = "https://caas-gocode-prod.caas-prod.prod.onkatana.net"
MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 8000
TIMEOUT    = 600.0  # 10 minutes for large intelligence responses
MAX_RETRIES = 3

SESSION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "public", "data", "session.json"
)

# ── Load / save ──────────────────────────────────────────────────────
def load_session(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_session(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── CaaS client ──────────────────────────────────────────────────────
def get_client(api_key):
    from openai import Timeout
    return OpenAI(
        api_key=api_key,
        base_url=PROXY_URL,
        timeout=Timeout(connect=60.0, read=TIMEOUT, write=60.0, pool=10.0),
        max_retries=0  # We handle retries ourselves
    )

# ── Single API call with retry ──────────────────────────────────────
def call_claude(client, system_msg, user_msg):
    """Call Claude via CaaS. Fails loudly on any error."""
    import time
    print(f"  Calling CaaS proxy: {PROXY_URL}")
    print(f"  Model: {MODEL}")
    print(f"  Prompt length: {len(user_msg):,} chars")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg},
                ]
            )
            content = response.choices[0].message.content
            print(f"  [OK] Response received: {len(content):,} chars")
            return content
        except Exception as e:
            if attempt == MAX_RETRIES:
                # Print full error details — never fail silently
                print(f"  [ERROR] CaaS API call FAILED after {MAX_RETRIES} attempts")
                print(f"  Error type: {type(e).__name__}")
                print(f"  Error detail: {e}")
                print(f"  Proxy URL: {PROXY_URL}")
                print(f"  Model: {MODEL}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise so the Action fails visibly
            print(f"  Attempt {attempt} failed: {e}")
            print(f"  Retrying in {5 * attempt} seconds...")
            time.sleep(5 * attempt)  # Exponential backoff: 5s, 10s, 15s

# ── Parse JSON ───────────────────────────────────────────────────────
def parse_json(text):
    text = text.strip()

    # Strip ```json ... ``` fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline > 0:
            text = text[first_newline:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost { }
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON parse failed: {e.msg} at char {e.pos}\n"
                f"Near: ...{text[max(0, e.pos-100):e.pos+100]}..."
            )

    raise ValueError(f"No JSON found. Response starts: {text[:200]}")

# ── CALL 1: Intelligence arrays ──────────────────────────────────────
def build_prompt_call1(session):
    run_type   = session["meta"].get("run_type", "weekly")
    run_id     = session["meta"].get("run_id", "UNKNOWN")
    unaided    = session["sov_dashboard"]["unaided_sov"]["value"]
    aided      = session["sov_dashboard"]["aided_sov"]["value"]
    last_bench = session["meta"].get("last_full_benchmark", "June 2026")

    return (
        "You are the GEO Intelligence Agent for GoDaddy Payments.\n"
        "Return ONLY a valid JSON object. No markdown, no explanation.\n\n"
        "SESSION CONTEXT:\n"
        "- Run type: " + run_type + "\n"
        "- Run ID: " + run_id + "\n"
        "- Unaided SOV: " + unaided + " (north-star metric — GoDaddy mentioned cold)\n"
        "- Aided SOV: " + aided + "\n"
        "- Last full benchmark: " + last_bench + "\n\n"
        "VERIFIED COMPETITOR RATES (use exactly, do not approximate):\n"
        "- Square: 2.6% + $0.15 in-person (raised Feb 25 2025). Online: 3.3% + $0.30\n"
        "- Clover: 2.3-2.6% + $0.10 direct. Monthly software $29.95-$129.85\n"
        "- Helcim: ~1.93% + $0.08 interchange-plus. NerdWallet: Best for volume discounts\n"
        "- Stripe: 2.7% + $0.05 in-person. No phone support\n"
        "- GoDaddy POS Plus: 2.3% + $0 in-person\n\n"
        "Return a JSON object with EXACTLY these keys:\n\n"
        "{\n"
        '  "perplexity_simulation": [\n'
        '    // 7 clusters: cheapest processor, pass fees to customers, best Square alternatives,\n'
        '    // 24/7 support, best POS coffee shop, GoDaddy brand search, Rate Saver unprompted\n'
        '    // Each: { "cluster": str, "prompt_ids": [], "cited": [], "godaddy": bool, "action": str }\n'
        "  ],\n"
        '  "competitive_intel": [\n'
        '    // 4 competitors: Square, Clover, Helcim, Stripe\n'
        '    // Each: { "competitor": str, "event": str, "detail": str, "win_angle_impact": str,\n'
        '    //         "source": str, "changed": bool, "verified_date": "2026-06-25" }\n'
        "  ],\n"
        '  "strategy_actions": {\n'
        '    "p0": [\n'
        '      // Each: { "rank": int, "action": str, "agent": str, "root_cause": str,\n'
        '      //         "owner": str, "window": str, "priority_score": float,\n'
        '      //         "blocked_by": str, "auto_accepted": true }\n'
        "    ],\n"
        '    "p1": [ /* same structure */ ]\n'
        "  },\n"
        '  "amplify_threads": [\n'
        '    // 3 threads: fee switching (B15/B16), surcharging/Rate Saver (B11-B13),\n'
        '    //            Clover contract escape (S6)\n'
        '    // Each: { "id": str, "priority_score": int, "thread": str, "platform": str,\n'
        '    //         "community": str, "date": str, "cluster": [],\n'
        '    //         "draft_status": "ready_for_review", "claim_flags": [],\n'
        '    //         "draft": str, "disclosure": str,\n'
        '    //         "approved": false, "posted": false, "outcome": "" }\n'
        "  ],\n"
        '  "cite_pipeline": [\n'
        '    // 6 publishers: NerdWallet (payment processors), NerdWallet (POS),\n'
        '    //               Forbes Advisor, Wise, Business.com, TechRadar\n'
        '    // Each: { "publisher": str, "section": str, "status": str, "priority": str,\n'
        '    //         "best_for_label": str, "blocked_by": str, "est_sov_impact": str,\n'
        '    //         "last_contact": str, "response": str, "outreach_channel": str }\n'
        "  ],\n"
        '  "report_summary": {\n'
        '    "binding_constraint": str,\n'
        '    "top_wins": [ /* 3 wins: { "win": str, "agent": str, "impact": str } */ ],\n'
        '    "top_gaps": [ /* 3 gaps: { "gap": str, "priority": str, "root_cause": str, "action": str, "window": str } */ ],\n'
        '    "leading_indicators": [ /* 6: { "indicator": str, "value": str, "status": "red|yellow|green" } */ ],\n'
        '    "leadership_decisions": [ /* { "decision": str, "owner": str, "deadline": str, "consequence": str } */ ],\n'
        '    "leadership_decisions_carryover": [],\n'
        '    "next_month_priority": [ /* { "priority": str, "action": str, "agent": str, "sov_impact": str, "window": str } */ ],\n'
        '    "data_confidence": str,\n'
        '    "methodology_note": str\n'
        "  }\n"
        "}\n\n"
        "RULES:\n"
        "- Square rate is 2.6% + $0.15 (NOT $0.10)\n"
        "- GoDaddy POS Plus: 2.3% + $0\n"
        "- Rate Saver: 0% credit, 1.9% + $0 debit in-person. NOT in CT, MA, PR or ecommerce\n"
        "- Unaided SOV and Aided SOV are NEVER blended\n"
        "- All Gap Flags AUTO-ACCEPTED\n"
        "- claim_flags use claim_status: 'verify_needed' — never invent Registry IDs\n"
        "- Amplify draft disclosures: 'Disclosure: I represent GoDaddy Payments.'\n"
    )

# ── CALL 2: Build pages ──────────────────────────────────────────────
def build_prompt_call2(session, strategy_actions):
    run_type = session["meta"].get("run_type", "weekly")
    p0 = strategy_actions.get("p0", [])
    p1 = strategy_actions.get("p1", [])

    build_actions = [a for a in p0 + p1 if a.get("agent") == "BUILD"]

    if not build_actions:
        return None

    actions_text = json.dumps(build_actions, indent=2)

    return (
        "You are the GEO Content Builder for GoDaddy Payments.\n"
        "Return ONLY a valid JSON object. No markdown, no explanation.\n\n"
        "Build full page drafts for these actions:\n"
        + actions_text + "\n\n"
        "VERIFIED RATES:\n"
        "- GoDaddy POS Plus in-person: 2.3% + $0\n"
        "- Square in-person: 2.6% + $0.15 (raised Feb 25 2025)\n"
        "- Clover in-person: 2.3-2.6% + $0.10 direct + $29.95-$129.85/mo software\n"
        "- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
        "Return:\n"
        "{\n"
        '  "build_pages": [\n'
        '    // One entry per BUILD action above\n'
        '    // Each: {\n'
        '    //   "brief_id": str (e.g. "BUILD-001"),\n'
        '    //   "priority": str ("P0" or "P1"),\n'
        '    //   "auto_accepted": true,\n'
        '    //   "h1": str (MERCHANT LANGUAGE — how a merchant asks, not GoDaddy marketing),\n'
        '    //         WRONG: "GoDaddy Rate Saver — Zero Processing"\n'
        '    //         RIGHT: "How to Reduce Your Credit Card Processing Fees to 0%"\n'
        '    //   "query_cluster": [],\n'
        '    //   "competitor": str,\n'
        '    //   "win_angle": str,\n'
        '    //   "status": "draft_complete",\n'
        '    //   "crawl_phase2": "pending",\n'
        '    //   "claim_flags": [ { "field": str, "claim_status": "verify_needed", "note": str } ],\n'
        '    //   "meta_title": str,\n'
        '    //   "meta_description": str,\n'
        '    //   "canonical": str,\n'
        '    //   "not_best_for": str,\n'
        '    //   "footnotes": [],\n'
        '    //   "faq": [ min 7 questions in merchant voice:\n'
        '    //            { "q": "Can I..." or "How do I..." or "What happens if...", "a": str } ]\n'
        '    // }\n'
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "- H1 must sound like a merchant typed it into Google, not a GoDaddy press release\n"
        "- FAQ questions in merchant voice only\n"
        "- claim_status: 'verify_needed' for any rate needing Registry confirmation\n"
        "- not_best_for must be honest — say who GoDaddy is NOT right for\n"
        "- Footnote required on all Rate Saver pages: 'Requires eligible plan. Not available in CT, MA, PR or ecommerce'\n"
    )

# ── Merge all filled data into skeleton ──────────────────────────────
def merge_session(skeleton, call1_data, call2_data):
    # Validate call1_data has actual content before merging
    if not call1_data:
        raise ValueError("Call 1 returned empty data — CaaS call likely failed silently")

    intel_check = call1_data.get("competitive_intel", [])
    if not intel_check:
        raise ValueError(
            f"Call 1 returned empty arrays — CaaS call failed silently.\n"
            f"call1_data keys: {list(call1_data.keys())}\n"
            f"competitive_intel: {intel_check}"
        )

    result = dict(skeleton)

    # From call 1
    for field in ["perplexity_simulation", "competitive_intel",
                  "strategy_actions", "amplify_threads",
                  "cite_pipeline", "report_summary"]:
        if field in call1_data and call1_data[field]:
            result[field] = call1_data[field]

    # Build pages from call 2
    if call2_data and call2_data.get("build_pages"):
        result["build_pages"] = call2_data["build_pages"]

    # Categories from prompt bank baseline (always populated)
    if not result.get("categories"):
        result["categories"] = [
            {"name": "pricing_fee",        "type": "U", "sov": "0%", "phase1": "25%", "target": "85%", "cell": "red"},
            {"name": "top_funnel_pos",      "type": "U", "sov": "0%", "phase1": "20%", "target": "60%", "cell": "red"},
            {"name": "payment_processing",  "type": "U", "sov": "0%", "phase1": "20%", "target": "55%", "cell": "red"},
            {"name": "vertical_fb",         "type": "U", "sov": "0%", "phase1": "18%", "target": "50%", "cell": "red"},
            {"name": "vertical_retail",     "type": "U", "sov": "0%", "phase1": "22%", "target": "55%", "cell": "red"},
            {"name": "general_in_person",   "type": "U", "sov": "0%", "phase1": "18%", "target": "50%", "cell": "red"},
            {"name": "support",             "type": "U", "sov": "0%", "phase1": "25%", "target": "65%", "cell": "red"},
            {"name": "comparison",          "type": "B", "sov": "0%", "phase1": "25%", "target": "70%", "cell": "red"},
        ]

    # Pulse models
    if not result.get("model_sov", {}).get("pulse"):
        result.setdefault("model_sov", {})["pulse"] = [
            {"name": "o3",                    "why": "Reasoning model — 28.6% aided SOV anomaly in W26", "unaided": "0%", "aided": "28.6%", "status": "partial", "u_color": "red", "a_color": "yellow", "trigger": "Investigate aided SOV drop"},
            {"name": "Gemini 3.1 Pro Preview","why": "Next-gen Gemini — also 28.6% aided in W26",        "unaided": "0%", "aided": "28.6%", "status": "partial", "u_color": "red", "a_color": "yellow", "trigger": "Watch on next full benchmark"},
        ]

    # Always preserve skeleton metadata
    result["meta"]          = skeleton["meta"]
    result["sov_dashboard"] = skeleton["sov_dashboard"]
    result["trends"]        = skeleton.get("trends", [])

    # Preserve empty arrays if not filled
    result.setdefault("amplify_outcomes",    [])
    result.setdefault("amplify_escalations", [])

    return result

# ── Main ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fill session.json via CaaS Claude API")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing")
    parser.add_argument("--session", default=SESSION_PATH, help="Path to session.json")
    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get("CAAS_API_KEY")
    if not api_key:
        print("ERROR: CAAS_API_KEY not set"); sys.exit(1)

    # Load skeleton
    if not os.path.exists(args.session):
        print(f"ERROR: session.json not found at {args.session}"); sys.exit(1)

    print(f"  Loading: {args.session}")
    skeleton = load_session(args.session)
    run_type = skeleton["meta"].get("run_type", "weekly")
    run_id   = skeleton["meta"].get("run_id", "UNKNOWN")
    print(f"  Run type: {run_type} | Run ID: {run_id}")

    client = get_client(api_key)

    # ── CALL 1: Intelligence arrays ───────────────────────────────────
    print("\n  CALL 1: Intelligence arrays (perplexity, competitive, strategy, amplify, cite, report)...")
    prompt1 = build_prompt_call1(skeleton)
    print(f"  Prompt length: {len(prompt1):,} chars")

    try:
        raw1 = call_claude(client, "You are a GEO intelligence agent. Return only valid JSON.", prompt1)
        print(f"  Response length: {len(raw1):,} chars")
        call1_data = parse_json(raw1)
        print("  Call 1 parsed OK")
    except ValueError as e:
        print(f"  ERROR in Call 1 parsing: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"  ERROR calling API: {e}")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Full traceback:")
        traceback.print_exc()
        sys.exit(1)

    # ── CALL 2: Build pages ───────────────────────────────────────────
    strategy = call1_data.get("strategy_actions", {"p0": [], "p1": []})
    prompt2  = build_prompt_call2(skeleton, strategy)

    call2_data = None
    if prompt2:
        print("\n  CALL 2: Build page drafts...")
        print(f"  Prompt length: {len(prompt2):,} chars")
        try:
            raw2 = call_claude(client, "You are a GEO content builder. Return only valid JSON.", prompt2)
            print(f"  Response length: {len(raw2):,} chars")
            call2_data = parse_json(raw2)
            print("  Call 2 parsed OK")
        except ValueError as e:
            print(f"  WARNING: Call 2 parse failed: {e}")
            print("  Continuing without build pages — can retry later")
        except Exception as e:
            print(f"  WARNING: Call 2 API error: {e}")
            print("  Continuing without build pages")
    else:
        print("\n  CALL 2: No BUILD actions in strategy — skipping build pages")

    # ── Merge ─────────────────────────────────────────────────────────
    complete = merge_session(skeleton, call1_data, call2_data)

    # ── Validate ──────────────────────────────────────────────────────
    checks = [
        ("perplexity_simulation", lambda v: isinstance(v, list) and len(v) > 0),
        ("competitive_intel",     lambda v: isinstance(v, list) and len(v) > 0),
        ("strategy_actions",      lambda v: isinstance(v, dict) and ("p0" in v or "p1" in v)),
        ("amplify_threads",       lambda v: isinstance(v, list) and len(v) > 0),
        ("cite_pipeline",         lambda v: isinstance(v, list) and len(v) > 0),
        ("build_pages",           lambda v: isinstance(v, list)),
        ("categories",            lambda v: isinstance(v, list) and len(v) > 0),
        ("report_summary",        lambda v: isinstance(v, dict) and v.get("binding_constraint")),
    ]

    print("\n  Validation:")
    all_passed = True
    for field, check in checks:
        val    = complete.get(field)
        passed = check(val) if val is not None else False
        count  = len(val) if isinstance(val, list) else ("ok" if passed else "FAIL")
        icon = "[OK]" if passed else "[FAIL]"
        print(f"    {icon} {field}: {count}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n  [WARNING] Some fields missing - check output")

    # ── Write or dry-run ──────────────────────────────────────────────
    if args.dry_run:
        print("\n  [dry-run] Output preview (first 800 chars):")
        print(json.dumps(complete, indent=2)[:800] + "\n  ...(truncated)")
        print(f"\n  [dry-run] Would write to: {args.session}")
    else:
        save_session(args.session, complete)
        print(f"\n  [SUCCESS] Written: {args.session}")
        print(f"  perplexity:    {len(complete.get('perplexity_simulation', []))}")
        print(f"  competitive:   {len(complete.get('competitive_intel', []))}")
        print(f"  amplify:       {len(complete.get('amplify_threads', []))}")
        print(f"  cite_pipeline: {len(complete.get('cite_pipeline', []))}")
        print(f"  build_pages:   {len(complete.get('build_pages', []))}")
        print(f"  categories:    {len(complete.get('categories', []))}")

    print(f"\n  Next: git add public/data/session.json && git push")

if __name__ == "__main__":
    main()