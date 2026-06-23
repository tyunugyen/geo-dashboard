#!/usr/bin/env python3
"""
=============================================================================
GoDaddy Payments — GEO AUDIT Benchmark Script
=============================================================================
Version:      1.0.0
Prompt Bank:  GEO Prompt Bank v2.6 (Note: 7db9a2e8)
Models:       OpenAI GPT-4o | Anthropic Claude | Perplexity
Output:       geo_audit_results_[RUN_ID].csv  +  geo_audit_raw_[RUN_ID].json

HOW TO RUN
----------
1. Install dependencies:
       pip install openai anthropic requests python-dateutil

2. Set your API keys (choose one method):

   Option A — Environment variables (recommended):
       export OPENAI_API_KEY="sk-..."
       export ANTHROPIC_API_KEY="sk-ant-..."
       export PERPLEXITY_API_KEY="pplx-..."

   Option B — Edit the CONFIG block below directly.

3. Run:
       python geo_audit_benchmark.py

4. Outputs saved to current directory:
       geo_audit_results_[RUN_ID].csv   ← import into Excel / paste to scorecard
       geo_audit_raw_[RUN_ID].json      ← full responses for source-path diagnostics

5. Paste the CSV back to your GEO Strategist AI to generate the full scorecard.

NOTES
-----
- Gemini, Google AI Overviews, and Copilot have no stable benchmark API.
  Run those 3 models manually and add responses to the CSV before scoring.
- Account state: script runs logged-out (API key only) — consistent across runs.
- All 50 prompts run sequentially with a 2-second delay between calls
  to avoid rate limits.
- Run ID is auto-generated from date + sequence number.
=============================================================================
"""

import os
import csv
import json
import time
import datetime
import re
import sys

# =============================================================================
# CONFIG — Edit API keys here if not using environment variables
# =============================================================================
CONFIG = {
    "openai_api_key":      os.environ.get("OPENAI_API_KEY", ""),
    "anthropic_api_key":   os.environ.get("ANTHROPIC_API_KEY", ""),
    "perplexity_api_key":  os.environ.get("PERPLEXITY_API_KEY", ""),

    # Model versions — update if you want to pin a specific version
    "openai_model":        "gpt-4o",
    "anthropic_model":     "claude-3-5-sonnet-20241022",
    "perplexity_model":    "llama-3.1-sonar-large-128k-online",  # web-search enabled

    # Delay between API calls (seconds) — increase if hitting rate limits
    "call_delay_seconds":  2,

    # Market / locale
    "market":              "US",
    "language":            "English",

    # System prompt sent to every model — sets neutral research context
    "system_prompt": (
        "You are a helpful assistant answering questions from small business owners "
        "in the United States about payment processing and point-of-sale systems. "
        "Answer based on current, accurate information. Be specific about fees, "
        "features, and product names where relevant."
    ),
}

