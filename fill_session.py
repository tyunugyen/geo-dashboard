#!/usr/bin/env python3
"""
fill_session.py — GEO dashboard intelligence layer via CaaS proxy
NOW WITH LIVE DYNAMIC CRAWLING based on cite_pipeline and strategy_actions

Uses OpenAI SDK + GoDaddy CaaS proxy (same pattern as benchmark scripts)
Two-call strategy: avoids proxy timeout on large responses

Usage:
  python fill_session.py
  python fill_session.py --dry-run
"""

import os, sys, json, argparse, time, re
from openai import OpenAI

# Import URL maps (fallback only - prefer publisher_map.json)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.publisher_urls import COMPETITOR_RATE_URLS, KNOWN_RATES

# ── Config ──────────────────────────────────────────────────────────
PROXY_URL  = "https://caas-gocode-prod.caas-prod.prod.onkatana.net"
MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 16000  # Increased from 8000 - claude-sonnet-4-6 supports up to 64K output tokens
TIMEOUT    = 600.0  # 10 minutes for large intelligence responses
MAX_RETRIES = 3

SESSION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "public", "data", "session.json"
)

PUBLISHER_MAP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "publisher_map.json"
)

# Search query templates for finding replacement URLs
PUBLISHER_SEARCH_QUERIES = {
    "NerdWallet":       "site:nerdwallet.com best payment processors small business",
    "Forbes Advisor":   "site:forbes.com/advisor best payment processors small business",
    "Wise":             "site:wise.com credit card processing small business",
    "Business.com":     "site:business.com best credit card processing",
    "TechRadar":        "site:techradar.com best pos systems small business",
    "FitSmallBusiness": "site:fitsmallbusiness.com cheapest credit card processing",
    "Investopedia":     "site:investopedia.com best payment processors",
    "Merchant Maverick": "site:merchantmaverick.com best payment processors",
}

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

