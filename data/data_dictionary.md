# Data dictionary — Telco Customer Churn (raw file, `data/raw/`)

| File | Rows | Grain | Key columns |
|---|---|---|---|
| Telco-Customer-Churn.csv | 7,043 | customer | customerID, Churn (target: Yes/No), tenure, Contract, MonthlyCharges, TotalCharges |

Clean fact: `data/clean/telco_churn_clean.csv` (7,043 rows, one per customer).
Cleaning (see `scripts/01_clean_analyse.py`): `TotalCharges` converted from
text to numeric; its 11 blank values (all tenure 0, new customers) set to
0.00 instead of dropping the rows; `SeniorCitizen` 0/1 mapped to No/Yes;
`churn` added as 0/1; `tenure_band` added (0-12, 13-24, 25-48, 49-72).

## Columns

| Column | Type | Meaning |
|---|---|---|
| customerID | text | Unique customer identifier |
| gender | Male / Female | Customer gender |
| SeniorCitizen | 0 / 1 | Whether the customer is a senior citizen |
| Partner | Yes / No | Whether the customer has a partner |
| Dependents | Yes / No | Whether the customer has dependents |
| tenure | int, 0–72 | Months the customer has stayed |
| PhoneService | Yes / No | Whether the customer has a phone service |
| MultipleLines | Yes / No / No phone service | Multiple lines |
| InternetService | DSL / Fiber optic / No | Internet service type |
| OnlineSecurity | Yes / No / No internet service | Online security add-on |
| OnlineBackup | Yes / No / No internet service | Online backup add-on |
| DeviceProtection | Yes / No / No internet service | Device protection add-on |
| TechSupport | Yes / No / No internet service | Tech support add-on |
| StreamingTV | Yes / No / No internet service | Streaming TV add-on |
| StreamingMovies | Yes / No / No internet service | Streaming movies add-on |
| Contract | Month-to-month / One year / Two year | Contract type |
| PaperlessBilling | Yes / No | Paperless billing |
| PaymentMethod | Electronic check / Mailed check / Bank transfer (automatic) / Credit card (automatic) | Payment method |
| MonthlyCharges | numeric, USD | Monthly bill |
| TotalCharges | numeric, USD | Total amount charged to date (blank for 11 new customers, set to 0.00) |
| Churn | Yes / No | Whether the customer left in the last month (target) |

## Caveats
- One snapshot in time: the data shows who left, not the sequence of events
  before leaving. No usage, complaint or network-quality history.
- One provider, one market: patterns may not transfer to other regions,
  price tiers or prepaid customers.
- Correlation is not cause: fibre customers churn more, but that may reflect
  price or competitor offers, not the technology itself.
- `TotalCharges` for the 11 tenure-0 customers is 0.00 by construction (see
  cleaning note above), not a measured value.
