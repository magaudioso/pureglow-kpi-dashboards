"""03_dashboard_leadership.py
================================================================================
PureGlow - Leadership KPI Dashboard  (Streamlit)

Audience : CEO + leadership team.  Accountable owner: Maya Chen.
Design   : sparse, outcome-level, restrained. A small number of large tiles,
           generous white space, status reserved to green/amber/red + glyph.
Period   : a PRESET dropdown (this month / last month / this quarter / YTD /
           full phase) - executives toggle, they do not fiddle with calendars.

Run:  streamlit run 03_dashboard_leadership.py
================================================================================
"""
import datetime as dt
import os

import plotly.graph_objects as go
import streamlit as st
from PIL import Image

import kpi_lib
import theme

P = theme.LEADERSHIP
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON = Image.open(os.path.join(ASSETS, "pureglow_icon.png"))
LOGO = os.path.join(ASSETS, "pureglow_logo.png")

st.set_page_config(page_title="PureGlow - Leadership KPI Dashboard",
                   page_icon=ICON, layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(theme.streamlit_css(P), unsafe_allow_html=True)

fact = kpi_lib.load_fact_daily()
data_min, data_max = kpi_lib.data_bounds(fact)

# ---------------------------------------------------------------- header + period
left, mid, right = st.columns([1.1, 3, 1.2], vertical_alignment="center")
with left:
    st.image(LOGO, width=190)
with mid:
    st.markdown("<div class='pg-title'>Leadership KPI Dashboard</div>",
                unsafe_allow_html=True)
with right:
    presets = kpi_lib.leadership_presets(data_min, data_max)
    choice = st.selectbox("Period", list(presets.keys()),
                          index=0, label_visibility="collapsed")
    start, end = presets[choice]
st.markdown("<hr class='pg-rule'>", unsafe_allow_html=True)

prior = kpi_lib.prior_window(start, end, data_min)
kpis = kpi_lib.leadership_kpis(fact, start, end, prior=prior)
by_id = {k["id"]: k for k in kpis}

st.markdown(theme.status_rollup_html(kpis), unsafe_allow_html=True)

# ---------------------------------------------------------------- lagging tiles
st.markdown("<div class='pg-section'>Lagging indicators</div>",
            unsafe_allow_html=True)
lag = [k for k in kpis if k["indicator"] == "lagging"]
lead = [k for k in kpis if k["indicator"] == "leading"]
n_grid = max(len(lag), 1)
for col, k in zip(st.columns(n_grid), lag):
    col.markdown(theme.tile_html(k), unsafe_allow_html=True)

# leading indicator(s) on the left, full scorecard fitted to the right ----------
st.markdown("<div class='pg-section'>Leading indicator &amp; scorecard</div>",
            unsafe_allow_html=True)
n_lead = max(len(lead), 1)
row = st.columns([1] * n_lead + [n_grid - n_lead], vertical_alignment="top")
for col, k in zip(row, lead):
    col.markdown(theme.tile_html(k), unsafe_allow_html=True)
sc_col = row[-1]

# ---- scorecard, fitted to the right of the leading-indicator tile ------------
import pandas as pd

rows, status_keys = [], []
for k in kpis:
    s = theme.STATUS[k["status"]]
    rows.append({
        "KPI": k["name"], "Owner": k["owner"], "Value": k["value_fmt"],
        "Target": k["target_fmt"], "Delta": k["delta_fmt"] or "-",
        "Status": f"{s['glyph']} {s['label']}",
    })
    status_keys.append(k["status"])
scorecard = pd.DataFrame(rows)


def _color_cells(df_):
    """Tint the scorecard's Status + Value cells to the status palette."""
    style = pd.DataFrame("", index=df_.index, columns=df_.columns)
    for i, sk in enumerate(status_keys):
        c = theme.STATUS[sk]["color"]
        style.iloc[i, df_.columns.get_loc("Status")] = (
            f"background-color: {c}; color: #0B0F14; font-weight: 700;"
            " text-align: center;")
        style.iloc[i, df_.columns.get_loc("Value")] = (
            f"color: {c}; font-weight: 700;")
    return style


sc_col.dataframe(scorecard.style.apply(_color_cells, axis=None),
                 width="stretch", hide_index=True,
                 height=36 * (len(scorecard) + 1))
st.markdown("<hr class='pg-rule'>", unsafe_allow_html=True)

# ---------------------------------------------------------------- charts
# Always show the FULL phase for context, with the selected window shaded.
def base_fig(title):
    fig = go.Figure()
    layout = theme.plotly_layout(P)
    layout["margin"] = dict(l=48, r=18, t=44, b=28)
    fig.update_layout(**layout,
                      title=dict(text=title, x=0, y=0.95,
                                 font=dict(size=14, color=P["ink"])),
                      height=230)
    fig.add_vrect(x0=start, x1=end, fillcolor=P["accent"], opacity=0.06, line_width=0)
    return fig


ts_rev = kpi_lib.kpi_timeseries(fact, "LEAD_REVENUE_RR", freq="W")
ts_roas = kpi_lib.kpi_timeseries(fact, "LEAD_ROAS", freq="W")
weekly = fact.set_index("date").resample("W").sum(numeric_only=True).reset_index()

c1, c2, c3 = st.columns(3)

with c1:
    fig = base_fig("Online revenue run-rate (weekly)")
    fig.add_trace(go.Scatter(x=ts_rev["date"], y=ts_rev["value"], mode="lines",
                             line=dict(color=P["accent"], width=2.5), name="Run-rate"))
    fig.add_hline(y=kpi_lib.CONFIG["revenue_runrate_target"],
                  line=dict(color=theme.STATUS["on_track"]["color"], dash="dash", width=1.5),
                  annotation_text="Target $8.4M", annotation_font_size=10)
    fig.update_yaxes(tickprefix="$", tickformat=".2s")
    st.plotly_chart(fig, width="stretch", theme=None)

with c2:
    fig = base_fig("Revenue mix: new vs returning customers (weekly)")
    fig.add_trace(go.Bar(x=weekly["date"], y=weekly["revenue"] - weekly["returning_revenue"],
                         name="New customers", marker_color=theme.CHANNEL["Paid search"]))
    fig.add_trace(go.Bar(x=weekly["date"], y=weekly["returning_revenue"],
                         name="Returning customers", marker_color=theme.CHANNEL["Email / CRM"]))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(tickprefix="$", tickformat=".2s")
    st.plotly_chart(fig, width="stretch", theme=None)

with c3:
    fig = base_fig("Blended ROAS (weekly)")
    fig.add_trace(go.Scatter(x=ts_roas["date"], y=ts_roas["value"], mode="lines",
                             line=dict(color=P["accent"], width=2.5), name="Blended ROAS"))
    fig.add_hline(y=4.0, line=dict(color=theme.STATUS["on_track"]["color"], dash="dash", width=1.5),
                  annotation_text="Target 4.0x", annotation_font_size=10)
    fig.update_yaxes(ticksuffix="x")
    st.plotly_chart(fig, width="stretch", theme=None)

st.markdown(
    "<div class='pg-foot'>Synthetic case data &middot; not real PureGlow data.</div>",
    unsafe_allow_html=True)
