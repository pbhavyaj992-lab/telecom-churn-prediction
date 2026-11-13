# Power BI model — Telecom Customer Churn Prediction

No .pbix is in this repo (no Power BI Desktop here). Build it from this document:
load `data/clean/telco_churn_clean.csv`, or connect Power BI to the PostgreSQL
schema in `sql/schema.sql`.

## Star schema
- **FactCustomers** (grain: one row per customer) — `data/clean/telco_churn_clean.csv`.
  Keys: customer_id. Measures live here: churn, MonthlyCharges, TotalCharges,
  tenure.
- **DimContract** — Month-to-month / One year / Two year.
- **DimInternet** — DSL / Fiber optic / No.
- **DimPayment** — Electronic check / Mailed check / Bank transfer (automatic) /
  Credit card (automatic).
- **DimTenureBand** — 0-12 / 13-24 / 25-48 / 49-72 months.
- **DimService** — OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport,
  StreamingTV, StreamingMovies (each Yes / No / No internet service).
- Relationships: FactCustomers → each dimension (many-to-one).

## DAX measures (paste into Power BI)
```dax
Customers = COUNTROWS(FactCustomers)
Churned Customers = CALCULATE(COUNTROWS(FactCustomers), FactCustomers[churn] = 1)
Churn Rate % = 100 * DIVIDE([Churned Customers], [Customers])
Avg Monthly Charges = AVERAGE(FactCustomers[MonthlyCharges])
Avg Monthly Charges (Churned) =
    CALCULATE(AVERAGE(FactCustomers[MonthlyCharges]), FactCustomers[churn] = 1)
Avg Monthly Charges (Stayed) =
    CALCULATE(AVERAGE(FactCustomers[MonthlyCharges]), FactCustomers[churn] = 0)
Avg Tenure (Months) = AVERAGE(FactCustomers[tenure])
Avg Tenure (Churned) =
    CALCULATE(AVERAGE(FactCustomers[tenure]), FactCustomers[churn] = 1)
Churn Rate by Contract % =
    DIVIDE(
        CALCULATE(COUNTROWS(FactCustomers), FactCustomers[churn] = 1),
        COUNTROWS(FactCustomers))
Churn Share % = DIVIDE([Churned Customers], CALCULATE([Churned Customers], ALL(FactCustomers)))
```

## Model scores in Power BI
The trained XGBoost model is not inside the .pbix. Score customers in Python
(`scripts/02_train_models.py`), write the probabilities to a `churn_score`
column, and load that column into FactCustomers. Then add:
```dax
High Risk Customers = CALCULATE(COUNTROWS(FactCustomers), FactCustomers[churn_score] >= 0.70)
Medium Risk Customers =
    CALCULATE(COUNTROWS(FactCustomers),
        FactCustomers[churn_score] >= 0.40, FactCustomers[churn_score] < 0.70)
At-Risk Revenue Protected (12m) = [High Risk Customers] * 0.20 * 64.76 * 12
```
The 0.20 is the assumed save rate and $64.76 is the measured average monthly
bill (see README.md — change both if the business gives better numbers).

## Pages
1. **Overview** — customers, churn rate, churned count, avg monthly charges;
   churn rate by contract; churn rate by tenure band.
2. **Drivers** — churn rate by internet service, payment method, online
   security and tech support; fibre + month-to-month spotlight.
3. **Model results** — accuracy, precision, recall, F1, ROC-AUC by model
   (measured: XGBoost 75.4% accuracy, 77.0% recall, 0.84 AUC on the test set);
   confusion matrix; threshold table (0.40 → 81.8% recall).
4. **Retention playbook** — high / medium / new-customer segments with the
   offer for each and the ROI card (1,000 targeted × 20% saved × $64.76 × 12
   = $155,424 protected, $25,000 cost, $130,424 net).
