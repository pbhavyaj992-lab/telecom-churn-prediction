-- Telecom Customer Churn — PostgreSQL schema.
-- Load the clean CSV with \copy (header included) after running
-- scripts/01_clean_analyse.py. One row per customer; churn is 0/1.
CREATE SCHEMA IF NOT EXISTS telecom;

CREATE TABLE telecom.customers (
    customer_id TEXT PRIMARY KEY,
    gender TEXT,
    senior_citizen TEXT,
    partner TEXT,
    dependents TEXT,
    tenure INT,
    phone_service TEXT,
    multiple_lines TEXT,
    internet_service TEXT,
    online_security TEXT,
    online_backup TEXT,
    device_protection TEXT,
    tech_support TEXT,
    streaming_tv TEXT,
    streaming_movies TEXT,
    contract TEXT,
    paperless_billing TEXT,
    payment_method TEXT,
    monthly_charges NUMERIC(10,2),
    total_charges NUMERIC(10,2),
    churn INT,
    tenure_band TEXT
);

-- \copy telecom.customers FROM 'data/clean/telco_churn_clean.csv'
--   WITH (FORMAT csv, HEADER true);
--
-- Column mapping (clean CSV -> table):
--   customerID -> customer_id, SeniorCitizen -> senior_citizen,
--   PhoneService -> phone_service, MultipleLines -> multiple_lines,
--   InternetService -> internet_service, OnlineSecurity -> online_security,
--   OnlineBackup -> online_backup, DeviceProtection -> device_protection,
--   TechSupport -> tech_support, StreamingTV -> streaming_tv,
--   StreamingMovies -> streaming_movies, Contract -> contract,
--   PaperlessBilling -> paperless_billing, PaymentMethod -> payment_method,
--   MonthlyCharges -> monthly_charges, TotalCharges -> total_charges,
--   churn -> churn, tenure_band -> tenure_band
--   (Churn Yes/No is in the raw file only; the clean file carries churn 0/1.)
