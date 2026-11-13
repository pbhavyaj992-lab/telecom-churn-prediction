# Telecom Customer Churn Prediction

**Dataset:** IBM Telco Customer Churn (public sample data)
**Scale:** 7,043 customers, 21 columns (19 predictive features + customerID + target); 1,869 churned (26.54%).

## Business question
Which customers are about to leave, why, and what is a targeted retention
offer worth? Predict individual churn probability from billing, contract and
service data, explain the drivers, and turn the scores into a costed
retention playbook.

## Licence and commercial use
**Licence: portfolio / learning use ONLY, never sellable.**
The dataset is IBM Sample Data — Kaggle lists its licence as "Data files ©
Original Authors". It is not an open licence, so this project, its outputs
and the data must never be sold or offered commercially. Use it to show the
work, not to sell it.

## Data source and how to reproduce
Source: IBM's public GitHub repository `IBM/telco-customer-churn-on-icp4d`
(file `data/Telco-Customer-Churn.csv`), the same file mirrored on Kaggle as
`blastchar/telco-customer-churn` (IBM Sample Data Sets, 7,043 rows, 21 columns).
Obtained without a login from IBM's public repository. To reproduce: download
that file, place it in `data/raw/` as `Telco-Customer-Churn.csv`, then run:

```
python3 scripts/01_clean_analyse.py
python3 scripts/02_train_models.py
python3 scripts/03_build_workbook.py
```

**Status: REAL DATA PROCESSED.** Every figure below was computed from the real
dataset by the scripts. Nothing is fabricated. See `output/reconciliation.txt`
for the full reconciliation.

## Key figures (from `output/kpis.txt`)
- customers: 7043
- churned: 1869
- stayed: 5174
- churn_rate_pct: 26.54
- blank_totalcharges_rows: 11 (all tenure 0, set to 0.00 — see cleaning note)
- duplicate_rows: 0
- avg_monthly_charges_usd: 64.76
- avg_monthly_charges_churned_usd: 74.44
- avg_monthly_charges_stayed_usd: 61.27
- avg_tenure_months_churned: 18.0
- avg_tenure_months_stayed: 37.6
- avg_total_charges_usd: 2279.73
- features_before_encoding: 19

## Model results — measured, test set n=1,409 (80/20 stratified split)
Class-weighted setup (recall-first: missing a churner costs more than a
wasted offer). Full tables in `output/model_results.csv`,
`output/confusion_matrices.csv`, `output/threshold_analysis.csv`.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Test confusion (TN / FP / FN / TP) |
|---|---:|---:|---:|---:|---:|---|
| Logistic Regression | 73.8% | 50.4% | 78.3% | 61.4% | 0.84 | 747 / 288 / 81 / 293 |
| Random Forest | 78.9% | 63.3% | 48.4% | 54.8% | 0.82 | 930 / 105 / 193 / 181 |
| Gradient Boosting | 80.3% | 66.6% | 51.6% | 58.1% | 0.84 | 938 / 97 / 181 / 193 |
| **XGBoost (chosen)** | **75.4%** | **52.5%** | **77.0%** | **62.4%** | **0.84** | **774 / 261 / 86 / 288** |

XGBoost is chosen on the best F1 (62.4%) and near-best recall (77.0%): it
catches 288 of 374 test-set churners — 95 more than Gradient Boosting (193)
and 107 more than Random Forest (181), and only 5 fewer than Logistic
Regression (293) while keeping a higher F1 (62.4% vs 61.4%). At a 0.40 decision
threshold it flags 629 customers with 81.8% recall at 48.6% precision.

**How this differs from the presentation.** The companion presentation
("Predicting Customer Churn in Indian Telecom", Deakin major project) reports
classroom figures of 80.1% / 82.6% / 83.4% / 84.2% accuracy and 0.84 / 0.85 /
0.86 / 0.86 AUC. Re-running the same four models unweighted on the same split
gives 80.6% / 78.9% / 80.3% / 80.1% accuracy and 0.84 / 0.82 / 0.84 / 0.84 AUC
(`output/model_results_unweighted.csv`) — only Logistic Regression reproduces
closely. The presentation's tenure-band chart (34.1% / 22.9% / 17.9% / 10.6%)
also does not reproduce: measured bands are 47.4% / 28.7% / 20.4% / 9.5%.
This repo reports the measured figures, not the presentation's, and the
qualitative conclusion survives: contract, tenure and charges dominate, and
the weighted XGBoost model is the best balance for a retention campaign.

## What the data actually says
- Contract is king: month-to-month customers churn at 42.7% — about 15x the
  rate of two-year contracts (2.8%). One-year contracts sit at 11.3%.
