"""05_render_previews.py
================================================================================
Render static PNG previews of the two dashboards.

The interactive dashboards live in Streamlit (scripts 03 and 04). This script
produces faithful STILL images of them - same theme module, same kpi_lib
numbers - for the alignment document and for anyone who wants to see the design
without spinning up Streamlit.

Outputs:  previews/preview_leadership.png
          previews/preview_marketing.png

Run:  python 05_render_previews.py
================================================================================
"""
import os
import datetime as dt
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter

import kpi_lib
import theme

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "previews")
os.makedirs(OUT, exist_ok=True)

fact = kpi_lib.load_fact_daily()
fkw = kpi_lib.load_fact_keyword()
data_min, data_max = kpi_lib.data_bounds(fact)

USD_M = FuncFormatter(lambda v, _: f"${v/1e6:.1f}M")
USD_K = FuncFormatter(lambda v, _: f"${v/1e3:.0f}K")
PCT = FuncFormatter(lambda v, _: f"{v*100:.1f}%")
RATIO = FuncFormatter(lambda v, _: f"{v:.1f}x")
USD2 = FuncFormatter(lambda v, _: f"${v:.2f}")


# ------------------------------------------------------------------ tile drawing
def tile(ax, x, y, w, h, k, pal):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.5",
        facecolor=pal["panel"], edgecolor=pal["border"], linewidth=1.0))
    s = theme.STATUS[k["status"]]
    pad = 0.8
    # name - wrapped to at most two lines
    lines = textwrap.wrap(k["name"], width=27)[:2]
    ty = y + h - 1.0
    for ln in lines:
        ax.text(x + pad, ty, ln, fontsize=6.4, color=pal["muted"],
                fontweight="bold", va="top")
        ty -= 1.42
    if k.get("is_new"):
        ax.text(x + w - pad, y + h - 0.9, "NEW", fontsize=5.0, color="#7A5C00",
                fontweight="bold", va="top", ha="right",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="#FCEFC7",
                          edgecolor="none"))
    # value
    ax.text(x + pad, y + h * 0.40, k["value_fmt"], fontsize=14, color=pal["ink"],
            fontweight="bold", va="center")
    # status + target + mapping
    ax.text(x + pad, y + 2.45, f"{s['glyph']} {s['label']}", fontsize=6.8,
            color=s["color"], fontweight="bold", va="center")
    tgt = f"target {k['target_fmt']}"
    if k.get("delta_fmt"):
        tgt += f"   {k['delta_fmt']}"
    ax.text(x + pad, y + 1.25, tgt, fontsize=5.7, color="#8A8F98", va="center")
    ax.text(x + pad, y + 0.25, f"{k['maps_to']}  -  {k['owner']}", fontsize=4.9,
            color=pal["muted"], va="bottom", style="italic")


def tile_row(ax, kpis, y, h, pal, x0=1.5, x1=98.5, gap=0.9):
    n = len(kpis)
    w = (x1 - x0 - gap * (n - 1)) / n
    for i, k in enumerate(kpis):
        tile(ax, x0 + i * (w + gap), y, w, h, k, pal)


def canvas(pal, w_in=13.4, h_in=8.7):
    fig = plt.figure(figsize=(w_in, h_in), dpi=150)
    fig.patch.set_facecolor(pal["bg"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 100, 100, facecolor=pal["bg"], zorder=-1))
    return fig, ax


def mini_axes(fig, x, y, w, h, pal):
    ax = fig.add_axes([x / 100, y / 100, w / 100, h / 100])
    ax.set_facecolor(pal["panel"])
    for sp in ax.spines.values():
        sp.set_color(pal["border"])
    ax.tick_params(colors=pal["muted"], labelsize=6, length=2)
    ax.grid(color=pal["grid"], linewidth=0.6)
    return ax


def section(ax, x, y, txt, pal):
    ax.text(x, y, txt, fontsize=7.6, color=pal["accent"], fontweight="bold",
            va="top")


