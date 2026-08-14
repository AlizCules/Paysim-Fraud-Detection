# %% [markdown]
# # FEATURE ENGINEERING - FRAUD DETECTION

# %% [markdown]
# ## Cell 0: Imports + config

# %%
import numpy as np
import pandas as pd

from typing import Dict, List, Tuple, Optional

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

# %% [markdown]
# ## Cell 1: Load + cleaning (drop leakage column)

# %%
path = r"C:\Users\PC\PycharmProjects\PythonProject\ML\PROJECT\CHí BI=ình\data.csv"
df = pd.read_csv(path)

# %%
# target
df["isFraud"] = df["isFraud"].astype(int)

# HARD leakage removal
if "isFlaggedFraud" in df.columns:
    df = df.drop(columns=["isFlaggedFraud"])

df.head()


# %% [markdown]
# ## Cell 2: Base Feature Engineering (NO leakage, fraud-grade)

# %%
def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- time ---
    df["hour"] = df["step"] % 24
    df["day"]  = df["step"] // 24

    # fraud peak heuristics (EDA-driven)
    df["is_night"] = ((df["hour"] >= 0) & (df["hour"] <= 6)).astype(int)
    df["is_fraud_peak_hour"] = df["hour"].isin([3, 4, 5]).astype(int)

    # --- type flags (keep both raw type + flags for trees; LR can drop 'type') ---
    df["is_TRANSFER"] = (df["type"] == "TRANSFER").astype(int)
    df["is_CASH_OUT"] = (df["type"] == "CASH_OUT").astype(int)

    # --- role proxy ---
    df["dest_is_merchant"] = df["nameDest"].astype(str).str.startswith("M").astype(int)
    df["dest_is_customer"] = df["nameDest"].astype(str).str.startswith("C").astype(int)
    df["illegal_merchant_transfer"] = ((df["dest_is_merchant"] == 1) & (df["is_TRANSFER"] == 1)).astype(int)
    df["merchant_cashout_flag"] = ((df["dest_is_merchant"] == 1) & (df["is_CASH_OUT"] == 1)).astype(int)

    # --- accounting residuals ---
    df["org_residual"]  = df["oldbalanceOrg"] - df["newbalanceOrig"] - df["amount"]
    df["dest_residual"] = df["newbalanceDest"] - df["oldbalanceDest"] - df["amount"]

    df["abs_org_residual"]  = df["org_residual"].abs()
    df["abs_dest_residual"] = df["dest_residual"].abs()

    # relative violations (robust)
    df["rel_org_residual"]  = df["abs_org_residual"] / (df["oldbalanceOrg"].abs() + 1.0)
    df["rel_dest_residual"] = df["abs_dest_residual"] / (df["oldbalanceDest"].abs() + 1.0)

    # flags
    eps = 1e-6
    df["org_residual_flag"]  = (df["abs_org_residual"]  > eps).astype(int)
    df["dest_residual_flag"] = (df["abs_dest_residual"] > eps).astype(int)

    # requested EDA flags
    df["balance_diff_zero"] = (df["abs_org_residual"] <= eps).astype(int)
    df["errorBalanceDest_negative"] = (df["dest_residual"] < 0).astype(int)

    # --- amount realism ---
    df["amount_over_oldbalanceOrg"] = (df["amount"] > df["oldbalanceOrg"]).astype(int)
    df["amount_ratio_org"] = df["amount"] / (df["oldbalanceOrg"].abs() + 1.0)

    # --- deltas (interpretability) ---
    df["org_delta"]  = df["newbalanceOrig"] - df["oldbalanceOrg"]
    df["dest_delta"] = df["newbalanceDest"] - df["oldbalanceDest"]

    df["dest_jump_ratio"] = df["dest_delta"] / (df["amount"].abs() + 1.0)
    df["org_jump_ratio"]  = df["org_delta"]  / (df["amount"].abs() + 1.0)

    # --- masking proxies ---
    df["org_old_zero_amount_pos"]  = ((df["oldbalanceOrg"]  == 0) & (df["amount"] > 0)).astype(int)
    df["dest_old_zero_amount_pos"] = ((df["oldbalanceDest"] == 0) & (df["amount"] > 0)).astype(int)

    # --- rounding proxies (optional but cheap) ---
    df["is_amount_round_100"]  = (df["amount"] % 100  == 0).astype(int)
    df["is_amount_round_1000"] = (df["amount"] % 1000 == 0).astype(int)

    # --- stable transforms ---
    df["log_amount"] = np.log1p(df["amount"].clip(lower=0))
    df["log_oldbalanceOrg"]  = np.log1p(df["oldbalanceOrg"].clip(lower=0))
    df["log_oldbalanceDest"] = np.log1p(df["oldbalanceDest"].clip(lower=0))

    # safety: inf handling
    df = df.replace([np.inf, -np.inf], np.nan)

    return df