- The first year decides loyalty: 47.4% of customers in months 0–12 churn,
  falling to 28.7% (13–24), 20.4% (25–48) and 9.5% (49–72).
- Fibre optic churns most (41.9%) against DSL (19.0%) and no internet (7.4%).
  Fibre customers also pay the most ($91.50/month average) — likely a price /
  expectation gap, not the technology itself.
- Manual payers churn ~3x more than auto-pay: electronic check 45.3%,
  mailed check 19.1%, bank transfer 16.7%, credit card 15.2%.
- No online security (41.8%) and no tech support (41.6%) churn far more than
  customers who have them. Senior citizens churn at 41.7% vs 23.6% for others.
- Churned customers pay more ($74.44 vs $61.27/month) and leave sooner
  (18.0 vs 37.6 months average tenure).
- Top drivers (XGBoost gain, scaled to 100): month-to-month contract 100,
  fibre optic 27, no online security 16, no tech support 9. Permutation
  importance agrees on the same drivers, with tenure second (Contract 0.084,
  tenure 0.048) — see `output/feature_importance_permutation.csv`.

## The decision this answers
Score the base monthly and work three segments, not one blast offer:

- **High risk (score 70%+): personal save offer.** Proactive call plus a
  contract upgrade incentive (e.g. 2 months free on a 1-year plan). Human
  contact, not just an email.
- **Medium risk (40–70%): value nudge.** Bundle online security / tech
  support free for 3 months — the exact services whose absence predicts churn.
- **New customers (<12 months): onboarding fix.** Check-in at months 3, 6
  and 9, plus a nudge from electronic check to auto-pay.

ROI, measured inputs: average monthly bill $64.76. Targeting 1,000 high-risk
customers at 20% saved keeps 200 customers: 200 × $64.76 × 12 = **$155,424**
annual revenue protected, against a $25,000 campaign cost (1,000 × $25),
for a **$130,424** net benefit. Change the save rate or the offer cost and the
maths changes with it — that is the point of the exercise, not a promise.

## Reconciliation
```
TELECOM CHURN — RECONCILIATION (computed from the real file, 2026-11-13)
raw rows: 7043
duplicate rows: 0; duplicate customerIDs: 0
blank TotalCharges values: 11 — all tenure 0, set to 0.00
clean rows written: 7043 (no rows dropped)
churned: 1869; stayed: 5174; churn rate: 26.54%
Per-file scope (each output file sums only to its own defined total):
churn_by_contract.csv / churn_by_internet.csv / churn_by_payment.csv /
churn_by_tenure.csv: every customer appears once per file, so each file sums
to 7,043 customers and 1,869 churned.
churn_by_demographics_services.csv: one row per feature value; rows do not sum
to the customer total (each customer appears once per feature).
charges_by_segment.csv: 2 rows (stayed / churned), sums to 7,043.
model_results.csv / confusion_matrices.csv / feature_importance.csv are
written by scripts/02_train_models.py from the same clean file.
```

## What is in this folder
- `data/raw/` — LOCAL-ONLY: the real source file, as downloaded. Not on GitHub — download it with the links above, then run the pipeline to regenerate.
- `data/clean/` — LOCAL-ONLY: cleaned customer table produced by the pipeline (regenerated by the script, not on GitHub).
- `data/data_dictionary.md` — column meanings, grain, caveats.
- `scripts/01_clean_analyse.py` — cleaning + EDA + reconciliation.
- `scripts/02_train_models.py` — the four models, threshold analysis, feature importance (gain + permutation).
- `scripts/03_build_workbook.py` — builds the Excel workbook from the outputs.
- `sql/schema.sql` — PostgreSQL schema for the same model.
- `sql/analysis_queries.sql` — the key analytical queries in SQL.
- `powerbi/model.md` — star schema, DAX measures and page plan (no .pbix in this repo; build it from this document).
- `excel/` — Excel dashboard workbook built from the real aggregates (charts linked to the data sheets; no slicers).
- `output/` — aggregate CSVs, `kpis.txt`, `model_metrics.txt`, `reconciliation.txt`.

## Limitations — honest limits
- One snapshot in time: the data shows who left, not the sequence of events
  before leaving. No usage, complaint or network-quality history.
- One provider, one market: patterns may not transfer to other regions, price
  tiers or prepaid customers.
- Correlation is not cause: fibre customers churn more, but that may reflect
  price or competitor offers, not the technology itself.
- Class imbalance caps recall: even the best model misses about 1 in 4
  churners (86 of 374 in the test set).

## Stack
Python (pandas, scikit-learn, XGBoost), SQL, PostgreSQL, Power BI, DAX, Excel.
Built by Bhavya Patel.
