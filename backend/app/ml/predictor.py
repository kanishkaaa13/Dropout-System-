"""
predictor.py
────────────
JEE Dropout Prediction System — Phase 2
Loads trained models and runs single / batch predictions.

Usage
-----
    from backend.app.ml.predictor import JEEDropoutPredictor

    predictor = JEEDropoutPredictor(model_dir="models/")
    predictor.load_models()

    result = predictor.predict_single({
        "attendance_rate": 73.2,
        "mock_test_avg": 167.5,
        ...
    })
    # result = {"ensemble_probability": 0.71, "predicted_dropout": True, ...}
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap

# ─── Feature contract ────────────────────────────────────────────────────────

FEATURE_COLS: list[str] = [
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

# Ensemble weights (must sum to 1.0)
_W_XGB: float = 0.55
_W_RF:  float = 0.35
_W_LR:  float = 0.10

# Decision threshold for binary prediction (recall-optimised)
DEFAULT_THRESHOLD: float = 0.35


# ─── Predictor class ─────────────────────────────────────────────────────────

class JEEDropoutPredictor:
    """
    Loads the trained JEE dropout prediction models and runs inference.

    Parameters
    ----------
    model_dir : str
        Directory containing preprocessor.pkl, xgb_model.pkl,
        rf_model.pkl, lr_model.pkl, and metadata.json.
    threshold : float
        Decision threshold for binary dropout/stay classification.
        Defaults to 0.35 (recall-optimised for early intervention).

    Notes
    -----
    Call ``load_models()`` before any prediction method.
    The constructor is side-effect-free so the class is unit-testable.
    """

    def __init__(self, model_dir: str, threshold: float = DEFAULT_THRESHOLD) -> None:
        self.model_dir  = model_dir
        self.threshold  = threshold

        # Populated by load_models()
        self._preprocessor   = None
        self._xgb_model      = None
        self._rf_model       = None
        self._lr_model       = None
        self._shap_explainer: shap.TreeExplainer | None = None
        self._metadata: dict[str, Any] = {}
        self._loaded = False
        self._feature_cols: list[str] = FEATURE_COLS  # overridden after load
        self._pipeline: str = "synthetic"             # "synthetic" or "real"

    # ── Public API ────────────────────────────────────────────────────────────

    def load_models(self) -> None:
        """
        Load all serialised artefacts from ``model_dir``.

        Supports both old structure (preprocessor.pkl, xgb_model.pkl, etc.)
        and new structure (model.pkl, scaler.pkl, features.json).

        Raises
        ------
        FileNotFoundError
            If any expected .pkl file is missing.
        """
        # Check for new artifact structure (model.pkl, scaler.pkl, features.json)
        new_structure = os.path.exists(os.path.join(self.model_dir, "model.pkl"))
        
        if new_structure:
            # Load new structure
            model_path = os.path.join(self.model_dir, "model.pkl")
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
            features_path = os.path.join(self.model_dir, "features.json")
            metadata_path = os.path.join(self.model_dir, "metadata.json")

            for path in [model_path, scaler_path, features_path]:
                if not os.path.exists(path):
                    raise FileNotFoundError(
                        f"[JEEDropoutPredictor] Missing artefact: {path}"
                    )

            # Load single best model
            self._xgb_model = joblib.load(model_path)
            self._rf_model = self._xgb_model  # Use same model for RF
            self._lr_model = self._xgb_model  # Use same model for LR
            self._preprocessor = joblib.load(scaler_path)

            # Load feature names from features.json
            with open(features_path, encoding="utf-8") as f:
                self._feature_cols = json.load(f)

            # Load metadata if available
            if os.path.exists(metadata_path):
                with open(metadata_path, encoding="utf-8") as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {
                    "version": "1.0.0",
                    "dataset": "jee_training_data",
                    "model_type": type(self._xgb_model).__name__
                }

            self._pipeline = "real"
            self.threshold = self._metadata.get("test_metrics", {}).get("roc_auc", 0.5)
        else:
            # Load old structure (preprocessor.pkl, xgb_model.pkl, rf_model.pkl, lr_model.pkl)
            paths = {
                "preprocessor": os.path.join(self.model_dir, "preprocessor.pkl"),
                "xgb":          os.path.join(self.model_dir, "xgb_model.pkl"),
                "rf":           os.path.join(self.model_dir, "rf_model.pkl"),
                "lr":           os.path.join(self.model_dir, "lr_model.pkl"),
                "metadata":     os.path.join(self.model_dir, "metadata.json"),
            }

            for key, path in paths.items():
                if not os.path.exists(path):
                    raise FileNotFoundError(
                        f"[JEEDropoutPredictor] Missing artefact: {path}"
                    )

            self._preprocessor = joblib.load(paths["preprocessor"])
            self._xgb_model    = joblib.load(paths["xgb"])
            self._rf_model     = joblib.load(paths["rf"])
            self._lr_model     = joblib.load(paths["lr"])

            with open(paths["metadata"], encoding="utf-8") as f:
                self._metadata = json.load(f)

            # Resolve active feature columns from metadata (supports both pipelines)
            if "feature_cols" in self._metadata:
                self._feature_cols = self._metadata["feature_cols"]
            elif "numeric_features" in self._metadata and "categorical_features" in self._metadata:
                self._feature_cols = (
                    self._metadata["numeric_features"]
                    + self._metadata["categorical_features"]
                )
            else:
                self._feature_cols = FEATURE_COLS  # fallback to synthetic

            # Detect pipeline type
            self._pipeline = self._metadata.get("dataset", "synthetic")
            if "JEE_Dropout_After" in self._pipeline or "real" in self._pipeline.lower():
                self._pipeline = "real"
                self.threshold = self._metadata.get("threshold", 0.30)
            else:
                self._pipeline = "synthetic"

        # SHAP TreeExplainer on XGBoost
        self._shap_explainer = shap.TreeExplainer(self._xgb_model)
        self._loaded = True

    # ── Prediction helpers ────────────────────────────────────────────────────

    def _validate_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(
                "Models not loaded. Call load_models() before predicting."
            )

    def _dict_to_df(self, features: dict[str, Any]) -> pd.DataFrame:
        """Convert a feature dict to a 1-row DataFrame in the correct column order."""
        missing = [c for c in self._feature_cols if c not in features]
        if missing:
            raise ValueError(
                f"[JEEDropoutPredictor] Missing features: {missing}"
            )
        return pd.DataFrame([{col: features[col] for col in self._feature_cols}])

    def _preprocess(self, df: pd.DataFrame) -> np.ndarray:
        """Apply the fitted preprocessor pipeline."""
        return self._preprocessor.transform(df[self._feature_cols])

    def _ensemble_proba(self, X_proc: np.ndarray) -> np.ndarray:
        """
        Compute the weighted ensemble probability for each row.

        Returns
        -------
        np.ndarray, shape (n,)
            Dropout probability in [0, 1].
        """
        p_xgb = self._xgb_model.predict_proba(X_proc)[:, 1]
        p_rf  = self._rf_model.predict_proba(X_proc)[:, 1]
        p_lr  = self._lr_model.predict_proba(X_proc)[:, 1]
        return p_xgb * _W_XGB + p_rf * _W_RF + p_lr * _W_LR

    # ── Public prediction methods ─────────────────────────────────────────────

    def predict_single(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Run the ensemble on a single student's features.

        Parameters
        ----------
        features : dict
            Mapping of all 17 JEE feature names to their values.

        Returns
        -------
        dict with keys:
            ensemble_probability : float   – dropout probability in [0, 1]
            predicted_dropout    : bool    – True if probability >= threshold
            threshold            : float
            model_probabilities  : dict    – per-model probabilities
            feature_names        : list[str]
            model_version        : str
            inference_time_ms    : float
        """
        self._validate_loaded()

        t0 = time.perf_counter()
        df      = self._dict_to_df(features)
        X_proc  = self._preprocess(df)

        p_xgb   = float(self._xgb_model.predict_proba(X_proc)[0, 1])
        p_rf    = float(self._rf_model.predict_proba(X_proc)[0, 1])
        p_lr    = float(self._lr_model.predict_proba(X_proc)[0, 1])
        p_ens   = p_xgb * _W_XGB + p_rf * _W_RF + p_lr * _W_LR

        elapsed = (time.perf_counter() - t0) * 1000.0

        return {
            "ensemble_probability": round(p_ens, 6),
            "predicted_dropout":    p_ens >= self.threshold,
            "threshold":            self.threshold,
            "model_probabilities": {
                "xgboost":             round(p_xgb, 6),
                "random_forest":       round(p_rf,  6),
                "logistic_regression": round(p_lr,  6),
            },
            "feature_names": self._feature_cols,
            "pipeline":      self._pipeline,
            "model_version": self._metadata.get("version", "unknown"),
            "inference_time_ms": round(elapsed, 3),
        }

    def predict_batch(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Run the ensemble on a DataFrame of students.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain all 17 FEATURE_COLS columns.
            May include extra columns (e.g., student_id); they are ignored.

        Returns
        -------
        list[dict]
            One result dict per row, with the same keys as ``predict_single``
            plus ``row_index``.
        """
        self._validate_loaded()

        missing = [c for c in self._feature_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"[JEEDropoutPredictor] Batch input missing columns: {missing}"
            )

        t0     = time.perf_counter()
        X_proc = self._preprocess(df)
        p_ens  = self._ensemble_proba(X_proc)

        p_xgb = self._xgb_model.predict_proba(X_proc)[:, 1]
        p_rf  = self._rf_model.predict_proba(X_proc)[:, 1]
        p_lr  = self._lr_model.predict_proba(X_proc)[:, 1]

        elapsed = (time.perf_counter() - t0) * 1000.0

        results = []
        for i in range(len(df)):
            results.append({
                "row_index":             i,
                "ensemble_probability":  round(float(p_ens[i]), 6),
                "predicted_dropout":     bool(p_ens[i] >= self.threshold),
                "threshold":             self.threshold,
                "model_probabilities": {
                    "xgboost":             round(float(p_xgb[i]), 6),
                    "random_forest":       round(float(p_rf[i]),  6),
                    "logistic_regression": round(float(p_lr[i]),  6),
                },
                "model_version":         self._metadata.get("version", "unknown"),
            })

        # Attach total batch timing to first element as a convenience
        if results:
            results[0]["batch_inference_time_ms"] = round(elapsed, 3)

        return results

    # ── SHAP access ───────────────────────────────────────────────────────────

    def get_shap_explainer(self) -> shap.TreeExplainer:
        """Return the initialised SHAP TreeExplainer (for use by SHAPExplainer)."""
        self._validate_loaded()
        return self._shap_explainer

    def get_preprocessor(self):
        """Return the fitted preprocessor pipeline."""
        self._validate_loaded()
        return self._preprocessor

    # ── Metadata ──────────────────────────────────────────────────────────────

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the metadata dict loaded from metadata.json."""
        return self._metadata

    @property
    def feature_cols(self) -> list[str]:
        """Ordered list of feature column names for the active pipeline."""
        return self._feature_cols

    @property
    def pipeline(self) -> str:
        """Active pipeline: 'synthetic' or 'real'."""
        return self._pipeline

    @property
    def is_loaded(self) -> bool:
        """True if load_models() has been called successfully."""
        return self._loaded
