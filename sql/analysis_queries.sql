-- Telecom Customer Churn — key analytical queries (PostgreSQL).
-- Run against telecom.customers after loading data/clean/telco_churn_clean.csv
-- with sql/schema.sql. All figures below were measured by
-- scripts/01_clean_analyse.py; these queries reproduce them in SQL.

-- 1. Headline: overall churn rate (measured: 26.54%, 1,869 of 7,043)
SELECT COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 2) AS churn_rate_pct
FROM telecom.customers;

-- 2. Churn by contract — the headline finding (month-to-month 42.7%,
-- one year 11.3%, two year 2.8%)
SELECT contract, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct,
       ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges_usd,
       ROUND(AVG(tenure), 1) AS avg_tenure_months
FROM telecom.customers
GROUP BY 1 ORDER BY churn_rate_pct DESC;

-- 3. Churn by internet service (fibre optic 41.9%, DSL 19.0%, none 7.4%)
SELECT internet_service, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
GROUP BY 1 ORDER BY churn_rate_pct DESC;

-- 4. Churn by payment method (electronic check 45.3%, mailed check 19.1%,
-- bank transfer 16.7%, credit card 15.2%)
SELECT payment_method, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
GROUP BY 1 ORDER BY churn_rate_pct DESC;

-- 5. Churn by tenure band — the first year decides loyalty
-- (0-12 months 47.4%, 13-24 28.7%, 25-48 20.4%, 49-72 9.5%)
SELECT tenure_band, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
GROUP BY 1 ORDER BY tenure_band;

-- 6. Charges: churned customers pay more and leave sooner
-- (churned $74.44/month, 18.0 months; stayed $61.27/month, 37.6 months)
SELECT CASE WHEN churn = 1 THEN 'churned' ELSE 'stayed' END AS segment,
       COUNT(*) AS customers,
       ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges_usd,
       ROUND(AVG(total_charges), 2) AS avg_total_charges_usd,
       ROUND(AVG(tenure), 1) AS avg_tenure_months
FROM telecom.customers
GROUP BY 1;

-- 7. Support services: no online security (41.8%) and no tech support (41.6%)
-- churn far more than customers who have them
SELECT online_security, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
GROUP BY 1 ORDER BY churn_rate_pct DESC;

SELECT tech_support, COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
GROUP BY 1 ORDER BY churn_rate_pct DESC;

-- 8. The highest-risk segment: month-to-month + fibre optic + electronic check
SELECT COUNT(*) AS customers, SUM(churn) AS churned,
       ROUND(100.0 * AVG(churn), 1) AS churn_rate_pct
FROM telecom.customers
WHERE contract = 'Month-to-month'
  AND internet_service = 'Fiber optic'
  AND payment_method = 'Electronic check';

-- 9. Reconciliation: every query above sums to the same base
SELECT COUNT(*) AS customers, SUM(churn) AS churned FROM telecom.customers;
