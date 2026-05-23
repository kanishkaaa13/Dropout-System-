"""
smoke_test_phase2.py
────────────────────
Quick end-to-end validation of Phase 2 modules.
Run from the project root:

    python smoke_test_phase2.py

Does NOT require a database — uses build_features_from_dict() instead.
"""

import sys
import os
import json
import pprint

# ── Make sure project root is on sys.path ─────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Sample student (high-risk profile) ───────────────────────────────────────
SAMPLE_STUDENT = {
    "attendance_rate":            67.0,
    "mock_test_avg":              148.5,
    "physics_score":              42.0,
    "chemistry_score":            55.0,
    "maths_score":                51.5,
    "mock_score_trend":          -18.2,
    "assignment_completion_rate": 58.0,
    "dpp_accuracy":               49.0,
    "test_attempt_rate":          72.0,
    "burnout_score":               8,
    "stress_level":                7,
    "sleep_hours_avg":             4.8,
    "study_hours_per_day":         9.5,
    "study_consistency_score":    35.0,
    "parental_pressure_level":     9,
    "peer_comparison_stress":      7,
    "coaching_engagement_score":  48.0,
}

SEP = "=" * 60


def main():
    print(SEP)
    print("  PHASE 2 SMOKE TEST")
    print(SEP)

    # ── 1. feature_builder ────────────────────────────────────────────────────
    print("\n[1] feature_builder.py")
    from backend.app.ml.feature_builder import (
        build_features_from_dict,
        compute_mock_score_trend,
        compute_study_consistency,
    )

    scores = [210, 195, 178, 162, 148]
    trend  = compute_mock_score_trend(scores)
    print(f"    compute_mock_score_trend({scores}) = {trend:.2f}  (expected ~-15.5)")

    hours = [10, 2, 11, 1, 10, 0, 9]
    cons  = compute_study_consistency(hours)
    print(f"    compute_study_consistency({hours}) = {cons:.1f}  (expected ~50-60)")

    features_df = build_features_from_dict(SAMPLE_STUDENT)
    assert features_df.shape == (1, 17), f"Expected (1,17), got {features_df.shape}"
    print(f"    build_features_from_dict -> DataFrame shape: {features_df.shape}  OK")

    # ── 2. predictor ──────────────────────────────────────────────────────────
    print("\n[2] predictor.py — JEEDropoutPredictor")
    from backend.app.ml.predictor import JEEDropoutPredictor

    MODEL_DIR = os.path.join(ROOT, "models")
    predictor = JEEDropoutPredictor(model_dir=MODEL_DIR)
    predictor.load_models()
    print(f"    Models loaded. Version: {predictor.metadata.get('version')}")

    pred = predictor.predict_single(SAMPLE_STUDENT)
    print(f"    Ensemble probability : {pred['ensemble_probability']:.4f}")
    print(f"    Predicted dropout    : {pred['predicted_dropout']}")
    print(f"    Inference time       : {pred['inference_time_ms']} ms")
    print(f"    Per-model probs      : {pred['model_probabilities']}")

    # Batch prediction
    import pandas as pd
    batch_df = pd.DataFrame([SAMPLE_STUDENT, SAMPLE_STUDENT])
    batch    = predictor.predict_batch(batch_df)
    assert len(batch) == 2, "Batch should return 2 results"
    print(f"    Batch predict (n=2)  : probs = "
          f"{[r['ensemble_probability'] for r in batch]}")

    # ── 3. risk_scorer ────────────────────────────────────────────────────────
    print("\n[3] risk_scorer.py — compute_risk_score")
    from backend.app.ml.risk_scorer import (
        compute_risk_score,
        compute_risk_score_from_prediction,
    )

    risk = compute_risk_score(
        ml_probability    = pred["ensemble_probability"],
        burnout_score     = SAMPLE_STUDENT["burnout_score"],
        mock_score_trend  = SAMPLE_STUDENT["mock_score_trend"],
        attendance_rate   = SAMPLE_STUDENT["attendance_rate"],
        sleep_hours       = SAMPLE_STUDENT["sleep_hours_avg"],
        parental_pressure = SAMPLE_STUDENT["parental_pressure_level"],
    )
    print(f"    Risk score   : {risk['score']}")
    print(f"    Risk level   : {risk['level']}")
    print(f"    Color (hex)  : {risk['color']}")
    print(f"    Urgency      : {risk['urgency']}")
    print(f"    Components   :")
    for k, v in risk["components"].items():
        print(f"        {k:<30} {v:.2f}")

    risk2 = compute_risk_score_from_prediction(pred, SAMPLE_STUDENT)
    assert risk2["score"] == risk["score"], "Convenience wrapper must match"
    print(f"    compute_risk_score_from_prediction -> score={risk2['score']}  OK")

    # ── 4. explainer ──────────────────────────────────────────────────────────
    print("\n[4] explainer.py — SHAPExplainer")
    from backend.app.ml.explainer import SHAPExplainer

    explainer = SHAPExplainer(
        shap_explainer = predictor.get_shap_explainer(),
        preprocessor   = predictor.get_preprocessor(),
        feature_cols   = predictor.feature_cols,
        top_n          = 10,
    )

    explanation = explainer.explain(features_df)
    print(f"    Base value   : {explanation['base_value']:.4f}")
    print(f"    Top 5 factors:")
    for i, f in enumerate(explanation["top_factors"][:5], 1):
        sign = "+" if f["direction"] == "increases_risk" else "-"
        print(f"        {i}. {f['human_label']:<28}  "
              f"SHAP={sign}{f['magnitude']:.4f}  "
              f"value={f['actual_value']}{f['unit']}")

    text = explainer.generate_summary_text(explanation["top_factors"], student_name="Arjun")
    print(f"\n    Counselor summary:\n    {text}\n")

    print("\n[5] Waterfall plot (base64 PNG)")
    b64 = explainer.generate_waterfall_plot(features_df)
    assert len(b64) > 1000, "Base64 output seems too short"
    print(f"    Generated. Length: {len(b64):,} chars.  OK")

    # Save the plot so we can inspect it
    import base64
    out_path = os.path.join(ROOT, "shap_waterfall_smoke.png")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"    Saved to: {out_path}")

    print("\n" + SEP)
    print("  ALL CHECKS PASSED — Phase 2 modules are working correctly.")
    print(SEP)


if __name__ == "__main__":
    main()
