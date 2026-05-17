"""kpi_lib.py
================================================================================
Shared logic for the two PureGlow KPI dashboards and the preview renderer.

  * CONFIG    - phase targets and planning constants (one place to re-baseline)
  * CATALOG   - the KPI catalogue: id, name, audience, owner, target, direction
  * loaders   - read the processed fact tables produced by 02_build_kpi_tables.py
  * periods   - preset date windows (leadership) + prior-window helper
  * compute   - turn a slice of fact_daily into a list of KPI result dicts
  * format    - currency / percent / ratio / index formatters
  * status    - on-track / watch / off-track logic (direction-aware)

The dashboards never compute a KPI themselves - they ask this module, so both
audiences are guaranteed to read the same number the same way.
================================================================================
"""
import os
import datetime as dt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(HERE, "data", "processed")
CONFIG_DIR = os.path.join(HERE, "config")

# ------------------------------------------------------------------ CONFIG
# Every target and planning number lives here. Re-baseline in Month 1 by
# editing this block - no dashboard or ETL logic has to change.
CONFIG = {
    "phase_start":              dt.date(2025, 12, 1),
    "phase_end":                dt.date(2026, 5, 31),
    "data_through":             dt.date(2026, 5, 14),
    "revenue_runrate_target":   8_400_000,   # KR 1.1 - completes the doubling
    "monthly_revenue_target":   700_000,     # used for pipeline-coverage denominator
    "weekly_new_customer_plan": 1_250,       # pace needed for the run-rate target
    "gross_margin":             0.70,        # CLV assumption (see doc Part 6)
    "runrate_window_days":      90,          # trailing window for the run-rate
}

