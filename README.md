# PureGlow KPI Dashboards — Python prototype

Made for MBAP_481, Case Western Weatherhead School of Management.

Two role-specific KPI dashboards for the PureGlow case study, built in Python
from the OKR → KPI alignment in `PureGlow_KPI_OKR_Alignment.docx`.

- **Leadership dashboard** — CEO + leadership team. Sparse, outcome-level, with a
  **preset reporting-period dropdown** (this month / last month / this quarter /
  full phase).
- **Marketing Execution dashboard** — Maya Chen, Derek Osei, Sofia Reyes. Denser,
  channel-level, with a **fully custom date-range picker + granularity toggle**
  and function tabs (Paid/SEM, Email/CRM, Landing pages).

Both dashboards read the **same OKRs and the same KPI numbers** — they differ
only in which KPIs they show and how the period is chosen.

## How to run

```bash
pip install -r requirements.txt

python 01_generate_sample_data.py     # raw "exports" -> data/raw/  + config/
python 02_build_kpi_tables.py         # ETL -> data/processed/ fact tables
python 05_render_previews.py          # static PNG previews -> previews/

streamlit run 03_dashboard_leadership.py
streamlit run 04_dashboard_marketing.py
```

Scripts 01, 02 and 05 run in order. The two dashboards can then be launched any
time — they just read `data/processed/`.

## File map

| File | Role |
|---|---|
| `01_generate_sample_data.py` | Generates raw exports that mirror real Google Ads / GA4 / HubSpot schemas. **Swap this step for live API/connector feeds in production.** |
| `02_build_kpi_tables.py` | ETL — cleans, joins (GCLID, contact id), derives the integration glue, writes the fact tables. **This is the data-table builder.** |
| `kpi_lib.py` | Shared logic: config/targets, the KPI catalogue, loaders, period presets, KPI computation, status + formatting. Both dashboards call this so the numbers are identical. |
| `theme.py` | Shared visual theme — two audience palettes, status colours, tile HTML. |
| `03_dashboard_leadership.py` | Streamlit — leadership view (preset period dropdown). |
| `04_dashboard_marketing.py` | Streamlit — marketing view (custom date range + granularity + tabs). |
| `05_render_previews.py` | Renders static PNG previews of both dashboards. |
| `data/raw/` | Synthetic raw exports (stand-ins for the real platform feeds). |
| `config/` | `keyword_classification.csv` (marketing-ops lookup) and `kpi_catalog.csv`. |
| `data/processed/` | `fact_daily.csv` + keyword / landing-page / email fact tables. |
| `previews/` | `preview_leadership.png`, `preview_marketing.png`. |

## Data pipeline

```
 Google Ads API  ─┐
 GA4 Data API  ───┼─►  data/raw/*.csv  ──►  02_build_kpi_tables.py  ──►  data/processed/*.csv  ──►  Streamlit dashboards
 HubSpot API   ──┘     (scheduled exports        (clean • join • derive)        (fact tables)            (03 / 04)
                        or a managed connector
                        — Supermetrics, Fivetran, Airbyte)
```

In this prototype `01_generate_sample_data.py` stands in for the platform feeds.
In production the raw files would be refreshed automatically — the transform
logic in `02` and the dashboards do not change. All targets live in one place
(`kpi_lib.CONFIG`) so the team can re-baseline in Month 1 without touching logic.

> Synthetic data for an MBA case prototype — not real PureGlow data.
