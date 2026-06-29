# Dynamic Competitor Rate Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make competitor rate injection fully dynamic by parsing live scraped data instead of using hardcoded rates in CaaS prompts.

**Architecture:** Add two new functions (`parse_competitor_rate()`, `build_competitor_rates_block()`) to fill_session.py that convert raw scraped patterns into formatted strings and inject them into both CaaS call prompts. Remove KNOWN_RATES fallback to force explicit "RATE UNVERIFIED" signaling when fetches fail. Update generate_session_json.py placeholders to be clearly labeled as non-authoritative.

**Tech Stack:** Python 3, regex pattern matching, string formatting

## Global Constraints

- Python 3.x (existing project constraint)
- Must maintain backward compatibility with existing session.json schema
- No external dependencies beyond what's already in fill_session.py
- GoDaddy rates (POS Plus 2.3% + $0, Rate Saver 0% credit/1.9% debit) always hardcoded — product specs, not scraped
- Helcim effective average rate is ~1.79% + 8¢, NOT the 0.40% + 8¢ margin
- All commits follow conventional commits format: `feat:`, `fix:`, `refactor:`

---

## Task 1: Implement parse_competitor_rate() Function

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py` (add function after line 617, before `format_live_data_for_prompt`)

**Interfaces:**
- Consumes: None (pure function, operates on input parameters only)
- Produces: `parse_competitor_rate(competitor: str, rate_data: dict) -> str | None`
  - Returns formatted rate string like `"2.6% + $0.15 in-person Free plan (live 2026-06-29)"` or `None` if failed

- [ ] **Step 1: Add parse_competitor_rate() function**

Add after line 617 in fill_session.py:

```python
def parse_competitor_rate(competitor, rate_data):
    """
    Convert raw scraped rate patterns into clean verified string
    for injection into the CaaS prompt.
    Falls back to None if fetch completely failed.
    
    Args:
        competitor: Competitor name ("Square", "Stripe", "Helcim", "Clover", etc.)
        rate_data: Dict with {"raw_patterns": [...], "verified_date": "...", "fetch_status": "..."}
    
    Returns:
        Formatted string like "2.6% + $0.15 in-person Free plan (live 2026-06-29)"
        or None if fetch failed
    """
    patterns = rate_data.get("raw_patterns", [])
    status   = rate_data.get("fetch_status", "failed")
    verified_date = rate_data.get("verified_date", "")

    if status == "failed" or not patterns:
        # Fetch failed — return None so CaaS knows it's unverified
        return None

    if competitor == "Helcim":
        # Find the Helcim-specific effective average rate (1.5%-2.0% range with 8¢)
        # NOT the interchange-plus margin (0.40%)
        helcim_rates = [p for p in patterns if "1." in p and ("8¢" in p or "0.08" in p or "$0.08" in p)]
        if helcim_rates:
            return f"{helcim_rates[0]} interchange-plus average (live {verified_date})"
        # Fall back to first pattern found
        return f"{patterns[0]} interchange-plus (live {verified_date})"

    if competitor == "Square":
        # Square page lists multiple tiers — find the Free plan rate (2.6% range)
        free_rate = [p for p in patterns if "2.6" in p and ("15" in p or "$0.15" in p or "0.15" in p)]
        if free_rate:
            return f"{free_rate[0]} in-person Free plan (live {verified_date})"
        return f"{patterns[0]} in-person (live {verified_date})"

    if competitor == "Stripe":
        # Stripe pricing page leads with online rate — find in-person ($0.05 fixed fee)
        inperson = [p for p in patterns if "5¢" in p or "$0.05" in p or "0.05" in p]
        if inperson:
            return f"{inperson[0]} in-person (live {verified_date})"
        return f"{patterns[0]} (live {verified_date})"

    if competitor == "Clover":
        # Find in-person rate with $0.10 fixed fee
        inperson = [p for p in patterns if "10¢" in p or "$0.10" in p or "0.10" in p]
        if inperson:
            return f"{inperson[0]} in-person + software fee $29.95–$129.85/mo (live {verified_date})"
        return f"{patterns[0]} in-person (live {verified_date})"

    # Generic fallback for other competitors
    return f"{patterns[0]} (live {verified_date})"
```

- [ ] **Step 2: Test parse_competitor_rate() with Python REPL**

Run Python REPL test:

```bash
cd ~/geo-dashboard
python3 -c "
from fill_session import parse_competitor_rate

