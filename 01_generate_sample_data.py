"""01_generate_sample_data.py
================================================================================
Generate realistic *raw export* files for the PureGlow KPI dashboard prototype.

Each file mirrors the column layout you actually get when you export from the
real platform, so the ETL step (02_build_kpi_tables.py) demonstrates the same
cleaning/joining work PureGlow would do in production:

  data/raw/google_ads_keyword_report.csv  - Google Ads "Search keyword" report,
                                            segmented by Day. Has the 2 preamble
                                            lines a real Google Ads export ships
                                            with. GCLID is NOT in this export -
                                            it is captured CRM-side (see below).
  data/raw/ga4_landing_pages.csv          - GA4 Landing-page report (Data API /
                                            UI export). Dates in GA4's YYYYMMDD
                                            format; has '#' comment preamble.
  data/raw/hubspot_contacts.csv           - HubSpot Contacts export (lead funnel).
                                            This is where the Google Click ID
                                            actually lives (hs_google_click_id).
  data/raw/hubspot_deals.csv              - HubSpot Deals export (e-commerce
                                            orders + a few open deals).
  data/raw/hubspot_email_performance.csv  - HubSpot Marketing Email performance.
  data/raw/hubspot_carts.csv              - HubSpot/Shopify abandoned-cart export.
  data/raw/hubspot_open_pipeline.csv      - HubSpot deal-forecast snapshot.

The numbers are calibrated so the KPIs computed downstream land near the
PureGlow case study's 12-month outcome data and trend toward the 6-month-phase
targets in the alignment document. This is SYNTHETIC data for an MBA case
prototype - it is not real PureGlow data.
================================================================================
"""
import csv
import os
import random
from datetime import date, timedelta

SEED = 42
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
CONFIG = os.path.join(HERE, "config")
os.makedirs(RAW, exist_ok=True)
os.makedirs(CONFIG, exist_ok=True)

# ---------------------------------------------------------------- time window
# 12-month implementation period from the case study (Schroeder, 2026):
# starts April 2025 (the "before" state) and ends April 2026 (the case's
# 12-month outcome snapshot - $7.1M annualised revenue, 4.3x ROAS, etc.).
PHASE_START = date(2025, 4, 1)
TODAY = date(2026, 4, 30)
DATES = [PHASE_START + timedelta(d) for d in range((TODAY - PHASE_START).days + 1)]
N = len(DATES)


def lerp(a, b, t):
    return a + (b - a) * t


def noise(pct=0.06):
    return random.uniform(1 - pct, 1 + pct)


# DTC skincare: mild weekly seasonality, small weekend lift
WEEKDAY_FACTOR = {0: 0.99, 1: 0.97, 2: 0.97, 3: 1.00, 4: 1.03, 5: 1.05, 6: 1.02}


# ================================================================ keyword plan
# (campaign, ad group, keyword, match type, intent tier, crm_verified,
#  weight at phase start, weight at phase end)
# Weights shift toward high-intent over the phase -> % high-intent spend rises.
KEYWORDS = [
    ("Best Serum for Dry Skin", "Vitamin C Serum", "best vitamin c serum for dry skin",
     "Exact match", "Tier 1 - High Intent", True, 0.16, 0.18),
    ("Best Serum for Dry Skin", "Hydrating Serum", "buy hydrating face serum online",
     "Exact match", "Tier 1 - High Intent", True, 0.13, 0.15),
    ("SPF Moisturizer Bundle", "SPF Bundle", "spf moisturizer bundle",
     "Exact match", "Tier 1 - High Intent", True, 0.12, 0.14),
    ("SPF Moisturizer Bundle", "Daily SPF", "buy spf moisturizer online",
     "Exact match", "Tier 1 - High Intent", True, 0.09, 0.10),
    ("Skincare Routine Quiz", "Routine Quiz", "best skincare routine for dry skin",
     "Phrase match", "Tier 2 - Mid Intent", True, 0.08, 0.09),
    ("Skincare Routine Quiz", "Plant Based", "plant based moisturizer",
     "Phrase match", "Tier 2 - Mid Intent", True, 0.07, 0.07),
    ("Best Serum for Dry Skin", "Natural Serum", "natural skincare routine",
     "Phrase match", "Tier 2 - Mid Intent", False, 0.07, 0.06),
    ("SPF Moisturizer Bundle", "Vegan SPF", "vegan spf moisturizer",
     "Phrase match", "Tier 2 - Mid Intent", True, 0.05, 0.06),
    ("Brand Defense", "Brand Core", "pureglow skincare",
     "Exact match", "Tier 3 - Brand Defense", True, 0.06, 0.06),
    ("Brand Defense", "Brand Product", "pureglow vitamin c serum",
     "Exact match", "Tier 3 - Brand Defense", True, 0.05, 0.05),
    ("Brand Defense", "Brand Bundle", "pureglow spf bundle",
     "Exact match", "Tier 3 - Brand Defense", True, 0.03, 0.03),
    # legacy broad-match leftovers being phased down (not CRM-verified)
    ("Best Serum for Dry Skin", "Broad Skincare", "skincare",
     "Broad match", "Untiered - Broad", False, 0.07, 0.03),
    ("SPF Moisturizer Bundle", "Broad Moisturizer", "moisturizer",
     "Broad match", "Untiered - Broad", False, 0.06, 0.03),
]