# %% [markdown]
# ## Cell 3: Split (stratify) + build base-fe

# %%
df_fe = add_base_features(df)

TARGET = "isFraud"
X = df_fe.drop(columns=[TARGET])
y = df_fe[TARGET].values

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train.shape, X_val.shape


# %% [markdown]
# ## Cell 4: Train-only aggregates (NO leakage) + apply
# 
# ### ID raw không đưa vào model
# 
# ### Nhưng dùng ID để sinh feature (counts/burst) là OK nếu fit trên train.

# %%
ID_COLS = ["nameOrig", "nameDest"]

def fit_aggregates(train_X: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    tr = train_X.copy()

    # counts per ID
    orig_cnt = tr.groupby("nameOrig").size().rename("nameOrig_txn_count").to_frame()
    dest_cnt = tr.groupby("nameDest").size().rename("nameDest_txn_count").to_frame()

    # unique counterparties proxy
    dest_unique_orig = tr.groupby("nameDest")["nameOrig"].nunique().rename("nameDest_unique_orig_count").to_frame()

    # burst by (ID, day)
    orig_day_cnt = tr.groupby(["nameOrig", "day"]).size().rename("orig_txn_count_by_day").to_frame()
    dest_day_cnt = tr.groupby(["nameDest", "day"]).size().rename("dest_txn_count_by_day").to_frame()

    return {
        "orig_cnt": orig_cnt,
        "dest_cnt": dest_cnt,
        "dest_unique_orig": dest_unique_orig,
        "orig_day_cnt": orig_day_cnt,
        "dest_day_cnt": dest_day_cnt,
    }

def apply_aggregates(X: pd.DataFrame, aggs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    out = X.copy()

    out = out.join(aggs["orig_cnt"], on="nameOrig")
    out = out.join(aggs["dest_cnt"], on="nameDest")
    out = out.join(aggs["dest_unique_orig"], on="nameDest")
    out = out.join(aggs["orig_day_cnt"], on=["nameOrig", "day"])
    out = out.join(aggs["dest_day_cnt"], on=["nameDest", "day"])

    # fill missing for unseen IDs/days (val/test)
    fill0 = [
        "nameOrig_txn_count","nameDest_txn_count","nameDest_unique_orig_count",
        "orig_txn_count_by_day","dest_txn_count_by_day"
    ]
    for c in fill0:
        out[c] = out[c].fillna(0.0)
        out[f"log_{c}"] = np.log1p(out[c])

    # safety
    out = out.replace([np.inf, -np.inf], np.nan)

    return out

aggs = fit_aggregates(X_train)
X_train2 = apply_aggregates(X_train, aggs)
X_val2   = apply_aggregates(X_val, aggs)

# IMPORTANT: drop raw IDs from modeling matrix
X_train2 = X_train2.drop(columns=ID_COLS, errors="ignore")
X_val2   = X_val2.drop(columns=ID_COLS, errors="ignore")


# %% [markdown]
# ## Cell 5: Optional (Diagnostics only) day_bucket_risk (default OFF)
# 
# ### Nếu muốn dùng để “monitor drift” trong report, bật USE_DAY_RISK=True.
# ### Mặc định: False để tránh target-informed feature.

# %%
USE_DAY_RISK = False

def add_day_bucket_risk_train_only(Xtr: pd.DataFrame, ytr: np.ndarray, Xva: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    tr = Xtr.copy()
    tr["_y"] = ytr

    day_risk = tr.groupby("day")["_y"].mean().rename("day_bucket_risk").to_frame()

    Xtr2 = Xtr.join(day_risk, on="day")
    Xva2 = Xva.join(day_risk, on="day")

    mean_risk = float(day_risk["day_bucket_risk"].mean())
    Xtr2["day_bucket_risk"] = Xtr2["day_bucket_risk"].fillna(mean_risk)
    Xva2["day_bucket_risk"] = Xva2["day_bucket_risk"].fillna(mean_risk)

    return Xtr2, Xva2

if USE_DAY_RISK:
    # Need day column; already exists
    X_train2, X_val2 = add_day_bucket_risk_train_only(X_train2, y_train, X_val2)


# %% [markdown]
# ## Cell 6: Feature groups (đã sửa trùng, bỏ ID, sạch cho ablation)

# %%
FEATURE_GROUPS: Dict[str, List[str]] = {
    "G1_balance_accounting": [
        "org_residual","dest_residual","abs_org_residual","abs_dest_residual",
        "rel_org_residual","rel_dest_residual","org_residual_flag","dest_residual_flag",
        "org_delta","dest_delta","org_jump_ratio","dest_jump_ratio",
        "balance_diff_zero","errorBalanceDest_negative"
    ],
    "G2_txn_semantics": [
        "amount","log_amount","amount_over_oldbalanceOrg","amount_ratio_org",
        "is_TRANSFER","is_CASH_OUT"
        # NOTE: for Logistic, we will DROP raw 'type' to avoid redundancy + OHE costs
    ],
    "G3_identity_role": [
        "dest_is_merchant","dest_is_customer",
        "illegal_merchant_transfer","merchant_cashout_flag"
    ],
    "G4_time_context": ["step","hour","day","is_night","is_fraud_peak_hour"],
    "G5_train_only_freq_burst": [
        "nameOrig_txn_count","nameDest_txn_count","nameDest_unique_orig_count",
        "orig_txn_count_by_day","dest_txn_count_by_day",
        "log_nameOrig_txn_count","log_nameDest_txn_count","log_nameDest_unique_orig_count",
        "log_orig_txn_count_by_day","log_dest_txn_count_by_day",
    ],
    "G6_masking_rounding": [
        "org_old_zero_amount_pos","dest_old_zero_amount_pos",
        "is_amount_round_100","is_amount_round_1000",
        "log_oldbalanceOrg","log_oldbalanceDest"
    ],
}

if USE_DAY_RISK:
    FEATURE_GROUPS["G7_day_risk_diagnostics"] = ["day_bucket_risk"]


# %% [markdown]
# ## Cell 7: Logistic pipeline (scaling + no high-cardinality cat)
# 
# ### LR: không dùng raw type để tránh OHE không cần thiết (và PaySim type có ít category anyway, nhưng giữ flags là đủ).

# %%
def build_logit_pipeline(X: pd.DataFrame) -> Pipeline:
    # Categorical columns: keep only low-cardinality if any (e.g., 'type' if you decide to keep)
    cat_cols = [c for c in X.columns if X[c].dtype == "object"]
    num_cols = [c for c in X.columns if c not in cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), num_cols),
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=True))
            ]), cat_cols),
        ],
        remainder="drop"
    )

    clf = LogisticRegression(
        max_iter=300,
        n_jobs=-1,
        class_weight="balanced",
        solver="lbfgs"
    )

    return Pipeline([("pre", pre), ("clf", clf)])