# Test Helcim success case - should find 1.79% not 0.40%
rate_data = {
    'raw_patterns': ['1.79% + 8¢', '0.40% + 8¢'],
    'verified_date': '2026-06-29',
    'fetch_status': 'success'
}
result = parse_competitor_rate('Helcim', rate_data)
print(f'Helcim result: {result}')
assert '1.79% + 8¢' in result, f'Expected 1.79%, got {result}'
assert 'live 2026-06-29' in result

# Test Square success case
rate_data = {
    'raw_patterns': ['2.6% + \$0.15', '2.5% + \$0.15'],
    'verified_date': '2026-06-29',
    'fetch_status': 'success'
}
result = parse_competitor_rate('Square', rate_data)
print(f'Square result: {result}')
assert '2.6%' in result
assert 'Free plan' in result

# Test failure case
rate_data = {'raw_patterns': [], 'verified_date': '', 'fetch_status': 'failed'}
result = parse_competitor_rate('Helcim', rate_data)
print(f'Failure case result: {result}')
assert result is None

print('✅ All parse_competitor_rate() tests passed')
"
```

Expected output:
```
Helcim result: 1.79% + 8¢ interchange-plus average (live 2026-06-29)
Square result: 2.6% + $0.15 in-person Free plan (live 2026-06-29)
Failure case result: None
✅ All parse_competitor_rate() tests passed
```

- [ ] **Step 3: Commit parse_competitor_rate()**

```bash
git add fill_session.py
git commit -m "feat: add parse_competitor_rate() for dynamic rate formatting

- Converts raw scraped patterns into formatted strings
- Handles Helcim (effective avg), Square (Free plan), Stripe, Clover
- Returns None on fetch failure for explicit UNVERIFIED signaling"
```

---

## Task 2: Implement build_competitor_rates_block() Function

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py` (add function after parse_competitor_rate())

**Interfaces:**
- Consumes: `parse_competitor_rate(competitor: str, rate_data: dict) -> str | None` (from Task 1)
- Produces: `build_competitor_rates_block(live_results: dict) -> str`
  - Returns multi-line string for CaaS prompt injection

- [ ] **Step 1: Add build_competitor_rates_block() function**

Add after parse_competitor_rate() in fill_session.py:

```python
def build_competitor_rates_block(live_results):
    """
    Build the competitor rates section of the prompt entirely from
    live scraped data. Never uses hardcoded rate strings.
    
    Args:
        live_results: Dict from get_live_data() with competitor_rates and crawl_date
    
    Returns:
        Multi-line string for CaaS prompt with header, rates, and GoDaddy specs
    """
    today = live_results.get("crawl_date", time.strftime("%Y-%m-%d"))
    lines = [
        f"LIVE COMPETITOR RATES — scraped {today}:",
        "Use these exact figures. Where marked UNVERIFIED, do not state a specific rate.",
        ""
    ]

    competitor_rates = live_results.get("competitor_rates", {})

    # Order matters: Square, Stripe, Helcim, Clover, Toast, Shopify
    for comp in ["Square", "Stripe", "Helcim", "Clover", "Toast", "Shopify"]:
        rate_data = competitor_rates.get(comp)

        if not rate_data or rate_data.get("fetch_status") == "failed":
            lines.append(
                f"- {comp}: RATE UNVERIFIED — fetch failed. "
                f"Do not state a specific rate. Note as unverified."
            )
            continue

        rate_str = parse_competitor_rate(comp, rate_data)
        if rate_str:
            lines.append(f"- {comp}: {rate_str}")
        else:
            lines.append(
                f"- {comp}: RATE UNVERIFIED — could not parse. "
                f"Do not state a specific rate."
            )

    # GoDaddy rates are fixed product specs — not scraped, always accurate
    lines.append("- GoDaddy POS Plus: 2.3% + $0 in-person (product spec — always accurate)")
    lines.append("- Rate Saver: 0% credit, 1.9% + $0 debit in-person. NOT in CT, MA, PR or ecommerce")

    return "\n".join(lines)
```

- [ ] **Step 2: Test build_competitor_rates_block() with Python REPL**

Run Python REPL test:

```bash
python3 -c "
from fill_session import build_competitor_rates_block

# Test with mixed success/failure
live_results = {
    'competitor_rates': {
        'Square': {
            'raw_patterns': ['2.6% + \$0.15'],
            'verified_date': '2026-06-29',
            'fetch_status': 'success'
        },
        'Helcim': {
            'raw_patterns': [],
            'verified_date': '',
            'fetch_status': 'failed'
        },
        'Stripe': {
            'raw_patterns': ['2.7% + \$0.05'],
            'verified_date': '2026-06-29',
            'fetch_status': 'success'
        }
    },
    'crawl_date': '2026-06-29'
}

block = build_competitor_rates_block(live_results)
print(block)
print()

# Verify content
assert 'LIVE COMPETITOR RATES — scraped 2026-06-29:' in block
assert '2.6% + \$0.15' in block
assert 'RATE UNVERIFIED' in block
assert 'GoDaddy POS Plus: 2.3% + \$0' in block
assert 'Rate Saver' in block
print('✅ All build_competitor_rates_block() tests passed')
"
```

