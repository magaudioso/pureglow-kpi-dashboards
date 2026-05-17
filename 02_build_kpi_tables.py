"""02_build_kpi_tables.py
================================================================================
ETL: turn the raw platform exports in data/raw/ into clean, dashboard-ready
fact tables in data/processed/.

This is the script that "makes the data tables". In production the data/raw/
inputs would be refreshed automatically (Google Ads API, GA4 Data API or the
free GA4 -> BigQuery export, and the HubSpot API) on a schedule, or pulled by a
managed connector such as Supermetrics, Fivetran or Airbyte - see the alignment
document, Part 5. The transform logic below stays exactly the same whether the
CSVs arrive by hand or by pipeline.

What it does:
  1. Load each raw export, skipping the preamble lines real exports ship with.
  2. Clean + type-convert (dates, currency strings, percentages).
  3. Derive the "integration glue" the raw exports don't carry natively:
       - intent tier + CRM-verified flag  (join keyword report -> classification)
       - first-vs-repeat order sequence    (rank deals within each contact)
       - paid attribution                  (GCLID present on the deal)
       - 90-day repeat purchase            (look forward from each first order)
  4. Aggregate to a daily fact table + three breakdown fact tables.
  5. Write the KPI catalogue.

Outputs (data/processed/):
  fact_daily.csv         one row per day - the spine of both dashboards
  fact_keyword.csv       day x keyword - paid-search drill-down
  fact_landing_page.csv  day x landing page - GA4 drill-down
  fact_email.csv         day x email segment - CRM drill-down
  ../config/kpi_catalog.csv   the KPI catalogue (written via kpi_lib)
================================================================================
"""
import os
import numpy as np
import pandas as pd

import kpi_lib

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
PROCESSED = os.path.join(HERE, "data", "processed")
CONFIG = os.path.join(HERE, "config")
os.makedirs(PROCESSED, exist_ok=True)

GROSS_MARGIN = kpi_lib.CONFIG["gross_margin"]
print("Building KPI tables from raw exports...")


# ============================================================ 1. load raw
# Google Ads "Search keyword" report - 2 preamble lines before the header.
gads = pd.read_csv(os.path.join(RAW, "google_ads_keyword_report.csv"), skiprows=2)
gads["Day"] = pd.to_datetime(gads["Day"])
for col in ["Impressions", "Clicks", "Cost", "Conversions", "Conv. value"]:
    gads[col] = pd.to_numeric(gads[col], errors="coerce")

# GA4 landing-page report - '#' comment preamble; GA4 dates are YYYYMMDD ints.
ga4 = pd.read_csv(os.path.join(RAW, "ga4_landing_pages.csv"), comment="#")
ga4["Date"] = pd.to_datetime(ga4["Date"].astype(str), format="%Y%m%d")
for col in ["Sessions", "Engaged sessions", "Bounce rate", "Conversions",
            "Total revenue"]:
    ga4[col] = pd.to_numeric(ga4[col], errors="coerce")

# HubSpot exports - clean CSVs.
contacts = pd.read_csv(os.path.join(RAW, "hubspot_contacts.csv"))
contacts["Create Date"] = pd.to_datetime(contacts["Create Date"])
contacts["Became a Customer Date"] = pd.to_datetime(
    contacts["Became a Customer Date"], errors="coerce")

deals = pd.read_csv(os.path.join(RAW, "hubspot_deals.csv"))
deals["Amount"] = pd.to_numeric(deals["Amount"], errors="coerce")
deals["Close Date"] = pd.to_datetime(deals["Close Date"], errors="coerce")
deals["Google ad click id"] = deals["Google ad click id"].fillna("").astype(str)

email = pd.read_csv(os.path.join(RAW, "hubspot_email_performance.csv"))
email["Date sent"] = pd.to_datetime(email["Date sent"])
for col in ["Sends", "Delivered", "Opens", "Clicks"]:
    email[col] = pd.to_numeric(email[col], errors="coerce")

carts = pd.read_csv(os.path.join(RAW, "hubspot_carts.csv"))
carts["Cart Created Date"] = pd.to_datetime(carts["Cart Created Date"])
carts["Cart Value"] = pd.to_numeric(carts["Cart Value"], errors="coerce")

pipeline = pd.read_csv(os.path.join(RAW, "hubspot_open_pipeline.csv"))
pipeline["Snapshot Date"] = pd.to_datetime(pipeline["Snapshot Date"])
pipeline["Open Pipeline Value"] = pd.to_numeric(pipeline["Open Pipeline Value"],
                                                errors="coerce")

