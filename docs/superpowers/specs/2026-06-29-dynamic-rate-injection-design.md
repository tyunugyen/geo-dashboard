# Dynamic Competitor Rate Injection — Design Specification

**Author:** Claude Sonnet 4.5  
**Date:** 2026-06-29  
**Status:** Approved  
**Scope:** fill_session.py, generate_session_json.py

---

## Problem Statement

Competitor rates are currently hardcoded in multiple locations:

1. `fill_session.py` lines 764-767 in `build_prompt_call2()` — hardcoded Square, Clover rates
2. `generate_session_json.py` lines 52-89 in `COMPETITIVE_INTEL_VERIFIED` — hardcoded Helcim "~1.93% + $0.08"
3. CaaS prompts receive these hardcoded strings, not live scraped data

When a competitor changes rates:
- Scraper finds new rate in `raw_patterns`
- Prompt still contains old hardcoded rate
- CaaS outputs wrong rate to session.json

**Example failure:** Helcim changes from 1.93% to 1.79%. Scraper detects it. Prompt says 1.93%. CaaS says 1.93%. Session.json is wrong.

**Root cause:** Rate data flows from scraper → `raw_patterns` but not from `raw_patterns` → prompt. The injection point uses hardcoded strings that never update.

---

## Design Goals

1. **Automatic rate updates** — When competitor rates change, new rates flow scraper → prompt → CaaS → session.json with zero code changes
2. **Clear error signaling** — When fetch fails, CaaS gets explicit "RATE UNVERIFIED" instruction, not a silent stale fallback
3. **Separation of concerns** — `generate_session_json.py` stays offline/fast. `fill_session.py` owns all network dependencies.
4. **No duplication** — Scrape once per execution, reuse across both CaaS calls

---

## Architecture Overview

### Separation of Concerns

Two scripts, two distinct responsibilities:

| Script | Job | When It Runs | Network Access |
|---|---|---|---|
| `generate_session_json.py` | Reads benchmark CSV → writes skeleton | After benchmark, needs to be fast and offline-safe | Should NOT need internet |
| `fill_session.py` | Fetches live data → fills intelligence arrays | Explicitly the live intelligence step | Needs internet + VPN for CaaS |

**Key principle:** `generate_session_json.py` runs as part of the benchmark pipeline — 9 AM Monday, automated, no human watching. It must not fail due to network issues. `fill_session.py` already owns live scraping responsibility. No duplication.

### Data Flow

```
generate_session_json.py → session.json (with placeholders)
                                ↓
fill_session.py scrapes live → build_competitor_rates_block()
                                ↓
                           CaaS prompt (with live rates)
                                ↓
                     CaaS fills competitive_intel[]
                                ↓
                     merge_session() overwrites placeholders
                                ↓
                        final session.json (live data)
```

The placeholder in `generate_session_json.py` ensures session.json is valid JSON during the ~60 seconds between skeleton push and fill completion. `merge_session()` in `fill_session.py` completely replaces it with live data.

---

## Implementation Details

### 1. New Functions in fill_session.py

#### Function: `parse_competitor_rate(competitor, rate_data)`

**Purpose:** Convert raw scraped rate patterns into clean, dated strings ready for CaaS prompt injection.

**Signature:**
```python
def parse_competitor_rate(competitor: str, rate_data: dict) -> str | None
```

**Inputs:**
- `competitor`: Competitor name ("Square", "Stripe", "Helcim", "Clover", etc.)
- `rate_data`: Dict with structure:
  ```python
  {
      "raw_patterns": ["2.6% + $0.15", "2.5% + $0.15", ...],
      "verified_date": "2026-06-29",
      "fetch_status": "success" | "failed"
  }
  ```

**Output:**
- Formatted string like `"2.6% + $0.15 in-person Free plan (live 2026-06-29)"`
- `None` if fetch failed and no valid pattern found

**Logic per competitor:**

**Helcim:**
- Find the **effective average rate** (e.g., "1.79% + 8¢"), NOT the interchange-plus margin (0.40%)
- The compare page shows both. The effective average is what merchants and NerdWallet compare against.
- Pattern match: look for rates in the 1.5%-2.0% range with 8¢ or $0.08 fixed fee
- Format: `"{rate} interchange-plus average (live {verified_date})"`

**Square:**
- Find Free plan rate (2.6% range, $0.15 fixed fee)
- Distinguish from Plus (2.5%) and Premium (2.4%)
- Pattern match: look for "2.6% + $0.15" or "2.6% + 15"
- Format: `"{rate} in-person Free plan (live {verified_date})"`