LANDING_PAGES = [
    # (url, channel, base conv-rate start, base conv-rate end, bounce start, bounce end, traffic weight)
    ("/lp/free-serum-sample",      "Paid search",    0.030, 0.043, 0.66, 0.55, 0.30),
    ("/lp/spf-bundle-20-off",      "Paid search",    0.052, 0.066, 0.55, 0.45, 0.26),
    ("/lp/skincare-routine-quiz",  "Paid search",    0.028, 0.040, 0.61, 0.50, 0.18),
    ("/products/vitamin-c-serum",  "Landing / site", 0.034, 0.045, 0.58, 0.49, 0.12),
    ("/collections/bestsellers",   "Landing / site", 0.022, 0.030, 0.64, 0.57, 0.08),
    ("/",                          "Other",          0.012, 0.017, 0.71, 0.66, 0.06),
]

EMAIL_SEGMENTS = [
    # (segment, open-rate start, end, ctr start, end, sends/send-day start, end)
    # Segmented programme begins as a pilot and matures over the year to the
    # case's 12-month outcome (31% open, 5.2% CTR blended across segments).
    ("New Leads",        0.17, 0.32, 0.022, 0.058, 600,  1950),
    ("Cart Abandoners",  0.18, 0.36, 0.025, 0.070, 200,  820),
    ("First-Time Buyers",0.16, 0.31, 0.020, 0.052, 350,  1150),
    ("Lapsed Customers", 0.13, 0.28, 0.018, 0.046, 450,  1250),
    ("VIP Loyalists",    0.20, 0.42, 0.028, 0.080, 140,  470),
]

TRAFFIC_SOURCES = [
    ("Paid Search", "google / cpc"),
    ("Organic Search", "google / organic"),
    ("Social Media", "instagram / social"),
    ("Direct Traffic", "(direct) / (none)"),
    ("Email Marketing", "hubspot / email"),
]


def write_csv(path, header, rows, preamble=None):
    with open(path, "w", newline="") as f:
        if preamble:
            for line in preamble:
                f.write(line + "\n")
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, HERE)}  ({len(rows):,} rows)")


# ================================================================ daily plan
# Build one calibrated "plan" per day, then emit raw rows from it.
plan = []
for i, d in enumerate(DATES):
    t = i / (N - 1)
    wf = WEEKDAY_FACTOR[d.weekday()]

    # Endpoints chosen to land at the case's 12-month outcome data:
    #   revenue 4.2M -> 7.1M (annualised), ROAS 1.8x -> 4.3x, CPA $34 -> $16.50,
    #   L2C 2.1% -> 5.6%, cart recovery N/A -> 22%, email open 14% -> 31%.
    # Hidden constraint that links everything: AOV = ROAS x CPA. At start
    # 1.8 x 34 = $61.2; at end 4.3 x 16.5 = $70.95. So AOV lerps 61 -> 71.
    monthly_revenue = lerp(350_000, 592_000, t)          # $4.2M -> $7.1M annualised
    revenue = monthly_revenue / 30.0 * wf * noise(0.07)
    aov = lerp(61.0, 71.0, t) * noise(0.03)
    orders = max(1, round(revenue / aov))
    revenue = round(orders * aov, 2)

    roas_paid = lerp(1.80, 4.30, t) * noise(0.03)        # case before/after
    paid_share = lerp(0.75, 0.85, t)                     # paid share grows with discipline
    paid_orders = max(1, round(orders * paid_share))
    paid_revenue = round(paid_orders * aov, 2)
    ad_spend = round(paid_revenue / roas_paid, 2)

    returning_share = lerp(0.12, 0.38, t)                # no retention -> mature programme
    returning_orders = round(orders * returning_share)
    new_customers = orders - returning_orders
    returning_revenue = round(returning_orders * aov, 2)

    cpc = lerp(2.10, 1.05, t) * noise(0.04)              # broad keywords are expensive
    clicks = max(1, round(ad_spend / cpc))
    ctr = lerp(0.0210, 0.0520, t) * noise(0.04)          # case's CTR target >=4.5%
    impressions = round(clicks / ctr)

    leads = max(1, round(lerp(55, 120, t) * wf * noise(0.10)))
    l2c = lerp(0.021, 0.060, t)                          # case 2.1% -> 5.6%
    leads_converted = round(leads * l2c * noise(0.10))

    carts = max(1, round(lerp(70, 150, t) * wf * noise(0.10)))
    recovery_rate = lerp(0.000, 0.245, t) * noise(0.05)  # no programme -> 22% (case)
    carts_recovered = round(carts * recovery_rate)

    clv_value = round(aov * lerp(1.40, 2.05, t) * 0.70, 2)   # AOV x freq x 70% margin

    nm_target = lerp(370_000, 615_000, t)                    # next-month revenue target
    coverage = lerp(1.10, 1.65, t) * noise(0.04)
    open_pipeline = round(coverage * nm_target, 2)

    plan.append(dict(
        d=d, t=t, revenue=revenue, aov=aov, orders=orders, paid_orders=paid_orders,
        paid_revenue=paid_revenue, ad_spend=ad_spend, returning_orders=returning_orders,
        returning_revenue=returning_revenue, new_customers=new_customers,
        cpc=cpc, clicks=clicks, ctr=ctr, impressions=impressions, leads=leads,
        leads_converted=leads_converted, carts=carts, carts_recovered=carts_recovered,
        clv_value=clv_value, open_pipeline=open_pipeline, roas_paid=roas_paid,
    ))