# Marketing-ops keyword classification (a CONFIG input, not a platform export).
kw_class = pd.read_csv(os.path.join(CONFIG, "keyword_classification.csv"))
print(f"  loaded raw: {len(gads):,} keyword rows | {len(deals):,} deals | "
      f"{len(contacts):,} contacts | {len(email):,} emails | {len(carts):,} carts")


# ============================================================ 2-3. keyword fact
# Join the keyword report to the classification lookup so each row carries an
# intent tier and a CRM-verified flag. The keyword report has a "Label" column
# too; we trust the reviewed classification file as the source of truth.
gads = gads.merge(
    kw_class.rename(columns={"Search keyword": "Search keyword"}),
    on="Search keyword", how="left",
)
gads["Intent tier"] = gads["Intent tier"].fillna("Untiered - Broad")
gads["CRM-verified profitable"] = gads["CRM-verified profitable"].fillna("No")
gads["is_high_intent"] = gads["Intent tier"].str.startswith(("Tier 1", "Tier 2"))
gads["is_crm_verified"] = gads["CRM-verified profitable"].eq("Yes")

fact_keyword = (gads.rename(columns={
        "Day": "date", "Campaign": "campaign", "Ad group": "ad_group",
        "Search keyword": "keyword", "Match type": "match_type",
        "Intent tier": "intent_tier", "Impressions": "impressions",
        "Clicks": "clicks", "Cost": "cost", "Conversions": "gads_conversions",
        "Conv. value": "gads_conv_value"})
    [["date", "campaign", "ad_group", "keyword", "match_type", "intent_tier",
      "is_high_intent", "is_crm_verified", "impressions", "clicks", "cost",
      "gads_conversions", "gads_conv_value"]]
    .sort_values(["date", "campaign", "keyword"]))
fact_keyword.to_csv(os.path.join(PROCESSED, "fact_keyword.csv"), index=False)
print(f"  fact_keyword.csv      {len(fact_keyword):,} rows")


# ============================================================ landing-page fact
fact_lp = ga4.rename(columns={
    "Date": "date", "Landing page": "landing_page", "Sessions": "sessions",
    "Engaged sessions": "engaged_sessions", "Bounce rate": "bounce_rate",
    "Conversions": "conversions", "Total revenue": "revenue"})
fact_lp = fact_lp[["date", "landing_page", "sessions", "engaged_sessions",
                   "bounce_rate", "conversions", "revenue"]].sort_values(
    ["date", "landing_page"])
fact_lp.to_csv(os.path.join(PROCESSED, "fact_landing_page.csv"), index=False)
print(f"  fact_landing_page.csv {len(fact_lp):,} rows")


# ============================================================ email fact
email["segmented"] = email["Audience"].ne("All contacts (batch)")
fact_email = email.rename(columns={
    "Date sent": "date", "Audience": "segment", "Sends": "sends",
    "Delivered": "delivered", "Opens": "opens", "Clicks": "clicks"})
fact_email = (fact_email.groupby(["date", "segment", "segmented"], as_index=False)
              [["sends", "delivered", "opens", "clicks"]].sum()
              .sort_values(["date", "segment"]))
fact_email.to_csv(os.path.join(PROCESSED, "fact_email.csv"), index=False)
print(f"  fact_email.csv        {len(fact_email):,} rows")


# ============================================================ deal derivations
won = deals[deals["Deal Stage"].eq("Closed won")].copy()
won["Customer first order date"] = pd.to_datetime(
    won["Customer first order date"], errors="coerce")
won = won.sort_values(["Associated Contact ID", "Close Date"])
won["order_sequence"] = won.groupby("Associated Contact ID").cumcount() + 1

# First-vs-repeat uses the HubSpot "first order date" property, NOT a rank within
# this export - a returning customer's earlier orders pre-date the 6-month window
# and would not appear here, so ranking alone would misclassify them as new.
won["is_new_customer"] = won["Close Date"].dt.normalize().eq(
    won["Customer first order date"].dt.normalize())
won["is_returning"] = ~won["is_new_customer"]
# Paid attribution: the GCLID lands on the deal/contact CRM-side (it is not in
# the Google Ads keyword export).
won["is_paid"] = won["Google ad click id"].str.len().gt(0)
won["paid_amount"] = won["Amount"].where(won["is_paid"], 0.0)
won["returning_amount"] = won["Amount"].where(won["is_returning"], 0.0)

