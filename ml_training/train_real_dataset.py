"""
ml_training/train_real_dataset.py
───────────────────────────────────
Train the JEE Dropout Prediction ensemble on the real
"JEE Dropout After Class 12" dataset.

Dataset: data/JEE_Dropout_After_Class_12.csv
  - 5,000 rows, 14 features, target = dropout (0/1)
  - Mixed numeric + categorical features
  - 20.7% positive (dropout) rate

Output: same models/ directory as the synthetic pipeline
  preprocessor_real.pkl, xgb_real.pkl, rf_real.pkl,
  lr_real.pkl, metadata_real.json

Usage:
    python ml_training/train_real_dataset.py
"""

from __future__ import annotations

import json
import os
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy  as np
import pandas as pd
from sklearn.ensemble         import RandomForestClassifier
from sklearn.linear_model     import LogisticRegression
from sklearn.metrics          import (
    classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection  import RandomizedSearchCV, StratifiedShuffleSplit
from sklearn.pipeline         import Pipeline
from sklearn.preprocessing    import RobustScaler, OrdinalEncoder
from sklearn.impute            import SimpleImputer
from sklearn.compose          import ColumnTransformer

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
DATA_PATH  = ROOT / "data" / "JEE_Dropout_After_Class_12.csv"
MODEL_DIR  = ROOT / "models" / "real"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD  = 0.30   # lower than synthetic: real data has 20.7% positives

# ── Feature definitions ───────────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "jee_main_score",
    "jee_advanced_score",
    "mock_test_score_avg",
    "class_12_percent",
    "attempt_count",
    "daily_study_hours",
]

CATEGORICAL_FEATURES = [
    "school_board",
    "coaching_institute",
    "family_income",
    "parent_education",
    "location_type",
    "peer_pressure_level",
    "mental_health_issues",
    "admission_taken",
]

TARGET = "dropout"

# ── Pretty print helpers ──────────────────────────────────────────────────────