# ------------------------------------------------------------------ CATALOG
# audience: "leadership" | "marketing"      indicator: "lagging" | "leading"
# direction: "higher" (more is better) | "lower" (less is better)
# unit: "currency" | "pct" | "ratio" | "index" | "number"
CATALOG = [
    # ---- Leadership - lagging -------------------------------------------------
    dict(id="LEAD_REVENUE_RR", name="Online revenue (annualised run-rate)",
         audience="leadership", indicator="lagging", owner="CEO / Maya Chen",
         maps_to="O1 - KR 1.1", target=CONFIG["revenue_runrate_target"],
         direction="higher", unit="currency", is_new=False,
         desc="Trailing-90-day online revenue, annualised. Target completes the "
              "CEO's doubling mandate."),
    dict(id="LEAD_ROAS", name="Blended ROAS",
         audience="leadership", indicator="lagging", owner="Maya Chen",
         maps_to="O1 - KR 1.2", target=4.0, direction="higher", unit="ratio",
         is_new=False,
         desc="Total online revenue divided by total ad spend."),
    dict(id="LEAD_CPA", name="Blended CPA (cost per order)",
         audience="leadership", indicator="lagging", owner="Maya Chen",
         maps_to="O2 - KR 2.3", target=15.0, direction="lower", unit="currency",
         is_new=False,
         desc="Total ad spend divided by all orders (paid + organic + returning)."),
    dict(id="LEAD_CLV", name="Customer lifetime value (CLV index)",
         audience="leadership", indicator="lagging", owner="Maya Chen",
         maps_to="O3 - KR 3.2", target=108.0, direction="higher", unit="index",
         is_new=False,
         desc="CLV indexed to the phase start (=100). Target is +8% over the phase."),
    dict(id="LEAD_RET_REV", name="Returning-customer revenue share",
         audience="leadership", indicator="lagging", owner="Sofia Reyes",
         maps_to="O3 - KR 3.3", target=0.40, direction="higher", unit="pct",
         is_new=True,
         desc="Share of revenue from customers placing their 2nd+ order. NEW metric."),
    dict(id="LEAD_D30_PAYBACK", name="Day-30 gross-profit payback on CAC",
         audience="leadership", indicator="lagging", owner="CEO / Maya Chen",
         maps_to="O1 - KR 1.3", target=1.0, direction="higher", unit="ratio",
         is_new=True,
         desc="For new customers acquired in the period, gross profit earned in "
              "their first 30 days divided by total acquisition spend. Hormozi's "
              "self-funding-growth threshold (1.0x means a cohort pays back its CAC "
              "in gross profit within 30 days). NEW metric."),
    # ---- Leadership - leading ------------------------------------------------
    dict(id="LEAD_PIPE_COV", name="Pipeline coverage ratio",
         audience="leadership", indicator="leading", owner="Maya Chen",
         maps_to="O1 - KR 1.1", target=1.5, direction="higher", unit="ratio",
         is_new=True,
         desc="Open pipeline value divided by the monthly revenue target. NEW metric."),
    dict(id="LEAD_L2C", name="Lead-to-customer conversion rate",
         audience="leadership", indicator="leading", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.07, direction="higher", unit="pct",
         is_new=False,
         desc="New customers divided by new leads. Leadership's revenue early-warning."),
    dict(id="LEAD_NEWCUST_PACE", name="Weekly new-customer run-rate vs plan",
         audience="leadership", indicator="leading", owner="Maya Chen",
         maps_to="O1 - KR 1.1", target=1.0, direction="higher", unit="pct",
         is_new=False,
         desc="Actual weekly new customers divided by the planned weekly pace."),
    dict(id="LEAD_CRM_SPEND", name="% ad spend on CRM-verified keywords",
         audience="leadership", indicator="leading", owner="Derek Osei",
         maps_to="O1 - KR 1.2", target=0.70, direction="higher", unit="pct",
         is_new=True,
         desc="Share of paid spend on keywords confirmed profitable in the CRM. NEW metric."),
    # ---- Marketing - lagging -------------------------------------------------
    dict(id="MKT_CPA", name="Cost per acquisition (CPA) - paid search",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O2 - KR 2.3", target=15.0, direction="lower", unit="currency",
         is_new=False,
         desc="Paid-search spend divided by GCLID-attributed orders."),
    dict(id="MKT_ROAS", name="Return on ad spend (ROAS) - paid search",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O1 - KR 1.2", target=4.0, direction="higher", unit="ratio",
         is_new=False,
         desc="GCLID-attributed revenue divided by paid-search spend."),
    dict(id="MKT_LP_CONV", name="Landing page conversion rate",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O2 - KR 2.1", target=0.045, direction="higher", unit="pct",
         is_new=False,
         desc="Landing-page conversions divided by landing-page sessions (GA4)."),
    dict(id="MKT_L2C", name="Lead-to-customer conversion rate",
         audience="marketing", indicator="lagging", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.07, direction="higher", unit="pct",
         is_new=False,
         desc="New customers divided by new leads (HubSpot lifecycle stages)."),
    dict(id="MKT_CART", name="Cart recovery rate",
         audience="marketing", indicator="lagging", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.20, direction="higher", unit="pct",
         is_new=False,
         desc="Recovered carts divided by abandoned carts."),
    # ---- Marketing - leading -------------------------------------------------
    dict(id="MKT_CPC", name="Cost per click (CPC)",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O2 - KR 2.3", target=1.20, direction="lower", unit="currency",
         is_new=False,
         desc="Paid-search cost divided by clicks."),
    dict(id="MKT_CTR", name="Click-through rate (CTR) - paid search",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O2 - KR 2.1", target=0.045, direction="higher", unit="pct",
         is_new=False,
         desc="Paid-search clicks divided by impressions."),
    dict(id="MKT_HIGH_INTENT", name="% ad spend on high-intent (Tier 1 & 2) keywords",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O1 - KR 1.2", target=0.75, direction="higher", unit="pct",
         is_new=True,
         desc="Share of paid spend on Tier 1 + Tier 2 keywords. NEW metric."),
    dict(id="MKT_EMAIL_OPEN", name="Email open rate",
         audience="marketing", indicator="leading", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.28, direction="higher", unit="pct",
         is_new=False,
         desc="Email opens divided by emails delivered."),
    dict(id="MKT_EMAIL_CTR", name="Email click-through rate",
         audience="marketing", indicator="leading", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.045, direction="higher", unit="pct",
         is_new=False,
         desc="Email clicks divided by emails delivered."),
]
CATALOG_BY_ID = {k["id"]: k for k in CATALOG}