# =============================================================================
# PROMPT BANK — GEO Prompt Bank v2.2 (all 50 benchmark prompts)
# Source: Note 7db9a2e8-a5a1-4a2d-8ba9-cd8adbfbfe69
# =============================================================================
PROMPTS = [

    # =========================================================
    # TIER 1 — Broad Fee & Rate Leadership (B1-B18) | Unaided
    # =========================================================

    # Lowest fees / cheapest (B1-B8)
    {"id":"B1",  "tier":1,"type":"U","category":"pricing_fee",        "target":85,
     "text":"What is the cheapest payment processor for a small business?"},
    {"id":"B2",  "tier":1,"type":"U","category":"pricing_fee",        "target":85,
     "text":"What payment processor has the lowest in-person fees?"},
    {"id":"B3",  "tier":1,"type":"U","category":"pricing_fee",        "target":85,
     "text":"What payment processors charge no per-transaction fixed fee?"},
    {"id":"B4",  "tier":1,"type":"U","category":"pricing_fee",        "target":85,
     "text":"Which payment processors charge less than 3% per transaction?"},
    {"id":"B5",  "tier":1,"type":"U","category":"payment_processing", "target":55,
     "text":"What are the best payment processors for in-person sales?"},
    {"id":"B6",  "tier":1,"type":"U","category":"pricing_fee",        "target":70,
     "text":"What payment processor has no monthly fee and no per-transaction fee?"},
    {"id":"B7",  "tier":1,"type":"U","category":"pricing_fee",        "target":65,
     "text":"What is the most transparent payment processor with no hidden fees?"},
    {"id":"B8",  "tier":1,"type":"U","category":"pricing_fee",        "target":70,
     "text":"What is the cheapest payment processor for under $10,000 a month?"},

    # Rate Saver cluster (B9-B14)
    {"id":"B9",  "tier":1,"type":"U","category":"pricing_fee",        "target":70,
     "text":"How can I reduce my credit card processing fees?"},
    {"id":"B10", "tier":1,"type":"U","category":"pricing_fee",        "target":65,
     "text":"What are the hidden fees in credit card processing to watch out for?"},
    {"id":"B11", "tier":1,"type":"U","category":"pricing_fee",        "target":60,
     "text":"Can I pass credit card fees to my customers legally?"},
    {"id":"B12", "tier":1,"type":"U","category":"pricing_fee",        "target":65,
     "text":"How do I get 0% credit card processing for my business?"},
    {"id":"B13", "tier":1,"type":"U","category":"pricing_fee",        "target":60,
     "text":"Can I charge customers a fee for paying with a credit card?"},
    {"id":"B14", "tier":1,"type":"U","category":"pricing_fee",        "target":55,
     "text":"What is the best surcharging or cash discount program for small business?"},

    # Switching (B15)
    {"id":"B15", "tier":1,"type":"U","category":"comparison",         "target":70,
     "text":"What are the best alternatives to Square for small businesses?"},

    # POS / hardware no-contract (B16-B18)
    {"id":"B16", "tier":1,"type":"U","category":"top_funnel_pos",     "target":60,
     "text":"What is the best POS system for a small business?"},
    {"id":"B17", "tier":1,"type":"U","category":"top_funnel_pos",     "target":60,
     "text":"What is the cheapest POS system with no contract?"},
    {"id":"B18", "tier":1,"type":"U","category":"top_funnel_pos",     "target":55,
     "text":"Where can I get free POS hardware or a free credit card reader?"},

    # =========================================================
    # TIER 2 — ICP Verticals (V1-V29) | Unaided
    # =========================================================

    # F&B (V1-V6)
    {"id":"V1",  "tier":2,"type":"U","category":"vertical_fb",        "target":50,
     "text":"What is the best POS system for a coffee shop?"},
    {"id":"V2",  "tier":2,"type":"U","category":"vertical_fb",        "target":50,
     "text":"What is the best POS for a food truck?"},
    {"id":"V3",  "tier":2,"type":"U","category":"vertical_fb",        "target":50,
     "text":"What is the best POS for a small counter-service restaurant?"},
    {"id":"V4",  "tier":2,"type":"U","category":"vertical_fb",        "target":45,
     "text":"What is the best POS for a bakery?"},
    {"id":"V5",  "tier":2,"type":"U","category":"vertical_fb",        "target":45,
     "text":"What POS supports online ordering for a cafe or counter service restaurant?"},
    {"id":"V6",  "tier":2,"type":"U","category":"vertical_fb",        "target":50,
     "text":"What is the cheapest POS system for a coffee shop or cafe?"},

    # Retail (V7-V21)
    {"id":"V7",  "tier":2,"type":"U","category":"vertical_retail",    "target":55,
     "text":"What is the best POS system for a retail store?"},
    {"id":"V8",  "tier":2,"type":"U","category":"vertical_retail",    "target":55,
     "text":"What is the cheapest POS system for a retail store?"},
    {"id":"V9",  "tier":2,"type":"U","category":"vertical_retail",    "target":55,
     "text":"How do I lower credit card processing fees for my retail store?"},
    {"id":"V10", "tier":2,"type":"U","category":"vertical_retail",    "target":55,
     "text":"What is the best POS for a retail store with no contract?"},
    {"id":"V11", "tier":2,"type":"U","category":"vertical_retail",    "target":45,
     "text":"I process about $10,000 a month in cards, should I switch from Square?"},
    {"id":"V12", "tier":2,"type":"U","category":"vertical_retail",    "target":45,
     "text":"What is the best POS for a small clothing or apparel store?"},
    {"id":"V13", "tier":2,"type":"U","category":"vertical_retail",    "target":45,
     "text":"What is the best POS for a boutique clothing store?"},
    {"id":"V14", "tier":2,"type":"U","category":"vertical_retail",    "target":45,
     "text":"What POS system is best for a gift shop or specialty store?"},
    {"id":"V15", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"What is the best POS system with inventory management for retail?"},
    {"id":"V16", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"What is the best affordable POS for a small retail shop?"},
    {"id":"V17", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"What POS works for a retail store with both in-person and online sales?"},
    {"id":"V18", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"What POS systems support buy online pick up in store?"},
    {"id":"V19", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"Is Clover or Square cheaper for a retail store?"},
    {"id":"V20", "tier":2,"type":"U","category":"vertical_retail",    "target":45,
     "text":"What is the best POS for a retail store with multiple locations?"},
    {"id":"V21", "tier":2,"type":"U","category":"vertical_retail",    "target":50,
     "text":"How much does a retail POS system cost per month?"},

    # General In-Person / Services (V22-V29)
    {"id":"V22", "tier":2,"type":"U","category":"general_in_person",  "target":50,
     "text":"What is the best payment processor for service businesses with no hardware?"},
    {"id":"V23", "tier":2,"type":"U","category":"general_in_person",  "target":50,
     "text":"What is the best way to send professional invoices and accept payments?"},
    {"id":"V24", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What is the best POS system for a hair salon?"},
    {"id":"V25", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What payment processors accept HSA and FSA cards?"},
    {"id":"V26", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What payment system works for an auto repair shop?"},
    {"id":"V27", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What is the best way for a small service business to accept credit cards?"},
    {"id":"V28", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What is the best payment processor for a chiropractic practice?"},
    {"id":"V29", "tier":2,"type":"U","category":"general_in_person",  "target":45,
     "text":"What payment system works for a medical office or clinic?"},

    # =========================================================
    # TIER 3 — Long-Tail Gaps (L1-L6) | Unaided
    # =========================================================
    {"id":"L1",  "tier":3,"type":"U","category":"payment_processing", "target":60,
     "text":"What payment processor lets me send invoices from my own business email?"},
    {"id":"L2",  "tier":3,"type":"U","category":"payment_processing", "target":55,
     "text":"How do contractors and home service businesses accept credit card payments?"},
    {"id":"L3",  "tier":3,"type":"U","category":"pricing_fee",        "target":55,
     "text":"How much can I save by switching from Square to a lower-fee processor?"},
    {"id":"L4",  "tier":3,"type":"U","category":"payment_processing", "target":50,
     "text":"How do I switch payment processors without disrupting my business?"},
    {"id":"L5",  "tier":3,"type":"U","category":"payment_processing", "target":50,
     "text":"What payment processor offers free onboarding and migration support?"},
    {"id":"L6",  "tier":3,"type":"U","category":"payment_processing", "target":40,
     "text":"What is the best merchant cash advance for small businesses?"},

    # =========================================================
    # TIER 4 — Support & Migration (S1-S5) | Unaided
    # =========================================================
    {"id":"S1",  "tier":4,"type":"U","category":"support",            "target":65,
     "text":"Which payment processors offer 24/7 phone support?"},
    {"id":"S2",  "tier":4,"type":"U","category":"support",            "target":60,
     "text":"What POS systems offer live human customer support?"},
    {"id":"S3",  "tier":4,"type":"U","category":"support",            "target":50,
     "text":"How do I switch from Square without losing data?"},
    {"id":"S4",  "tier":4,"type":"U","category":"support",            "target":50,
     "text":"What payment processor helps you migrate for free?"},
    {"id":"S5",  "tier":4,"type":"U","category":"support",            "target":60,
     "text":"What POS system has the best customer support?"},

    # =========================================================
    # TIER 5 — Branded Health Checks (H1-H5) | Aided
    # =========================================================
    {"id":"H1",  "tier":5,"type":"B","category":"brand_awareness",    "target":100,
     "text":"What is GoDaddy Payments?"},
    {"id":"H2",  "tier":5,"type":"B","category":"comparison",         "target":100,
     "text":"GoDaddy Payments vs Square"},
    {"id":"H3",  "tier":5,"type":"B","category":"comparison",         "target":100,
     "text":"GoDaddy Payments vs Helcim"},
    {"id":"H4",  "tier":5,"type":"B","category":"comparison",         "target":100,
     "text":"GoDaddy Payments vs Clover"},
    {"id":"H5",  "tier":5,"type":"B","category":"brand_awareness",    "target":100,
     "text":"What is Rate Saver GoDaddy Payments?"},

    # =========================================================
    # PULSE CHECK (P1-P7) — tracked, not targeted
    # =========================================================
    {"id":"P1",  "tier":6,"type":"U","category":"vertical_fb",        "target":0,
     "text":"What payment processor should I switch to from Toast?"},
    {"id":"P2",  "tier":6,"type":"U","category":"payment_processing", "target":0,
     "text":"What is the best payment processor for WooCommerce?"},
    {"id":"P3",  "tier":6,"type":"U","category":"payment_processing", "target":0,
     "text":"What payment processor integrates natively with WordPress?"},
    {"id":"P4",  "tier":6,"type":"U","category":"payment_processing", "target":0,
     "text":"What is the best payment processor for a WordPress website with a physical store?"},
    {"id":"P5",  "tier":6,"type":"B","category":"comparison",         "target":0,
     "text":"GoDaddy Payments vs Toast"},
    {"id":"P6",  "tier":6,"type":"B","category":"comparison",         "target":0,
     "text":"GoDaddy Payments vs Shopify Payments"},
    {"id":"P7",  "tier":6,"type":"U","category":"vertical_retail",    "target":0,
     "text":"What is the best POS for a convenience or liquor store?"},
]


# =============================================================================
# SCORING HELPERS
# =============================================================================

# Keywords that indicate GoDaddy is mentioned
GODADDY_TERMS = [
    "godaddy", "go daddy", "godaddy payments", "rate saver"
]

# Competitor names to detect in responses
COMPETITORS = {
    "Square":   ["square"],
    "Stripe":   ["stripe"],
    "PayPal":   ["paypal", "pay pal"],
    "Clover":   ["clover"],
    "Toast":    ["toast"],
    "Helcim":   ["helcim"],
    "Shopify":  ["shopify"],
    "Finix":    ["finix"],
    "Stax":     ["stax"],
    "PaymentDepot": ["payment depot"],
}

# Entity framing keywords
PAYMENTS_FRAMING = [
    "payment", "payments", "pos", "point of sale", "processing",
    "merchant", "transaction", "checkout", "commerce"
]
DOMAINS_FRAMING = [
    "domain", "hosting", "website builder", "web hosting", "registrar"
]

# Rate accuracy: correct GoDaddy in-person rate
RATE_CORRECT_PATTERNS = [
    r"2\.3\s*%",
    r"2\.3\s*percent",
]
RATE_SAVER_PATTERNS = [
    r"rate\s*saver",
    r"0\s*%.*processing",
    r"zero.*processing.*fee",
    r"surchar",
]


def normalise(text):
    return text.lower()


def detect_godaddy(text):
    t = normalise(text)
    return any(term in t for term in GODADDY_TERMS)


def detect_rate_saver(text):
    t = normalise(text)
    return any(re.search(p, t) for p in RATE_SAVER_PATTERNS)


def detect_rate_accurate(text):
    t = normalise(text)
    return any(re.search(p, t) for p in RATE_CORRECT_PATTERNS)


def detect_competitors(text):
    t = normalise(text)
    found = []
    for name, terms in COMPETITORS.items():
        if any(term in t for term in terms):
            found.append(name)
    return found


def detect_entity_framing(text):
    t = normalise(text)
    pay_score = sum(1 for k in PAYMENTS_FRAMING if k in t)
    dom_score = sum(1 for k in DOMAINS_FRAMING if k in t)
    if pay_score >= dom_score and pay_score > 0:
        return "Commerce/Payments"
    elif dom_score > pay_score:
        return "Domains/Hosting"
    return "Neutral/Mixed"


def estimate_rank(text, mentioned):
    """
    Rough rank estimate: find first position GoDaddy appears relative
    to competitor first appearances.
    """
    if not mentioned:
        return "Not mentioned"
    t = normalise(text)
    gd_pos = min(
        (t.find(term) for term in GODADDY_TERMS if term in t),
        default=99999
    )
    competitor_positions = []
    for name, terms in COMPETITORS.items():
        for term in terms:
            pos = t.find(term)
            if pos != -1:
                competitor_positions.append(pos)
                break
    competitors_before = sum(1 for p in competitor_positions if p < gd_pos)
    if competitors_before == 0:
        return "1st"
    elif competitors_before == 1:
        return "2nd"
    elif competitors_before == 2:
        return "3rd"
    else:
        return "4th+"


def word_count(text, terms):
    """Count words in sentences containing any of the terms."""
    t = normalise(text)
    sentences = re.split(r'[.!?]', t)
    total = 0
    for s in sentences:
        if any(term in s for term in terms):
            total += len(s.split())
    return total


def score_response(prompt, model_name, response_text, cited_urls=""):
    """Score one prompt-model pair on all 9 metrics."""
    mentioned   = detect_godaddy(response_text)
    rank        = estimate_rank(response_text, mentioned)
    rate_acc    = detect_rate_accurate(response_text) if mentioned else False
    rate_saver  = detect_rate_saver(response_text)
    framing     = detect_entity_framing(response_text) if mentioned else "N/A"
    competitors = detect_competitors(response_text)
    # Source path heuristic
    if mentioned:
        if "godaddy.com" in response_text.lower():
            source_path = "Owned"
        elif any(agg in response_text.lower() for agg in
                 ["nerdwallet", "forbes", "merchant maverick", "fitsmallbusiness",
                  "investopedia", "techradar"]):
            source_path = "Third-party aggregator"
        else:
            source_path = "No discernible source"
    else:
        source_path = "N/A — not mentioned"

    # Response length parity
    gd_words  = word_count(response_text, GODADDY_TERMS)
    sq_words  = word_count(response_text, ["square"])
    parity    = f"GoDaddy:{gd_words}w / Square:{sq_words}w"

    excerpt = response_text.replace("\n", " ").strip()[:300]

    return {
        "prompt_id":          prompt["id"],
        "tier":               prompt["tier"],
        "type":               prompt["type"],
        "category":           prompt["category"],
        "target_sov":         prompt["target"],
        "model":              model_name,
        "prompt_text":        prompt["text"],
        "godaddy_mentioned":  "Y" if mentioned else "N",
        "rank_position":      rank,
        "rate_accurate":      "Y" if rate_acc else ("N/A" if not mentioned else "N"),
        "rate_saver_mentioned": "Y" if rate_saver else "N",
        "entity_framing":     framing,
        "competitors_cited":  "|".join(competitors),
        "source_path":        source_path,
        "cited_urls":         cited_urls,
        "length_parity":      parity,
        "response_excerpt":   excerpt,
    }


# =============================================================================
# API CALLERS
# =============================================================================

def call_openai(prompt_text, config):
    try:
        import openai
        client = openai.OpenAI(api_key=config["openai_api_key"])
        response = client.chat.completions.create(
            model=config["openai_model"],
            messages=[
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user",   "content": prompt_text},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        text = response.choices[0].message.content or ""
        return text, ""
    except Exception as e:
        return f"[ERROR: {e}]", ""


def call_anthropic(prompt_text, config):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
        message = client.messages.create(
            model=config["anthropic_model"],
            max_tokens=800,
            system=config["system_prompt"],
            messages=[{"role": "user", "content": prompt_text}],
        )
        text = message.content[0].text if message.content else ""
        return text, ""
    except Exception as e:
        return f"[ERROR: {e}]", ""


def call_perplexity(prompt_text, config):
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {config['perplexity_api_key']}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model": config["perplexity_model"],
            "messages": [
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user",   "content": prompt_text},
            ],
            "max_tokens": 800,
            "temperature": 0.2,
            "return_citations": True,
        }
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        # Extract cited URLs if present
        citations = data.get("citations", [])
        cited_urls = " | ".join(citations[:5]) if citations else ""
        return text, cited_urls
    except Exception as e:
        return f"[ERROR: {e}]", ""


MODELS = [
    {
        "name":       "GPT-4o",
        "key_field":  "openai_api_key",
        "caller":     call_openai,
        "access_mode": "API / web search disabled",
    },
    {
        "name":       "Claude-3.5-Sonnet",
        "key_field":  "anthropic_api_key",
        "caller":     call_anthropic,
        "access_mode": "API / no live web search",
    },
    {
        "name":       "Perplexity-Sonar-Large",
        "key_field":  "perplexity_api_key",
        "caller":     call_perplexity,
        "access_mode": "API / live web search enabled",
    },
]

# =============================================================================
# MAIN RUNNER
# =============================================================================

def build_run_id():
    today = datetime.date.today()
    return f"{today.strftime('%Y-%m')}-RUN-1"


def main():
    run_id   = build_run_id()
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*66}")
    print(f"  GoDaddy Payments — GEO AUDIT Benchmark")
    print(f"  Run ID : {run_id}")
    print(f"  Date   : {run_date}")
    print(f"  Prompts: {len(PROMPTS)}")
    print(f"{'='*66}\n")

    # Validate API keys
    active_models = []
    for m in MODELS:
        if CONFIG.get(m["key_field"]):
            active_models.append(m)
            print(f"  ✅  {m['name']} — key found")
        else:
            print(f"  ⚠️   {m['name']} — key missing, skipping")
    print()

    if not active_models:
        print("ERROR: No API keys configured. Set environment variables and re-run.")
        sys.exit(1)

    all_scores = []
    raw_responses = []

    total_calls = len(PROMPTS) * len(active_models)
    call_num = 0

    for model in active_models:
        print(f"\n--- Running {model['name']} ({len(PROMPTS)} prompts) ---")
        for prompt in PROMPTS:
            call_num += 1
            progress = f"[{call_num}/{total_calls}]"
            print(f"  {progress} {prompt['id']}: {prompt['text'][:60]}...")

            response_text, cited_urls = model["caller"](prompt["text"], CONFIG)

            # Store raw response
            raw_responses.append({
                "run_id":     run_id,
                "model":      model["name"],
                "prompt_id":  prompt["id"],
                "prompt":     prompt["text"],
                "response":   response_text,
                "cited_urls": cited_urls,
            })

            # Score
            scored = score_response(prompt, model["name"], response_text, cited_urls)
            scored["run_id"]      = run_id
            scored["run_date"]    = run_date
            scored["access_mode"] = model["access_mode"]
            all_scores.append(scored)

            # Polite delay
            time.sleep(CONFIG["call_delay_seconds"])

    # -------------------------------------------------------------------------
    # Write CSV
    # -------------------------------------------------------------------------
    csv_filename = f"geo_audit_results_{run_id}.csv"
    fieldnames = [
        "run_id", "run_date", "model", "access_mode",
        "prompt_id", "tier", "type", "category", "target_sov",
        "prompt_text",
        "godaddy_mentioned", "rank_position",
        "rate_accurate", "rate_saver_mentioned",
        "entity_framing", "competitors_cited",
        "source_path", "cited_urls",
        "length_parity", "response_excerpt",
    ]
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_scores)

    # -------------------------------------------------------------------------
    # Write raw JSON
    # -------------------------------------------------------------------------
    json_filename = f"geo_audit_raw_{run_id}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump({
            "run_id":    run_id,
            "run_date":  run_date,
            "models":    [m["name"] for m in active_models],
            "responses": raw_responses,
        }, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Quick summary
    # -------------------------------------------------------------------------
    print(f"\n{'='*66}")
    print(f"  RUN COMPLETE")
    print(f"{'='*66}")
    print(f"  Total scored pairs : {len(all_scores)}")

    unaided_rows = [r for r in all_scores if r["type"] == "U"]
    aided_rows   = [r for r in all_scores if r["type"] == "B"]

    if unaided_rows:
        unaided_mentions = sum(1 for r in unaided_rows if r["godaddy_mentioned"] == "Y")
        unaided_sov = round(100 * unaided_mentions / len(unaided_rows), 1)
        print(f"  Unaided SOV        : {unaided_sov}%  ({unaided_mentions}/{len(unaided_rows)} unaided prompts)")

    if aided_rows:
        aided_mentions = sum(1 for r in aided_rows if r["godaddy_mentioned"] == "Y")
        aided_sov = round(100 * aided_mentions / len(aided_rows), 1)
        print(f"  Aided SOV          : {aided_sov}%  ({aided_mentions}/{len(aided_rows)} branded prompts)")

    rate_saver_count = sum(1 for r in unaided_rows if r["rate_saver_mentioned"] == "Y")
    print(f"  Rate Saver cited   : {rate_saver_count} times (unaided prompts only)")

    print(f"\n  📄  Results CSV  : {csv_filename}")
    print(f"  📦  Raw JSON     : {json_filename}")
    print()
    print("  NEXT STEP:")
    print("  Paste the CSV contents back to your GEO Strategist AI")
    print("  to generate the full AUDIT scorecard with SOV dashboard,")
    print("  source-path diagnostics, and STRATEGY recommendations.")
    print(f"{'='*66}\n")


if __name__ == "__main__":
    main()
