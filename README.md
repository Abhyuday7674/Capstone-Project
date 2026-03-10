# Capstone Project — Checkout Experiment & Growth Analytics

## Project Overview

This project is an end-to-end business analytics capstone analyzing a checkout A/B experiment
at an e-commerce company. The goal is to determine whether Variant B (new checkout experience)
should be rolled out to all eligible users, and to quantify the business impact.

**Key Questions Answered:**
1. Should we roll out Variant B to everyone?
2. Where are the biggest funnel leaks?
3. Which segments drive the results?
4. What is the expected business impact over the next 30 days?

---

## Folder Structure

```
AbhyudayMishra_ba_2507632_Capstone_CheckoutAnalytics
│
├── README.md
│
├── data
│   ├── fact_sessions.csv
│   ├── fact_orders.csv
│   └── dim_users_enriched.csv
│
├── etl
│   └── etl_pipeline.py
│
├── analysis
│   ├── analysis.ipynb
│   └── full_analysis_report.docx
│
├── dashboard
│   ├── checkout_dashboard.twbx
│   └── dashboard_screenshots
│       ├── dashboard1.png
│       ├── dashboard2.png
│       ├── dashboard3.png
│       └── dashboard4.png
│
└── final_story
    └── final_memo.pdf
```

---

## Setup

```bash
pip install pandas numpy scipy
```

---

## How to Run ETL (End-to-End)

1. Place all raw data files into the `raw/` folder.
2. Run the ETL pipeline:

```bash
cd etl/
python etl_pipeline.py
```

This will produce three curated datasets in `data/`:
- `fact_sessions.csv` — 1 row per session, with funnel flags, time-to-step, and revenue
- `fact_orders.csv` — 1 row per order, enriched with basket summary and margin proxy
- `dim_users_enriched.csv` — 1 row per user, with lifetime metrics and value band

---

## How to Run Analysis

```bash
cd analysis/
python analysis.py
```

Outputs printed to console:
- Overall KPIs
- Funnel conversion by step
- Weekly KPI trends
- Segment breakdowns (device, channel, city_tier, segment)
- A/B test results (lift, p-value, significance)
- HTE-lite (heterogeneous treatment effects by segment)
- 30-day impact estimation (best/base/worst case)

---

## Data Outputs

| File | Rows | Description |
|------|------|-------------|
| fact_sessions.csv | 9,000 | 1 row per session; funnel flags, revenue, time-to-step |
| fact_orders.csv | 707 | 1 row per order; basket, category, margin proxy |
| dim_users_enriched.csv | 2,200 | 1 row per user; lifetime metrics, value band |

---

## Dashboard

The dashboard is built as a React-based interactive HTML file (`dashboard/dashboard.html`).

To open:
- Simply double-click `dashboard.html` in your browser (no server needed).
- Contains 4 views: Executive Summary, Funnel & Drop-offs, Segment Explorer, Experiment Deep Dive.

---

## Key Findings Summary

- **Variant B shows +18.7% conversion lift** (p=0.137 — directionally strong, not yet statistically significant at 95%)
- **Biggest funnel leak**: Product View → Add to Cart (71.7% drop-off)
- **B works best for**: Search channel (+48.6% lift), New Users (+34.5%), Premium Segment (+31.6%)
- **30-day base case impact**: ~16 incremental orders, ~₹1.22L incremental revenue, ~₹50K margin
- **Recommendation**: Conditional rollout to Search + New Users; run powered test (5K+/arm) for full rollout decision