# For Logistic: drop raw 'type' to avoid redundancy
Xtr_lr = X_train2.drop(columns=["type"], errors="ignore")
Xva_lr = X_val2.drop(columns=["type"], errors="ignore")

# Subsample train set (stratified)
from sklearn.model_selection import StratifiedShuffleSplit

sss = StratifiedShuffleSplit(
    n_splits=1,
    train_size=1_000_000,  # 1 triệu là QUÁ ĐỦ cho LR
    random_state=42
)

idx, _ = next(sss.split(Xtr_lr, y_train))
Xtr_lr_sub = Xtr_lr.iloc[idx]
ytr_sub = y_train[idx]

pipe = build_logit_pipeline(Xtr_lr_sub)
pipe.fit(Xtr_lr_sub, ytr_sub)

pred = pipe.predict_proba(Xva_lr)[:, 1]
roc_auc_score(y_val, pred)



# %% [markdown]
# ## Cell 8: Ablation runner (AUC drop)

# %%
def run_ablation_logit(
    Xtr: pd.DataFrame, ytr: np.ndarray,
    Xva: pd.DataFrame, yva: np.ndarray,
    groups: Dict[str, List[str]],
) -> pd.DataFrame:

    # fit full
    pipe = build_logit_pipeline(Xtr)
    pipe.fit(Xtr, ytr)
    auc_full = roc_auc_score(yva, pipe.predict_proba(Xva)[:, 1])

    rows = []
    for gname, gcols in groups.items():
        drop_cols = [c for c in gcols if c in Xtr.columns]
        Xtr_g = Xtr.drop(columns=drop_cols, errors="ignore")
        Xva_g = Xva.drop(columns=drop_cols, errors="ignore")

        pipe_g = build_logit_pipeline(Xtr_g)
        pipe_g.fit(Xtr_g, ytr)
        auc_g = roc_auc_score(yva, pipe_g.predict_proba(Xva_g)[:, 1])

        rows.append({
            "group": gname,
            "removed_n": len(drop_cols),
            "auc_full": auc_full,
            "auc_wo_group": auc_g,
            "auc_drop": auc_full - auc_g
        })

    return pd.DataFrame(rows).sort_values("auc_drop", ascending=False).reset_index(drop=True)

