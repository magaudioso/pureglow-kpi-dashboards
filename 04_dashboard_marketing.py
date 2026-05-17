"""04_dashboard_marketing.py
================================================================================
PureGlow - Marketing Execution KPI Dashboard  (Streamlit)

Audience : the marketing team in the case - Maya Chen (Marketing Director),
           Derek Osei (Digital Ads Specialist), Sofia Reyes (CRM & Email Manager).
Design   : denser than the leadership view - channel breakdowns, drill-down
           tables, week-over-week deltas, tabbed by function.
Period   : a fully CUSTOM date-range picker + granularity toggle - the people
           pulling the levers need to slice freely, not pick from presets.

Run:  streamlit run 04_dashboard_marketing.py
================================================================================
"""
import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import kpi_lib
import theme

P = theme.MARKETING
FREQ = {"Daily": "D", "Weekly": "W", "Monthly": "M"}

st.set_page_config(page_title="PureGlow - Marketing Execution Dashboard",
                   page_icon="*", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(theme.streamlit_css(P, dense=True), unsafe_allow_html=True)

fact = kpi_lib.load_fact_daily()
fkw = kpi_lib.load_fact_keyword()
flp = kpi_lib.load_fact_landing_page()
fem = kpi_lib.load_fact_email()
data_min, data_max = kpi_lib.data_bounds(fact)

# ---------------------------------------------------------------- header + controls
bcol, dcol, gcol = st.columns([2.6, 1.7, 1.5], vertical_alignment="center")
with bcol:
    st.markdown(theme.brand_header_html(P, "Marketing Execution Dashboard"),
                unsafe_allow_html=True)
with dcol:
    default_start = max(data_min, data_max - dt.timedelta(days=29))
    rng = st.date_input("Date range", value=(default_start, data_max),
                        min_value=data_min, max_value=data_max,
                        label_visibility="collapsed")
    if isinstance(rng, tuple) and len(rng) == 2:
        start, end = rng
    else:
        start, end = default_start, data_max
with gcol:
    gran = st.radio("Granularity", list(FREQ.keys()), index=1,
                    horizontal=True, label_visibility="collapsed")

freq = FREQ[gran]
st.markdown("<hr class='pg-rule'>", unsafe_allow_html=True)
prior = kpi_lib.prior_window(start, end, data_min)
kpis = kpi_lib.compute_kpis(fact, start, end, audience="marketing", prior=prior)

# ---------------------------------------------------------------- tiles
st.markdown("<div class='pg-section'>Lagging indicators</div>",
            unsafe_allow_html=True)
lag = [k for k in kpis if k["indicator"] == "lagging"]
for col, k in zip(st.columns(len(lag)), lag):
    col.markdown(theme.tile_html(k), unsafe_allow_html=True)

st.markdown("<div class='pg-section'>Leading indicators</div>",
            unsafe_allow_html=True)
lead = [k for k in kpis if k["indicator"] == "leading"]
for col, k in zip(st.columns(len(lead)), lead):
    col.markdown(theme.tile_html(k), unsafe_allow_html=True)

st.markdown("<hr class='pg-rule'>", unsafe_allow_html=True)

# ---------------------------------------------------------------- helpers
def in_range(df):
    return df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)].copy()


def fig(title, height=250):
    f = go.Figure()
    f.update_layout(**theme.plotly_layout(P),
                    title=dict(text=title, x=0, y=0.95,
                               font=dict(size=15, color=P["ink"])),
                    margin=dict(l=48, r=18, t=46, b=30),
                    height=height)
    return f


tab_paid, tab_email, tab_lp = st.tabs(
    ["  Paid / SEM  (Derek)  ", "  Email / CRM  (Sofia)  ", "  Landing pages  (Derek + Maya)  "])