Expected output should include:
```
LIVE COMPETITOR RATES — scraped 2026-06-29:
Use these exact figures. Where marked UNVERIFIED, do not state a specific rate.

- Square: 2.6% + $0.15 in-person Free plan (live 2026-06-29)
- Stripe: 2.7% + $0.05 in-person (live 2026-06-29)
- Helcim: RATE UNVERIFIED — fetch failed. Do not state a specific rate. Note as unverified.
...
```

- [ ] **Step 3: Commit build_competitor_rates_block()**

```bash
git add fill_session.py
git commit -m "feat: add build_competitor_rates_block() for prompt injection

- Builds full competitor rates section from live_results
- Calls parse_competitor_rate() for each competitor
- Injects explicit UNVERIFIED message on fetch failures
- Appends GoDaddy hardcoded product specs at end"
```

---

## Task 3: Update build_prompt_call1() to Use Dynamic Rates

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py:656-740` (build_prompt_call1 function)

**Interfaces:**
- Consumes: `build_competitor_rates_block(live_results: dict) -> str` (from Task 2)
- Produces: Updated `build_prompt_call1()` that injects dynamic rates block

- [ ] **Step 1: Update build_prompt_call1() to inject dynamic rates**

Find lines 675-677 in fill_session.py:

```python
"FIXED KNOWN RATES (always accurate):\n"
"- GoDaddy POS Plus: 2.3% + $0 in-person\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
```

Replace with:

```python
"FIXED KNOWN RATES (always accurate):\n"
"- GoDaddy POS Plus: 2.3% + $0 in-person\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
+ build_competitor_rates_block(live_results) + "\n\n"
```

- [ ] **Step 2: Verify build_prompt_call1() syntax**

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from fill_session import build_prompt_call1

# Should not throw syntax errors
print('✅ build_prompt_call1() syntax valid')
"
```

- [ ] **Step 3: Commit build_prompt_call1() update**

```bash
git add fill_session.py
git commit -m "feat: inject dynamic competitor rates into CaaS call 1 prompt

- Add build_competitor_rates_block() call after GoDaddy fixed rates
- Rates now flow from scraper -> prompt automatically
- GoDaddy product specs remain hardcoded (correct behavior)"
```

---

## Task 4: Update build_prompt_call2() to Use Dynamic Rates

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py:742-802` (build_prompt_call2 function)
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py:948` (main function call site)

**Interfaces:**
- Consumes: `build_competitor_rates_block(live_results: dict) -> str` (from Task 2)
- Produces: Updated `build_prompt_call2(session, strategy_actions, live_results)` with new signature

- [ ] **Step 1: Update build_prompt_call2() signature**

Change line 742 from:

```python
def build_prompt_call2(session, strategy_actions):
```

To:

```python
def build_prompt_call2(session, strategy_actions, live_results):
```

- [ ] **Step 2: Replace hardcoded rates in build_prompt_call2()**

Find lines 764-767:

```python
"VERIFIED RATES:\n"
"- GoDaddy POS Plus in-person: 2.3% + $0\n"
"- Square in-person: 2.6% + $0.15 (raised Feb 25 2025)\n"
"- Clover in-person: 2.3-2.6% + $0.10 direct + $29.95-$129.85/mo software\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
```

Replace entire block with:

```python
+ build_competitor_rates_block(live_results) + "\n\n"
```

- [ ] **Step 3: Update call site in main()**

Find line 948:

```python
prompt2 = build_prompt_call2(skeleton, strategy)
```

Replace with:

```python
prompt2 = build_prompt_call2(skeleton, strategy, live_results)
```

- [ ] **Step 4: Verify build_prompt_call2() syntax**

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from fill_session import build_prompt_call2

# Should not throw syntax errors
print('✅ build_prompt_call2() syntax valid')
"
```

- [ ] **Step 5: Commit build_prompt_call2() updates**

```bash
git add fill_session.py
git commit -m "feat: inject dynamic competitor rates into CaaS call 2 prompt

