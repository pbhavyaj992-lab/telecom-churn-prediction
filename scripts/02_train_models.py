"""Telecom Customer Churn — train + compare models (real data).
Models: Logistic Regression, Random Forest, Gradient Boosting, XGBoost.
Same held-out test set for every model (80/20 stratified split,
random_state=42, test n=1,409). No model is selected on training accuracy.
Run:  python3 scripts/02_train_models.py   (from the project folder)
Reads data/clean/telco_churn_clean.csv (written by 01_clean_analyse.py),
writes output/model_results.csv, output/confusion_matrices.csv,
output/feature_importance.csv, output/model_metrics.txt
"""
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix)
from xgboost import XGBClassifier

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(os.path.join(CLEAN, "telco_churn_clean.csv"))
X = df.drop(columns=["customerID", "Churn", "churn", "tenure_band"])
y = df["churn"]
print(f"rows: {len(df)}, features before encoding: {X.shape[1]}")

cat_cols = X.select_dtypes(include="object").columns.tolist()
num_cols = X.select_dtypes(exclude="object").columns.tolist()
print("categorical:", cat_cols)
print("numeric:", num_cols)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42)
print(f"train: {len(X_train)} (churn {y_train.mean():.1%}), "
      f"test: {len(X_test)} (churn {y_test.mean():.1%})")

# Imbalance handled with class weighting, not oversampling: the churn rate
# (26.5%) is kept intact in both sets.
neg, pos = int((y_train == 0).sum()), int((y_train == 1).sum())
scale_pos_weight = neg / pos
print(f"scale_pos_weight (neg/pos): {scale_pos_weight:.2f}")

pre_tree = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("num", "passthrough", num_cols),
])
pre_lr = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("num", StandardScaler(), num_cols),
])

models = {
    "Logistic Regression": Pipeline([
        ("pre", pre_lr),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000,
                                   random_state=42))]),
    "Random Forest": Pipeline([
        ("pre", pre_tree),
        ("clf", RandomForestClassifier(n_estimators=300,
                                       class_weight="balanced_subsample",
                                       random_state=42, n_jobs=-1))]),
    "Gradient Boosting": Pipeline([
        ("pre", pre_tree),
        ("clf", GradientBoostingClassifier(random_state=42))]),
    "XGBoost": Pipeline([
        ("pre", pre_tree),
        ("clf", XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                              subsample=0.9, colsample_bytree=0.9,
                              scale_pos_weight=scale_pos_weight,
                              eval_metric="logloss", random_state=42,
                              n_jobs=-1))]),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rows, cm_rows = [], []
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    cv_auc = cross_val_score(model, X_train, y_train, cv=cv,
                             scoring="roc_auc").mean()
    rows.append({
        "model": name,
        "accuracy_pct": round(100 * accuracy_score(y_test, pred), 1),
        "precision_pct": round(100 * precision_score(y_test, pred), 1),
        "recall_pct": round(100 * recall_score(y_test, pred), 1),
        "f1_pct": round(100 * f1_score(y_test, pred), 1),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 2),
        "cv_roc_auc_train": round(float(cv_auc), 2),
        "test_n": len(X_test),
        "test_churners": int(y_test.sum()),
        "churners_caught_tp": int(tp),
        "churners_missed_fn": int(fn),
    })
    cm_rows.append({"model": name, "TN": int(tn), "FP": int(fp),
                    "FN": int(fn), "TP": int(tp)})
    print(f"{name}: acc {rows[-1]['accuracy_pct']}% prec {rows[-1]['precision_pct']}% "
          f"rec {rows[-1]['recall_pct']}% f1 {rows[-1]['f1_pct']}% "
          f"AUC {rows[-1]['roc_auc']} | TN {tn} FP {fp} FN {fn} TP {tp}")

results = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
results.to_csv(os.path.join(OUT, "model_results.csv"), index=False)
pd.DataFrame(cm_rows).to_csv(os.path.join(OUT, "confusion_matrices.csv"),
                             index=False)

# ---- unweighted comparison (verification) ----------------------------------
# The presentation's classroom figures were reported without class weights.
# Re-running the same four models unweighted checks whether they reproduce.
# They do not fully: Logistic Regression matches closely (80.6% vs 80.1%
# reported), but Random Forest / Gradient Boosting / XGBoost accuracy in the
# presentation (82.6% / 83.4% / 84.2%) is higher than measured here
# (78.9% / 80.3% / 80.1%). The repo reports the measured figures below, not
# the presentation's. The qualitative conclusion survives: with class
# weighting XGBoost has the best F1 and near-best recall, which is what a
# retention campaign pays for.
unweighted = {
    "Logistic Regression": Pipeline([
        ("pre", pre_lr),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))]),
    "Random Forest": Pipeline([
        ("pre", pre_tree),
        ("clf", RandomForestClassifier(n_estimators=300, random_state=42,
                                       n_jobs=-1))]),
    "Gradient Boosting": Pipeline([
        ("pre", pre_tree),
        ("clf", GradientBoostingClassifier(random_state=42))]),
    "XGBoost": Pipeline([
        ("pre", pre_tree),
        ("clf", XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                              subsample=0.9, colsample_bytree=0.9,
                              eval_metric="logloss", random_state=42,
                              n_jobs=-1))]),
}
urows = []
for name, model in unweighted.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    urows.append({
        "model": name,
        "accuracy_pct": round(100 * accuracy_score(y_test, pred), 1),
        "precision_pct": round(100 * precision_score(y_test, pred), 1),
        "recall_pct": round(100 * recall_score(y_test, pred), 1),
        "f1_pct": round(100 * f1_score(y_test, pred), 1),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 2),
    })
    print(f"UNWEIGHTED {name}: acc {urows[-1]['accuracy_pct']}% prec "
          f"{urows[-1]['precision_pct']}% rec {urows[-1]['recall_pct']}% "
          f"F1 {urows[-1]['f1_pct']}% AUC {urows[-1]['roc_auc']}")
