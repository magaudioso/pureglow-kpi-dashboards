"""generate_logo_assets.py
Generate PureGlow logo assets for the dashboards (one-time setup script).
Approximates the brand logo - an 8-petal teal/green flower + 'PureGlow' wordmark.

Outputs (assets/):
  pureglow_icon.png   ~80x80    transparent  - for Streamlit page_icon
  pureglow_logo.png   ~600x140  transparent  - for the dashboard header

Run once:  python generate_logo_assets.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

# PureGlow brand teals - tuned to the uploaded logo
PETAL_OUTER = "#1F8F7A"
PETAL_INNER = "#3CCAAE"
CENTER      = "#6CDFC6"
WORDMARK    = "#23B392"


def draw_flower(ax, cx=0.0, cy=0.0, r=1.0):
    # outer ring of 8 petals (darker, larger)
    for i in range(8):
        ax.add_patch(Ellipse((cx, cy), width=0.55 * r, height=1.70 * r,
                             angle=i * 45, facecolor=PETAL_OUTER, alpha=0.92,
                             edgecolor="none"))
    # inner ring of 8 petals (lighter, offset 22.5deg)
    for i in range(8):
        ax.add_patch(Ellipse((cx, cy), width=0.36 * r, height=1.20 * r,
                             angle=i * 45 + 22.5, facecolor=PETAL_INNER,
                             alpha=0.95, edgecolor="none"))
    # bright centre
    ax.add_patch(Circle((cx, cy), 0.26 * r, color=CENTER))


# ---------------- icon (used as Streamlit page_icon)
fig, ax = plt.subplots(figsize=(2.2, 2.2), dpi=64)
fig.patch.set_alpha(0)
ax.set_aspect("equal")
ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.3, 1.3); ax.axis("off")
draw_flower(ax)
plt.savefig(os.path.join(ASSETS, "pureglow_icon.png"), dpi=64,
            transparent=True, bbox_inches="tight", pad_inches=0.05)
plt.close(fig)

# ---------------- full logo with wordmark (header banner)
fig, ax = plt.subplots(figsize=(8, 2), dpi=150)
fig.patch.set_alpha(0)
ax.set_aspect("equal")
ax.set_xlim(0, 8); ax.set_ylim(-1.2, 1.2); ax.axis("off")
draw_flower(ax, cx=0.85, cy=0.0, r=1.0)
ax.text(2.05, 0.0, "PureGlow", fontsize=64, color=WORDMARK,
        family="sans-serif", weight="light", va="center", ha="left")
plt.savefig(os.path.join(ASSETS, "pureglow_logo.png"), dpi=150,
            transparent=True, bbox_inches="tight", pad_inches=0.1)
plt.close(fig)

print("Logo assets written to", os.path.relpath(ASSETS, HERE))