# 90-day repeat: from each NEW customer's first order, is there another order
# within 90 days? (a new customer's repeat orders DO fall inside this export).
second = (won[won["order_sequence"].eq(2)]
          .drop_duplicates("Associated Contact ID")
          .set_index("Associated Contact ID")["Close Date"])
first = won[won["is_new_customer"]].copy()
first["second_date"] = first["Associated Contact ID"].map(second)
first["repeat_90d"] = (
    (first["second_date"] - first["Close Date"]).dt.days.between(1, 90))
first_by_day = (first.groupby("Close Date").agg(
    first_order_customers=("Record ID", "count"),
    repeat_within_90d=("repeat_90d", "sum"))
    .reset_index().rename(columns={"Close Date": "date"}))

# daily order / revenue rollup
won_daily = won.groupby("Close Date").agg(
    orders=("Record ID", "count"),
    revenue=("Amount", "sum"),
    paid_orders=("is_paid", "sum"),
    paid_revenue=("paid_amount", "sum"),
    new_customers=("is_new_customer", "sum"),
    returning_orders=("is_returning", "sum"),
    returning_revenue=("returning_amount", "sum"),
).reset_index().rename(columns={"Close Date": "date"})

# Day-30 cohort gross profit (Hormozi-style payback denominator).
# For each contact whose FIRST order falls in-phase, sum gross profit from all of
# that contact's orders in the 30 days starting at the first order, then bucket
# by the first-order date. This is what kpi_lib pairs with ad spend.
nc_first = (won.loc[won["is_new_customer"]]
            .drop_duplicates("Associated Contact ID")
            .set_index("Associated Contact ID")["Close Date"])
nc_orders = won[won["Associated Contact ID"].isin(nc_first.index)].copy()
nc_orders["first_date"] = nc_orders["Associated Contact ID"].map(nc_first)
nc_orders["days_from_first"] = (
    nc_orders["Close Date"] - nc_orders["first_date"]).dt.days
in30 = nc_orders[(nc_orders["days_from_first"] >= 0) &
                 (nc_orders["days_from_first"] <= 29)].copy()
in30["gp"] = in30["Amount"] * GROSS_MARGIN
cohort_d30 = (in30.groupby("first_date")["gp"].sum().reset_index()
              .rename(columns={"first_date": "date", "gp": "cohort_d30_gp"}))


# ============================================================ contact derivations
leads_created = (contacts.groupby("Create Date").size()
                 .reset_index(name="leads_created")
                 .rename(columns={"Create Date": "date"}))
# lead-to-customer is cohort-based: a converted lead is credited to its CREATE date
converted = contacts[contacts["Became a Customer Date"].notna()]
leads_converted = (converted.groupby("Create Date").size()
                   .reset_index(name="leads_converted")
                   .rename(columns={"Create Date": "date"}))


# ============================================================ other daily rollups
gads_daily = gads.groupby("Day").agg(
    ad_spend=("Cost", "sum"),
    impressions=("Impressions", "sum"),
    clicks=("Clicks", "sum"),
    gads_conversions=("Conversions", "sum"),
    gads_conv_value=("Conv. value", "sum"),
    spend_high_intent=("Cost", lambda s: s[gads.loc[s.index, "is_high_intent"]].sum()),
    spend_crm_verified=("Cost", lambda s: s[gads.loc[s.index, "is_crm_verified"]].sum()),
).reset_index().rename(columns={"Day": "date"})

ga4_daily = ga4.groupby("Date").agg(
    sessions=("Sessions", "sum"),
    engaged_sessions=("Engaged sessions", "sum"),
    lp_conversions=("Conversions", "sum"),
    lp_revenue=("Total revenue", "sum"),
).reset_index().rename(columns={"Date": "date"})

email_daily = email.groupby("Date sent").agg(
    emails_sent=("Sends", "sum"),
    emails_delivered=("Delivered", "sum"),
    emails_opened=("Opens", "sum"),
    emails_clicked=("Clicks", "sum"),
).reset_index().rename(columns={"Date sent": "date"})
# segmented-only email aggregates - the email open/CTR KPIs measure the
# lifecycle programme, not the legacy batch-and-blast sends being retired.
email_seg_daily = (email[email["segmented"]].groupby("Date sent").agg(
    emails_sent_segmented=("Sends", "sum"),
    emails_delivered_segmented=("Delivered", "sum"),
    emails_opened_segmented=("Opens", "sum"),
    emails_clicked_segmented=("Clicks", "sum"),
).reset_index().rename(columns={"Date sent": "date"}))