# ── Parse JSON with truncation recovery ─────────────────────────────
def parse_json(text):
    text = text.strip()

    # Strip ```json ... ``` fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline > 0:
            text = text[first_newline:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    # Direct parse — fast path
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost { }
    start = text.find("{")
    if start < 0:
        raise ValueError(f"No JSON found. Response starts: {text[:200]}")

    # Try full content first
    end = text.rfind("}") + 1
    if end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # ── RECOVERY: response was truncated mid-JSON ──────────────────
    # Try to salvage by closing all open brackets/braces
    print("  [PARSE] Direct parse failed — attempting truncation recovery...")
    truncated = text[start:]

    # Count unclosed brackets and braces
    stack = []
    in_string = False
    escape_next = False
    last_valid_pos = 0

    for i, ch in enumerate(truncated):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
                last_valid_pos = i

    if stack:
        # Truncated — close all open brackets in reverse order
        closers = {"[": "]", "{": "}"}
        closing = "".join(closers[b] for b in reversed(stack))

        # Find a clean cut point — end of last complete key-value pair
        clean_text = truncated[:last_valid_pos + 1] + closing
        print(f"  [PARSE] Truncation detected — closing {len(stack)} open bracket(s): {closing}")

        try:
            result = json.loads(clean_text)
            print("  [PARSE] ✅ Recovery successful — truncated response salvaged")
            return result
        except json.JSONDecodeError:
            # Last resort — try progressively shorter cuts
            for cut in range(last_valid_pos, max(0, last_valid_pos - 500), -10):
                try:
                    candidate = truncated[:cut]
                    # Close at last complete object
                    candidate = candidate.rstrip().rstrip(",") + closing
                    result = json.loads(candidate)
                    print(f"  [PARSE] ✅ Recovery at cut position {cut}")
                    return result
                except json.JSONDecodeError:
                    continue

    raise ValueError(
        f"JSON parse failed after recovery attempt.\n"
        f"Original error near char {start + last_valid_pos}\n"
        f"Near: ...{text[max(0, start + last_valid_pos - 100):start + last_valid_pos + 100]}..."
    )

# ── Publisher Map Management ─────────────────────────────────────────
def load_publisher_map():
    """Load publisher_map.json from disk. Falls back to empty dict if missing."""
    if os.path.exists(PUBLISHER_MAP_PATH):
        with open(PUBLISHER_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Remove _meta key for use in code
            return {k: v for k, v in data.items() if not k.startswith("_")}
    print(f"  [MAP] publisher_map.json not found at {PUBLISHER_MAP_PATH}")
    print(f"  [MAP] Will use empty map - add publishers to publisher_map.json")
    return {}

def save_publisher_map(pub_map, repairs_made):
    """Write updated map back to disk with metadata."""
    if not os.path.exists(PUBLISHER_MAP_PATH):
        return
    with open(PUBLISHER_MAP_PATH, "r", encoding="utf-8") as f:
        full_data = json.load(f)
    # Update with repaired entries
    for publisher, sections in pub_map.items():
        full_data[publisher] = sections
    full_data["_meta"]["last_validated"] = time.strftime("%Y-%m-%d")
    full_data["_meta"]["last_repairs"] = repairs_made
    with open(PUBLISHER_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2)
    if repairs_made:
        print(f"  [MAP] ✅ publisher_map.json updated with {len(repairs_made)} repair(s)")

def check_url_status(url):
    """
    Returns: 'ok' | 'blocked' | 'not_found' | 'error'
    Does not raise — always returns a status string.
    """
    if url.startswith("BLOCKED:") or url.startswith("STALE:"):
        return "blocked"
    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GEO-dashboard/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return "ok"
            return f"http_{resp.status}"
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "blocked"
        if e.code == 404:
            return "not_found"
        return f"http_{e.code}"
    except Exception:
        return "error"

def search_for_replacement_url(publisher, section):
    """
    Use DuckDuckGo HTML search (no API key needed) to find
    the current URL for a publisher+section combination.
    Returns best candidate URL or None.
    """
    import urllib.parse

    query = PUBLISHER_SEARCH_QUERIES.get(publisher)
    if not query:
        return None

    # Add section keywords to query
    section_keywords = section.lower().replace("best ", "").replace(" for small business", "")
    full_query = f"{query} {section_keywords}"
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(full_query)}"

    try:
        import urllib.request
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GEO-dashboard/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Extract result URLs matching the publisher domain
        publisher_domain = {
            "NerdWallet":       "nerdwallet.com",
            "Forbes Advisor":   "forbes.com/advisor",
            "Wise":             "wise.com",
            "Business.com":     "business.com",
            "TechRadar":        "techradar.com",
            "FitSmallBusiness": "fitsmallbusiness.com",
            "Investopedia":     "investopedia.com",
            "Merchant Maverick":"merchantmaverick.com",
        }.get(publisher, "")

        if not publisher_domain:
            return None

        # Find all https URLs containing the publisher domain
        pattern = rf'https://(?:www\.)?{re.escape(publisher_domain)}/[^\s"\'<>]+'
        matches = re.findall(pattern, html)

        # Filter out non-content pages
        skip_patterns = ["login", "signup", "register", "cdn-cgi", ".jpg", ".png",
                         ".css", ".js", "advertise", "careers", "about"]
        candidates = [
            url for url in matches
            if not any(skip in url.lower() for skip in skip_patterns)
        ]

        if candidates:
            # Prefer URLs with relevant keywords
            preferred = [u for u in candidates if any(
                kw in u.lower() for kw in ["best", "payment", "processor", "pos", "credit-card"]
            )]
            return preferred[0] if preferred else candidates[0]

    except Exception as e:
        print(f"  [SEARCH] Search failed for {publisher}/{section}: {e}")

    return None

def validate_and_repair_urls(pub_map, publishers_needed):
    """
    For each publisher+section about to be crawled:
    1. Check current URL status
    2. If 404/error: search for replacement and update map
    3. If 403/blocked: mark as BLOCKED: and skip gracefully
    4. Return updated map + list of repairs made
    """
    repairs_made = []
    updated_map = {k: dict(v) for k, v in pub_map.items()}  # deep copy

    print(f"\n  [VALIDATE] Checking {len(publishers_needed)} URLs before crawl...")

    for item in publishers_needed:
        publisher = item["publisher"]
        section   = item["section"]

        if publisher not in updated_map:
            print(f"  [VALIDATE] ⚠️  {publisher} not in publisher_map — will be skipped")
            continue

        # Find the URL for this section
        section_map = updated_map[publisher]
        url = None
        matched_section = section

        if section in section_map:
            url = section_map[section]
        else:
            # Fuzzy match
            for key in section_map:
                if any(w in section.lower() for w in key.lower().split()):
                    url = section_map[key]
                    matched_section = key
                    break
            if not url and section_map:
                url = list(section_map.values())[0]
                matched_section = list(section_map.keys())[0]

        if not url:
            continue

        # Check status
        status = check_url_status(url)
        print(f"  [VALIDATE] {publisher} / {matched_section}: {status.upper()}")

        if status == "ok" or status == "blocked":
            continue  # ok = use it; blocked = already marked, handled in fetch_url

        if status in ("not_found", "error") or status.startswith("http_"):
            print(f"  [VALIDATE] 🔍 Searching for replacement URL...")
            replacement = search_for_replacement_url(publisher, matched_section)

            if replacement:
                # Verify the replacement actually works
                replacement_status = check_url_status(replacement)
                if replacement_status == "ok":
                    print(f"  [VALIDATE] ✅ Found replacement: {replacement}")
                    updated_map[publisher][matched_section] = replacement
                    repairs_made.append({
                        "publisher": publisher,
                        "section": matched_section,
                        "old_url": url,
                        "new_url": replacement,
                        "date": time.strftime("%Y-%m-%d")
                    })
                elif replacement_status == "blocked":
                    print(f"  [VALIDATE] ⚠️  Replacement is bot-blocked: {replacement}")
                    updated_map[publisher][matched_section] = f"BLOCKED:{replacement}"
                    repairs_made.append({
                        "publisher": publisher,
                        "section": matched_section,
                        "old_url": url,
                        "new_url": f"BLOCKED:{replacement}",
                        "date": time.strftime("%Y-%m-%d")
                    })
                else:
                    print(f"  [VALIDATE] ❌ Replacement also failed ({replacement_status})")
                    updated_map[publisher][matched_section] = f"STALE:{url}"
            else:
                print(f"  [VALIDATE] ❌ No replacement found — marking as stale")
                updated_map[publisher][matched_section] = f"STALE:{url}"

        time.sleep(0.5)  # polite delay between checks

    return updated_map, repairs_made

# ── URL Fetcher ──────────────────────────────────────────────────────
def fetch_url(url, timeout=15):
    """
    Fetch URL with minimal dependencies. Returns HTML text or None on failure.
    Uses urllib (standard library) to avoid external dependencies.
    Handles BLOCKED: prefix for known bot-protected sites.
    """
    # Known bot-blocked publishers — skip fetch, mark as blocked
    if url.startswith("BLOCKED:"):
        real_url = url[8:]
        print(f"  [KNOWN-BLOCKED] {real_url} — bot protection, cannot scrape")
        return None

    try:
        import urllib.request
        import urllib.error

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GEO-dashboard/1.0; +https://godaddy.com)'
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
            return html
    except Exception as e:
        print(f"  [FETCH FAILED] {url}: {e}")
        return None

# ── LIVE DATA CRAWLER ────────────────────────────────────────────────
def get_live_data(session, publisher_map=None):
    """
    Dynamically determine what to crawl based on:
    - cite_pipeline: which publishers and sections to check
    - strategy_actions: which competitors to verify rates for
    - perplexity_simulation: which clusters need citation checking

    publisher_map: dict from publisher_map.json (validated URLs)

    Returns live_results dict to inject into the CaaS prompt.
    """
    # Use provided map or fall back to config
    if publisher_map is None:
        from config.publisher_urls import PUBLISHER_URL_MAP
        publisher_map = PUBLISHER_URL_MAP
    today = time.strftime("%Y-%m-%d")
    results = {
        "publisher_checks": [],   # what we found on each publisher page
        "competitor_rates": {},   # live verified rates
        "crawl_date": today,
        "fallback_used": []       # which fetches failed and used fallback
    }

    # ── 1. Determine which publishers to crawl from cite_pipeline ────
    cite_pipeline = session.get("cite_pipeline", [])

    # If cite_pipeline is empty (skeleton not yet filled), use a minimal default
    if not cite_pipeline:
        print("  [LIVE] cite_pipeline empty — using default publisher set")
        cite_pipeline = [
            {"publisher": "NerdWallet", "section": "Best Payment Processors", "priority": "P0"},
        ]

    publishers_to_crawl = []
    for entry in cite_pipeline:
        publisher = entry.get("publisher", "")
        section   = entry.get("section", "")
        priority  = entry.get("priority", "P1")
        status    = entry.get("status", "not_contacted")

        # Only crawl P0 and P1 — skip P2/P3 to keep runtime manageable
        if priority not in ("P0", "P1", "critical", "high"):
            continue

        if publisher in publisher_map:
            # Find the best URL match for this section
            url = None
            section_map = publisher_map[publisher]

            # Exact match first
            if section in section_map:
                url = section_map[section]
            else:
                # Fuzzy match — find closest section key
                for key in section_map:
                    if any(word in section.lower() for word in key.lower().split()):
                        url = section_map[key]
                        break
                # Fallback to first URL for this publisher
                if not url:
                    url = list(section_map.values())[0]

            publishers_to_crawl.append({
                "publisher": publisher,
                "section": section,
                "priority": priority,
                "status": status,
                "url": url
            })
        else:
            print(f"  [LIVE] No URL map for publisher: {publisher} — skipping")

    # ── 2. Crawl each publisher page ─────────────────────────────────
    print(f"\n  [LIVE] Crawling {len(publishers_to_crawl)} publisher pages from cite_pipeline...")

    for pub in publishers_to_crawl:
        print(f"  [LIVE] Checking {pub['publisher']} — {pub['section']}...")
        html = fetch_url(pub["url"])

        if not html:
            print(f"  [LIVE] ⚠️  Fetch failed for {pub['publisher']} — marking as fetch_failed")
            results["publisher_checks"].append({
                "publisher": pub["publisher"],
                "section": pub["section"],
                "url": pub["url"],
                "priority": pub["priority"],
                "fetch_status": "failed",
                "godaddy_present": None,
                "competitors_found": [],
                "godaddy_label": None,
                "note": "Fetch failed — could not verify"
            })
            results["fallback_used"].append(pub["publisher"])
            continue

        # Check GoDaddy presence
        godaddy_present = "godaddy" in html.lower()

        # Find which competitors appear
        competitors_found = []
        for name in ["Square", "Stripe", "Helcim", "Clover", "Toast", "PayPal",
                     "Shopify", "Finix", "Lightspeed", "Stax", "Merchant Maverick"]:
            if name.lower() in html.lower():
                competitors_found.append(name)

        # Try to find GoDaddy's label if present
        godaddy_label = None
        if godaddy_present:
            label_match = re.search(
                r'GoDaddy[^\n]{0,100}?best\s+for[^\n]{0,80}',
                html, re.IGNORECASE
            )
            if label_match:
                godaddy_label = label_match.group(0).strip()[:100]

        check_result = {
            "publisher": pub["publisher"],
            "section": pub["section"],
            "url": pub["url"],
            "priority": pub["priority"],
            "fetch_status": "success",
            "godaddy_present": godaddy_present,
            "competitors_found": competitors_found,
            "godaddy_label": godaddy_label,
            "note": f"Verified {today}"
        }
        results["publisher_checks"].append(check_result)

        status_icon = "✅" if godaddy_present else "❌"
        print(f"  [LIVE] {status_icon} {pub['publisher']}: GoDaddy={'PRESENT' if godaddy_present else 'ABSENT'}, competitors={competitors_found[:4]}")

    # ── 3. Determine which competitors to verify from strategy_actions ─
    strategy = session.get("strategy_actions", {})
    all_actions = strategy.get("p0", []) + strategy.get("p1", [])

    # Extract competitor names mentioned in actions
    competitors_to_check = set()
    for action in all_actions:
        action_text = action.get("action", "") + " " + action.get("root_cause", "")
        for comp in COMPETITOR_RATE_URLS:
            if comp.lower() in action_text.lower():
                competitors_to_check.add(comp)

    # Always verify Square and Stripe as baseline
    competitors_to_check.update(["Square", "Stripe"])

    print(f"\n  [LIVE] Verifying rates for: {sorted(competitors_to_check)}")

    for comp in sorted(competitors_to_check):
        url = COMPETITOR_RATE_URLS.get(comp)
        if not url:
            continue

        html = fetch_url(url)
        if not html:
            print(f"  [LIVE] ⚠️  Rate fetch failed for {comp} — using fallback")
            results["fallback_used"].append(f"{comp} rates")
            # Use known fallback rates
            if comp in KNOWN_RATES:
                results["competitor_rates"][comp] = {
                    "raw_patterns": [KNOWN_RATES[comp].get("in_person", "")],
                    "source": url,
                    "verified_date": KNOWN_RATES[comp].get("verified_date", ""),
                    "fetch_status": "fallback",
                    "note": "Fetch failed — using last known rate"
                }
            continue

        # Extract rate patterns — look for percentage + cents format
        rate_patterns = re.findall(
            r'(\d+\.\d+%\s*(?:\+|plus)\s*[\d¢$\.]+\s*(?:cents|¢|\$[\d\.]+)?)',
            html, re.IGNORECASE
        )

        results["competitor_rates"][comp] = {
            "raw_patterns": rate_patterns[:6],  # first 6 matches
            "source": url,
            "verified_date": today,
            "fetch_status": "success"
        }
        print(f"  [LIVE] {comp} rate patterns found: {rate_patterns[:3]}")

    return results


def format_live_data_for_prompt(live_results):
    """
    Format the live crawl results into a clear string for the CaaS prompt.
    """
    today = live_results.get("crawl_date", "today")
    lines = [f"LIVE DATA — scraped {today}\n"]

    # Publisher status
    lines.append("PUBLISHER CITATION STATUS (from cite_pipeline targets):")
    for check in live_results.get("publisher_checks", []):
        status = "✅ PRESENT" if check.get("godaddy_present") else "❌ ABSENT"
        if check.get("fetch_status") == "failed":
            status = "⚠️ FETCH FAILED"
        lines.append(
            f"  {check['priority']} | {check['publisher']} — {check['section']}: "
            f"GoDaddy {status} | Competitors: {check.get('competitors_found', [])[:4]}"
        )
        if check.get("godaddy_label"):
            lines.append(f"       GoDaddy label found: {check['godaddy_label']}")

    # Competitor rates
    lines.append("\nCOMPETITOR RATE VERIFICATION (from strategy_actions targets):")
    for comp, data in live_results.get("competitor_rates", {}).items():
        if data.get("fetch_status") == "success":
            lines.append(f"  {comp}: raw patterns = {data.get('raw_patterns', [])[:3]} | source: {data['source']}")
        elif data.get("fetch_status") == "fallback":
            lines.append(f"  {comp}: USING FALLBACK — {data.get('raw_patterns', [])[0]} | {data.get('note', '')}")
        else:
            lines.append(f"  {comp}: FETCH FAILED — use last known rate")

    if live_results.get("fallback_used"):
        lines.append(f"\n⚠️ Fallbacks used (fetch failed): {live_results['fallback_used']}")

    return "\n".join(lines)

# ── CALL 1: Intelligence arrays ──────────────────────────────────────
def build_prompt_call1(session, live_results):
    run_type   = session["meta"].get("run_type", "weekly")
    run_id     = session["meta"].get("run_id", "UNKNOWN")
    unaided    = session["sov_dashboard"]["unaided_sov"]["value"]
    aided      = session["sov_dashboard"]["aided_sov"]["value"]
    last_bench = session["meta"].get("last_full_benchmark", "June 2026")

    live_data_str = format_live_data_for_prompt(live_results)

    return (
        "You are the GEO Intelligence Agent for GoDaddy Payments.\n"
        "Return ONLY a valid JSON object. No markdown, no explanation.\n\n"
        "SESSION CONTEXT:\n"
        "- Run type: " + run_type + "\n"
        "- Run ID: " + run_id + "\n"
        "- Unaided SOV: " + unaided + " (north-star metric — GoDaddy mentioned cold)\n"
        "- Aided SOV: " + aided + "\n"
        "- Last full benchmark: " + last_bench + "\n\n"
        + live_data_str + "\n\n"
        "FIXED KNOWN RATES (always accurate):\n"
        "- GoDaddy POS Plus: 2.3% + $0 in-person\n"
        "- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
        "Use the LIVE DATA above to populate competitive_intel and perplexity_simulation "
        "with real current citations. Where fetch failed, use best available knowledge "
        "but note it as estimated.\n\n"
        "Return a JSON object with EXACTLY these keys:\n\n"
        "{\n"
        '  "perplexity_simulation": [\n'
        '    // 7 clusters: cheapest processor, pass fees to customers, best Square alternatives,\n'
        '    // 24/7 support, best POS coffee shop, GoDaddy brand search, Rate Saver unprompted\n'
        '    // Each: { "cluster": str, "prompt_ids": [], "cited": [], "godaddy": bool, "action": str }\n'
        "  ],\n"
        '  "competitive_intel": [\n'
        '    // Use LIVE DATA from publisher crawls and competitor rate checks\n'
        '    // 4 competitors: Square, Clover, Helcim, Stripe\n'
        '    // Each: { "competitor": str, "event": str, "detail": str, "win_angle_impact": str,\n'
        '    //         "source": str, "changed": bool, "verified_date": "2026-06-29" }\n'
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
        '    // Use LIVE DATA from publisher crawls to update status\n'
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
        "- Use LIVE crawl data for competitive_intel and cite_pipeline status\n"
        "- Square rate is 2.6% + $0.15 (NOT $0.10) — verified from LIVE DATA\n"
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

    # Match any action that involves building content/pages
    build_actions = [a for a in p0 + p1 if any(
        keyword in a.get("agent", "").lower() or keyword in a.get("action", "").lower()
        for keyword in ["build", "content", "page", "landing", "seo", "publish"]
    )]

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

    # Pulse models - updated to reflect current 8-model tracking
    if not result.get("model_sov", {}).get("pulse"):
        result.setdefault("model_sov", {})["pulse"] = [
            {"name": "Gemini 2.5 Flash",       "why": "Promoted to stable release — behaviour consolidating", "unaided": "0%", "aided": "100%", "status": "tracking", "u_color": "red", "a_color": "green"},
            {"name": "o3-mini",                "why": "OpenAI reasoning model — usage pattern emerging",       "unaided": "0%", "aided": "100%", "status": "tracking", "u_color": "red", "a_color": "green"},
            {"name": "Gemini 3.1 Pro Preview", "why": "Next-gen Gemini — 28.6% aided SOV anomaly in W26",     "unaided": "0%", "aided": "28.6%", "status": "partial",  "u_color": "red", "a_color": "yellow"},
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
    parser = argparse.ArgumentParser(description="Fill session.json via CaaS Claude API with LIVE crawling")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing")
    parser.add_argument("--session", default=SESSION_PATH, help="Path to session.json")
    parser.add_argument("--skip-crawl", action="store_true", help="Skip live crawling (use for testing)")
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

    # ── LOAD + VALIDATE PUBLISHER MAP ────────────────────────────────
    publisher_map = None
    if not args.skip_crawl:
        print("\n  Loading publisher map...")
        publisher_map = load_publisher_map()

        if publisher_map:
            # Determine which publishers we'll need based on cite_pipeline
            cite_pipeline = skeleton.get("cite_pipeline", [])
            publishers_needed = [
                {"publisher": e["publisher"], "section": e["section"]}
                for e in cite_pipeline
                if e.get("priority") in ("P0", "P1", "critical", "high")
                and e.get("publisher") in publisher_map
            ]

            if publishers_needed:
                # Validate and auto-repair before crawling
                publisher_map, repairs = validate_and_repair_urls(publisher_map, publishers_needed)

                # Write repaired map back to disk
                if repairs:
                    save_publisher_map(publisher_map, repairs)
                    print(f"\n  [MAP] {len(repairs)} URL(s) auto-repaired and saved to publisher_map.json")

    # ── LIVE CRAWL (now with validated URLs) ─────────────────────────
    if args.skip_crawl:
        print("\n  [SKIP] Live crawling disabled")
        live_results = {"publisher_checks": [], "competitor_rates": {}, "crawl_date": time.strftime("%Y-%m-%d"), "fallback_used": []}
    else:
        print("\n  [LIVE] Starting dynamic crawl based on cite_pipeline and strategy_actions...")
        live_results = get_live_data(skeleton, publisher_map)
        print(f"\n  [LIVE] Crawl complete:")
        print(f"    Publishers checked: {len(live_results['publisher_checks'])}")
        print(f"    Competitor rates:   {len(live_results['competitor_rates'])}")
        print(f"    Fallbacks used:     {len(live_results['fallback_used'])}")

    client = get_client(api_key)

    # ── CALL 1: Intelligence arrays ───────────────────────────────────
    print("\n  CALL 1: Intelligence arrays (perplexity, competitive, strategy, amplify, cite, report)...")
    prompt1 = build_prompt_call1(skeleton, live_results)
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

        # Show live crawl summary
        if not args.skip_crawl:
            print(f"\n  [LIVE] Crawl summary:")
            print(f"    ✅ Publishers present: {sum(1 for p in live_results['publisher_checks'] if p.get('godaddy_present'))}")
            print(f"    ❌ Publishers absent:  {sum(1 for p in live_results['publisher_checks'] if not p.get('godaddy_present') and p.get('fetch_status') == 'success')}")
            print(f"    ⚠️  Fetch failures:    {len(live_results['fallback_used'])}")

    print(f"\n  Next: git add public/data/session.json && git push")

if __name__ == "__main__":
    main()
