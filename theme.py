"""theme.py - shared visual theme for the two PureGlow KPI dashboards (dark mode).

Two audiences, two looks, one source of truth.

Colour governance:
  * Green / yellow / red are RESERVED for KPI status (the BAN value + its top
    border carry the colour). Never used for branding or channels.
  * Channel colours are blue / purple / teal / grey - distinct from status.
"""

# ---------------------------------------------------------------- brand
BRAND = {
    "name":      "PureGlow",
    "tagline":   "Clean beauty, measured",
    "logo":      "#2E9C3A",   # signature green
    "logo_lt":   "#B7E4B0",
    "logo_dk":   "#155B22",
}

# ---------------------------------------------------------------- status (bright for dark mode)
STATUS = {
    "on_track":  {"color": "#22C55E", "label": "On track",  "glyph": "▲"},
    "watch":     {"color": "#F5C842", "label": "Watch",     "glyph": "●"},
    "off_track": {"color": "#EF4444", "label": "Off track", "glyph": "▼"},
    "no_target": {"color": "#94A3B8", "label": "Tracking",  "glyph": "○"},
}

# ---------------------------------------------------------------- channels (bright for dark mode)
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
    "accent":  "#7AA7FF",   # bright slate-blue
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
    "accent":  "#5DD6E5",   # bright teal
    "grid":    "#1E2731",
    "serif":   "Georgia, 'Times New Roman', serif",
    "sans":    "'Helvetica Neue', Arial, sans-serif",
}


def streamlit_css(p, dense=False):
    """Return a <style> block that themes a Streamlit page for palette `p`."""
    tile_pad = "0.45rem 0.7rem" if dense else "0.55rem 0.85rem"
    return f"""
    <style>
      /* hide streamlit chrome to reclaim vertical space */
      header[data-testid="stHeader"] {{ display: none !important; }}
      #MainMenu, footer {{ visibility: hidden; }}
      [data-testid="stDecoration"], [data-testid="stToolbar"] {{ display: none; }}

      .stApp, .stApp p, .stApp span, .stApp div, .stApp label {{ color: {p['ink']}; }}
      .stApp {{ background: {p['bg']}; }}
      .block-container {{ padding-top: 0.6rem !important; padding-bottom: 0.4rem;
                          padding-left: 1.4rem; padding-right: 1.4rem;
                          max-width: 1680px; }}

      /* brand header (single-row bar, left aligned) */
      .pg-brand {{ display: flex; align-items: center; justify-content: flex-start;
                  gap: 0.6rem; margin: 0; }}
      .pg-brand .pg-mark {{ display: inline-flex; align-items: center; }}
      .pg-brand .pg-name {{ font-family: {p['serif']}; font-weight: 700;
                           font-size: 1.7rem; letter-spacing: -0.3px;
                           color: {p['ink']}; line-height: 1; }}
      .pg-brand .pg-divider {{ width: 1px; height: 1.4rem;
                              background: {p['border']}; margin: 0 0.15rem; }}
      .pg-brand .pg-audience {{ font-family: {p['sans']}; font-weight: 600;
                               font-size: 0.8rem; letter-spacing: 1.6px;
                               text-transform: uppercase; color: {p['accent']};
                               white-space: nowrap; }}

      h1, h2, h3 {{ color: {p['ink']}; font-family: {p['serif']}; margin: 0; }}
      .pg-sub {{ color: {p['muted']}; font-family: {p['sans']};
                font-size: 0.78rem; margin: 0; }}
      .pg-rule {{ height: 2px; background: {p['accent']}; border: 0;
                 margin: 0.25rem 0 0.4rem 0; }}
      .pg-section {{ color: {p['accent']}; font-family: {p['sans']};
                    font-weight: 700; font-size: 0.72rem; letter-spacing: 1.2px;
                    text-transform: uppercase; margin: 0.25rem 0 0.15rem 0; }}

      /* tile - top border colour set per-status inline in tile_html */
      .pg-tile {{ background: {p['panel']}; border: 1px solid {p['border']};
                 border-top: 3px solid {p['border']};
                 border-radius: 6px; padding: {tile_pad}; height: 100%; }}
      .pg-tile .lbl {{ color: {p['ink']}; font-family: {p['sans']};
                      font-size: 0.74rem; font-weight: 600;
                      line-height: 1.15; min-height: 1.6em; }}
      .pg-tile .val {{ font-family: {p['sans']}; font-weight: 700;
                      font-size: 1.55rem; line-height: 1.05;
                      margin: 0.1rem 0 0.15rem 0; }}
      .pg-tile .meta {{ font-family: {p['sans']}; font-size: 0.72rem;
                       color: {p['ink']}; line-height: 1.3; }}
      .pg-tile .owner {{ color: {p['muted']}; font-family: {p['sans']};
                        font-size: 0.66rem; margin-top: 0.1rem; }}

      .pg-foot {{ color: {p['muted']}; font-family: {p['sans']};
                 font-size: 0.66rem; margin-top: 0.3rem; }}

      /* widgets - dark mode */
      [data-testid="stMetricValue"] {{ font-size: 1.4rem; color: {p['ink']}; }}
      .stSelectbox label, .stRadio label, .stDateInput label {{
          color: {p['muted']} !important; font-size: 0.7rem !important;
          font-weight: 600 !important; text-transform: uppercase;
          letter-spacing: 0.5px; margin-bottom: 0.1rem !important; }}
      .stSelectbox, .stRadio, .stDateInput {{ margin-bottom: 0 !important; }}
      div[data-baseweb="select"] > div,
      div[data-baseweb="input"] > div,
      div[data-baseweb="popover"] {{ background: {p['panel']} !important;
          border-color: {p['border']} !important; color: {p['ink']} !important;
          min-height: 32px; }}
      div[data-baseweb="select"] svg,
      div[data-baseweb="input"] svg {{ color: {p['ink']} !important;
          fill: {p['ink']} !important; }}
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
      [data-testid="stExpander"] {{ background: {p['panel']};
          border: 1px solid {p['border']} !important; border-radius: 6px; }}
      [data-testid="stExpander"] summary {{ color: {p['ink']} !important; }}
      [data-testid="stExpander"] svg {{ fill: {p['ink']} !important; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: 4px;
          border-bottom: 1px solid {p['border']}; }}
      .stTabs [data-baseweb="tab"] {{ color: {p['muted']}; font-weight: 600;
                                     padding: 4px 12px; background: transparent; }}
      .stTabs [aria-selected="true"] {{ color: {p['accent']}; }}
      .stTabs [data-baseweb="tab-highlight"] {{ background: {p['accent']} !important; }}
      [data-baseweb="calendar"], [data-baseweb="calendar"] * {{
          background: {p['panel']} !important; color: {p['ink']} !important; }}
      a, a:visited {{ color: {p['accent']}; }}

      /* compact vertical rhythm */
      .element-container {{ margin-bottom: 0.15rem !important; }}
      .stMarkdown {{ margin-bottom: 0 !important; }}
      hr {{ margin: 0.3rem 0 !important; }}
    </style>
    """


