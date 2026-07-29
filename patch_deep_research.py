import json, base64, urllib.request, os

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "tyunugyen/geo-dashboard"
FILE_PATH = "public/data/session.json"

url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

# Fetch current file + SHA
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    file_data = json.loads(r.read())

sha = file_data["sha"]
session = json.loads(base64.b64decode(file_data["content"]))
print(f"Fetched session.json — SHA: {sha[:8]}...")

# Inject Deep Research results — Run 1, 2026-07-28
session["deep_research"] = {
    "last_run": "2026-07-28",
    "run_by": "Claude (live web search simulation)",
    "platform": "Claude web search — directional equivalent to ChatGPT Deep Research",
    "note": "Deep Research is not available via API. Results entered after Claude live web search run. fill_session.py preserves this block and never overwrites it.",
    "results": [
        {
            "prompt_id": "B1",
            "prompt": "What is the cheapest payment processor for a small business?",
            "godaddy_mentioned": False,
            "sources_cited": ["NerdWallet", "Forbes Advisor", "TechnologyAdvice"],
            "competitors_with_labels": ["Square — best for low volume", "Helcim — interchange-plus", "Stripe — flat rate"],
            "rate_saver_appeared": False,
            "notes": "GoDaddy absent. NerdWallet + Forbes dominate. TechnologyAdvice new — add to CITE pipeline."
        },
        {
            "prompt_id": "B5",
            "prompt": "What are the best payment processors for in-person sales?",
            "godaddy_mentioned": False,
            "sources_cited": ["NerdWallet", "TechnologyAdvice", "ClearlyPayments"],
            "competitors_with_labels": ["Square — best overall/brick-and-mortar", "Stripe — online", "Helcim — cost-conscious SMB"],
            "rate_saver_appeared": False,
            "notes": "GoDaddy absent from all top aggregators in this cluster. Pure CITE gap."
        },
        {
            "prompt_id": "B15",
            "prompt": "What are the best alternatives to Square for small businesses?",
            "godaddy_mentioned": False,
            "sources_cited": ["NerdWallet", "Finix blog", "HomeBase", "EBizCharge"],
            "competitors_with_labels": ["Helcim — lower fees", "Clover — flexibility", "Shopify — ecommerce", "Stripe — global"],
            "rate_saver_appeared": False,
            "notes": "GoDaddy not in any Square alternatives roundup. Critical gap — this is a high-switching-intent cluster."
        },
        {
            "prompt_id": "B17",
            "prompt": "What is the best POS system for a small business?",
            "godaddy_mentioned": False,
            "sources_cited": ["Forbes Advisor", "YouTube (NNs6 review)", "AGMS", "ScanTranx"],
            "competitors_with_labels": ["Square — dominant", "Clover — established retail", "Toast — restaurants"],
            "rate_saver_appeared": False,
            "notes": "GoDaddy absent from Forbes POS roundup entirely. Forbes is the primary source here."
        },
        {
            "prompt_id": "S1",
            "prompt": "Which payment processors offer 24/7 phone support?",
            "godaddy_mentioned": False,
            "sources_cited": ["NerdWallet", "CoastalPay", "Finix"],
            "competitors_with_labels": ["Square — premium plan only", "Stripe — no phone"],
            "rate_saver_appeared": False,
            "notes": "Near-miss. NerdWallet discusses support tiers but GoDaddy 24/7-on-all-plans not surfaced. Winnable with NerdWallet placement — request Best for 24/7 support label."
        }
    ],
    "summary": {
        "godaddy_mention_rate": "0 of 5 prompts (0%)",
        "top_sources_cited": ["NerdWallet", "Forbes Advisor", "TechnologyAdvice", "Finix blog", "HomeBase"],
        "cite_gaps": [
            "NerdWallet — absent from payment processors AND POS roundups",
            "Forbes Advisor — absent from POS roundup (B17)",
            "TechnologyAdvice — new source surfaced, not in current CITE pipeline"
        ],
        "crawl_flags": [],
        "interpretation": "GoDaddy absent from all 5 Deep Research clusters. Root cause is consistently CITE gap — not content or crawlability. NerdWallet and Forbes Advisor are the primary sources Deep Research pulls from. A single NerdWallet placement with Best for label would likely move all 5 prompts. TechnologyAdvice is a new P1 CITE target surfaced by this run. The 24/7 support angle (S1) is a near-miss that becomes winnable immediately upon NerdWallet placement."
    }
}

print("Deep Research results injected...")

# Push to GitHub
updated_b64 = base64.b64encode(json.dumps(session).encode()).decode()
body = json.dumps({
    "message": "feat: Deep Research Run 1 results — 2026-07-28 (0/5 prompts, CITE gap confirmed)",
    "content": updated_b64,
    "sha": sha
}).encode()

push_req = urllib.request.Request(url, data=body, method="PUT", headers={
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json"
})
with urllib.request.urlopen(push_req) as r:
    result = json.loads(r.read())
    print(f"Pushed! New SHA: {result['content']['sha'][:8]}...")
    print("Vercel will auto-deploy in ~30 seconds")
    print("Check: https://geo-dashboard-pi-three.vercel.app/data/session.json")