def _banner(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def _step(n: int, total: int, title: str) -> None:
    print(f"\n{'-'*55}")
    print(f"  Step {n} / {total} -- {title}")
    print(f"{'-'*55}")


# -----------------------------------------------------------------------------
# Main training pipeline
# -----------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    TOTAL_STEPS = 7
    _banner("JEE DROPOUT (Post-12th) — REAL DATASET TRAINING  v1.0.0")

    # ── Step 1: Load ──────────────────────────────────────────────────────────
    _step(1, TOTAL_STEPS, "Data Loading")
    df = pd.read_csv(DATA_PATH)
    print(f"  Loaded {len(df):,} rows, {df.shape[1]} columns from:")
    print(f"  {DATA_PATH}")
    print(f"  Dropout rate: {df[TARGET].mean()*100:.1f}%  ({df[TARGET].sum()} positives)")
    print(f"  Nulls per column:\n{df.isnull().sum()[df.isnull().sum()>0].to_string()}")

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df[TARGET].copy()

    # ── Step 2: Split ─────────────────────────────────────────────────────────
    _step(2, TOTAL_STEPS, "Stratified Split (60/20/20)")
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(sss.split(X, y))
    X_train_full, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train_full, y_test = y.iloc[train_idx], y.iloc[test_idx]

    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    tr_idx, val_idx = next(sss2.split(X_train_full, y_train_full))
    X_train, X_val = X_train_full.iloc[tr_idx], X_train_full.iloc[val_idx]
    y_train, y_val = y_train_full.iloc[tr_idx], y_train_full.iloc[val_idx]

    print(f"  Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")
    pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    print(f"  scale_pos_weight → {pos_weight:.3f}")

    # ── Step 3: Preprocessor ─────────────────────────────────────────────────
    _step(3, TOTAL_STEPS, "Preprocessing Pipeline")

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  RobustScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe,      NUMERIC_FEATURES),
        ("cat", categorical_pipe,  CATEGORICAL_FEATURES),
    ])

    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t   = preprocessor.transform(X_val)
    X_test_t  = preprocessor.transform(X_test)
    print(f"  Transformed shape: {X_train_t.shape}")

    # ── Step 4: XGBoost ───────────────────────────────────────────────────────
    _step(4, TOTAL_STEPS, "XGBoost + RandomizedSearchCV")
    try:
        from xgboost import XGBClassifier
        xgb_param_dist = {
            "n_estimators":    [200, 300, 400],
            "max_depth":       [3, 4, 5],
            "learning_rate":   [0.05, 0.08, 0.1],
            "subsample":       [0.7, 0.8, 0.9],
            "colsample_bytree":[0.7, 0.8],
            "gamma":           [0, 0.1, 0.3],
            "reg_alpha":       [0, 0.5, 1.0],
            "reg_lambda":      [1, 2],
        }
        xgb_base = XGBClassifier(
            objective        = "binary:logistic",
            eval_metric      = "auc",
            use_label_encoder= False,
            scale_pos_weight = pos_weight,
            random_state     = 42,
            n_jobs           = -1,
        )
        xgb_cv = RandomizedSearchCV(
            xgb_base, xgb_param_dist,
            n_iter=20, cv=5, scoring="roc_auc",
            n_jobs=-1, random_state=42, verbose=0,
        )
        t0 = time.time()
        xgb_cv.fit(X_train_t, y_train)
        xgb_model = xgb_cv.best_estimator_
        print(f"  Best CV AUC: {xgb_cv.best_score_:.4f}  | elapsed: {time.time()-t0:.1f}s")
        print(f"  Best params: {xgb_cv.best_params_}")
    except ImportError:
        print("  [WARN] xgboost not installed — skipping, using RandomForest only")
        xgb_model = None

    # ── Step 5: RandomForest ──────────────────────────────────────────────────
    _step(5, TOTAL_STEPS, "RandomForest")
    rf_model = RandomForestClassifier(
        n_estimators  = 200,
        max_depth     = None,
        class_weight  = "balanced",
        random_state  = 42,
        n_jobs        = -1,
    )
    rf_model.fit(X_train_t, y_train)
    print("  [OK] RandomForest trained.")

    # ── Step 6: Logistic Regression ───────────────────────────────────────────
    _step(6, TOTAL_STEPS, "Logistic Regression (Baseline)")
    lr_model = LogisticRegression(
        C            = 0.5,
        class_weight = "balanced",
        solver       = "lbfgs",
        max_iter     = 500,
        random_state = 42,
    )
    lr_model.fit(X_train_t, y_train)
    print("  [OK] LogisticRegression trained.")

    # ── Step 7: Evaluation ────────────────────────────────────────────────────
    _step(7, TOTAL_STEPS, f"Evaluation (threshold={THRESHOLD})")

    def _eval(name: str, model, X_t, y_true):
        if model is None:
            return 0.0
        proba = model.predict_proba(X_t)[:, 1]
        pred  = (proba >= THRESHOLD).astype(int)
        auc   = roc_auc_score(y_true, proba)
        f1    = f1_score(y_true, pred)
        prec  = precision_score(y_true, pred, zero_division=0)
        rec   = recall_score(y_true, pred)
        cm    = confusion_matrix(y_true, pred)
        print(f"\n  {name:<22} AUC={auc:.4f}  F1={f1:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")
        print(f"  Confusion Matrix:\n{cm}")
        return auc

    models = {
        "XGBoost":           xgb_model,
        "RandomForest":      rf_model,
        "LogisticRegression":lr_model,
    }
    weights    = {"XGBoost": 0.55, "RandomForest": 0.35, "LogisticRegression": 0.10}
    aucs: dict[str, float] = {}

    for name, mdl in models.items():
        aucs[name] = _eval(name, mdl, X_test_t, y_test)

    # Ensemble
    ensemble_proba = np.zeros(len(y_test))
    total_w = 0.0
    for name, mdl in models.items():
        if mdl is not None:
            ensemble_proba += weights[name] * mdl.predict_proba(X_test_t)[:, 1]
            total_w        += weights[name]
    if total_w > 0:
        ensemble_proba /= total_w
    ensemble_pred = (ensemble_proba >= THRESHOLD).astype(int)
    ens_auc  = roc_auc_score(y_test, ensemble_proba)
    ens_f1   = f1_score(y_test, ensemble_pred)
    ens_prec = precision_score(y_test, ensemble_pred, zero_division=0)
    ens_rec  = recall_score(y_test, ensemble_pred)

    print(f"\n  {'Ensemble':<22} AUC={ens_auc:.4f}  F1={ens_f1:.4f}  "
          f"Prec={ens_prec:.4f}  Rec={ens_rec:.4f}")
    print(f"\n  Classification Report (Ensemble):")
    print(classification_report(y_test, ensemble_pred,
          target_names=["Stay (0)", "Dropout (1)"]))

    # ── Save artefacts ────────────────────────────────────────────────────────
    print(f"\n{'-'*55}")
    print("  Saving artefacts ...")

    def _save(obj, fname: str) -> None:
        path = MODEL_DIR / fname
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        size_kb = path.stat().st_size / 1024
        print(f"    +-- {fname:<35} ({size_kb:.1f} KB)")

    _save(preprocessor,        "preprocessor.pkl")
    _save(xgb_model,           "xgb_model.pkl")
    _save(rf_model,            "rf_model.pkl")
    _save(lr_model,            "lr_model.pkl")

    metadata = {
        "version":            "2.0.0",
        "dataset":            "JEE_Dropout_After_Class_12.csv",
        "n_samples":          int(len(df)),
        "n_train":            int(len(X_train)),
        "dropout_rate":       float(df[TARGET].mean()),
        "threshold":          THRESHOLD,
        "numeric_features":   NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_cols":       NUMERIC_FEATURES + CATEGORICAL_FEATURES,
        "weights":            weights,
        "test_metrics": {
            "xgboost":            {"auc": aucs.get("XGBoost", 0)},
            "random_forest":      {"auc": aucs.get("RandomForest", 0)},
            "logistic_regression":{"auc": aucs.get("LogisticRegression", 0)},
            "ensemble": {
                "auc": ens_auc, "f1": ens_f1,
                "precision": ens_prec, "recall": ens_rec,
            },
        },
    }
    meta_path = MODEL_DIR / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    print(f"    +-- metadata.json")

    _banner("TRAINING COMPLETE")
    print(f"  {'Model':<28} {'AUC':>7}  {'F1':>7}  {'Prec':>7}  {'Rec':>7}")
    print(f"  {'-'*60}")
    for name, auc in aucs.items():
        print(f"  {name:<28} {auc:>7.4f}")
    print(f"  {'Ensemble (weighted avg)':<28} {ens_auc:>7.4f}  {ens_f1:>7.4f}  "
          f"{ens_prec:>7.4f}  {ens_rec:>7.4f}")
    print(f"\n  Models saved to: {MODEL_DIR}")
    print(f"  Threshold used:  {THRESHOLD}  (recall-optimised for early intervention)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
