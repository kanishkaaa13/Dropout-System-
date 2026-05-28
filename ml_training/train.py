"""
train.py
--------
JEE Aspirant Dropout Prediction System -- Phase 1
Production-grade ML training pipeline with 5-fold CV, SMOTE, and SHAP explainability

Models trained
--------------
  1. XGBoost           (primary  -- n_estimators=300, scale_pos_weight)
  2. RandomForest      (secondary -- class_weight='balanced')
  3. LogisticRegression (baseline)

Features
--------
  - 5-fold stratified cross-validation
  - SMOTE for class imbalance handling
  - SHAP explainability (summary + waterfall plots)
  - Model comparison with detailed metrics

Output artefacts (models/)
--------------------------
  preprocessor.pkl  -- fitted sklearn Pipeline (imputer + robust scaler)
  xgb_model.pkl     -- best XGBoost from RandomizedSearchCV
  rf_model.pkl      -- trained RandomForestClassifier
  lr_model.pkl      -- trained LogisticRegression
  metadata.json     -- feature list, AUC, version, training date
  shap_summary.png -- SHAP summary plot
  shap_waterfall.png -- SHAP waterfall plot for sample prediction

Run
---
    python ml_training/train.py
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import json
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from imblearn.over_sampling import SMOTE

import xgboost as xgb

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Constants from .env
# ---------------------------------------------------------------------------

SEED = 42
N_SAMPLES = int(os.getenv("N_SAMPLES", 8000))
THRESHOLD = float(os.getenv("DROPOUT_PROBABILITY_THRESHOLD", 0.35))
MODEL_DIR = Path(os.getenv("MODEL_DIR", "models"))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_CSV = DATA_DIR / "jee_training_data.csv"
VERSION = os.getenv("APP_VERSION", "1.0.0")
CV_FOLDS = int(os.getenv("CV_FOLDS", 5))
USE_SMOTE = os.getenv("USE_SMOTE", "true").lower() == "true"
ENABLE_SHAP = os.getenv("ENABLE_SHAP", "true").lower() == "true"
SAVE_SHAP_PLOTS = os.getenv("SAVE_SHAP_PLOTS", "true").lower() == "true"

FEATURE_COLS = [
    "attendance_rate",
    "mock_test_avg",
    "physics_score",
    "chemistry_score",
    "maths_score",
    "mock_score_trend",
    "assignment_completion_rate",
    "dpp_accuracy",
    "test_attempt_rate",
    "burnout_score",
    "stress_level",
    "sleep_hours_avg",
    "study_hours_per_day",
    "study_consistency_score",
    "parental_pressure_level",
    "peer_comparison_stress",
    "coaching_engagement_score",
]

TARGET_COL = "dropout"

np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Pretty-print helpers  (pure ASCII -- Windows cp1252 safe)
# ---------------------------------------------------------------------------

def _banner(text: str, width: int = 65) -> None:
    print("\n" + "=" * width)
    print("  " + text)
    print("=" * width)


def _section(text: str) -> None:
    print("\n" + "-" * 55)
    print("  " + text)
    print("-" * 55)


# ---------------------------------------------------------------------------
# Data generation
# (mirrors generate_dataset.py -- kept inline so train.py is self-contained)
# ---------------------------------------------------------------------------

def _sigmoid(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))


def _skewed_int(low: int, high: int, n: int, skew_high: bool = False) -> np.ndarray:
    vals    = np.arange(low, high + 1)
    weights = np.linspace(1, 3, len(vals)) if skew_high else np.ones(len(vals))
    return np.random.choice(vals, size=n, p=weights / weights.sum())


def generate_jee_dataset(n: int = N_SAMPLES) -> pd.DataFrame:
    """
    Generate JEE-domain synthetic data with realistic inter-feature correlations.
    Dropout rate is engineered to fall in the 28-32% range.
    """
    burnout                = _skewed_int(1, 10, n)
    stress_level           = _skewed_int(1, 10, n)
    parental_pressure      = _skewed_int(1, 10, n, skew_high=True)
    peer_comparison_stress = _skewed_int(1, 10, n)

    sleep_hours_avg = np.random.normal(5.8, 1.2, n).clip(3, 10)

    attendance_rate = (
        np.random.beta(8, 2, n) * 100
        - (burnout - 5) * 0.8
        + np.random.normal(0, 3, n)
    ).clip(0, 100)

    mock_test_avg = (
        200
        + (attendance_rate - 75) * 0.9
        - (burnout - 5) * 6
        + np.random.normal(0, 22, n)
    ).clip(0, 360)

    physics_score   = (mock_test_avg / 3 + np.random.normal(0, 11, n)).clip(0, 120)
    chemistry_score = (mock_test_avg / 3 + np.random.normal(0, 10, n)).clip(0, 120)
    maths_score     = (mock_test_avg / 3 + np.random.normal(0, 13, n)).clip(0, 120)

    mock_score_trend = (
        -(burnout - 5) * 4 + np.random.normal(0, 15, n)
    ).clip(-100, 100)

    assignment_completion_rate = (
        attendance_rate * 0.45
        + (10 - burnout) * 4.5
        + np.random.normal(0, 8, n)
    ).clip(0, 100)

    dpp_accuracy = (
        assignment_completion_rate * 0.55 + np.random.normal(20, 10, n)
    ).clip(0, 100)

    test_attempt_rate = (
        attendance_rate * 0.65 + np.random.normal(18, 9, n)
    ).clip(0, 100)

    study_hours_per_day = (
        8.5 - burnout * 0.55 + np.random.normal(0, 1.2, n)
    ).clip(0, 16)

    study_consistency_score = (
        100 - burnout * 7 + np.random.normal(0, 14, n)
    ).clip(0, 100)

    coaching_engagement_score = (
        attendance_rate * 0.40
        + (10 - stress_level) * 3.0
        + (10 - burnout) * 2.5
        + np.random.normal(15, 8, n)
    ).clip(0, 100)

    # Raw risk score (higher = more at-risk). Coefficients define DIRECTION and
    # relative importance; absolute magnitude no longer determines the base rate.
    dropout_logit = (
          (100 - attendance_rate)            * 0.032   # absenteeism
        + burnout                             * 0.28    # dominant driver
        + (360 - mock_test_avg)              * 0.0055  # low mock scores
        + (10  - sleep_hours_avg)            * 0.22    # sleep deprivation
        + stress_level                        * 0.16    # perceived stress
        + parental_pressure                   * 0.13    # external pressure
        + (100 - assignment_completion_rate) * 0.018   # disengagement
        + peer_comparison_stress              * 0.11    # social pressure
        + np.where(mock_score_trend < -20, 0.45, 0)   # sharp score decline
        + np.where(burnout >= 9,           0.60, 0)   # extreme burnout spike
        + np.random.normal(0, 0.30, n)                 # irreducible noise
    )

    # Percentile-rank labelling: flag the top 28-32% by logit score as dropout.
    # Guarantees the target rate while logit still correctly ranks risk.
    target_rate = np.random.uniform(0.28, 0.32)
    cutoff      = np.percentile(dropout_logit, (1.0 - target_rate) * 100)
    dropout     = (dropout_logit >= cutoff).astype(int)

    return pd.DataFrame({
        "attendance_rate":            attendance_rate.round(2),
        "mock_test_avg":              mock_test_avg.round(2),
        "physics_score":              physics_score.round(2),
        "chemistry_score":            chemistry_score.round(2),
        "maths_score":                maths_score.round(2),
        "mock_score_trend":           mock_score_trend.round(3),
        "assignment_completion_rate": assignment_completion_rate.round(2),
        "dpp_accuracy":               dpp_accuracy.round(2),
        "test_attempt_rate":          test_attempt_rate.round(2),
        "burnout_score":              burnout.astype(int),
        "stress_level":               stress_level.astype(int),
        "sleep_hours_avg":            sleep_hours_avg.round(2),
        "study_hours_per_day":        study_hours_per_day.round(2),
        "study_consistency_score":    study_consistency_score.round(2),
        "parental_pressure_level":    parental_pressure.astype(int),
        "peer_comparison_stress":     peer_comparison_stress.astype(int),
        "coaching_engagement_score":  coaching_engagement_score.round(2),
        TARGET_COL:                   dropout,
    })


# ---------------------------------------------------------------------------
# Step 1 -- Data
# ---------------------------------------------------------------------------

def load_or_generate_data() -> pd.DataFrame:
    """Load existing CSV if present; otherwise generate and save."""
    if os.path.exists(DATA_CSV):
        print(f"  [DATA] Found existing dataset: {DATA_CSV}")
        df = pd.read_csv(DATA_CSV)
        print(f"         Loaded {len(df):,} rows, {df.shape[1]} columns.")
    else:
        print(f"  [DATA] Generating {N_SAMPLES:,} synthetic JEE student records ...")
        df = generate_jee_dataset(N_SAMPLES)
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(DATA_CSV, index=False)
        print(f"  [DATA] Saved -> {os.path.abspath(DATA_CSV)}")

    actual_rate = df[TARGET_COL].mean() * 100
    print(f"  [DATA] Dropout rate: {actual_rate:.1f}%  (target 28-32%)")
    return df


# ---------------------------------------------------------------------------
# Step 2 -- Pre-processing pipeline
# ---------------------------------------------------------------------------

def build_preprocessor() -> Pipeline:
    """
    sklearn Pipeline:
      1. SimpleImputer (strategy='median') -- handles any future missing values
      2. RobustScaler                       -- robust to outliers; needed for LR
    """
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  RobustScaler()),
    ])


# ---------------------------------------------------------------------------
# Step 3 -- Model training with 5-fold CV and SMOTE
# ---------------------------------------------------------------------------

def apply_smote(X_train: np.ndarray, y_train: np.ndarray) -> tuple:
    """Apply SMOTE for class imbalance handling."""
    if not USE_SMOTE:
        print("  [SMOTE] SMOTE disabled (USE_SMOTE=false)")
        return X_train, y_train
    
    print("  [SMOTE] Applying SMOTE for class imbalance...")
    smote = SMOTE(
        sampling_strategy='auto',
        random_state=SEED,
        k_neighbors=5
    )
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
    
    original_neg, original_pos = np.bincount(y_train)
    resampled_neg, resampled_pos = np.bincount(y_resampled)
    
    print(f"  [SMOTE] Original distribution: stay={original_neg}, dropout={original_pos}")
    print(f"  [SMOTE] Resampled distribution: stay={resampled_neg}, dropout={resampled_pos}")
    
    return X_resampled, y_resampled


def train_xgboost_with_tuning(
    X_train: np.ndarray,
    y_train: np.ndarray,
    scale_pos_weight: float,
) -> xgb.XGBClassifier:
    """
    RandomizedSearchCV over XGBoost (n_iter=20, cv=5, scoring='roc_auc').
    Returns the best estimator re-fitted on the full training set.
    """
    param_dist = {
        "n_estimators":     [100, 200, 300, 400],
        "max_depth":        [4, 5, 6, 7],
        "learning_rate":    [0.01, 0.05, 0.08, 0.10],
        "subsample":        [0.70, 0.80, 0.90],
        "colsample_bytree": [0.70, 0.80, 0.90],
        "gamma":            [0, 0.1, 0.3],
        "reg_alpha":        [0, 0.1, 0.5],
        "reg_lambda":       [1, 1.5, 2],
    }

    base_xgb = xgb.XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        eval_metric="auc",
        use_label_encoder=False,
        random_state=SEED,
        n_jobs=-1,
        verbosity=0,
    )

    # Use StratifiedKFold for cross-validation
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    
    search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=20,
        cv=cv,
        scoring="roc_auc",
        n_jobs=-1,
        random_state=SEED,
        verbose=0,
        refit=True,
    )

    print(f"  [XGB] Running RandomizedSearchCV (n_iter=20, cv={CV_FOLDS}) ...")
    t0 = time.time()
    search.fit(X_train, y_train)
    elapsed = time.time() - t0
    print(f"  [XGB] Best CV AUC: {search.best_score_:.4f}  | elapsed: {elapsed:.1f}s")
    print(f"  [XGB] Best params: {search.best_params_}")
    return search.best_estimator_


def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> RandomForestClassifier:
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=15,
        min_samples_leaf=6,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    return rf


def train_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> LogisticRegression:
    lr = LogisticRegression(
        C=0.5,
        class_weight="balanced",
        solver="lbfgs",
        max_iter=2000,
        random_state=SEED,
    )
    lr.fit(X_train, y_train)
    return lr


# ---------------------------------------------------------------------------
# Step 4 -- Ensemble
# ---------------------------------------------------------------------------

def ensemble_predict_proba(
    xgb_model: xgb.XGBClassifier,
    rf_model:  RandomForestClassifier,
    lr_model:  LogisticRegression,
    X_proc:    np.ndarray,
) -> np.ndarray:
    """
    Weighted soft-voting ensemble:
        XGBoost x0.55 + RandomForest x0.35 + LogisticRegression x0.10
    """
    p_xgb = xgb_model.predict_proba(X_proc)[:, 1]
    p_rf  = rf_model.predict_proba(X_proc)[:, 1]
    p_lr  = lr_model.predict_proba(X_proc)[:, 1]
    return p_xgb * 0.55 + p_rf * 0.35 + p_lr * 0.10


# ---------------------------------------------------------------------------
# Step 5 -- Evaluation with 5-fold CV
# ---------------------------------------------------------------------------

def evaluate_model_with_cv(
    name:      str,
    model,
    X:         np.ndarray,
    y:         np.ndarray,
    threshold: float = THRESHOLD,
) -> dict:
    """Compute metrics with 5-fold stratified cross-validation."""
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    
    cv_auc_scores = []
    cv_f1_scores = []
    cv_precision_scores = []
    cv_recall_scores = []
    
    for train_idx, val_idx in cv.split(X, y):
        X_train_fold, X_val_fold = X[train_idx], X[val_idx]
        y_train_fold, y_val_fold = y[train_idx], y[val_idx]
        
        # Clone and fit model
        from sklearn.base import clone
        model_clone = clone(model)
        model_clone.fit(X_train_fold, y_train_fold)
        
        # Predict
        y_proba = model_clone.predict_proba(X_val_fold)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)
        
        # Calculate metrics
        cv_auc_scores.append(roc_auc_score(y_val_fold, y_proba))
        cv_f1_scores.append(f1_score(y_val_fold, y_pred, zero_division=0))
        cv_precision_scores.append(precision_score(y_val_fold, y_pred, zero_division=0))
        cv_recall_scores.append(recall_score(y_val_fold, y_pred, zero_division=0))
    
    return {
        "name":      name,
        "cv_auc_mean":       round(np.mean(cv_auc_scores), 4),
        "cv_auc_std":        round(np.std(cv_auc_scores), 4),
        "cv_f1_mean":        round(np.mean(cv_f1_scores), 4),
        "cv_f1_std":         round(np.std(cv_f1_scores), 4),
        "cv_precision_mean": round(np.mean(cv_precision_scores), 4),
        "cv_precision_std":  round(np.std(cv_precision_scores), 4),
        "cv_recall_mean":    round(np.mean(cv_recall_scores), 4),
        "cv_recall_std":     round(np.std(cv_recall_scores), 4),
    }


def evaluate_model(
    name:      str,
    y_true:    np.ndarray,
    y_proba:   np.ndarray,
    threshold: float = THRESHOLD,
) -> dict:
    """Compute AUC, F1, Precision, Recall at the given threshold."""
    y_pred = (y_proba >= threshold).astype(int)
    auc    = roc_auc_score(y_true, y_proba)
    f1     = f1_score(y_true, y_pred, zero_division=0)
    prec   = precision_score(y_true, y_pred, zero_division=0)
    rec    = recall_score(y_true, y_pred, zero_division=0)
    cm     = confusion_matrix(y_true, y_pred)

    return {
        "name":      name,
        "auc":       round(auc,  4),
        "f1":        round(f1,   4),
        "precision": round(prec, 4),
        "recall":    round(rec,  4),
        "cm":        cm.tolist(),
        "y_pred":    y_pred,
    }


def print_confusion_matrix(cm: list, model_name: str) -> None:
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    print(f"\n  Confusion Matrix -- {model_name} (threshold={THRESHOLD})")
    print(f"  {'':>16}  Pred: Stay  Pred: Dropout")
    print(f"  {'Actual: Stay':>16}      {tn:>6}        {fp:>6}")
    print(f"  {'Actual: Dropout':>16}      {fn:>6}        {tp:>6}")


# ---------------------------------------------------------------------------
# Step 6 -- SHAP Explainability
# ---------------------------------------------------------------------------

def generate_shap_explanations(
    model: object,
    X_train: np.ndarray,
    X_test: np.ndarray,
    feature_names: list,
) -> None:
    """Generate SHAP summary and waterfall plots."""
    if not ENABLE_SHAP:
        print("  [SHAP] SHAP disabled (ENABLE_SHAP=false)")
        return
    
    print("  [SHAP] Generating SHAP explanations...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create SHAP explainer
        if hasattr(model, 'predict_proba'):
            # For tree-based models, use TreeExplainer for better performance
            if hasattr(model, 'estimators_') or hasattr(model, 'feature_importances_'):
                explainer = shap.TreeExplainer(model)
            else:
                # Fallback to KernelExplainer for other models
                explainer = shap.KernelExplainer(model.predict_proba, X_train[:100])
        else:
            explainer = shap.Explainer(model, X_train)
        
        # Calculate SHAP values for test set
        shap_values = explainer.shap_values(X_test[:100])
        
        # If shap_values is a list (for classification), take the positive class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Generate summary plot
        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, X_test[:100], feature_names=feature_names, show=False)
        summary_path = ARTIFACTS_DIR / "shap_summary.png"
        plt.savefig(summary_path, bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  [SHAP] Summary plot saved -> {summary_path}")
        
        # Generate waterfall plot for a single prediction
        plt.figure(figsize=(12, 8))
        shap.waterfall_plot(shap.Explanation(values=shap_values[0], 
                                            base_values=explainer.expected_value,
                                            data=X_test[0],
                                            feature_names=feature_names), show=False)
        waterfall_path = ARTIFACTS_DIR / "shap_waterfall.png"
        plt.savefig(waterfall_path, bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  [SHAP] Waterfall plot saved -> {waterfall_path}")
        
    except Exception as e:
        print(f"  [SHAP] Error generating SHAP plots: {e}")
        print(f"  [SHAP] Skipping SHAP visualization...")


# Step 7 -- Serialisation
# ---------------------------------------------------------------------------

def save_artefacts(
    preprocessor: Pipeline,
    xgb_model:    xgb.XGBClassifier,
    rf_model:     RandomForestClassifier,
    lr_model:     LogisticRegression,
    ensemble_auc: float,
    train_size:   int,
    test_size:    int,
    cv_results:   dict,
) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(preprocessor, MODEL_DIR / "preprocessor.pkl")
    joblib.dump(xgb_model,    MODEL_DIR / "xgb_model.pkl")
    joblib.dump(rf_model,     MODEL_DIR / "rf_model.pkl")
    joblib.dump(lr_model,     MODEL_DIR / "lr_model.pkl")

    metadata = {
        "version":       VERSION,
        "trained_at":    datetime.now().isoformat(timespec="seconds"),
        "n_features":    len(FEATURE_COLS),
        "feature_names": FEATURE_COLS,
        "threshold":     THRESHOLD,
        "train_size":    train_size,
        "test_size":     test_size,
        "cv_folds":      CV_FOLDS,
        "use_smote":     USE_SMOTE,
        "ensemble_auc":  round(ensemble_auc, 4),
        "ensemble_weights": {
            "xgboost":             0.55,
            "random_forest":       0.35,
            "logistic_regression": 0.10,
        },
        "cv_results":    cv_results,
        "models": {
            "xgboost":             "xgb_model.pkl",
            "random_forest":       "rf_model.pkl",
            "logistic_regression": "lr_model.pkl",
            "preprocessor":        "preprocessor.pkl",
        },
    }

    meta_path = MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    abs_model_dir = MODEL_DIR.absolute()
    print(f"\n  [SAVE] Artefacts -> {abs_model_dir}/")
    for fname in ["preprocessor.pkl", "xgb_model.pkl", "rf_model.pkl",
                  "lr_model.pkl", "metadata.json"]:
        fpath = MODEL_DIR / fname
        size  = fpath.stat().st_size
        print(f"         +-- {fname:<22}  ({size / 1024:.1f} KB)")


# ---------------------------------------------------------------------------
# Step 8 -- Final summary table
# ---------------------------------------------------------------------------

def print_summary_table(results: list, cv_results: dict) -> None:
    _banner("TRAINING COMPLETE -- FINAL RESULTS SUMMARY", width=75)
    
    # Print test set results
    col_w = 28
    header = (
        f"  {'Model':<{col_w}}  {'AUC':>6}  {'F1':>6}  "
        f"{'Precision':>9}  {'Recall':>6}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in results:
        print(
            f"  {r['name']:<{col_w}}  "
            f"{r['auc']:>6.4f}  "
            f"{r['f1']:>6.4f}  "
            f"{r['precision']:>9.4f}  "
            f"{r['recall']:>6.4f}"
        )
    print()
    
    # Print 5-fold CV results
    _section("5-Fold Stratified Cross-Validation Results")
    cv_header = (
        f"  {'Model':<{col_w}}  {'CV AUC':>10}  {'CV F1':>10}  "
        f"{'CV Precision':>14}  {'CV Recall':>10}"
    )
    print(cv_header)
    print("  " + "-" * (len(cv_header) - 2))
    for model_name, cv_metrics in cv_results.items():
        print(
            f"  {model_name:<{col_w}}  "
            f"{cv_metrics['cv_auc_mean']:>6.4f}±{cv_metrics['cv_auc_std']:<4.2f}  "
            f"{cv_metrics['cv_f1_mean']:>6.4f}±{cv_metrics['cv_f1_std']:<4.2f}  "
            f"{cv_metrics['cv_precision_mean']:>8.4f}±{cv_metrics['cv_precision_std']:<4.2f}  "
            f"{cv_metrics['cv_recall_mean']:>6.4f}±{cv_metrics['cv_recall_std']:<4.2f}"
        )
    print()
    
    best = max(results, key=lambda x: x["auc"])
    print(f"  [BEST] Best model by AUC : {best['name']}  (AUC={best['auc']:.4f})")
    print(f"  [INFO] Decision threshold: {THRESHOLD}  (recall-optimised)")
    print(f"  [INFO] CV Folds: {CV_FOLDS}  |  SMOTE: {USE_SMOTE}  |  SHAP: {ENABLE_SHAP}")
    print(f"  [INFO] Artefacts saved   : {MODEL_DIR.absolute()}/")
    if ENABLE_SHAP and SAVE_SHAP_PLOTS:
        print(f"  [INFO] SHAP plots saved : {ARTIFACTS_DIR.absolute()}/")
    print("=" * 75)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    _banner("JEE DROPOUT PREDICTION -- ML TRAINING PIPELINE  v" + VERSION)

    # ---- 1. Data -----------------------------------------------------------
    _section("Step 1 / 8 -- Data Loading / Generation")
    df = load_or_generate_data()

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    # Stratified 60 / 20 / 20 split
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.20, random_state=SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=SEED,
        stratify=y_train_val
    )
    # Result: Train 60% | Val 20% | Test 20%

    print(f"\n  Split (stratified 60/20/20):")
    print(f"    Train : {len(X_train):>5} samples  (dropout={y_train.mean()*100:.1f}%)")
    print(f"    Val   : {len(X_val):>5} samples  (dropout={y_val.mean()*100:.1f}%)")
    print(f"    Test  : {len(X_test):>5} samples  (dropout={y_test.mean()*100:.1f}%)")

    # ---- 2. Preprocessor ---------------------------------------------------
    _section("Step 2 / 8 -- Preprocessing Pipeline")
    print("  Pipeline: SimpleImputer(strategy='median') -> RobustScaler")
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc   = preprocessor.transform(X_val)
    X_test_proc  = preprocessor.transform(X_test)

    neg_count, pos_count = np.bincount(y_train)
    spw = round(neg_count / pos_count, 3)
    print(f"  Class distribution (train):  stay={neg_count}  |  dropout={pos_count}")
    print(f"  scale_pos_weight computed -> {spw}")

    # ---- 3. SMOTE ----------------------------------------------------------
    _section("Step 3 / 8 -- SMOTE for Class Imbalance")
    X_train_proc, y_train = apply_smote(X_train_proc, y_train)

    # ---- 4. XGBoost --------------------------------------------------------
    _section("Step 4 / 8 -- XGBoost (Primary) + Hyperparameter Tuning")
    xgb_model = train_xgboost_with_tuning(X_train_proc, y_train, spw)

    # ---- 5. RandomForest ---------------------------------------------------
    _section("Step 5 / 8 -- RandomForest (Secondary)")
    print("  Training RandomForestClassifier (n_estimators=200, balanced) ...")
    rf_model = train_random_forest(X_train_proc, y_train)
    print("  [OK] RandomForest trained.")

    # ---- 6. Logistic Regression --------------------------------------------
    _section("Step 6 / 8 -- Logistic Regression (Baseline)")
    print("  Training LogisticRegression (C=0.5, balanced, lbfgs) ...")
    lr_model = train_logistic_regression(X_train_proc, y_train)
    print("  [OK] LogisticRegression trained.")

    # ---- 7. Evaluation -----------------------------------------------------
    _section("Step 7 / 8 -- Evaluation on Hold-Out Test Set")
    print(f"  Threshold = {THRESHOLD}  (recall-optimised for early intervention)\n")

    results = []
    cv_results = {}

    for name, model in [
        ("XGBoost",            xgb_model),
        ("RandomForest",       rf_model),
        ("LogisticRegression", lr_model),
    ]:
        proba = model.predict_proba(X_test_proc)[:, 1]
        r     = evaluate_model(name, y_test, proba)
        results.append(r)
        
        # 5-fold CV evaluation
        cv_r = evaluate_model_with_cv(name, model, X_train_proc, y_train)
        cv_results[name] = cv_r
        
        print(
            f"  {name:<22}  AUC={r['auc']:.4f}  F1={r['f1']:.4f}  "
            f"Precision={r['precision']:.4f}  Recall={r['recall']:.4f}"
        )
        print(
            f"  {'':22}  CV AUC={cv_r['cv_auc_mean']:.4f}±{cv_r['cv_auc_std']:.4f}  "
            f"CV F1={cv_r['cv_f1_mean']:.4f}±{cv_r['cv_f1_std']:.4f}"
        )
        print_confusion_matrix(r["cm"], name)
        print()

    # Ensemble
    ens_proba = ensemble_predict_proba(xgb_model, rf_model, lr_model, X_test_proc)
    ens_r     = evaluate_model("Ensemble (0.55+0.35+0.10)", y_test, ens_proba)
    results.append(ens_r)
    print(
        f"  {'Ensemble':<22}  AUC={ens_r['auc']:.4f}  F1={ens_r['f1']:.4f}  "
        f"Precision={ens_r['precision']:.4f}  Recall={ens_r['recall']:.4f}"
    )
    print_confusion_matrix(ens_r["cm"], "Ensemble")

    print("\n  -- Classification Report (Ensemble) --")
    print(classification_report(
        y_test,
        ens_r["y_pred"],
        target_names=["Stay (0)", "Dropout (1)"],
        digits=4,
    ))

    # ---- 8. SHAP Explainability -------------------------------------------
    _section("Step 8 / 8 -- SHAP Explainability")
    generate_shap_explanations(xgb_model, X_train_proc, X_test_proc, FEATURE_COLS)

    # ---- 9. Save artefacts -------------------------------------------------
    _section("Serialising Artefacts")
    save_artefacts(
        preprocessor = preprocessor,
        xgb_model    = xgb_model,
        rf_model     = rf_model,
        lr_model     = lr_model,
        ensemble_auc = ens_r["auc"],
        train_size   = len(X_train),
        test_size    = len(X_test),
        cv_results   = cv_results,
    )

    # ---- Final summary -----------------------------------------------------
    print_summary_table(results, cv_results)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
