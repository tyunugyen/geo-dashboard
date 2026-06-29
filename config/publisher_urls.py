"""
Publisher and competitor URL mappings for dynamic live crawling.
Used by fill_session.py to determine what to crawl based on cite_pipeline and strategy_actions.
"""

# ── Publisher URL Map ────────────────────────────────────────────────────
# Maps publisher names to their citation page URLs
# Key: Publisher name (must match cite_pipeline entries)
# Value: Dict of section names to URLs

PUBLISHER_URL_MAP = {
    "NerdWallet": {
        "Best Payment Processors":             "https://www.nerdwallet.com/business/software/learn/payment-processors",
        "Best POS Systems":                    "https://www.nerdwallet.com/best/small-business/payment-processing-companies",
        "Best Payment Processing Companies":   "https://www.nerdwallet.com/best/small-business/payment-processing-companies",
        "Surcharging Guide":                   "https://www.nerdwallet.com/business/software/learn/passing-on-credit-card-fees-to-customers",
        "Pass Fees to Customers":              "https://www.nerdwallet.com/business/software/learn/passing-on-credit-card-fees-to-customers",
    },
    "Forbes Advisor": {
        "Best Payment Processing Companies":   "https://www.forbes.com/advisor/business/software/best-payment-processing-companies/",
        "Best POS Systems":                    "https://www.forbes.com/advisor/business/software/best-pos-system-for-small-business/",
        "Best Retail POS":                     "https://www.forbes.com/advisor/business/software/best-retail-pos-system/",
        "Best Restaurant POS":                 "https://www.forbes.com/advisor/business/software/best-restaurant-pos-system/",
    },
    "Wise": {
        "Best Payment Processors for Small Business": "https://wise.com/us/blog/cheapest-way-to-accept-credit-cards",
        "Cheapest Credit Card Processing":             "https://wise.com/us/blog/cheapest-way-to-accept-credit-cards",
    },
    "Business.com": {
        "Best Credit Card Processing Companies": "https://www.business.com/categories/credit-card-processing-for-small-business/",
        "Best Payment Processors":               "https://www.business.com/categories/credit-card-processing-for-small-business/",
    },
    "TechRadar": {
        "Best POS Systems for Small Business": "https://www.techradar.com/best/best-pos-system",
        "Best POS Systems":                    "https://www.techradar.com/best/best-pos-system",
    },
    "FitSmallBusiness": {
        "Cheapest Credit Card Processing":     "https://fitsmallbusiness.com/cheapest-credit-card-processing/",
        "Best Payment Processors":             "https://fitsmallbusiness.com/best-credit-card-processing-companies/",
    },
    "Investopedia": {
        "Best Payment Processors":             "https://www.investopedia.com/best-payment-processors-5088735",
        "Best Credit Card Processing":         "https://www.investopedia.com/best-payment-processors-5088735",
    },
    "Merchant Maverick": {
        "Best Payment Processors":             "https://www.merchantmaverick.com/reviews/",
        "Payment Processor Reviews":           "https://www.merchantmaverick.com/reviews/",
    },
}

# ── Competitor Rate URLs ─────────────────────────────────────────────────
# Direct links to competitor pricing pages
# Used to verify rates mentioned in strategy_actions

COMPETITOR_RATE_URLS = {
    "Square":   "https://squareup.com/us/en/payments/our-fees",
    "Stripe":   "https://stripe.com/pricing",
    "Helcim":   "https://www.helcim.com/pricing/",
    "Clover":   "https://www.clover.com/pricing",
    "Toast":    "https://pos.toasttab.com/pricing",
    "Shopify":  "https://www.shopify.com/pricing",
    "PayPal":   "https://www.paypal.com/us/webapps/mpp/merchant-fees",
    "Finix":    "https://www.finixpayments.com/pricing",
    "Lightspeed": "https://www.lightspeedhq.com/pos/restaurant/pricing/",
    "Stax":     "https://www.staxpayments.com/pricing/",
}

# ── Known Rate Patterns ──────────────────────────────────────────────────
# Fallback rates when live fetch fails
# These are updated monthly when rates are verified

KNOWN_RATES = {
    "Square": {
        "in_person": "2.6% + $0.15",
        "online": "3.3% + $0.30",
        "verified_date": "2026-06-25",
        "source": "squareup.com/us/en/payments/our-fees",
        "note": "Raised from 2.6% + $0.10 on Feb 25, 2025"
    },
    "Stripe": {
        "in_person": "2.7% + $0.05",
        "online": "2.9% + $0.30",
        "verified_date": "2026-06-25",
        "source": "stripe.com/pricing",
        "note": "No phone support"
    },
    "Helcim": {
        "in_person": "~1.93% + $0.08 interchange-plus",
        "online": "interchange + 0.50% + $0.25",
        "verified_date": "2026-06-25",
        "source": "helcim.com/pricing",
        "note": "NerdWallet: Best for volume discounts"
    },
    "Clover": {
        "in_person": "2.3-2.6% + $0.10 direct",
        "monthly": "$29.95-$129.85/mo software",
        "verified_date": "2026-06-25",
        "source": "clover.com/pricing",
        "note": "Direct pricing varies by package"
    },
    "GoDaddy": {
        "pos_plus": "2.3% + $0 in-person",
        "rate_saver": "0% credit, 1.9% + $0 debit",
        "verified_date": "2026-06-25",
        "source": "godaddy.com/payments",
        "note": "Rate Saver not available in CT, MA, PR or ecommerce"
    },
}
