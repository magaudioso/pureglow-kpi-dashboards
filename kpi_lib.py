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
    "phase_start":              dt.date(2025, 4, 1),    # implementation kick-off
    "phase_end":                dt.date(2026, 4, 30),   # case's 12-month outcome point
    "data_through":             dt.date(2026, 4, 30),
    "revenue_runrate_target":   7_100_000,   # case 12-month outcome (annualised)
    "monthly_revenue_target":   592_000,     # = $7.1M / 12
    "weekly_new_customer_plan": 1_200,       # implied by the run-rate target
    "gross_margin":             0.70,        # CLV / Day-30 payback assumption
    "runrate_window_days":      90,          # trailing window for the run-rate
}

# ------------------------------------------------------------------ CATALOG
# audience: "leadership" | "marketing"      indicator: "lagging" | "leading"
# direction: "higher" (more is better) | "lower" (less is better)
# unit: "currency" | "pct" | "ratio" | "index" | "number"
CATALOG = [
    # ---- Leadership  (5 lagging - all outcome-level)
    dict(id="LEAD_REVENUE_RR", name="Online revenue (annualised run-rate)",
         audience="leadership", indicator="lagging", owner="CEO / Maya Chen",
         maps_to="O1 - KR 1.1", target=CONFIG["revenue_runrate_target"],
         direction="higher", unit="currency", is_new=False,
         desc="Trailing-90-day online revenue, annualised. Year-1 milestone toward "
              "the CEO's 18-month doubling mandate."),
    dict(id="LEAD_ROAS", name="Blended ROAS",
         audience="leadership", indicator="lagging", owner="Maya Chen",
         maps_to="O1 - KR 1.2", target=4.0, direction="higher", unit="ratio",
         is_new=False,
         desc="Total online revenue divided by total ad spend. Case target floor."),
    dict(id="LEAD_CLV", name="Customer lifetime value (CLV index)",
         audience="leadership", indicator="lagging", owner="Maya Chen",
         maps_to="O3 - KR 3.3", target=115.0, direction="higher", unit="index",
         is_new=False,
         desc="CLV indexed to phase start (=100). Case target is +15% YoY."),
    dict(id="LEAD_RET_REV", name="Returning-customer revenue share",
         audience="leadership", indicator="lagging", owner="Sofia Reyes",
         maps_to="O3 - KR 3.2", target=0.35, direction="higher", unit="pct",
         is_new=True,
         desc="Share of revenue from customers placing their 2nd+ order. NEW metric "
              "extending the case framework toward a retention KPI."),
    dict(id="LEAD_D30_PAYBACK", name="Day-30 gross-profit payback on CAC",
         audience="leadership", indicator="lagging", owner="CEO / Maya Chen",
         maps_to="O1 - KR 1.3", target=1.0, direction="higher", unit="ratio",
         is_new=True,
         desc="For new customers acquired in the period, gross profit earned in "
              "their first 30 days divided by total acquisition spend. Hormozi's "
              "1.0x self-funding-growth threshold. NEW metric."),

    # ---- Marketing  (5 lagging + 5 leading)
    dict(id="MKT_CPA", name="Cost per acquisition (CPA) - paid search",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O1 - KR 1.3", target=18.0, direction="lower", unit="currency",
         is_new=False,
         desc="Paid-search spend divided by GCLID-attributed orders. Case target <=$18."),
    dict(id="MKT_ROAS", name="Return on ad spend (ROAS) - paid search",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O1 - KR 1.2", target=4.0, direction="higher", unit="ratio",
         is_new=False,
         desc="GCLID-attributed revenue divided by paid-search spend. Case target >=4.0x."),
    dict(id="MKT_LP_CONV", name="Landing page conversion rate",
         audience="marketing", indicator="lagging", owner="Derek Osei",
         maps_to="O2 - KR 2.1", target=0.035, direction="higher", unit="pct",
         is_new=False,
         desc="Landing-page conversions divided by sessions (GA4). Case target >=3.5%."),
    dict(id="MKT_L2C", name="Lead-to-customer conversion rate",
         audience="marketing", indicator="lagging", owner="Sofia Reyes",
         maps_to="O2 - KR 2.2", target=0.05, direction="higher", unit="pct",
         is_new=False,
         desc="New customers divided by new leads (HubSpot lifecycle stages). "
              "Case target >=5%. Shared with the leadership view as a leading signal."),
    dict(id="MKT_CART", name="Cart recovery rate",
         audience="marketing", indicator="lagging", owner="Sofia Reyes",
         maps_to="O2 - KR 2.3", target=0.20, direction="higher", unit="pct",
         is_new=False,
         desc="Recovered carts divided by abandoned carts. Case target >=20%."),
    dict(id="MKT_CPC", name="Cost per click (CPC)",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O1 - KR 1.3", target=1.20, direction="lower", unit="currency",
         is_new=False,
         desc="Paid-search cost divided by clicks. Case target <=$1.20."),
    dict(id="MKT_CTR", name="Click-through rate (CTR) - paid search",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O2 - KR 2.1", target=0.045, direction="higher", unit="pct",
         is_new=False,
         desc="Paid-search clicks divided by impressions. Case target >=4.5%."),
    dict(id="MKT_HIGH_INTENT", name="% ad spend on high-intent (Tier 1 + 2) keywords",
         audience="marketing", indicator="leading", owner="Derek Osei",
         maps_to="O1 - KR 1.2", target=0.75, direction="higher", unit="pct",
         is_new=True,
         desc="Share of paid spend on Tier 1 + Tier 2 keywords. Operationalises "
              "Decision 6 keyword discipline. NEW metric."),
    dict(id="MKT_EMAIL_OPEN", name="Email open rate",
         audience="marketing", indicator="leading", owner="Sofia Reyes",
         maps_to="O3 - KR 3.1", target=0.28, direction="higher", unit="pct",
         is_new=False,
         desc="Opens divided by delivered (segmented campaigns). Case target >=28%."),
    dict(id="MKT_EMAIL_CTR", name="Email click-through rate",
         audience="marketing", indicator="leading", owner="Sofia Reyes",
         maps_to="O3 - KR 3.1", target=0.045, direction="higher", unit="pct",
         is_new=False,
         desc="Clicks divided by delivered (segmented campaigns). Case target >=4.5%."),
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
    # latest full month (default - this is the case 'outcome month')
    presets["Latest month"] = (end.replace(day=1), end)
    # last 90 days - the trailing window that drives the run-rate
    presets["Last 90 days"] = (max(end - dt.timedelta(days=89), data_min), end)
    # calendar YTD
    presets["Year to date"] = (max(dt.date(end.year, 1, 1), data_min), end)
    # second half - the maturation period
    presets["Last 6 months"] = (max(end - dt.timedelta(days=182), data_min), end)
    # the whole 12-month implementation window
    presets["Full implementation period"] = (data_min, end)
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
            return f"${value / 1_000_000:.1f}M"   # case precision: $7.1M
        if abs(value) >= 10_000:
            return f"${value / 1_000:.0f}K"
        return f"${value:,.2f}"
    if unit == "pct":
        return f"{value * 100:.1f}%"
    if unit == "ratio":
        return f"{value:.1f}x"                     # case precision: 4.3x
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
        return f"{arrow}{delta:.1f}x"
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
    # ---- leadership lagging (5)
    v["LEAD_REVENUE_RR"] = _runrate(df_full, end)
    v["LEAD_ROAS"] = _safe_div(p["revenue"], p["ad_spend"])
    base_clv = df_full.sort_values("date")["clv_value"].head(7).mean()
    end_clv = df_period.sort_values("date")["clv_value"].tail(7).mean()
    v["LEAD_CLV"] = _safe_div(end_clv, base_clv) * 100.0
    v["LEAD_RET_REV"] = _safe_div(p["returning_revenue"], p["revenue"])
    # Day-30 gross-profit payback on CAC - cohort metric, 30-day maturity lag.
    # If the period has too few mature days, fall back to the trailing 30 mature days.
    data_max = df_full["date"].max()
    cut30 = data_max - pd.Timedelta(days=30)
    mat30 = df_period[df_period["date"] <= cut30]
    if len(mat30) < 14:
        lo = cut30 - pd.Timedelta(days=29)
        mat30 = df_full[(df_full["date"] >= lo) & (df_full["date"] <= cut30)]
    v["LEAD_D30_PAYBACK"] = _safe_div(mat30["cohort_d30_gp"].sum(),
                                      mat30["ad_spend"].sum())
    # ---- marketing lagging (5)
    v["MKT_CPA"] = _safe_div(p["ad_spend"], p["paid_orders"])
    v["MKT_ROAS"] = _safe_div(p["paid_revenue"], p["ad_spend"])
    v["MKT_LP_CONV"] = _safe_div(p["lp_conversions"], p["sessions"])
    # Lead-to-customer is cohort-based with a ~12-day conversion lag.
    cut12 = data_max - pd.Timedelta(days=12)
    mat12 = df_period[df_period["date"] <= cut12]
    if len(mat12) < 14:
        lo = cut12 - pd.Timedelta(days=29)
        mat12 = df_full[(df_full["date"] >= lo) & (df_full["date"] <= cut12)]
    v["MKT_L2C"] = _safe_div(mat12["leads_converted"].sum(),
                             mat12["leads_created"].sum())
    v["MKT_CART"] = _safe_div(p["carts_recovered"], p["carts_created"])
    # ---- marketing leading (5)
    v["MKT_CPC"] = _safe_div(p["ad_spend"], p["clicks"])
    v["MKT_CTR"] = _safe_div(p["clicks"], p["impressions"])
    v["MKT_HIGH_INTENT"] = _safe_div(p["spend_high_intent"], p["ad_spend"])
    # email open / CTR measure the segmented lifecycle programme
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


def leadership_kpis(df_full, start, end, prior=None):
    """Leadership tiles - the 5 leadership-lagging metrics plus a borrowed
    lead-to-customer tile shown as the leading indicator. (L2C is owned by
    Sofia on the marketing dashboard, but it's the CEO's revenue early-warning.)
    """
    lead = compute_kpis(df_full, start, end, audience="leadership", prior=prior)
    mkt = compute_kpis(df_full, start, end, audience="marketing", prior=prior)
    l2c = next((k for k in mkt if k["id"] == "MKT_L2C"), None)
    if l2c:
        l2c = dict(l2c)
        l2c["indicator"] = "leading"   # render in the leading section
        lead.append(l2c)
    return lead


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