**Stripe:**
- Find in-person rate (look for $0.05 fixed fee)
- Stripe page leads with online rate (2.9% + $0.30), need to find the in-person section
- Pattern match: look for rates with "5¢" or "$0.05" or "0.05"
- Format: `"{rate} in-person (live {verified_date})"`

**Clover:**
- Find in-person rate (2.3-2.6% range, $0.10 fixed fee)
- Append monthly software fee note
- Pattern match: look for rates with "10¢" or "$0.10" or "0.10"
- Format: `"{rate} in-person + software fee $29.95–$129.85/mo (live {verified_date})"`

**Generic fallback:**
- If specific logic doesn't match, return first pattern found with verified date
- Format: `"{patterns[0]} (live {verified_date})"`

**Error handling:**
- If `fetch_status == "failed"` or `raw_patterns` is empty, return `None`
- Caller will inject "RATE UNVERIFIED" message

---

#### Function: `build_competitor_rates_block(live_results)`

**Purpose:** Build the entire competitor rates section of the CaaS prompt dynamically from live scrape results.

**Signature:**
```python
def build_competitor_rates_block(live_results: dict) -> str
```

**Input:**
- `live_results`: The dict returned by `get_live_data()`, contains:
  ```python
  {
      "competitor_rates": {
          "Square": { "raw_patterns": [...], "verified_date": "...", "fetch_status": "..." },
          "Helcim": { ... },
          ...
      },
      "crawl_date": "2026-06-29",
      "fallback_used": [...]
  }
  ```

**Output:**
Multi-line string for injection into CaaS prompt:

```
LIVE COMPETITOR RATES — scraped 2026-06-29:
Use these exact figures. Where marked UNVERIFIED, do not state a specific rate.

- Square: 2.6% + $0.15 in-person Free plan (live 2026-06-29)
- Helcim: 1.79% + 8¢ interchange-plus average (live 2026-06-29)
- Clover: 2.3% + $0.10 in-person + software fee $29.95–$129.85/mo (live 2026-06-29)
- Stripe: 2.7% + $0.05 in-person (live 2026-06-29)
- GoDaddy POS Plus: 2.3% + $0 in-person (product spec — always accurate)
- Rate Saver: 0% credit, 1.9% + $0 debit in-person. NOT in CT, MA, PR or ecommerce
```

**For failed fetches:**
```
- Helcim: RATE UNVERIFIED — fetch failed. Do not state a specific rate. Note as unverified.
```

**Order:**
1. Header with crawl date
2. Instruction line for CaaS
3. Blank line
4. Competitor rates (Square, Stripe, Helcim, Clover, Toast, Shopify — in that order)
5. GoDaddy rates (POS Plus, Rate Saver) — always accurate, never scraped

**Why:** This gives CaaS clear, unambiguous rate data with explicit dates and fetch status. When a rate is unverified, CaaS knows not to make a specific claim.

---

### 2. Changes to Existing Functions

#### `build_prompt_call1()` (lines 656-740)

**Current state (lines 675-677):**
```python
"FIXED KNOWN RATES (always accurate):\n"
"- GoDaddy POS Plus: 2.3% + $0 in-person\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
```

**Change:**
Keep the GoDaddy fixed rates (correct — these are product specs). Add dynamic competitor rates block immediately after:

```python
"FIXED KNOWN RATES (always accurate):\n"
"- GoDaddy POS Plus: 2.3% + $0 in-person\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
+ build_competitor_rates_block(live_results) + "\n\n"
```

**Why:** GoDaddy's own rates stay hardcoded (they're product specs that only change on deliberate product decisions). Competitor rates are injected dynamically from live scrape.

---

#### `build_prompt_call2()` (lines 742-802)

**Current state (lines 764-767):**
```python
"VERIFIED RATES:\n"
"- GoDaddy POS Plus in-person: 2.3% + $0\n"
"- Square in-person: 2.6% + $0.15 (raised Feb 25 2025)\n"
"- Clover in-person: 2.3-2.6% + $0.10 direct + $29.95-$129.85/mo software\n"
"- Rate Saver: 0% credit, 1.9% + $0 debit. NOT in CT, MA, PR or ecommerce\n\n"
```

**Change:**
Replace entire hardcoded block with dynamic injection:

```python
+ build_competitor_rates_block(live_results) + "\n\n"
```