# ================================================================ LEADERSHIP
def render_leadership():
    pal = theme.LEADERSHIP
    presets = kpi_lib.leadership_presets(data_min, data_max)
    start, end = presets["Last full month"]
    prior = kpi_lib.prior_window(start, end, data_min)
    kpis = kpi_lib.compute_kpis(fact, start, end, audience="leadership", prior=prior)
    lag = [k for k in kpis if k["indicator"] == "lagging"]
    lead = [k for k in kpis if k["indicator"] == "leading"]

    fig, ax = canvas(pal)
    ax.text(1.5, 97.2, "PureGlow  -  Leadership KPI Dashboard", fontsize=17,
            color=pal["ink"], fontweight="bold", family="serif", va="top")
    ax.text(1.5, 93.0, "6-month growth phase   |   finishing the doubling "
            f"profitably   |   data through {data_max:%d %b %Y}",
            fontsize=8, color=pal["muted"], va="top")
    # preset dropdown
    ax.add_patch(FancyBboxPatch((80.5, 92.3), 18, 4.7,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor=pal["panel"], edgecolor=pal["accent"], linewidth=1.2))
    ax.text(81.6, 96.0, "REPORTING PERIOD", fontsize=5.6, color=pal["muted"],
            fontweight="bold", va="top")
    ax.text(81.6, 94.1, "Last full month   v", fontsize=8.2, color=pal["ink"],
            fontweight="bold", va="center")
    ax.add_patch(Rectangle((1.5, 91.0), 97, 0.18, facecolor=pal["accent"]))
    ax.text(1.5, 89.7, f"PRESET PERIOD   {start:%d %b} - {end:%d %b %Y}     "
            "executives toggle presets - they do not pick raw dates",
            fontsize=6.8, color=pal["muted"], va="top", style="italic")

    section(ax, 1.5, 87.0, "NORTH-STAR OUTCOMES  -  LAGGING INDICATORS", pal)
    tile_row(ax, lag, y=71.5, h=13.5, pal=pal)

    section(ax, 1.5, 68.5, "FORWARD SIGNALS  -  LEADING INDICATORS", pal)
    tile_row(ax, lead, y=53.0, h=13.5, pal=pal, x0=1.5, x1=78.5)
    ax.add_patch(FancyBboxPatch((79.8, 53.0), 18.7, 13.5,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor="#F2F4F0", edgecolor=pal["border"], linewidth=1))
    ax.text(81.0, 65.3, "HOW TO READ", fontsize=6.4, color=pal["accent"],
            fontweight="bold", va="top")
    for i, ln in enumerate([
            "Every tile maps to an OKR", "Key Result.",
            "Status is reserved to", "green / amber / red + a glyph.",
            "Deltas compare the prior", "period (same length)."]):
        ax.text(81.0, 63.0 - i * 1.6, ln, fontsize=6.0, color=pal["muted"], va="top")

    section(ax, 1.5, 49.8, "TREND CONTEXT  -  FULL PHASE, SELECTED WINDOW SHADED", pal)
    weekly = fact.set_index("date").resample("W").sum(numeric_only=True).reset_index()
    weekly["new_rev"] = weekly["revenue"] - weekly["returning_revenue"]
    ts_rev = kpi_lib.kpi_timeseries(fact, "LEAD_REVENUE_RR", freq="W")
    ts_roas = kpi_lib.kpi_timeseries(fact, "LEAD_ROAS", freq="W")

    a1 = mini_axes(fig, 1.5, 6.5, 30, 38, pal)
    a1.plot(ts_rev["date"], ts_rev["value"], color=pal["accent"], lw=2)
    a1.axhline(kpi_lib.CONFIG["revenue_runrate_target"],
               color=theme.STATUS["on_track"]["color"], ls="--", lw=1)
    a1.axvspan(start, end, color=pal["accent"], alpha=0.08)
    a1.set_title("Online revenue run-rate (weekly)", fontsize=10.5,
                 color=pal["ink"], loc="left", fontweight="bold", pad=8)
    a1.set_ylim(6.4e6, 9.0e6)
    a1.yaxis.set_major_formatter(USD_M)

    a2 = mini_axes(fig, 35.5, 6.5, 30, 38, pal)
    a2.bar(weekly["date"], weekly["new_rev"], width=5,
           color=theme.CHANNEL["Paid search"], label="New")
    a2.bar(weekly["date"], weekly["returning_revenue"], width=5,
           bottom=weekly["new_rev"], color=theme.CHANNEL["Email / CRM"],
           label="Returning")
    a2.set_title("Revenue mix: new vs returning (weekly)", fontsize=10.5,
                 color=pal["ink"], loc="left", fontweight="bold", pad=8)
    a2.yaxis.set_major_formatter(USD_K)
    a2.legend(fontsize=5.5, loc="upper left", frameon=False)

    a3 = mini_axes(fig, 69.5, 6.5, 29, 38, pal)
    a3.plot(ts_roas["date"], ts_roas["value"], color=pal["accent"], lw=2)
    a3.axhline(4.0, color=theme.STATUS["on_track"]["color"], ls="--", lw=1)
    a3.axvspan(start, end, color=pal["accent"], alpha=0.08)
    a3.set_title("Blended ROAS (weekly)", fontsize=10.5, color=pal["ink"], loc="left", fontweight="bold", pad=8)
    a3.yaxis.set_major_formatter(RATIO)

    ax.text(1.5, 2.2, "Static preview - the interactive version runs in Streamlit "
            "(03_dashboard_leadership.py). Synthetic case data, not real PureGlow data.",
            fontsize=6.2, color=pal["muted"], va="center", style="italic")

    path = os.path.join(OUT, "preview_leadership.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  wrote {os.path.relpath(path, HERE)}")