print(f"Generating raw exports for {N} days ({PHASE_START} -> {TODAY})...")

# ================================================================ Google Ads
gads_rows = []
for p in plan:
    d = p["d"]
    t = p["t"]
    wts = [(kw, lerp(kw[6], kw[7], t)) for kw in KEYWORDS]
    total_w = sum(w for _, w in wts)
    for kw, w in wts:
        share = w / total_w
        cost = round(p["ad_spend"] * share * noise(0.08), 2)
        clk = max(0, round(p["clicks"] * share * noise(0.08)))
        impr = max(clk, round(p["impressions"] * share * noise(0.10)))
        conv = round(p["paid_orders"] * share * lerp(1.05, 1.12, t) * noise(0.12), 1)
        conv_val = round(p["paid_revenue"] * share * lerp(1.04, 1.10, t) * noise(0.10), 2)
        gads_rows.append([
            d.strftime("%Y-%m-%d"), kw[0], kw[1], kw[2], kw[3], "Enabled",
            kw[4], impr, clk, f"{cost:.2f}", f"{conv:.1f}", f"{conv_val:.2f}",
        ])
write_csv(
    os.path.join(RAW, "google_ads_keyword_report.csv"),
    ["Day", "Campaign", "Ad group", "Search keyword", "Match type", "Keyword status",
     "Label", "Impressions", "Clicks", "Cost", "Conversions", "Conv. value"],
    gads_rows,
    preamble=["Search keyword report",
              f'"{PHASE_START:%b %d, %Y} - {TODAY:%b %d, %Y}"'],
)

# Keyword classification lookup - a CONFIG input the marketing-ops team maintains
# (NOT a platform export). True keyword->customer attribution needs click-level
# data from the Google Ads API (click_view); in practice teams keep a reviewed
# mapping table flagging which keywords have proven profitable in the CRM. The
# ETL joins the keyword report to this file.
write_csv(
    os.path.join(CONFIG, "keyword_classification.csv"),
    ["Search keyword", "Intent tier", "CRM-verified profitable", "Last reviewed"],
    [[kw[2], kw[4], "Yes" if kw[5] else "No", "2025-11-24"] for kw in KEYWORDS],
)

# ================================================================ GA4
ga4_rows = []
for p in plan:
    d = p["d"]
    t = p["t"]
    # paid sessions ~= paid clicks; scale up for the rest of the traffic mix
    total_sessions = round(p["clicks"] / 0.34 * noise(0.05))
    for (url, channel, cr0, cr1, b0, b1, wt) in LANDING_PAGES:
        sess = max(1, round(total_sessions * wt * noise(0.08)))
        bounce = round(lerp(b0, b1, t) * noise(0.03), 4)
        engaged = round(sess * (1 - bounce))
        cr = lerp(cr0, cr1, t) * noise(0.06)
        conv = round(sess * cr)
        rev = round(conv * p["aov"] * noise(0.06), 2)
        ga4_rows.append([
            d.strftime("%Y%m%d"), url, sess, engaged, f"{bounce:.4f}", conv, f"{rev:.2f}",
        ])