carts_daily = carts.groupby("Cart Created Date").agg(
    carts_created=("Cart ID", "count"),
    carts_recovered=("Recovered", lambda s: s.eq("Yes").sum()),
).reset_index().rename(columns={"Cart Created Date": "date"})

pipe_daily = pipeline.rename(columns={
    "Snapshot Date": "date", "Open Pipeline Value": "open_pipeline_value"})[
    ["date", "open_pipeline_value"]]


# ============================================================ 4. fact_daily
spine = pd.DataFrame({"date": pd.date_range(
    kpi_lib.CONFIG["phase_start"], kpi_lib.CONFIG["data_through"], freq="D")})
fact = spine
for part in [gads_daily, ga4_daily, won_daily, first_by_day, leads_created,
             leads_converted, email_daily, email_seg_daily, carts_daily,
             pipe_daily, cohort_d30]:
    fact = fact.merge(part, on="date", how="left")
fact = fact.fillna(0)

fact["emails_sent_batch"] = fact["emails_sent"] - fact["emails_sent_segmented"]

# rolling-90-day CLV = AOV x expected orders per customer x gross margin.
# Expected orders per customer is derived from the repeat-order share, which is
# stable from day one (unlike a distinct-customer count on a partial window).
roll = fact[["date", "revenue", "orders", "returning_orders"]].set_index("date")
r90 = roll.rolling("90D", min_periods=7).sum()
aov90 = (r90["revenue"] / r90["orders"]).replace([np.inf, -np.inf], np.nan)
repeat_share90 = (r90["returning_orders"] / r90["orders"]).clip(0, 0.85)
clv = (aov90 * (1.0 / (1.0 - repeat_share90)) * GROSS_MARGIN)
fact["clv_value"] = clv.ffill().bfill().rolling(14, min_periods=1).mean().values

# tidy column order
cols = ["date", "ad_spend", "impressions", "clicks", "gads_conversions",
        "gads_conv_value", "spend_high_intent", "spend_crm_verified",
        "orders", "revenue", "paid_orders", "paid_revenue", "new_customers",
        "returning_orders", "returning_revenue", "first_order_customers",
        "repeat_within_90d", "leads_created", "leads_converted",
        "sessions", "engaged_sessions", "lp_conversions", "lp_revenue",
        "emails_sent", "emails_delivered", "emails_opened", "emails_clicked",
        "emails_sent_segmented", "emails_sent_batch",
        "emails_delivered_segmented", "emails_opened_segmented",
        "emails_clicked_segmented",
        "carts_created", "carts_recovered", "open_pipeline_value",
        "clv_value", "cohort_d30_gp"]
fact = fact[cols]
int_cols = [c for c in cols if c not in
            ("date", "ad_spend", "gads_conv_value", "revenue", "paid_revenue",
             "returning_revenue", "lp_revenue", "open_pipeline_value",
             "clv_value", "gads_conversions", "cohort_d30_gp")]
fact[int_cols] = fact[int_cols].round().astype(int)
for c in ["ad_spend", "gads_conv_value", "revenue", "paid_revenue",
          "returning_revenue", "lp_revenue", "open_pipeline_value",
          "clv_value", "gads_conversions", "cohort_d30_gp"]:
    fact[c] = fact[c].round(2)
fact.to_csv(os.path.join(PROCESSED, "fact_daily.csv"), index=False)
print(f"  fact_daily.csv        {len(fact):,} rows")


# ============================================================ 5. KPI catalogue
cat_path = kpi_lib.write_catalog()
print(f"  {os.path.relpath(cat_path, HERE)}     {len(kpi_lib.CATALOG)} KPIs")


# ============================================================ quick sanity read
full_start = kpi_lib.CONFIG["phase_start"]
full_end = kpi_lib.CONFIG["data_through"]
res = kpi_lib.compute_kpis(fact, full_start, full_end)
print("\nFull-phase KPI sanity check (vs target):")
for r in res:
    flag = {"on_track": "OK ", "watch": "watch", "off_track": "OFF",
            "no_target": "  -"}[r["status"]]
    print(f"  [{flag}] {r['name'][:46]:46s} {r['value_fmt']:>11s}"
          f"   target {r['target_fmt']}")
print("\nDone.  Next step:  streamlit run 03_dashboard_leadership.py")
