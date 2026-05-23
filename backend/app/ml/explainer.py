"""
explainer.py
────────────
JEE Dropout Prediction System — Phase 2
Real SHAP explanations using shap.TreeExplainer on XGBoost.

Usage
-----
    from backend.app.ml.predictor  import JEEDropoutPredictor
    from backend.app.ml.explainer  import SHAPExplainer

    predictor = JEEDropoutPredictor("models/")
    predictor.load_models()

    explainer = SHAPExplainer(
        shap_explainer = predictor.get_shap_explainer(),
        preprocessor   = predictor.get_preprocessor(),
        feature_cols   = predictor.feature_cols,
    )

    import pandas as pd
    features_df = pd.DataFrame([{...17 features...}])

    result  = explainer.explain(features_df)
    plot_b64 = explainer.generate_waterfall_plot(features_df)
    text     = explainer.generate_summary_text(result["top_factors"], student_name="Arjun")
"""

from __future__ import annotations

import base64
import io
import warnings
from typing import Any

import matplotlib
matplotlib.use("Agg")          # non-interactive backend — safe for servers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")


# ─── Human-readable feature labels ───────────────────────────────────────────

FEATURE_LABELS: dict[str, str] = {
    "attendance_rate":             "Attendance Rate",
    "mock_test_avg":               "Average Mock Score",
    "physics_score":               "Physics Score",
    "chemistry_score":             "Chemistry Score",
    "maths_score":                 "Mathematics Score",
    "mock_score_trend":            "Mock Score Trend",
    "assignment_completion_rate":  "Assignment Completion",
    "dpp_accuracy":                "DPP Accuracy",
    "test_attempt_rate":           "Test Attempt Rate",
    "burnout_score":               "Burnout Level",
    "stress_level":                "Stress Level",
    "sleep_hours_avg":             "Average Sleep Hours",
    "study_hours_per_day":         "Daily Study Hours",
    "study_consistency_score":     "Study Consistency",
    "parental_pressure_level":     "Parental Pressure",
    "peer_comparison_stress":      "Peer Comparison Stress",
    "coaching_engagement_score":   "Coaching Engagement",
}

# Units used when building natural-language sentences
_FEATURE_UNITS: dict[str, str] = {
    "attendance_rate":             "%",
    "mock_test_avg":               "/360",
    "physics_score":               "/120",
    "chemistry_score":             "/120",
    "maths_score":                 "/120",
    "mock_score_trend":            " marks/test",
    "assignment_completion_rate":  "%",
    "dpp_accuracy":                "%",
    "test_attempt_rate":           "%",
    "burnout_score":               "/10",
    "stress_level":                "/10",
    "sleep_hours_avg":             " h/night",
    "study_hours_per_day":         " h/day",
    "study_consistency_score":     "/100",
    "parental_pressure_level":     "/10",
    "peer_comparison_stress":      "/10",
    "coaching_engagement_score":   "/100",
}

# Severity adjectives used in counselor summaries
_SEVERITY_THRESHOLDS: dict[str, list[tuple[float, str]]] = {
    # (threshold, adjective when feature value is at/above threshold)
    "burnout_score":         [(9, "critically high"), (7, "very high"), (5, "elevated"), (0, "manageable")],
    "stress_level":          [(9, "critically high"), (7, "very high"), (5, "elevated"), (0, "low")],
    "parental_pressure_level":[(9, "extreme"),        (7, "very high"), (5, "moderate"), (0, "low")],
    "attendance_rate":       [(85, "excellent"), (70, "acceptable"), (60, "concerning"), (0, "critically low")],
    "mock_test_avg":         [(250, "strong"),  (180, "average"),  (120, "low"),      (0, "very low")],
    "sleep_hours_avg":       [(7, "healthy"),   (6, "borderline"), (5, "insufficient"), (0, "severely deprived")],
}


def _severity(feature: str, value: float) -> str:
    """Return a severity adjective for a feature value."""
    thresholds = _SEVERITY_THRESHOLDS.get(feature)
    if thresholds is None:
        return ""
    for threshold, adj in thresholds:
        if value >= threshold:
            return adj
    return ""


# ─── SHAPExplainer class ──────────────────────────────────────────────────────