**Signature change:**
```python
# From:
def build_prompt_call2(session, strategy_actions):

# To:
def build_prompt_call2(session, strategy_actions, live_results):
```

**Call site change in `main()`:**
```python
# From (line 948):
prompt2 = build_prompt_call2(skeleton, strategy)

# To:
prompt2 = build_prompt_call2(skeleton, strategy, live_results)
```

**Why:** `live_results` is already in scope in `main()` when `build_prompt_call2()` is called. Reuse the same scraped data — no additional network calls. Both CaaS calls get identical rate data.

---

### 3. Changes to generate_session_json.py

#### `COMPETITIVE_INTEL_VERIFIED` (lines 52-89)

**Current state:**
Hardcoded competitor rates that look authoritative but go stale.

**Change:**
Add prominent comments clarifying this is a placeholder. Update Helcim value from `~1.93% + $0.08` to `~1.79% + 8¢`.

```python
# ── Baseline placeholder — fill_session.py overwrites this with live data ──
# These values are NOT verified current rates. They exist only to keep
# session.json valid during the ~60 seconds between skeleton push and
# fill_session.py completing. Do not use these for content or outreach.
# When fill_session.py runs, it scrapes live rates and completely replaces
# this array via merge_session().
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
        "competitor": "Helcim",
        "event": "Placeholder — fill_session.py will overwrite with live rate",
        "detail": "Last known: ~1.79% + 8¢ average interchange-plus",
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

**Why:** The word "Placeholder" appears in the `event` field so it's visible in the actual JSON output, not just in source code comments. The `merge_session()` function in `fill_session.py` completely overwrites this array when live data is available.

---

### 4. Error Handling

#### When a competitor rate fetch fails

**Flow:**
1. `get_live_data()` fetches URL → HTML is `None`
2. `rate_data["fetch_status"] = "failed"`
3. `parse_competitor_rate()` returns `None`
4. `build_competitor_rates_block()` injects: `"- Helcim: RATE UNVERIFIED — fetch failed. Do not state a specific rate. Note as unverified."`
5. CaaS sees explicit instruction not to claim a specific rate

**Why:** An explicit "unverified" signal is better than a silent fallback to stale rates. CaaS knows to hedge or omit the rate rather than confidently stating a wrong number.

#### When ALL fetches fail

`build_competitor_rates_block()` still generates a valid block with all competitors marked as unverified. CaaS gets instructed to note rates as estimated/unverified. The prompt does not become malformed or empty.

#### Remove KNOWN_RATES fallback from get_live_data()

**Current behavior (lines 594-600):**
When fetch fails, falls back to `KNOWN_RATES` from `config/publisher_urls.py` and marks as `"fetch_status": "fallback"`.

**Change:**
Remove this fallback. If fetch fails, set `"fetch_status": "failed"` and move on.

**Why:**
- A silent fallback to stale rates is worse than an explicit "unverified" signal
- If CaaS receives a stale rate presented as current, it confidently states a wrong number
- If CaaS receives "RATE UNVERIFIED", it knows not to make a specific claim
- The `generate_session_json.py` placeholder already handles the "session.json must be valid" requirement
- The fallback in `fill_session.py` is redundant and dangerous

**Code change:**
```python
# Delete lines 594-600 in get_live_data():
if comp in KNOWN_RATES:
    results["competitor_rates"][comp] = {
        "raw_patterns": [KNOWN_RATES[comp].get("in_person", "")],
        "source": url,
        "verified_date": KNOWN_RATES[comp].get("verified_date", ""),
        "fetch_status": "fallback",
        "note": "Fetch failed — using last known rate"
    }