- Update signature to accept live_results parameter
- Replace hardcoded Square/Clover rates with dynamic block
- Update main() call site to pass live_results
- Both CaaS calls now use identical live scraped data"
```

---

## Task 5: Update generate_session_json.py Placeholders

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\generate_session_json.py:52-89` (COMPETITIVE_INTEL_VERIFIED)

**Interfaces:**
- Consumes: None (pure data update)
- Produces: Updated placeholder array with clear "Placeholder" labels

- [ ] **Step 1: Add placeholder comment header**

Find line 50-51 in generate_session_json.py:

```python
# ── Verified competitor rates (update when rates change) ────────────
# Square: raised from $0.10 to $0.15 on Feb 25, 2025 — confirmed squareup.com
```

Replace with:

```python
# ── Baseline placeholder — fill_session.py overwrites this with live data ──
# These values are NOT verified current rates. They exist only to keep
# session.json valid during the ~60 seconds between skeleton push and
# fill_session.py completing. Do not use these for content or outreach.
# When fill_session.py runs, it scrapes live rates and completely replaces
# this array via merge_session().
```

- [ ] **Step 2: Update COMPETITIVE_INTEL_VERIFIED array**

Replace lines 52-89 with:

```python
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
```

Note: Helcim updated from `~1.93% + $0.08` to `~1.79% + 8¢`

- [ ] **Step 3: Verify generate_session_json.py syntax**

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from generate_session_json import COMPETITIVE_INTEL_VERIFIED

assert len(COMPETITIVE_INTEL_VERIFIED) == 4
assert all('Placeholder' in item['event'] for item in COMPETITIVE_INTEL_VERIFIED)
helcim = next(item for item in COMPETITIVE_INTEL_VERIFIED if item['competitor'] == 'Helcim')
assert '1.79%' in helcim['detail'] or '1.79' in helcim['detail']
print('✅ generate_session_json.py placeholders valid')
"
```

- [ ] **Step 4: Commit generate_session_json.py updates**

```bash
git add generate_session_json.py
git commit -m "refactor: clarify COMPETITIVE_INTEL_VERIFIED as placeholder

- Add prominent comment explaining placeholder nature
- Update all event fields to say 'Placeholder'
- Update Helcim from 1.93% to 1.79% + 8¢ (current effective avg)
- Prevent confusion between skeleton and live-filled data"
```

---

## Task 6: Remove KNOWN_RATES Fallback from get_live_data()

**Files:**
- Modify: `C:\Users\tyunguyen\geo-dashboard\fill_session.py:586-615` (get_live_data function)

**Interfaces:**
- Consumes: None
- Produces: Updated `get_live_data()` that returns `"fetch_status": "failed"` instead of `"fallback"`

- [ ] **Step 1: Locate and remove KNOWN_RATES fallback**

Find lines 589-600 in fill_session.py (inside the `for comp in sorted(competitors_to_check):` loop):

```python
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
```

Replace with:

```python
        html = fetch_url(url)
        if not html:
            print(f"  [LIVE] ⚠️  Rate fetch failed for {comp} — will be marked unverified")
            results["fallback_used"].append(f"{comp} rates")
            results["competitor_rates"][comp] = {
                "raw_patterns": [],
                "source": url,
                "verified_date": "",
                "fetch_status": "failed",
                "note": "Fetch failed — rate unverified"
            }
            continue
```

- [ ] **Step 2: Verify get_live_data() syntax**

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from fill_session import get_live_data

# Should not throw syntax errors
print('✅ get_live_data() syntax valid')
"
```

- [ ] **Step 3: Commit KNOWN_RATES fallback removal**

```bash
git add fill_session.py
git commit -m "refactor: remove KNOWN_RATES fallback for explicit error signaling

- Replace silent fallback with fetch_status='failed'
- parse_competitor_rate() returns None for failed fetches
- build_competitor_rates_block() injects RATE UNVERIFIED message
- CaaS gets explicit instruction not to claim unverified rates"
```

---

## Task 7: Integration Testing with --dry-run

**Files:**
- Test: `C:\Users\tyunguyen\geo-dashboard\fill_session.py`
- Test: `C:\Users\tyunguyen\geo-dashboard\generate_session_json.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verification that prompts contain live dates, not hardcoded strings

- [ ] **Step 1: Generate skeleton with generate_session_json.py**

```bash
cd ~/geo-dashboard

# Generate a fresh skeleton from latest benchmark
python generate_session_json.py --weekly

# Verify session.json exists and has placeholder competitive_intel
python3 -c "
import json
with open('public/data/session.json') as f:
    data = json.load(f)