# ============================================================ PAID / SEM
with tab_paid:
    d = in_range(fact)
    g = d.set_index("date").resample(freq).sum(numeric_only=True).reset_index()
    g["cpc"] = g["ad_spend"] / g["clicks"].replace(0, pd.NA)
    g["ctr"] = g["clicks"] / g["impressions"].replace(0, pd.NA)

    a, b = st.columns(2)
    with a:
        f = fig(f"Ad spend & CPC ({gran.lower()})")
        f.add_trace(go.Bar(x=g["date"], y=g["ad_spend"], name="Ad spend",
                           marker_color=theme.CHANNEL["Paid search"], opacity=0.85))
        f.add_trace(go.Scatter(x=g["date"], y=g["cpc"], name="CPC", yaxis="y2",
                               mode="lines+markers", line=dict(color=P["accent"], width=2)))
        f.update_layout(yaxis=dict(title="Spend", tickprefix="$", tickformat=".2s"),
                        yaxis2=dict(title="CPC", overlaying="y", side="right",
                                    tickprefix="$", showgrid=False))
        f.add_hline(y=1.20, line=dict(color=theme.STATUS["watch"]["color"], dash="dot"),
                    yref="y2", annotation_text="CPC target $1.20", annotation_font_size=9)
        st.plotly_chart(f, width="stretch")
    with b:
        f = fig(f"Click-through rate ({gran.lower()})")
        f.add_trace(go.Scatter(x=g["date"], y=g["ctr"], name="CTR", mode="lines+markers",
                               line=dict(color=theme.CHANNEL["Paid search"], width=2.5)))
        f.add_hline(y=0.045, line=dict(color=theme.STATUS["on_track"]["color"], dash="dash"),
                    annotation_text="Target 4.5%", annotation_font_size=9)
        f.update_yaxes(tickformat=".1%")
        st.plotly_chart(f, width="stretch")

    st.markdown("<div class='pg-section'>Keyword intent tiers</div>",
                unsafe_allow_html=True)
    k = in_range(fkw)
    tier = k.groupby("intent_tier", as_index=False).agg(
        Spend=("cost", "sum"), Clicks=("clicks", "sum"),
        Conversions=("gads_conversions", "sum"))
    tot = tier["Spend"].sum() or 1
    tier["Spend share"] = (tier["Spend"] / tot * 100).round(1).astype(str) + "%"
    tier["CPC"] = (tier["Spend"] / tier["Clicks"].replace(0, pd.NA)).round(2)
    tier["Cost / conv."] = (tier["Spend"] / tier["Conversions"].replace(0, pd.NA)).round(2)
    tier["Spend"] = tier["Spend"].round(0)
    tier = tier.sort_values("Spend", ascending=False).rename(columns={"intent_tier": "Intent tier"})
    st.dataframe(tier[["Intent tier", "Spend", "Spend share", "Clicks",
                       "CPC", "Conversions", "Cost / conv."]],
                 width="stretch", hide_index=True)
    hi = k[k["is_high_intent"]]["cost"].sum() / tot
    cv = k[k["is_crm_verified"]]["cost"].sum() / tot
    st.markdown(
        f"<div class='pg-sub'>High-intent share <b>{hi*100:.1f}%</b> "
        f"(target &ge; 75%) &nbsp;·&nbsp; "
        f"CRM-verified <b>{cv*100:.1f}%</b> (target &ge; 70%)</div>",
        unsafe_allow_html=True)