def write_catalog():
    """Write the KPI catalogue to config/kpi_catalog.csv for transparency."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    rows = []
    for k in CATALOG:
        rows.append({
            "kpi_id": k["id"], "kpi_name": k["name"], "audience": k["audience"],
            "indicator_type": k["indicator"], "owner": k["owner"],
            "maps_to": k["maps_to"], "target": k["target"],
            "target_direction": k["direction"], "unit": k["unit"],
            "new_metric": "Yes" if k["is_new"] else "No", "description": k["desc"],
        })
    path = os.path.join(CONFIG_DIR, "kpi_catalog.csv")
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


# ------------------------------------------------------------------ loaders
def _load(name):
    return pd.read_csv(os.path.join(PROCESSED, name), parse_dates=["date"])


def load_fact_daily():
    return _load("fact_daily.csv")


def load_fact_keyword():
    return _load("fact_keyword.csv")


def load_fact_landing_page():
    return _load("fact_landing_page.csv")


def load_fact_email():
    return _load("fact_email.csv")


# ------------------------------------------------------------------ periods
def data_bounds(df):
    return df["date"].min().date(), df["date"].max().date()


def leadership_presets(data_min, data_max):
    """Return {label: (start, end)} - the executive period dropdown."""
    end = data_max
    presets = {}
    # this month to date
    presets["This month to date"] = (end.replace(day=1), end)
    # last full month
    first_this = end.replace(day=1)
    last_prev_end = first_this - dt.timedelta(days=1)
    presets["Last full month"] = (last_prev_end.replace(day=1), last_prev_end)
    # this quarter to date
    q_first_month = 1 + 3 * ((end.month - 1) // 3)
    presets["This quarter to date"] = (dt.date(end.year, q_first_month, 1), end)
    # full growth phase
    presets["Full growth phase (6 mo)"] = (data_min, end)
    return presets


def prior_window(start, end, data_min):
    """Immediately-preceding equal-length window, or None if it predates the data."""
    span = (end - start).days
    p_end = start - dt.timedelta(days=1)
    p_start = p_end - dt.timedelta(days=span)
    if p_start < data_min:
        return None
    return p_start, p_end


def slice_period(df, start, end):
    m = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    return df.loc[m].copy()


# ------------------------------------------------------------------ formatters
def fmt(value, unit):
    if value is None or pd.isna(value):
        return "n/a"
    if unit == "currency":
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        if abs(value) >= 10_000:
            return f"${value / 1_000:.0f}K"
        return f"${value:,.2f}"
    if unit == "pct":
        return f"{value * 100:.1f}%"
    if unit == "ratio":
        return f"{value:.2f}x"
    if unit == "index":
        return f"{value:.0f}"
    if unit == "number":
        return f"{value:,.0f}"
    return str(value)


def fmt_delta(delta, unit):
    if delta is None or pd.isna(delta):
        return ""
    arrow = "+" if delta >= 0 else ""
    if unit in ("pct",):
        return f"{arrow}{delta * 100:.1f} pts"
    if unit == "ratio":
        return f"{arrow}{delta:.2f}x"
    if unit == "index":
        return f"{arrow}{delta:.0f}"
    if unit == "currency":
        if abs(delta) >= 10_000:
            return f"{arrow}{delta / 1_000:.0f}K"
        return f"{arrow}${delta:,.2f}"
    return f"{arrow}{delta:,.0f}"


# ------------------------------------------------------------------ status
def status_key(value, target, direction):
    """Return 'on_track' | 'watch' | 'off_track' (direction-aware)."""
    if value is None or pd.isna(value):
        return "no_target"
    if direction == "higher":
        if value >= target:
            return "on_track"
        if value >= target * 0.95:
            return "watch"
        return "off_track"
    else:  # lower is better
        if value <= target:
            return "on_track"
        if value <= target * 1.05:
            return "watch"
        return "off_track"


# ------------------------------------------------------------------ compute
def _safe_div(a, b):
    return a / b if b else 0.0


def _runrate(df_full, end):
    win = CONFIG["runrate_window_days"]
    lo = end - dt.timedelta(days=win - 1)
    sl = df_full[(df_full["date"].dt.date >= lo) & (df_full["date"].dt.date <= end)]
    days = max(len(sl), 1)
    return sl["revenue"].sum() / days * 365.0


def _raw_kpi_values(df_period, df_full):
    """All KPI raw values for one period slice. Returns {kpi_id: value}."""
    if df_period.empty:
        return {k["id"]: None for k in CATALOG}
    p = df_period.sum(numeric_only=True)
    end = df_period["date"].max().date()
    period_days = (df_period["date"].max() - df_period["date"].min()).days + 1
    weeks = max(period_days / 7.0, 1e-9)

    v = {}
    # leadership lagging
    v["LEAD_REVENUE_RR"] = _runrate(df_full, end)
    v["LEAD_ROAS"] = _safe_div(p["revenue"], p["ad_spend"])
    v["LEAD_CPA"] = _safe_div(p["ad_spend"], p["orders"])
    base_clv = df_full.sort_values("date")["clv_value"].head(7).mean()
    end_clv = df_period.sort_values("date")["clv_value"].tail(7).mean()
    v["LEAD_CLV"] = _safe_div(end_clv, base_clv) * 100.0
    v["LEAD_RET_REV"] = _safe_div(p["returning_revenue"], p["revenue"])
    # Day-30 gross-profit payback on CAC - cohort metric with 30-day maturity lag.
    # For new customers whose first order falls in the mature sub-window of the
    # period, sum their first-30-day gross profit and divide by ad spend on the
    # same window. (Hormozi's self-funding-growth threshold is 1.0x.)
    data_max = df_full["date"].max()
    mature_cut = data_max - pd.Timedelta(days=30)
    mat = df_period[df_period["date"] <= mature_cut]
    if len(mat) < 14:
        lo = mature_cut - pd.Timedelta(days=29)
        mat = df_full[(df_full["date"] >= lo) & (df_full["date"] <= mature_cut)]
    v["LEAD_D30_PAYBACK"] = _safe_div(mat["cohort_d30_gp"].sum(),
                                      mat["ad_spend"].sum())
    # leadership leading
    v["LEAD_PIPE_COV"] = _safe_div(df_period.iloc[-1]["open_pipeline_value"],
                                   CONFIG["monthly_revenue_target"])
    # Lead-to-customer is cohort-based and has a conversion lag, so leads created
    # in the last ~12 days are not yet mature. Measure only mature cohorts; if the
    # period has too few mature days, fall back to the trailing 30 mature days.
    data_max = df_full["date"].max()
    mature_cut = data_max - pd.Timedelta(days=12)
    mat = df_period[df_period["date"] <= mature_cut]
    if len(mat) < 14:
        lo = mature_cut - pd.Timedelta(days=29)
        mat = df_full[(df_full["date"] >= lo) & (df_full["date"] <= mature_cut)]
    v["LEAD_L2C"] = _safe_div(mat["leads_converted"].sum(), mat["leads_created"].sum())
    v["LEAD_NEWCUST_PACE"] = _safe_div(p["new_customers"] / weeks,
                                       CONFIG["weekly_new_customer_plan"])
    v["LEAD_CRM_SPEND"] = _safe_div(p["spend_crm_verified"], p["ad_spend"])
    # marketing lagging
    v["MKT_CPA"] = _safe_div(p["ad_spend"], p["paid_orders"])
    v["MKT_ROAS"] = _safe_div(p["paid_revenue"], p["ad_spend"])
    v["MKT_LP_CONV"] = _safe_div(p["lp_conversions"], p["sessions"])
    v["MKT_L2C"] = v["LEAD_L2C"]
    v["MKT_CART"] = _safe_div(p["carts_recovered"], p["carts_created"])
    # marketing leading
    v["MKT_CPC"] = _safe_div(p["ad_spend"], p["clicks"])
    v["MKT_CTR"] = _safe_div(p["clicks"], p["impressions"])
    v["MKT_HIGH_INTENT"] = _safe_div(p["spend_high_intent"], p["ad_spend"])
    # email open / CTR measure the segmented lifecycle programme (the legacy
    # batch-and-blast sends being retired are tracked by the % segmented guardrail)
    v["MKT_EMAIL_OPEN"] = _safe_div(p["emails_opened_segmented"],
                                    p["emails_delivered_segmented"])
    v["MKT_EMAIL_CTR"] = _safe_div(p["emails_clicked_segmented"],
                                   p["emails_delivered_segmented"])
    return v


def compute_kpis(df_full, start, end, audience=None, prior=None):
    """Return a list of KPI result dicts for the period [start, end].

    df_full : the full fact_daily frame
    prior   : optional (p_start, p_end) for delta calculation
    audience: 'leadership' | 'marketing' | None (all)
    """
    df_period = slice_period(df_full, start, end)
    cur = _raw_kpi_values(df_period, df_full)
    pri = None
    if prior is not None:
        df_prior = slice_period(df_full, prior[0], prior[1])
        pri = _raw_kpi_values(df_prior, df_full)

    out = []
    for k in CATALOG:
        if audience and k["audience"] != audience:
            continue
        val = cur[k["id"]]
        delta = None
        if pri is not None and pri[k["id"]] is not None and val is not None:
            delta = val - pri[k["id"]]
        out.append({
            **k,
            "value": val,
            "delta": delta,
            "value_fmt": fmt(val, k["unit"]),
            "target_fmt": fmt(k["target"], k["unit"]),
            "delta_fmt": fmt_delta(delta, k["unit"]),
            "status": status_key(val, k["target"], k["direction"]),
        })
    return out


def kpi_timeseries(df_full, kpi_id, freq="W", start=None, end=None):
    """Return a (date, value) frame for one KPI, bucketed to freq (D/W/M).

    Each bucket is recomputed from the actual daily rows it contains, so both
    flow KPIs (summed) and snapshot KPIs (end-of-bucket) come out correct.
    """
    df = df_full
    if start is not None:
        df = df[df["date"].dt.date >= start]
    if end is not None:
        df = df[df["date"].dt.date <= end]
    if df.empty:
        return pd.DataFrame(columns=["date", "value"])
    buckets = df.set_index("date").resample(freq).size()
    rows = []
    for bucket_end, _ in buckets.items():
        if freq == "W":
            b_start = bucket_end - pd.Timedelta(days=6)
        elif freq == "M":
            b_start = bucket_end.replace(day=1)
        else:
            b_start = bucket_end
        sl = df[(df["date"] >= b_start) & (df["date"] <= bucket_end)]
        if sl.empty:
            continue
        v = _raw_kpi_values(sl, df_full)
        rows.append({"date": sl["date"].max(), "value": v.get(kpi_id)})
    return pd.DataFrame(rows)