write_csv(
    os.path.join(RAW, "ga4_landing_pages.csv"),
    ["Date", "Landing page", "Sessions", "Engaged sessions", "Bounce rate",
     "Conversions", "Total revenue"],
    ga4_rows,
    preamble=["# ----------------------------------------",
              "# Google Analytics 4 - Landing page report",
              f"# Start date: {PHASE_START:%Y%m%d}",
              f"# End date: {TODAY:%Y%m%d}",
              "# ----------------------------------------"],
)

# ================================================================ HubSpot contacts / deals
# Contact + deal IDs. Lead-funnel contacts go in the contacts export; every deal
# is linked to a contact (some of those contacts are outside the lead export,
# which is realistic - you export the lead list, not the entire CRM).
contact_rows = []
deal_rows = []
cid = 200000          # contact record id counter (lead funnel + new customers)
did = 500000          # deal record id counter
gclid_counter = 0

# Pre-phase customer base. PureGlow has been trading since 2019, so the 6-month
# phase opens with a large existing customer base that can place repeat orders.
# Their HubSpot "first order date" sits before the phase. IDs 110000-189999 keep
# them clear of the lead-funnel / new-customer IDs (200000+).
existing_customers = list(range(110000, 190000))   # 80,000 prior customers
first_order_date = {}
for _c in existing_customers:
    first_order_date[_c] = PHASE_START - timedelta(days=random.randint(20, 430))

def new_gclid():
    global gclid_counter
    gclid_counter += 1
    return f"Cj0KCQ{SEED}x{gclid_counter:08d}AbVxYz"

for p in plan:
    d = p["d"]
    t = p["t"]

    # ---- lead-funnel contacts created today ----
    for _ in range(p["leads"]):
        cid += 1
        src, drill = random.choices(
            TRAFFIC_SOURCES, weights=[0.42, 0.18, 0.16, 0.12, 0.12])[0]
        is_paid = src == "Paid Search"
        gclid = new_gclid() if is_paid else ""
        converted = random.random() < (p["leads_converted"] / max(p["leads"], 1))
        became_cust = ""
        stage = "Lead"
        if converted:
            lag = random.randint(1, 12)
            bc = d + timedelta(days=lag)
            if bc <= TODAY:
                became_cust = bc.strftime("%Y-%m-%d")
                stage = "Customer"
                existing_customers.append(cid)
            else:
                stage = "Sales Qualified Lead"
        contact_rows.append([
            cid, f"lead{cid}@example.com", d.strftime("%Y-%m-%d"), stage,
            became_cust, src, drill, gclid,
        ])

    # ---- e-commerce orders (closed-won deals) created today ----
    n_new = p["new_customers"]
    n_ret = p["returning_orders"]
    paid_target = p["paid_orders"]
    paid_assigned = 0
    order_specs = [("new", True)] * n_new + [("returning", False)] * n_ret
    random.shuffle(order_specs)

    for kind, _ in order_specs:
        did += 1
        amount = round(random.gauss(p["aov"], p["aov"] * 0.28), 2)
        amount = max(18.0, amount)
        # decide paid attribution to hit the day's paid-order count
        want_paid = paid_assigned < paid_target
        is_paid = want_paid and (random.random() < 0.92)
        if is_paid:
            paid_assigned += 1
        gclid = new_gclid() if is_paid else ""

        if kind == "returning" and existing_customers:
            # recency effect: most repeat orders come from recent cohorts
            if random.random() < 0.55:
                buyer = random.choice(existing_customers[-16000:])
            else:
                buyer = random.choice(existing_customers)
        else:
            cid += 1
            buyer = cid
            first_order_date[buyer] = d
            existing_customers.append(buyer)

        fod = first_order_date.get(buyer, d)
        deal_rows.append([
            did, f"Order {did}", "Closed won", "Ecommerce Pipeline",
            f"{amount:.2f}", d.strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d"),
            buyer, "PureGlow Storefront", gclid, fod.strftime("%Y-%m-%d"),
        ])

    # ---- a handful of open deals created today (subscription / wholesale enquiries) ----
    for _ in range(random.randint(2, 5)):
        did += 1
        amount = round(random.gauss(640, 240), 2)
        amount = max(120.0, amount)
        cid += 1
        stage = random.choice(["Qualified to buy", "Decision maker bought-in",
                               "Contract sent"])
        deal_rows.append([
            did, f"Open Deal {did}", stage, "Ecommerce Pipeline",
            f"{amount:.2f}", d.strftime("%Y-%m-%d"), "", cid,
            "PureGlow Storefront", "", "",
        ])