uresults = pd.DataFrame(urows)
uresults.to_csv(os.path.join(OUT, "model_results_unweighted.csv"), index=False)

# Chosen model: XGBoost under the class-weighted (recall-first) setup — best
# F1 (62.4%) and near-best recall (77.0%) at AUC 0.84. Threshold analysis and
# feature importance both use it.
best_name = "XGBoost"
best = models[best_name]
proba = best.predict_proba(X_test)[:, 1]

# Threshold tuning on the test-set probabilities of the best model, reported
# honestly as a threshold analysis (not a re-fit): recall is what a retention
# campaign pays for, so the table shows the recall/precision trade-off.
ths = [0.30, 0.35, 0.40, 0.45, 0.50]
thr_rows = []
for t in ths:
    p = (proba >= t).astype(int)
    thr_rows.append({
        "model": best_name, "threshold": t,
        "predicted_churners": int(p.sum()),
        "recall_pct": round(100 * recall_score(y_test, p), 1),
        "precision_pct": round(100 * precision_score(y_test, p), 1),
        "accuracy_pct": round(100 * accuracy_score(y_test, p), 1),
    })
thr = pd.DataFrame(thr_rows)
thr.to_csv(os.path.join(OUT, "threshold_analysis.csv"), index=False)
print(thr.to_string(index=False))

# Feature importance from the best tree model (XGBoost gain), scaled to 100.
xgb = best.named_steps["clf"]
enc = best.named_steps["pre"].named_transformers_["cat"]
feat_names = list(enc.get_feature_names_out(cat_cols)) + num_cols
imp = xgb.feature_importances_
fi = (pd.DataFrame({"feature": feat_names, "importance": imp})
      .sort_values("importance", ascending=False))
fi["importance_scaled_100"] = (100 * fi["importance"] / fi["importance"].max()).round(0).astype(int)
fi.to_csv(os.path.join(OUT, "feature_importance.csv"), index=False)
print(fi.head(12).to_string(index=False))

# Permutation importance (test set, ROC-AUC) — a second, fairer view. Gain
# importance over-credits the one-hot contract columns; permutation importance
# ranks the numeric drivers (tenure, charges) higher, closer to the
# presentation's chart, while agreeing on the same top drivers.
from sklearn.inspection import permutation_importance
perm = permutation_importance(best, X_test, y_test, n_repeats=5,
                              scoring="roc_auc", random_state=42)
# Permutation importance shuffles the pipeline's INPUT columns (19 original
# features), not the one-hot encoded ones, so use X_test.columns here.
perm_df = (pd.DataFrame({"feature": list(X_test.columns),
                         "importance_mean": perm.importances_mean,
                         "importance_std": perm.importances_std})
           .sort_values("importance_mean", ascending=False))
perm_df.to_csv(os.path.join(OUT, "feature_importance_permutation.csv"),
               index=False)
print("\nPERMUTATION IMPORTANCE (top 10):")
print(perm_df.head(10).to_string(index=False))

with open(os.path.join(OUT, "model_metrics.txt"), "w") as f:
    f.write("TELECOM CHURN — MODEL RESULTS (measured on the held-out test set, "
            "n=1,409, 80/20 stratified split, random_state=42)\n")
    f.write("Class-weighted setup (recall-first):\n")
    f.write(results.to_string(index=False))
    f.write("\n\nCONFUSION MATRICES (test set, class-weighted setup)\n")
    f.write(pd.DataFrame(cm_rows).to_string(index=False))
    f.write("\n\nUNWEIGHTED COMPARISON (same test set, no class weights) — "
            "verification against the presentation's classroom figures:\n")
    f.write(uresults.to_string(index=False))
    f.write("\nPresentation reported: LR 80.1%, RF 82.6%, GB 83.4%, XGB 84.2% "
            "accuracy; AUC 0.84/0.85/0.86/0.86. Measured unweighted: LR 80.6%, "
            "RF 78.9%, GB 80.3%, XGB 80.1%; AUC 0.84/0.82/0.84/0.84. Only "
            "Logistic Regression reproduces closely. The repo reports measured "
            "figures, not the presentation's.\n")
    f.write(f"\nTHRESHOLD ANALYSIS — {best_name} (same test set, class-weighted)\n")
    f.write(thr.to_string(index=False))
    f.write("\n\nTOP 10 FEATURES (XGBoost gain, scaled to 100)\n")
    f.write(fi.head(10).to_string(index=False))
    f.write("\n\nTOP 10 FEATURES (permutation importance, test set, ROC-AUC)\n")
    f.write(perm_df.head(10).to_string(index=False))
    f.write("\n")
print("DONE — outputs in", OUT)