class SHAPExplainer:
    """
    Generates real SHAP explanations from the XGBoost TreeExplainer.

    Parameters
    ----------
    shap_explainer : shap.TreeExplainer
        Initialised explainer (from JEEDropoutPredictor.get_shap_explainer()).
    preprocessor : sklearn.pipeline.Pipeline
        Fitted preprocessing pipeline (imputer + scaler).
    feature_cols : list[str]
        Ordered list of feature column names matching the training order.
    top_n : int
        Number of top features to include in the impact list.  Defaults to 10.

    Notes
    -----
    Constructor is side-effect-free — SHAP is run lazily per call.
    """

    def __init__(
        self,
        shap_explainer: shap.TreeExplainer,
        preprocessor: Any,
        feature_cols: list[str],
        top_n: int = 10,
    ) -> None:
        self._explainer    = shap_explainer
        self._preprocessor = preprocessor
        self._feature_cols = feature_cols
        self._top_n        = top_n

    # ── Core SHAP computation ────────────────────────────────────────────────

    def _compute_shap(
        self, features_df: pd.DataFrame
    ) -> tuple[np.ndarray, float]:
        """
        Run the TreeExplainer on a (preprocessed) feature DataFrame.

        Returns
        -------
        shap_values : np.ndarray, shape (n_rows, n_features)
        base_value  : float   — expected model output (log-odds space)
        """
        X_proc = self._preprocessor.transform(features_df[self._feature_cols])

        # TreeExplainer returns a shap.Explanation object when called directly
        # or an ndarray when .shap_values() is used.  We use .shap_values() for
        # maximum compatibility across shap versions.
        raw = self._explainer.shap_values(X_proc)

        # For binary classifiers XGBoost may return a single array (log-odds)
        # or a list [class0_shap, class1_shap].  Always use class-1 (dropout).
        if isinstance(raw, list):
            shap_values = raw[1]
        else:
            shap_values = raw   # single output → already log-odds for class 1

        base_value = float(
            self._explainer.expected_value[1]
            if isinstance(self._explainer.expected_value, (list, np.ndarray))
            else self._explainer.expected_value
        )

        return shap_values, base_value

    # ── Public API ────────────────────────────────────────────────────────────

    def explain(self, features_df: pd.DataFrame) -> dict[str, Any]:
        """
        Generate SHAP feature impacts for one or more students.

        Parameters
        ----------
        features_df : pd.DataFrame
            One-row (or multi-row) DataFrame with all feature columns.

        Returns
        -------
        dict with keys:
            base_value   : float   — SHAP base value (expected log-odds)
            top_factors  : list[dict]  — sorted by |SHAP value|, descending
                Each dict contains:
                    feature       : str   — raw feature name
                    human_label   : str   — readable label
                    shap_value    : float — SHAP contribution to log-odds
                    actual_value  : float — student's raw feature value
                    direction     : "increases_risk" | "decreases_risk"
                    magnitude     : float — abs(shap_value)
                    unit          : str   — e.g. "%", "/10"
                    severity      : str   — e.g. "very high", "acceptable"
            all_shap_values : dict[str, float]  — full shap map (all features)
        """
        shap_values, base_value = self._compute_shap(features_df)

        # Use the first row if batch; caller can loop for multi-student
        row_shap   = shap_values[0]
        row_values = features_df[self._feature_cols].iloc[0].to_dict()

        # Build and sort impact list
        impacts = []
        for feat, sv in zip(self._feature_cols, row_shap):
            actual = float(row_values[feat])
            impacts.append({
                "feature":     feat,
                "human_label": FEATURE_LABELS.get(feat, feat),
                "shap_value":  round(float(sv), 6),
                "actual_value": round(actual, 4),
                "direction":   "increases_risk" if sv > 0 else "decreases_risk",
                "magnitude":   round(abs(float(sv)), 6),
                "unit":        _FEATURE_UNITS.get(feat, ""),
                "severity":    _severity(feat, actual),
            })

        impacts.sort(key=lambda x: x["magnitude"], reverse=True)
        top_factors = impacts[: self._top_n]

        all_shap = {feat: round(float(sv), 6)
                    for feat, sv in zip(self._feature_cols, row_shap)}

        return {
            "base_value":      round(base_value, 6),
            "top_factors":     top_factors,
            "all_shap_values": all_shap,
        }

    def generate_waterfall_plot(self, features_df: pd.DataFrame) -> str:
        """
        Render a SHAP waterfall plot and return it as a base64-encoded PNG string.

        Parameters
        ----------
        features_df : pd.DataFrame
            One-row DataFrame with all feature columns.

        Returns
        -------
        str
            Base64-encoded PNG, suitable for embedding as
            ``<img src="data:image/png;base64,{result}" />``.
        """
        X_proc = self._preprocessor.transform(features_df[self._feature_cols])

        # shap.Explanation object required for waterfall plot
        explanation = self._explainer(X_proc)

        # Handle list output (binary classifier)
        if isinstance(explanation, list):
            explanation = explanation[1]

        # Replace processed feature names with human-readable labels
        human_labels = [FEATURE_LABELS.get(f, f) for f in self._feature_cols]
        explanation.feature_names = human_labels

        fig, ax = plt.subplots(figsize=(11, 7))
        plt.sca(ax)

        shap.plots.waterfall(
            explanation[0],
            max_display=min(self._top_n, len(self._feature_cols)),
            show=False,
        )

        plt.title("SHAP Feature Impact — Dropout Risk", fontsize=13, pad=12)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.read()).decode("utf-8")

    def generate_beeswarm_plot(self, features_df: pd.DataFrame) -> str:
        """
        Render a SHAP beeswarm summary plot for a batch of students.

        Parameters
        ----------
        features_df : pd.DataFrame
            Multi-row DataFrame (ideally >= 30 rows for meaningful spread).

        Returns
        -------
        str
            Base64-encoded PNG.
        """
        X_proc = self._preprocessor.transform(features_df[self._feature_cols])
        explanation = self._explainer(X_proc)

        if isinstance(explanation, list):
            explanation = explanation[1]

        human_labels = [FEATURE_LABELS.get(f, f) for f in self._feature_cols]
        explanation.feature_names = human_labels

        fig, _ = plt.subplots(figsize=(11, 7))
        shap.plots.beeswarm(explanation, max_display=15, show=False)
        plt.title("SHAP Summary — All Students", fontsize=13, pad=12)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.read()).decode("utf-8")

    # ── Summary text ─────────────────────────────────────────────────────────

    def generate_summary_text(
        self,
        top_factors: list[dict[str, Any]],
        student_name: str = "The student",
    ) -> str:
        """
        Generate 3 plain-English sentences for a counselor from the top SHAP factors.

        The method selects the three most impactful *risk-increasing* factors
        and phrases each one conversationally, using the actual feature value,
        the appropriate unit, and a severity adjective where applicable.

        Parameters
        ----------
        top_factors : list[dict]
            Output of ``explain()["top_factors"]``.
        student_name : str
            Student's first name or full name.  Defaults to "The student".

        Returns
        -------
        str
            Three sentences joined with a space, e.g.:
            "Arjun's burnout level is critically high at 9/10.
             His average mock score of 148/360 is low and has been
             declining by 8.2 marks per test.
             Attendance at 67% is significantly below the recommended 85%."
        """
        # Filter to risk-increasing factors only
        risk_factors = [f for f in top_factors if f["direction"] == "increases_risk"]

        if not risk_factors:
            return (
                f"{student_name} currently shows no strongly elevated risk indicators. "
                "Continued monitoring is recommended. "
                "Encourage maintenance of current study habits."
            )

        sentences: list[str] = []
        used_features: set[str] = set()

        # We try to produce exactly 3 sentences from the top risk factors
        for factor in risk_factors:
            if len(sentences) >= 3:
                break

            feat   = factor["feature"]
            label  = factor["human_label"]
            val    = factor["actual_value"]
            unit   = factor["unit"]
            sev    = factor["severity"]

            if feat in used_features:
                continue
            used_features.add(feat)

            name_poss = (
                f"{student_name}'s"
                if not student_name.endswith("'s") else student_name
            )

            # ── Feature-specific phrasing ─────────────────────────────────
            if feat == "burnout_score":
                adj = sev or "elevated"
                sentences.append(
                    f"{name_poss} burnout level is {adj} at "
                    f"{int(round(val))}{unit}."
                )

            elif feat == "mock_score_trend":
                direction = "declining" if val < 0 else "improving"
                sentences.append(
                    f"{name_poss} mock test scores are {direction} "
                    f"by {abs(round(val, 1))}{unit}."
                )

            elif feat == "attendance_rate":
                adj = "significantly below" if val < 70 else "below"
                sentences.append(
                    f"Attendance at {round(val, 1)}{unit} is {adj} the "
                    f"recommended 85%."
                )

            elif feat == "sleep_hours_avg":
                adj = sev or "insufficient"
                sentences.append(
                    f"{name_poss} average sleep of {round(val, 1)}{unit} "
                    f"is {adj} for sustained exam preparation."
                )

            elif feat == "mock_test_avg":
                adj = sev or "below average"
                sentences.append(
                    f"{name_poss} average mock score of "
                    f"{round(val, 1)}{unit} is {adj}."
                )

            elif feat == "stress_level":
                adj = sev or "elevated"
                sentences.append(
                    f"{name_poss} stress level is {adj} "
                    f"at {int(round(val))}{unit}."
                )

            elif feat == "parental_pressure_level":
                adj = sev or "high"
                sentences.append(
                    f"Parental pressure reported at {int(round(val))}{unit} "
                    f"is {adj}."
                )

            elif feat == "study_consistency_score":
                sentences.append(
                    f"{name_poss} study consistency score of "
                    f"{round(val, 1)}{unit} indicates irregular study habits."
                )

            elif feat == "assignment_completion_rate":
                sentences.append(
                    f"Only {round(val, 1)}% of assignments are being completed, "
                    f"suggesting declining academic engagement."
                )

            elif feat in ("physics_score", "chemistry_score", "maths_score"):
                subject = label.replace(" Score", "")
                sentences.append(
                    f"{name_poss} {subject} score of {round(val, 1)}{unit} "
                    f"needs targeted attention."
                )

            else:
                # Generic fallback for any other feature
                sentences.append(
                    f"{label} ({round(val, 1)}{unit}) is a significant risk factor."
                )

        # Pad to 3 sentences if we don't have enough risk factors
        while len(sentences) < 3:
            if len(sentences) == 0:
                sentences.append(
                    f"{student_name} shows elevated dropout risk based on "
                    f"the predictive model."
                )
            elif len(sentences) == 1:
                sentences.append(
                    "An immediate counseling session is recommended."
                )
            else:
                sentences.append(
                    "Close monitoring over the next two weeks is advised."
                )

        return " ".join(sentences[:3])