assert 'competitive_intel' in data
assert len(data['competitive_intel']) == 4
assert any('Placeholder' in item.get('event', '') for item in data['competitive_intel'])
print('✅ Skeleton generated with placeholders')
"
```

Expected: No errors, session.json created with placeholder competitive_intel

- [ ] **Step 2: Run fill_session.py with --dry-run**

```bash
# Set CAAS_API_KEY if not already set
export CAAS_API_KEY="${CAAS_API_KEY:-your-key-here}"

# Run fill_session.py in dry-run mode (doesn't write, shows output preview)
python fill_session.py --dry-run 2>&1 | tee /tmp/fill_session_dry_run.log
```

Expected output should include:
- `Calling CaaS proxy`
- `Prompt length: XXXXX chars`
- No hardcoded strings like "raised Feb 25 2025"

- [ ] **Step 3: Verify prompt contains live dates**

```bash
# Check that the dry-run log contains live rate format
grep -q "LIVE COMPETITOR RATES — scraped" /tmp/fill_session_dry_run.log && echo "✅ Live rates header found" || echo "❌ Missing live rates header"

# Verify no hardcoded date strings
! grep -q "raised Feb 25 2025" /tmp/fill_session_dry_run.log && echo "✅ No hardcoded dates" || echo "❌ Found hardcoded dates"

# Verify live date format present
grep -q "(live 202[0-9]-[0-9][0-9]-[0-9][0-9])" /tmp/fill_session_dry_run.log && echo "✅ Live date format found" || echo "❌ Missing live date format"
```

Expected: All checks pass with ✅

- [ ] **Step 4: Test with actual execution (optional, requires CAAS_API_KEY)**

```bash
# Only run this if CAAS_API_KEY is set and you want to verify end-to-end
# This will actually call CaaS and update session.json

# Backup current session.json
cp public/data/session.json public/data/session.json.backup

# Run fill_session.py (real execution)
python fill_session.py

# Check that competitive_intel was filled with live data
python3 -c "
import json
with open('public/data/session.json') as f:
    data = json.load(f)
assert 'competitive_intel' in data
assert len(data['competitive_intel']) > 0
# Should NOT have 'Placeholder' in event field anymore
has_placeholder = any('Placeholder' in item.get('event', '') for item in data['competitive_intel'])
assert not has_placeholder, 'competitive_intel still has placeholders after fill'
print('✅ session.json filled with live data (no placeholders)')
"

# Restore backup if needed
# cp public/data/session.json.backup public/data/session.json
```

- [ ] **Step 5: Commit integration test success**

```bash
git add -A
git commit -m "test: verify dynamic rate injection end-to-end

Integration test confirms:
- Skeleton generation with placeholders works offline
- fill_session.py --dry-run shows live dates not hardcoded strings
- LIVE COMPETITOR RATES header present in prompts
- No 'raised Feb 25 2025' hardcoded strings remain
- Full execution replaces placeholders with live data"
```

---

## Post-Implementation Checklist

After completing all tasks, verify:

- [ ] `parse_competitor_rate()` returns formatted strings for success, `None` for failure
- [ ] `build_competitor_rates_block()` injects "RATE UNVERIFIED" on fetch failures
- [ ] Both `build_prompt_call1()` and `build_prompt_call2()` use dynamic rates
- [ ] `generate_session_json.py` placeholders clearly labeled as non-authoritative
- [ ] KNOWN_RATES fallback removed from `get_live_data()`
- [ ] `--dry-run` shows live dates like "(live 2026-06-29)", not "raised Feb 25 2025"
- [ ] All commits follow conventional commits format
- [ ] No syntax errors in Python files

---

## Success Criteria

1. **Automatic updates:** When Helcim changes from 1.79% to 1.65%, the next `fill_session.py` run outputs the correct 1.65% rate with zero code changes.
2. **Clear errors:** When a fetch fails, CaaS prompt says "RATE UNVERIFIED" not a stale fallback rate.
3. **No duplication:** Scrape happens once in `main()`, results reused in both `build_prompt_call1()` and `build_prompt_call2()`.
4. **Offline skeleton:** `generate_session_json.py` runs successfully even when network is down.
5. **Test passes:** `--dry-run` shows live dates in prompt, not hardcoded strings.

---

## Rollback Plan

If this breaks production:

```bash
# Find the commit hash before this work
git log --oneline -10

# Revert all changes
git revert <commit-sha-range>

# Or hard reset (destructive)
git reset --hard <commit-before-changes>
git push --force-with-lease  # Only if needed and safe
```

The placeholders in `generate_session_json.py` are backward compatible — old `fill_session.py` will still overwrite them correctly.