write_csv(
    os.path.join(RAW, "hubspot_contacts.csv"),
    ["Record ID", "Email", "Create Date", "Lifecycle Stage", "Became a Customer Date",
     "Original Traffic Source", "Original Traffic Source Drill-Down 1",
     "Google ad click id"],
    contact_rows,
)
write_csv(
    os.path.join(RAW, "hubspot_deals.csv"),
    ["Record ID", "Deal Name", "Deal Stage", "Pipeline", "Amount", "Create Date",
     "Close Date", "Associated Contact ID", "Deal owner", "Google ad click id",
     "Customer first order date"],
    deal_rows,
)

# ================================================================ HubSpot email
email_rows = []
for p in plan:
    d = p["d"]
    t = p["t"]
    # legacy batch-and-blast dominates early then tapers as segmented programme
    # comes online (matches the case's batch-to-segmented transition).
    if random.random() < lerp(0.90, 0.02, t):
        sends = round(lerp(22000, 4000, t) * noise(0.10))
        delivered = round(sends * 0.975)
        opens = round(delivered * lerp(0.135, 0.175, t) * noise(0.05))   # case "before" 14%
        clicks = round(delivered * lerp(0.017, 0.026, t) * noise(0.06))  # case "before" 1.8%
        email_rows.append([
            f"{d:%Y-%m-%d} Monthly Newsletter (Batch)", "Monthly news + featured products",
            "All contacts (batch)", d.strftime("%Y-%m-%d"), sends, delivered,
            opens, clicks, round(delivered * 0.0016),
        ])
    # segmented lifecycle campaigns
    for (seg, o0, o1, c0, c1, s0, s1) in EMAIL_SEGMENTS:
        if random.random() < 0.62:          # not every segment sends every day
            continue
        sends = round(lerp(s0, s1, t) * noise(0.14))
        delivered = round(sends * random.uniform(0.974, 0.99))
        open_rate = lerp(o0, o1, t) * noise(0.05)
        ctr = lerp(c0, c1, t) * noise(0.06)
        opens = round(delivered * open_rate)
        clicks = round(delivered * ctr)
        subj = {
            "New Leads": "Your 3-step routine starts here",
            "Cart Abandoners": "Still thinking it over? 10% inside",
            "First-Time Buyers": "How to get the most from your serum",
            "Lapsed Customers": "We miss you - here's 15% back",
            "VIP Loyalists": "Early access: your VIP drop is live",
        }[seg]
        email_rows.append([
            f"{d:%Y-%m-%d} {seg} - lifecycle", subj, seg, d.strftime("%Y-%m-%d"),
            sends, delivered, opens, clicks, round(delivered * 0.0009),
        ])
write_csv(
    os.path.join(RAW, "hubspot_email_performance.csv"),
    ["Email name", "Subject", "Audience", "Date sent", "Sends", "Delivered",
     "Opens", "Clicks", "Unsubscribes"],
    email_rows,
)

# ================================================================ HubSpot carts
cart_rows = []
cart_id = 900000
for p in plan:
    d = p["d"]
    for _ in range(p["carts"]):
        cart_id += 1
        value = round(random.gauss(p["aov"] * 1.15, p["aov"] * 0.35), 2)
        value = max(20.0, value)
        recovered = random.random() < (p["carts_recovered"] / max(p["carts"], 1))
        rec_date = ""
        if recovered:
            rd = d + timedelta(days=random.randint(0, 3))
            rec_date = rd.strftime("%Y-%m-%d") if rd <= TODAY else ""
            recovered = bool(rec_date)
        cart_rows.append([
            cart_id, 200000 + random.randint(1, max(1, cid - 200000)),
            d.strftime("%Y-%m-%d"), f"{value:.2f}",
            "Yes" if recovered else "No", rec_date,
        ])
write_csv(
    os.path.join(RAW, "hubspot_carts.csv"),
    ["Cart ID", "Associated Contact ID", "Cart Created Date", "Cart Value",
     "Recovered", "Recovery Date"],
    cart_rows,
)

# ================================================================ HubSpot open pipeline
pipe_rows = []
for p in plan:
    pipe_rows.append([
        p["d"].strftime("%Y-%m-%d"), f"{p['open_pipeline']:.2f}",
        "Ecommerce Pipeline",
    ])
write_csv(
    os.path.join(RAW, "hubspot_open_pipeline.csv"),
    ["Snapshot Date", "Open Pipeline Value", "Pipeline"],
    pipe_rows,
)

print(f"\nDone. {7} raw export files written to {os.path.relpath(RAW, HERE)}/")
print("Next step:  python 02_build_kpi_tables.py")