# ================================================================ MARKETING
def render_marketing():
    pal = theme.MARKETING
    end = data_max
    start = end - dt.timedelta(days=29)
    prior = kpi_lib.prior_window(start, end, data_min)
    kpis = kpi_lib.compute_kpis(fact, start, end, audience="marketing", prior=prior)
    lag = [k for k in kpis if k["indicator"] == "lagging"]
    lead = [k for k in kpis if k["indicator"] == "leading"]

    fig, ax = canvas(pal)
    ax.text(1.5, 97.2, "PureGlow  -  Marketing Execution KPI Dashboard", fontsize=16,
            color=pal["ink"], fontweight="bold", family="serif", va="top")
    ax.text(1.5, 93.2, "Weekly cockpit for the marketing team   |   "
            "Maya Chen, Derek Osei, Sofia Reyes", fontsize=8,
            color=pal["muted"], va="top")
    # custom controls
    ax.add_patch(FancyBboxPatch((1.5, 86.4), 34, 4.8,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor=pal["panel"], edgecolor=pal["accent"], linewidth=1.2))
    ax.text(2.7, 90.0, "CUSTOM DATE RANGE", fontsize=5.6, color=pal["muted"],
            fontweight="bold", va="top")
    ax.text(2.7, 88.2, f"{start:%d %b %Y}   -   {end:%d %b %Y}", fontsize=8.0,
            color=pal["ink"], fontweight="bold", va="center")
    ax.add_patch(FancyBboxPatch((37, 86.4), 20, 4.8,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor=pal["panel"], edgecolor=pal["border"], linewidth=1))
    ax.text(38.1, 90.0, "GRANULARITY", fontsize=5.6, color=pal["muted"],
            fontweight="bold", va="top")
    ax.text(38.1, 88.2, "Daily   [Weekly]   Monthly", fontsize=7.6,
            color=pal["ink"], va="center")
    ax.text(59, 88.8, "fully custom - the team slices freely,\nnot from presets",
            fontsize=6.6, color=pal["muted"], va="center", style="italic")
    ax.add_patch(Rectangle((1.5, 85.0), 97, 0.18, facecolor=pal["accent"]))

    section(ax, 1.5, 83.0, "CHANNEL OUTCOMES  -  LAGGING INDICATORS", pal)
    tile_row(ax, lag, y=69.0, h=12.5, pal=pal)
    section(ax, 1.5, 66.0, "WEEKLY LEVERS  -  LEADING INDICATORS", pal)
    tile_row(ax, lead, y=52.0, h=12.5, pal=pal)

    # tab bar
    ax.text(4.5, 48.6, "Paid / SEM  (Derek)", fontsize=7.4, color="white",
            fontweight="bold", va="center", ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=pal["accent"],
                      edgecolor="none"))
    ax.text(22, 48.6, "Email / CRM  (Sofia)", fontsize=7.4, color=pal["muted"],
            va="center", ha="center")
    ax.text(42, 48.6, "Landing pages  (Derek + Maya)", fontsize=7.4,
            color=pal["muted"], va="center", ha="center")
    ax.add_patch(Rectangle((1.5, 46.6), 97, 0.12, facecolor=pal["border"]))
    ax.text(1.5, 44.5, "PAID / SEM TAB  -  one of three function tabs", fontsize=6.6,
            color=pal["muted"], va="top", style="italic")

    d = fact[(fact["date"].dt.date >= start) & (fact["date"].dt.date <= end)]
    g = d.set_index("date").resample("W").sum(numeric_only=True).reset_index()
    g["cpc"] = g["ad_spend"] / g["clicks"]
    g["ctr"] = g["clicks"] / g["impressions"]

    a1 = mini_axes(fig, 1.5, 7, 30, 33, pal)
    a1.bar(g["date"], g["ad_spend"], width=4.5, color=theme.CHANNEL["Paid search"],
           alpha=0.85)
    a1b = a1.twinx()
    a1b.plot(g["date"], g["cpc"], color=pal["accent"], lw=2, marker="o", ms=3)
    a1b.axhline(1.20, color=theme.STATUS["watch"]["color"], ls=":", lw=1)
    a1b.tick_params(colors=pal["muted"], labelsize=6)
    a1b.set_ylim(0.9, 1.4)
    a1b.yaxis.set_major_formatter(USD2)
    a1.set_title("Ad spend & CPC (weekly)", fontsize=10.5, color=pal["ink"], loc="left", fontweight="bold", pad=8)
    a1.yaxis.set_major_formatter(USD_K)

    a2 = mini_axes(fig, 35.5, 7, 28, 33, pal)
    a2.plot(g["date"], g["ctr"], color=theme.CHANNEL["Paid search"], lw=2,
            marker="o", ms=3)
    a2.axhline(0.045, color=theme.STATUS["on_track"]["color"], ls="--", lw=1)
    a2.set_title("Click-through rate (weekly)", fontsize=10.5, color=pal["ink"],
                 loc="left", fontweight="bold", pad=8)
    a2.yaxis.set_major_formatter(PCT)

    # keyword tier table
    k = fkw[(fkw["date"].dt.date >= start) & (fkw["date"].dt.date <= end)]
    tier = (k.groupby("intent_tier").agg(cost=("cost", "sum"),
            clicks=("clicks", "sum")).reset_index().sort_values("cost",
            ascending=False))
    tot = tier["cost"].sum()
    ax.text(67, 42.0, "KEYWORD INTENT TIERS  -  SPEND DISCIPLINE", fontsize=7,
            color=pal["accent"], fontweight="bold", va="top")
    ax.add_patch(FancyBboxPatch((66.5, 8), 32, 31,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor=pal["panel"], edgecolor=pal["border"], linewidth=1))
    hy = 37.0
    ax.text(68, hy, "Intent tier", fontsize=6.4, color=pal["muted"], fontweight="bold")
    ax.text(88, hy, "Spend", fontsize=6.4, color=pal["muted"], fontweight="bold")
    ax.text(94.5, hy, "Share", fontsize=6.4, color=pal["muted"], fontweight="bold")
    for i, (_, r) in enumerate(tier.iterrows()):
        yy = hy - 2.6 - i * 2.6
        ax.text(68, yy, r["intent_tier"], fontsize=6.2, color=pal["ink"])
        ax.text(88, yy, f"${r['cost']/1e3:.0f}K", fontsize=6.2, color=pal["ink"])
        ax.text(94.5, yy, f"{r['cost']/tot*100:.0f}%", fontsize=6.2, color=pal["ink"])
    hi = k[k["is_high_intent"]]["cost"].sum() / tot
    cv = k[k["is_crm_verified"]]["cost"].sum() / tot
    ax.text(68, hy - 2.6 - len(tier) * 2.6 - 1.0,
            f"High-intent share  {hi*100:.0f}%   (target 75%)\n"
            f"CRM-verified share  {cv*100:.0f}%   (target 70%)",
            fontsize=6.1, color=pal["muted"], va="top")

    ax.text(1.5, 2.2, "Static preview - the interactive version runs in Streamlit "
            "(04_dashboard_marketing.py), with Email/CRM and Landing-page tabs too. "
            "Synthetic case data.", fontsize=6.2, color=pal["muted"], va="center",
            style="italic")

    path = os.path.join(OUT, "preview_marketing.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    print("Rendering dashboard previews...")
    render_leadership()
    render_marketing()
    print("Done.")
