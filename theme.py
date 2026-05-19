"""theme.py - shared visual theme for the two PureGlow KPI dashboards (dark mode).

Two audiences, one source of truth.

Colour governance:
  * Green / yellow / red are RESERVED for KPI status. The BAN value AND the
    tile's top border both carry the status colour. Never used for branding.
  * Channel colours are blue / purple / teal / grey - distinct from status.
"""

# ---------------------------------------------------------------- status (bright on dark)
STATUS = {
    "on_track":  {"color": "#22C55E", "label": "On track",  "glyph": "▲"},
    "watch":     {"color": "#F5C842", "label": "Watch",     "glyph": "●"},
    "off_track": {"color": "#EF4444", "label": "Off track", "glyph": "▼"},
    "no_target": {"color": "#94A3B8", "label": "Tracking",  "glyph": "○"},
}

# ---------------------------------------------------------------- channels (bright on dark)
CHANNEL = {
    "Paid search":     "#60A5FA",
    "Email / CRM":     "#B091F0",
    "Landing / site":  "#5BC0BE",
    "Other":           "#9CA3AF",
}

# ---------------------------------------------------------------- audience palettes (dark)
LEADERSHIP = {
    "name":    "Leadership",
    "bg":      "#0B0F14",
    "panel":   "#141A21",
    "ink":     "#F3F4F6",
    "muted":   "#9CA3AF",
    "border":  "#243040",
    "accent":  "#7AA7FF",
    "grid":    "#1E2731",
    "serif":   "Georgia, 'Times New Roman', serif",
    "sans":    "'Helvetica Neue', Arial, sans-serif",
}

MARKETING = {
    "name":    "Marketing Execution",
    "bg":      "#0B0F14",
    "panel":   "#141A21",
    "ink":     "#F3F4F6",
    "muted":   "#9CA3AF",
    "border":  "#243040",
    "accent":  "#5DD6E5",
    "grid":    "#1E2731",
    "serif":   "Georgia, 'Times New Roman', serif",
    "sans":    "'Helvetica Neue', Arial, sans-serif",
}


def streamlit_css(p, dense=False):
    """Return a <style> block that themes a Streamlit page for palette `p`."""
    tile_pad = "0.5rem 0.75rem" if dense else "0.6rem 0.85rem"
    tile_min = "118px" if dense else "128px"
    return f"""
    <style>
      /* reclaim vertical space */
      header[data-testid="stHeader"] {{ display: none !important; }}
      #MainMenu, footer {{ visibility: hidden; }}
      [data-testid="stDecoration"], [data-testid="stToolbar"] {{ display: none; }}

      .stApp, .stApp p, .stApp span, .stApp div, .stApp label {{ color: {p['ink']}; }}
      .stApp {{ background: {p['bg']}; }}
      .block-container {{ padding-top: 0.6rem !important; padding-bottom: 0.4rem;
                          padding-left: 1.4rem; padding-right: 1.4rem;
                          max-width: 1750px; }}

      /* big centered title */
      .pg-title {{ font-family: {p['serif']}; font-weight: 700;
                  font-size: 2.15rem; letter-spacing: -0.4px; color: {p['ink']};
                  text-align: center; line-height: 1.05; margin: 0; }}
      h1, h2, h3 {{ color: {p['ink']}; font-family: {p['serif']}; margin: 0; }}
      .pg-sub {{ color: {p['muted']}; font-family: {p['sans']};
                font-size: 0.78rem; margin: 0; }}
      .pg-rule {{ height: 2px; background: {p['accent']}; border: 0;
                 margin: 0.3rem 0 0.45rem 0; }}
      .pg-section {{ color: {p['accent']}; font-family: {p['sans']};
                    font-weight: 700; font-size: 0.72rem; letter-spacing: 1.2px;
                    text-transform: uppercase; margin: 0.3rem 0 0.2rem 0; }}
      .pg-rollup {{ text-align: center; font-family: {p['sans']};
                   font-size: 0.9rem; letter-spacing: 0.3px;
                   margin: 0.1rem 0 0.4rem 0; }}
      .pg-rollup .sep {{ color: {p['muted']}; margin: 0 0.55rem; }}

      /* KPI tile - uniform size, status colour on value + top border */
      .pg-tile {{ background: {p['panel']}; border: 1px solid {p['border']};
                 border-radius: 8px; padding: {tile_pad};
                 min-height: {tile_min}; height: 100%;
                 display: flex; flex-direction: column; }}
      .pg-tile .lbl {{ color: {p['ink']}; font-family: {p['sans']};
                      font-size: 0.76rem; font-weight: 600; line-height: 1.2;
                      min-height: 2.4em;
                      display: -webkit-box; -webkit-line-clamp: 2;
                      -webkit-box-orient: vertical; overflow: hidden; }}
      .pg-tile .val {{ font-family: {p['sans']}; font-weight: 700;
                      font-size: 1.7rem; line-height: 1.05;
                      margin: 0.1rem 0 0.15rem 0; }}
      .pg-tile .meta {{ font-family: {p['sans']}; font-size: 0.73rem;
                       color: {p['ink']}; line-height: 1.3; }}
      .pg-tile .owner {{ color: {p['muted']}; font-family: {p['sans']};
                        font-size: 0.67rem; margin-top: auto;
                        padding-top: 0.2rem; }}

      .pg-foot {{ color: {p['muted']}; font-family: {p['sans']};
                 font-size: 0.66rem; margin-top: 0.4rem; }}

      /* widgets - dark */
      [data-testid="stMetricValue"] {{ color: {p['ink']}; }}
      .stSelectbox label, .stRadio label, .stDateInput label {{
          color: {p['muted']} !important; font-size: 0.7rem !important;
          font-weight: 600 !important; text-transform: uppercase;
          letter-spacing: 0.5px; margin-bottom: 0.1rem !important; }}
      .stSelectbox, .stRadio, .stDateInput {{ margin-bottom: 0 !important; }}
      div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
      div[data-baseweb="popover"] {{ background: {p['panel']} !important;
          border-color: {p['border']} !important; color: {p['ink']} !important; }}
      div[data-baseweb="select"] svg, div[data-baseweb="input"] svg {{
          color: {p['ink']} !important; fill: {p['ink']} !important; }}
      div[data-baseweb="menu"] {{ background: {p['panel']} !important;
          border: 1px solid {p['border']} !important; }}
      div[data-baseweb="menu"] li {{ color: {p['ink']} !important; }}
      div[data-baseweb="menu"] li:hover {{ background: {p['border']} !important; }}
      .stRadio [role="radiogroup"] label {{ color: {p['ink']} !important; }}
      .stDataFrame, .stDataFrame * {{ color: {p['ink']} !important; }}
      .stDataFrame [data-testid="stDataFrameResizable"] {{
          background: {p['panel']} !important; }}
      .stDataFrame thead tr th {{ background: {p['border']} !important;
          color: {p['ink']} !important; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: 4px;
          border-bottom: 1px solid {p['border']}; }}
      .stTabs [data-baseweb="tab"] {{ color: {p['muted']}; font-weight: 600;
                                     padding: 4px 12px; background: transparent; }}
      .stTabs [aria-selected="true"] {{ color: {p['accent']}; }}
      .stTabs [data-baseweb="tab-highlight"] {{ background: {p['accent']} !important; }}
      [data-baseweb="calendar"], [data-baseweb="calendar"] * {{
          background: {p['panel']} !important; color: {p['ink']} !important; }}
      a, a:visited {{ color: {p['accent']}; }}

      /* compact rhythm */
      .element-container {{ margin-bottom: 0.2rem !important; }}
      .stMarkdown {{ margin-bottom: 0 !important; }}
      hr {{ margin: 0.3rem 0 !important; }}
    </style>
    """