ablation_df = run_ablation_logit(Xtr_lr, y_train, Xva_lr, y_val, FEATURE_GROUPS)
ablation_df


# %% [markdown]
# ## Cell: Evaluation metrics cho imbalance (ROC-AUC + PR-AUC + CM)

# %%
from sklearn.metrics import (
    precision_recall_curve, auc,
    f1_score, precision_score, recall_score,
    confusion_matrix
)

def evaluate_imbalance(y_true, y_pred_proba, threshold=0.5):
    roc_auc = roc_auc_score(y_true, y_pred_proba)

    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    pr_auc = auc(recall, precision)

    y_pred = (y_pred_proba >= threshold).astype(int)

    metrics = {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "precision@thr": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall@thr": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1@thr": float(f1_score(y_true, y_pred, zero_division=0)),
        "threshold": float(threshold),
        "fraud_rate": float(np.mean(y_true)),
    }

    cm = confusion_matrix(y_true, y_pred)
    return metrics, cm, (precision, recall)

metrics, cm, pr_curve = evaluate_imbalance(y_val, pred, threshold=0.5)
metrics, cm


# %% [markdown]
# ## Cell: Chọn threshold tối ưu (F1) + plot

# %%
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score

def find_optimal_threshold_f1(y_true, y_pred_proba, t_min=0.01, t_max=0.5, n=60):
    thresholds = np.linspace(t_min, t_max, n)
    f1_scores = []

    best_t, best_f1 = 0.5, -1.0
    for t in thresholds:
        y_pred = (y_pred_proba >= t).astype(int)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        f1_scores.append(f1)
        if f1 > best_f1:
            best_f1, best_t = f1, t

    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, f1_scores)
    plt.axvline(best_t, linestyle="--")
    plt.xlabel("Threshold")
    plt.ylabel("F1-score")
    plt.title("F1-score vs Threshold")
    plt.grid(True, alpha=0.3)
    plt.show()

    return float(best_t), float(best_f1)

