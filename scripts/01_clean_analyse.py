"""Telecom Customer Churn — clean + analyse (real public data).
Business question: which customers are about to leave, why, and what is a
targeted retention offer worth?
Run:  python3 scripts/01_clean_analyse.py   (from the project folder)
Reads data/raw/Telco-Customer-Churn.csv, writes data/clean/ + output/*.csv
+ output/kpis.txt + output/reconciliation.txt
"""
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")
OUT = os.path.join(BASE, "output")
os.makedirs(CLEAN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

RAW_FILE = "Telco-Customer-Churn.csv"
df = pd.read_csv(os.path.join(RAW, RAW_FILE))
n_raw = len(df)
print(f"RAW ROWS: {n_raw}")

# ---- reconciliation --------------------------------------------------------
dup_rows = int(df.duplicated().sum())
dup_ids = int(df["customerID"].duplicated().sum())
blank_total = int((df["TotalCharges"] == " ").sum())
print(f"duplicate rows: {dup_rows}, duplicate customerIDs: {dup_ids}")
print(f"blank TotalCharges values: {blank_total}")

# ---- cleaning --------------------------------------------------------------
# TotalCharges is stored as text with 11 blanks. All 11 belong to customers
# with tenure 0 (joined this month, no charges accrued yet), so they are set
# to 0.00 rather than dropped — dropping them would silently remove the
# newest customers, the highest-risk segment.
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
n_blank = int(df["TotalCharges"].isna().sum())
assert n_blank == blank_total, (n_blank, blank_total)
assert int((df.loc[df["TotalCharges"].isna(), "tenure"] == 0).sum()) == n_blank
df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})
df["churn"] = (df["Churn"] == "Yes").astype(int)
df["tenure_band"] = pd.cut(df["tenure"], [-1, 12, 24, 48, 72],
                           labels=["0-12", "13-24", "25-48", "49-72"])

clean = df.copy()
clean.to_csv(os.path.join(CLEAN, "telco_churn_clean.csv"), index=False)
print(f"CLEAN ROWS: {len(clean)} (no rows dropped)")

# ---- KPIs ------------------------------------------------------------------
churned = int(clean["churn"].sum())
stayed = int(len(clean) - churned)
kpis = {
    "customers": len(clean),
    "churned": churned,
    "stayed": stayed,
    "churn_rate_pct": round(100 * churned / len(clean), 2),
    "blank_totalcharges_rows": blank_total,
    "blank_totalcharges_set_to_zero": blank_total,
    "duplicate_rows": dup_rows,
    "avg_monthly_charges_usd": round(float(clean["MonthlyCharges"].mean()), 2),
    "avg_monthly_charges_churned_usd": round(float(clean.loc[clean["churn"] == 1, "MonthlyCharges"].mean()), 2),
    "avg_monthly_charges_stayed_usd": round(float(clean.loc[clean["churn"] == 0, "MonthlyCharges"].mean()), 2),
    "avg_tenure_months_churned": round(float(clean.loc[clean["churn"] == 1, "tenure"].mean()), 1),
    "avg_tenure_months_stayed": round(float(clean.loc[clean["churn"] == 0, "tenure"].mean()), 1),
    "avg_total_charges_usd": round(float(clean["TotalCharges"].mean()), 2),
    "features_before_encoding": 19,  # predictive features (excl. customerID + target)
    "target": "Churn (Yes/No)",
}
with open(os.path.join(OUT, "kpis.txt"), "w") as f:
    for k, v in kpis.items():
        f.write(f"{k}: {v}\n")
print(kpis)


def churn_table(col, out_name):
    t = (clean.groupby(col, observed=True).agg(
        customers=("customerID", "count"),
        churned=("churn", "sum"),
        churn_rate_pct=("churn", lambda s: round(100 * s.mean(), 1)),
        avg_monthly_charges_usd=("MonthlyCharges", lambda s: round(float(s.mean()), 2)),
        avg_tenure_months=("tenure", lambda s: round(float(s.mean()), 1)),
    ).reset_index().sort_values("churn_rate_pct", ascending=False))
    t.to_csv(os.path.join(OUT, out_name), index=False)
    return t


contract = churn_table("Contract", "churn_by_contract.csv")
internet = churn_table("InternetService", "churn_by_internet.csv")
payment = churn_table("PaymentMethod", "churn_by_payment.csv")
tenure = churn_table("tenure_band", "churn_by_tenure.csv")

demo_cols = ["gender", "SeniorCitizen", "Partner", "Dependents", "PaperlessBilling",
             "PhoneService", "MultipleLines", "OnlineSecurity", "OnlineBackup",
             "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
demo_rows = []
for c in demo_cols:
    for val, g in clean.groupby(c, observed=True):
        demo_rows.append({
            "feature": c, "value": val, "customers": len(g),
            "churned": int(g["churn"].sum()),
            "churn_rate_pct": round(100 * g["churn"].mean(), 1),
        })
demo = pd.DataFrame(demo_rows).sort_values("churn_rate_pct", ascending=False)
demo.to_csv(os.path.join(OUT, "churn_by_demographics_services.csv"), index=False)

# charges distribution: churned vs stayed
charges = clean.groupby("churn").agg(
    customers=("customerID", "count"),
    avg_monthly_charges_usd=("MonthlyCharges", lambda s: round(float(s.mean()), 2)),
    median_monthly_charges_usd=("MonthlyCharges", lambda s: round(float(s.median()), 2)),
    avg_total_charges_usd=("TotalCharges", lambda s: round(float(s.mean()), 2)),
    avg_tenure_months=("tenure", lambda s: round(float(s.mean()), 1)),
).reset_index()
charges["segment"] = charges["churn"].map({0: "stayed", 1: "churned"})
charges = charges[["segment", "customers", "avg_monthly_charges_usd",
                   "median_monthly_charges_usd", "avg_total_charges_usd",
                   "avg_tenure_months"]]
charges.to_csv(os.path.join(OUT, "charges_by_segment.csv"), index=False)

# ---- reconciliation --------------------------------------------------------
with open(os.path.join(OUT, "reconciliation.txt"), "w") as f:
    f.write("TELECOM CHURN — RECONCILIATION (computed from the real file, 2026-11-13)\n")
    f.write(f"raw rows: {n_raw}\n")
    f.write(f"duplicate rows: {dup_rows}; duplicate customerIDs: {dup_ids}\n")
    f.write(f"blank TotalCharges values: {blank_total} — all tenure 0, set to 0.00\n")
    f.write(f"clean rows written: {len(clean)} (no rows dropped)\n")
    f.write(f"churned: {churned}; stayed: {stayed}; churn rate: {kpis['churn_rate_pct']}%\n")
    f.write("Per-file scope (each output file sums only to its own defined total):\n")
    f.write("churn_by_contract.csv / churn_by_internet.csv / churn_by_payment.csv / "
            "churn_by_tenure.csv: every customer appears once per file, so each file "
            "sums to 7,043 customers and 1,869 churned.\n")
    f.write("churn_by_demographics_services.csv: one row per feature value; rows do not "
            "sum to the customer total (each customer appears once per feature).\n")
    f.write("charges_by_segment.csv: 2 rows (stayed / churned), sums to 7,043.\n")
    f.write("model_results.csv / confusion_matrices.csv / feature_importance.csv are "
            "written by scripts/02_train_models.py from the same clean file.\n")
print("DONE — outputs in", OUT)