```

Replace with:
```python
results["competitor_rates"][comp] = {
    "raw_patterns": [],
    "source": url,
    "verified_date": "",
    "fetch_status": "failed",
    "note": "Fetch failed — rate unverified"
}
```

---

### 5. What Changes When Rates Update

#### Before (current broken state)

Helcim changes rate → scraper finds new pattern → hardcoded prompt still says old rate → CaaS outputs wrong rate

#### After (proposed fix)

Helcim changes rate → scraper finds new pattern → `parse_competitor_rate()` formats it → `build_competitor_rates_block()` injects it → CaaS outputs correct rate

**No code changes needed when competitor rates change.** The flow is fully automatic.

#### Human update still required when

1. **GoDaddy's own rates change** (POS Plus, Rate Saver) — these stay hardcoded in prompts as product specs. They only change on deliberate product decisions.
2. **New competitor needs to be tracked** — add to `COMPETITOR_RATE_URLS` in `config/publisher_urls.py`

**Why:** This is the right balance between automation and human oversight. GoDaddy rates are product decisions, not scraped facts. New competitors require a judgment call about whether they belong in the tracking set. Everything else is automatic.

---

## Implementation Order

Implement in this exact order to minimize breaking changes:

1. **`parse_competitor_rate()`** — Write function. Unit test with sample `rate_data` dicts.
2. **`build_competitor_rates_block()`** — Write function. Test with mock `live_results`.
3. **Update `build_prompt_call1()`** — Add the block after GoDaddy fixed rates.
4. **Update `build_prompt_call2()`** — Replace hardcoded lines, add `live_results` parameter.
5. **Update `generate_session_json.py`** — Add comments, update Helcim placeholder value.
6. **Remove `KNOWN_RATES` fallback** — Delete fallback logic from `get_live_data()`.
7. **Test** — Run `python fill_session.py --dry-run` and confirm the prompt contains live dates, not hardcoded strings.

---

## Testing Plan

### Unit tests (manual verification)

**Test `parse_competitor_rate()`:**
```python
# Success case — Helcim
rate_data = {
    "raw_patterns": ["1.79% + 8¢", "0.40% + 8¢"],
    "verified_date": "2026-06-29",
    "fetch_status": "success"
}
result = parse_competitor_rate("Helcim", rate_data)
assert "1.79% + 8¢" in result
assert "live 2026-06-29" in result

# Failure case
rate_data = {"raw_patterns": [], "verified_date": "", "fetch_status": "failed"}
result = parse_competitor_rate("Helcim", rate_data)
assert result is None
```

**Test `build_competitor_rates_block()`:**
```python
live_results = {
    "competitor_rates": {
        "Square": {
            "raw_patterns": ["2.6% + $0.15"],
            "verified_date": "2026-06-29",
            "fetch_status": "success"
        },
        "Helcim": {
            "raw_patterns": [],
            "verified_date": "",
            "fetch_status": "failed"
        }
    },
    "crawl_date": "2026-06-29"
}
block = build_competitor_rates_block(live_results)
assert "2.6% + $0.15" in block
assert "RATE UNVERIFIED" in block
assert "2026-06-29" in block
```

### Integration test

Run full pipeline:
```bash
# Generate skeleton
cd ~/geo-dashboard
python generate_session_json.py --weekly

# Fill with live data (dry run)
python fill_session.py --dry-run

# Check prompt output
# Should see:
# - "LIVE COMPETITOR RATES — scraped 2026-06-29:"
# - Actual dates like "(live 2026-06-29)"
# - NO hardcoded strings like "raised Feb 25 2025"
```

---

## Success Criteria

1. **Automatic updates:** When Helcim changes from 1.79% to 1.65%, the next `fill_session.py` run outputs the correct 1.65% rate with zero code changes.
2. **Clear errors:** When a fetch fails, CaaS prompt says "RATE UNVERIFIED" not a stale fallback rate.
3. **No duplication:** Scrape happens once in `main()`, results reused in both `build_prompt_call1()` and `build_prompt_call2()`.
4. **Offline skeleton:** `generate_session_json.py` runs successfully even when network is down.
5. **Test passes:** `--dry-run` shows live dates in prompt, not hardcoded strings.

---

## Non-Goals

- **Not** making `generate_session_json.py` scrape live rates (it stays offline)
- **Not** storing historical rate changes (out of scope — focus on current rates only)
- **Not** adding new competitors to tracking (that's a separate decision)
- **Not** validating rate math or calculating savings (CaaS does that)

---

## Related Files

- `fill_session.py` — main implementation
- `generate_session_json.py` — placeholder updates only
- `config/publisher_urls.py` — COMPETITOR_RATE_URLS map, KNOWN_RATES (to be deprecated)
- `public/data/session.json` — final output

---

## Rollback Plan

If this breaks production:

1. Revert `fill_session.py` changes — restore hardcoded strings in `build_prompt_call1()` and `build_prompt_call2()`
2. Revert `generate_session_json.py` comments (optional — doesn't affect runtime)
3. Git: `git revert <commit-sha>` or `git reset --hard <previous-commit>`

The placeholders in `generate_session_json.py` are backward compatible — old `fill_session.py` will still overwrite them correctly.