best_t, best_f1 = find_optimal_threshold_f1(y_val, pred)
best_t, best_f1


# %% [markdown]
# ## Cell: PR curve plot (report-friendly)

# %%
precision, recall = pr_curve

plt.figure(figsize=(8, 6))
plt.plot(recall, precision)
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve")
plt.grid(True, alpha=0.3)
plt.show()


# %% [markdown]
# ## Cell: Feature importance cho Logistic (đúng cách lấy feature names)

# %%
def get_feature_names_from_column_transformer(preprocessor: ColumnTransformer) -> List[str]:
    # sklearn >= 1.0 usually supports this
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        # fallback: rough names
        return [f"f_{i}" for i in range(preprocessor.transform(pd.DataFrame([{}])).shape[1])]

def logit_coefficients_table(pipe: Pipeline, top_k=25) -> pd.DataFrame:
    pre = pipe.named_steps["pre"]
    clf = pipe.named_steps["clf"]

    feat_names = get_feature_names_from_column_transformer(pre)
    coefs = clf.coef_.ravel()

    coef_df = pd.DataFrame({"feature": feat_names, "coef": coefs})
    coef_df["abs_coef"] = coef_df["coef"].abs()
    coef_df = coef_df.sort_values("abs_coef", ascending=False).reset_index(drop=True)

    display(coef_df.head(top_k))
    return coef_df

coef_df = logit_coefficients_table(pipe, top_k=30)


# %% [markdown]
# ## Cell: Save artifacts (đã fix folder + khuyến nghị parquet)

# %%
'''import os, json, pickle
from datetime import datetime

os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Save engineered sets (parquet recommended)
X_train2.to_parquet("data/processed/X_train_engineered.parquet", index=False)
X_val2.to_parquet("data/processed/X_val_engineered.parquet", index=False)
pd.Series(y_train, name="isFraud").to_frame().to_parquet("data/processed/y_train.parquet", index=False)
pd.Series(y_val, name="isFraud").to_frame().to_parquet("data/processed/y_val.parquet", index=False)

# Save model pipeline
with open("models/logistic_pipeline.pkl", "wb") as f:
    pickle.dump(pipe, f)

# Save aggregates (for future inference)
with open("data/processed/aggregates.pkl", "wb") as f:
    pickle.dump(aggs, f)

# Save metadata
final_metrics, final_cm, _ = evaluate_imbalance(y_val, pred, threshold=best_t)

metadata = {
    "created_at": datetime.now().isoformat(),
    "dataset": "PaySim Fraud",
    "train_shape": list(X_train2.shape),
    "val_shape": list(X_val2.shape),
    "features_count": int(X_train2.shape[1]),
    "fraud_rate_train": float(y_train.mean()),
    "fraud_rate_val": float(y_val.mean()),
    "logistic": {
        "roc_auc_val": float(roc_auc_score(y_val, pred)),
        "metrics_at_best_threshold_val": final_metrics,
        "confusion_matrix_at_best_threshold_val": final_cm.tolist(),
    },
    "feature_engineering_settings": {
        "use_day_risk": bool(USE_DAY_RISK),
        "id_columns_removed": ID_COLS,
        "leakage_features_removed": ["isFlaggedFraud"],
    }
}

with open("reports/feature_engineering_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Saved artifacts OK.")
print("Val ROC-AUC:", roc_auc_score(y_val, pred))
print("Val PR-AUC:", evaluate_imbalance(y_val, pred, threshold=0.5)[0]["pr_auc"])
print("Best threshold (val, F1):", best_t)'''