def brand_mark_svg(size=34):
    """Inline SVG glow mark for the PureGlow logo (green)."""
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="pgGlow" cx="40%" cy="40%" r="60%">
          <stop offset="0%" stop-color="{BRAND['logo_lt']}"/>
          <stop offset="55%" stop-color="{BRAND['logo']}"/>
          <stop offset="100%" stop-color="{BRAND['logo_dk']}"/>
        </radialGradient>
      </defs>
      <circle cx="11" cy="11" r="9" fill="url(#pgGlow)"/>
      <circle cx="8" cy="8" r="2.4" fill="#FFFFFF" fill-opacity="0.55"/>
    </svg>"""


def brand_header_html(p, audience):
    """Single-row brand bar: PureGlow mark + wordmark + audience tag, left aligned.

    Designed to sit on one Streamlit row next to the period/controls.
    """
    return f"""
    <div class="pg-brand">
      <span class="pg-mark">{brand_mark_svg(30)}</span>
      <span class="pg-name">{BRAND['name']}</span>
      <span class="pg-divider"></span>
      <span class="pg-audience">{audience}</span>
    </div>
    """


def tile_html(k):
    """Return the HTML for one KPI tile. `k` is a result dict from kpi_lib.

    The BAN value and the tile's top border both carry the status colour
    (green / yellow / red). No NEW badge, no OKR mapping, no status wording.
    """
    status_color = STATUS[k["status"]]["color"]
    delta = f" &nbsp;·&nbsp; {k['delta_fmt']}" if k.get("delta_fmt") else ""
    return f"""
    <div class="pg-tile" style="border-top-color:{status_color};">
      <div class="lbl">{k['name']}</div>
      <div class="val" style="color:{status_color};">{k['value_fmt']}</div>
      <div class="meta">target {k['target_fmt']}{delta}</div>
      <div class="owner">Owner: {k['owner']}</div>
    </div>
    """


def plotly_layout(p):
    """Base layout kwargs for Plotly figures themed to palette `p`.

    Note: deliberately does NOT set `margin` - call sites own margin so they
    can size the title area per chart without a keyword collision.
    """
    sans = p["sans"].split(",")[0].strip("'")
    return dict(
        paper_bgcolor=p["panel"],
        plot_bgcolor=p["panel"],
        font=dict(family=sans, color=p["ink"], size=13),
        xaxis=dict(gridcolor=p["grid"], zeroline=False, linecolor=p["border"],
                   tickfont=dict(size=12, color=p["ink"])),
        yaxis=dict(gridcolor=p["grid"], zeroline=False, linecolor=p["border"],
                   tickfont=dict(size=12, color=p["ink"])),
        legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=11, color=p["ink"])),
        colorway=[p["accent"], CHANNEL["Paid search"], CHANNEL["Email / CRM"],
                  CHANNEL["Landing / site"], CHANNEL["Other"]],
    )
