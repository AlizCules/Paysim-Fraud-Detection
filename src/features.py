"""Leakage-aware pre- and post-transaction feature definitions."""

from __future__ import annotations

import numpy as np
import pandas as pd

PRE_TRANSACTION_FEATURES = [
    "step",
    "hour",
    "day",
    "is_night",
    "type",
    "amount",
    "log_amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "amount_over_oldbalance_org",
    "amount_ratio_org",
    "is_TRANSFER",
    "is_CASH_OUT",
    "dest_is_merchant",
    "dest_is_customer",
]

POST_TRANSACTION_FEATURES = PRE_TRANSACTION_FEATURES + [
    "newbalanceOrig",
    "newbalanceDest",
    "org_residual",
    "dest_residual",
    "abs_org_residual",
    "abs_dest_residual",
    "rel_org_residual",
    "rel_dest_residual",
    "org_delta",
    "dest_delta",
    "org_jump_ratio",
    "dest_jump_ratio",
    "org_residual_flag",
    "dest_residual_flag",
    "balance_diff_zero",
    "errorBalanceDest_negative",
]

FEATURE_SETS = {
    "pre_transaction": PRE_TRANSACTION_FEATURES,
    "post_transaction": POST_TRANSACTION_FEATURES,
}


def _base_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    required = {"step", "type", "amount", "nameDest", "oldbalanceOrg", "oldbalanceDest"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    out["hour"] = out["step"].astype(int) % 24
    out["day"] = out["step"].astype(int) // 24
    out["is_night"] = out["hour"].between(0, 6).astype(int)
    out["is_TRANSFER"] = out["type"].eq("TRANSFER").astype(int)
    out["is_CASH_OUT"] = out["type"].eq("CASH_OUT").astype(int)
    out["dest_is_merchant"] = out["nameDest"].astype(str).str.startswith("M").astype(int)
    out["dest_is_customer"] = out["nameDest"].astype(str).str.startswith("C").astype(int)
    out["log_amount"] = np.log1p(out["amount"].clip(lower=0))
    out["amount_over_oldbalance_org"] = (out["amount"] > out["oldbalanceOrg"]).astype(int)
    out["amount_ratio_org"] = out["amount"] / (out["oldbalanceOrg"].abs() + 1.0)
    return out


def add_pre_transaction_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create features available before or at transaction submission time."""

    out = _base_features(frame)
    numeric = out.select_dtypes(include=[np.number]).columns
    out[numeric] = out[numeric].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["type"] = out["type"].fillna("UNKNOWN").astype(str)
    return out


def add_post_transaction_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add accounting consistency features for post-transaction monitoring."""

    required = {"newbalanceOrig", "newbalanceDest"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing post-transaction columns: {missing}")
    out = add_pre_transaction_features(frame)
    out["org_residual"] = out["oldbalanceOrg"] - out["newbalanceOrig"] - out["amount"]
    out["dest_residual"] = out["newbalanceDest"] - out["oldbalanceDest"] - out["amount"]
    out["abs_org_residual"] = out["org_residual"].abs()
    out["abs_dest_residual"] = out["dest_residual"].abs()
    out["rel_org_residual"] = out["abs_org_residual"] / (out["oldbalanceOrg"].abs() + 1.0)
    out["rel_dest_residual"] = out["abs_dest_residual"] / (out["oldbalanceDest"].abs() + 1.0)
    out["org_delta"] = out["newbalanceOrig"] - out["oldbalanceOrg"]
    out["dest_delta"] = out["newbalanceDest"] - out["oldbalanceDest"]
    out["org_jump_ratio"] = out["org_delta"] / (out["amount"].abs() + 1.0)
    out["dest_jump_ratio"] = out["dest_delta"] / (out["amount"].abs() + 1.0)
    out["org_residual_flag"] = (out["abs_org_residual"] > 1e-6).astype(int)
    out["dest_residual_flag"] = (out["abs_dest_residual"] > 1e-6).astype(int)
    out["balance_diff_zero"] = (out["abs_org_residual"] <= 1e-6).astype(int)
    out["errorBalanceDest_negative"] = (out["dest_residual"] < 0).astype(int)
    numeric = out.select_dtypes(include=[np.number]).columns
    out[numeric] = out[numeric].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def make_feature_frame(frame: pd.DataFrame, feature_set: str) -> pd.DataFrame:
    if feature_set not in FEATURE_SETS:
        raise ValueError(f"Unknown feature set: {feature_set}")
    transformed = (
        add_pre_transaction_features(frame)
        if feature_set == "pre_transaction"
        else add_post_transaction_features(frame)
    )
    columns = FEATURE_SETS[feature_set]
    result = transformed.loc[:, columns].copy()
    forbidden = {"isFraud", "isFlaggedFraud", "nameOrig", "nameDest"}
    if forbidden.intersection(result.columns):
        raise AssertionError("Target, system flag, or raw IDs leaked into feature matrix.")
    return result


def prepare_xy(frame: pd.DataFrame, feature_set: str) -> tuple[pd.DataFrame, pd.Series]:
    if "isFraud" not in frame.columns:
        raise ValueError("Input frame must contain isFraud.")
    return make_feature_frame(frame, feature_set), frame["isFraud"].astype(int)