# ============================================================ EMAIL / CRM
with tab_email:
    e = in_range(fem)
    seg = e.groupby("segment", as_index=False).agg(
        Sends=("sends", "sum"), Delivered=("delivered", "sum"),
        Opens=("opens", "sum"), Clicks=("clicks", "sum"))
    seg["Open rate"] = (seg["Opens"] / seg["Delivered"].replace(0, pd.NA))
    seg["CTR"] = (seg["Clicks"] / seg["Delivered"].replace(0, pd.NA))

    a, b = st.columns([1.4, 1])
    with a:
        f = fig(f"Open rate by segment ({gran.lower()})")
        eg = e.copy()
        eg["bucket"] = eg["date"].dt.to_period(freq).dt.to_timestamp()
        for s in sorted(eg["segment"].unique()):
            sub = (eg[eg["segment"] == s].groupby("bucket", as_index=False)
                   [["opens", "delivered"]].sum())
            sub["open_rate"] = sub["opens"] / sub["delivered"].replace(0, pd.NA)
            f.add_trace(go.Scatter(x=sub["bucket"], y=sub["open_rate"], name=s,
                                   mode="lines", line=dict(width=2)))
        f.add_hline(y=0.28, line=dict(color=theme.STATUS["on_track"]["color"], dash="dash"),
                    annotation_text="Target 28%", annotation_font_size=9)
        f.update_yaxes(tickformat=".0%")
        st.plotly_chart(f, width="stretch")
    with b:
        seg_show = seg.copy()
        seg_show["Open rate"] = (seg_show["Open rate"] * 100).round(1).astype(str) + "%"
        seg_show["CTR"] = (seg_show["CTR"] * 100).round(1).astype(str) + "%"
        st.markdown("<div class='pg-section'>Segment performance</div>",
                    unsafe_allow_html=True)
        st.dataframe(seg_show[["segment", "Sends", "Open rate", "CTR"]],
                     width="stretch", hide_index=True)

    # batch-and-blast retirement guardrail
    fr = in_range(fact)
    seg_share = fr["emails_sent_segmented"].sum() / max(fr["emails_sent"].sum(), 1)
    gstatus = theme.STATUS["on_track"] if seg_share >= 0.99 else (
        theme.STATUS["watch"] if seg_share >= 0.9 else theme.STATUS["off_track"])
    st.markdown(
        f"<div class='pg-sub'>Segmented send share <b>{seg_share*100:.1f}%</b> "
        f"<span style='color:{gstatus['color']};font-weight:700;'>"
        f"{gstatus['glyph']} {gstatus['label']}</span> &nbsp;·&nbsp; target 100%.</div>",
        unsafe_allow_html=True)

# ============================================================ LANDING PAGES
with tab_lp:
    l = in_range(flp)
    lp = l.groupby("landing_page", as_index=False).agg(
        Sessions=("sessions", "sum"), Engaged=("engaged_sessions", "sum"),
        Conversions=("conversions", "sum"), Revenue=("revenue", "sum"))
    lp["Conv. rate"] = lp["Conversions"] / lp["Sessions"].replace(0, pd.NA)
    lp["Bounce rate"] = 1 - lp["Engaged"] / lp["Sessions"].replace(0, pd.NA)

    a, b = st.columns([1, 1.25])
    with a:
        f = fig("Conversion rate by landing page")
        lp_sorted = lp.sort_values("Conv. rate")
        colors = [theme.STATUS["on_track"]["color"] if v >= 0.045
                  else (theme.STATUS["watch"]["color"] if v >= 0.045 * 0.85
                        else theme.STATUS["off_track"]["color"])
                  for v in lp_sorted["Conv. rate"]]
        f.add_trace(go.Bar(x=lp_sorted["Conv. rate"], y=lp_sorted["landing_page"],
                           orientation="h", marker_color=colors))
        f.add_vline(x=0.045, line=dict(color=P["accent"], dash="dash"),
                    annotation_text="Target 4.5%", annotation_font_size=9)
        f.update_xaxes(tickformat=".1%")
        st.plotly_chart(f, width="stretch")
    with b:
        lp_show = lp.sort_values("Sessions", ascending=False).copy()
        lp_show["Conv. rate"] = (lp_show["Conv. rate"] * 100).round(2).astype(str) + "%"
        lp_show["Bounce rate"] = (lp_show["Bounce rate"] * 100).round(1).astype(str) + "%"
        lp_show["Revenue"] = lp_show["Revenue"].round(0)
        st.markdown("<div class='pg-section'>Landing page detail</div>",
                    unsafe_allow_html=True)
        st.dataframe(lp_show[["landing_page", "Sessions", "Conv. rate",
                              "Bounce rate", "Revenue"]],
                     width="stretch", hide_index=True)

st.markdown(
    "<div class='pg-foot'>Synthetic case data &middot; not real PureGlow data.</div>",
    unsafe_allow_html=True)