def tile_html(k):
    """One KPI tile: status-coloured value + top border. No NEW badge, no OKR
    mapping, no status wording. Keeps name, value, target, delta, owner."""
    c = STATUS[k["status"]]["color"]
    delta = f" &nbsp;·&nbsp; {k['delta_fmt']}" if k.get("delta_fmt") else ""
    return f"""
    <div class="pg-tile" style="border-top:3px solid {c};">
      <div class="lbl">{k['name']}</div>
      <div class="val" style="color:{c};">{k['value_fmt']}</div>
      <div class="meta">target {k['target_fmt']}{delta}</div>
      <div class="owner">Owner: {k['owner']}</div>
    </div>
    """


def status_rollup_html(kpis):
    """One-glance status band: counts per status, coloured + glyphed."""
    counts = {}
    for k in kpis:
        counts[k["status"]] = counts.get(k["status"], 0) + 1
    parts = []
    for s in ("on_track", "watch", "off_track", "no_target"):
        n = counts.get(s)
        if not n:
            continue
        st = STATUS[s]
        parts.append(
            f"<span style='color:{st['color']};font-weight:700;'>"
            f"{st['glyph']} {n} {st['label']}</span>")
    return ("<div class='pg-rollup'>"
            + "<span class='sep'>·</span>".join(parts)
            + "</div>")


def plotly_layout(p):
    """Base layout kwargs for Plotly figures, themed dark for palette `p`.

    Call sites assign `layout["margin"] = ...` before splatting, so margin is
    safe to include here.
    """
    sans = p["sans"].split(",")[0].strip("'")
    return dict(
        paper_bgcolor=p["panel"],
        plot_bgcolor=p["panel"],
        font=dict(family=sans, color=p["ink"], size=13),
        margin=dict(l=50, r=18, t=46, b=32),
        xaxis=dict(gridcolor=p["grid"], zeroline=False, linecolor=p["border"],
                   tickfont=dict(size=12, color=p["ink"])),
        yaxis=dict(gridcolor=p["grid"], zeroline=False, linecolor=p["border"],
                   tickfont=dict(size=12, color=p["ink"])),
        legend=dict(orientation="h", y=-0.2, x=0,
                    font=dict(size=11, color=p["ink"])),
        colorway=[p["accent"], CHANNEL["Paid search"], CHANNEL["Email / CRM"],
                  CHANNEL["Landing / site"], CHANNEL["Other"]],
    )
