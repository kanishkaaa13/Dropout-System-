"""
generate_dataset.py
-------------------
JEE Aspirant Dropout Prediction System -- Phase 1
Generates 8,000 rows of JEE-domain synthetic training data and saves to
data/jee_training_data.csv

Run:
    python ml_training/generate_dataset.py
"""

import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42
N    = 8_000
np.random.seed(SEED)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "jee_training_data.csv"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return np.where(
        x >= 0,
        1 / (1 + np.exp(-x)),
        np.exp(x) / (1 + np.exp(x)),
    )


def _skewed_int(low: int, high: int, n: int, skew_high: bool = False) -> np.ndarray:
    """
    Draws integers in [low, high].
    skew_high=True -> more mass near high (e.g., parental pressure for JEE).
    """
    vals    = np.arange(low, high + 1)
    weights = np.linspace(1, 3, len(vals)) if skew_high else np.ones(len(vals))
    return np.random.choice(vals, size=n, p=weights / weights.sum())


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def generate_jee_dataset(n: int = N) -> pd.DataFrame:
    """
    Return a DataFrame with 17 JEE-specific features + dropout label.

    Feature design principles
    -------------------------
    attendance_rate   : beta(8, 2) -> most students attend > 70%
    burnout_score     : integer 1-10, roughly uniform (JEE pressure)
    sleep_hours_avg   : normal(5.8, 1.2).clip(3, 10) -- sleep-deprived cohort
    mock_test_avg     : correlated with attendance; inversely with burnout
    subject scores    : ~mock/3 + individual noise
    mock_score_trend  : simulated slope; declining students are higher risk
    dropout_logit     : domain-informed formula; target rate ~28-32%
    """

    # -- Psychological / behavioural root causes ----------------------------
    burnout                = _skewed_int(1, 10, n)
    stress_level           = _skewed_int(1, 10, n)
    parental_pressure      = _skewed_int(1, 10, n, skew_high=True)
    peer_comparison_stress = _skewed_int(1, 10, n)

    # Sleep: JEE aspirants average ~5.8 h; std 1.2; hard clip [3, 10]
    sleep_hours_avg = np.random.normal(5.8, 1.2, n).clip(3, 10)

    # -- Attendance ----------------------------------------------------------
    # beta(8,2) -> mean ~80%; high burnout drags attendance down slightly
    attendance_rate = (
        np.random.beta(8, 2, n) * 100
        - (burnout - 5) * 0.8
        + np.random.normal(0, 3, n)
    ).clip(0, 100)

    # -- Mock test average (0-360) ------------------------------------------
    mock_test_avg = (
        200
        + (attendance_rate - 75) * 0.9
        - (burnout - 5) * 6
        + np.random.normal(0, 22, n)
    ).clip(0, 360)

    # -- Subject scores (each 0-120) ----------------------------------------
    physics_score   = (mock_test_avg / 3 + np.random.normal(0, 11, n)).clip(0, 120)
    chemistry_score = (mock_test_avg / 3 + np.random.normal(0, 10, n)).clip(0, 120)
    maths_score     = (mock_test_avg / 3 + np.random.normal(0, 13, n)).clip(0, 120)

    # -- Mock score trend (slope of last 5 tests, -100 to +100) ------------
    mock_score_trend = (
        -(burnout - 5) * 4 + np.random.normal(0, 15, n)
    ).clip(-100, 100)

    # -- Academic engagement ------------------------------------------------
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

    # -- Study patterns ------------------------------------------------------
    study_hours_per_day = (
        8.5 - burnout * 0.55 + np.random.normal(0, 1.2, n)
    ).clip(0, 16)

    study_consistency_score = (
        100 - burnout * 7 + np.random.normal(0, 14, n)
    ).clip(0, 100)

    # -- Coaching engagement composite ---------------------------------------
    coaching_engagement_score = (
        attendance_rate * 0.40
        + (10 - stress_level) * 3.0
        + (10 - burnout) * 2.5
        + np.random.normal(15, 8, n)
    ).clip(0, 100)

    # -----------------------------------------------------------------------
    # Dropout label -- logistic formula with JEE-domain priors
    # -----------------------------------------------------------------------
    dropout_logit = (
        -2.2                                         # intercept (~30% base rate)
        + (100 - attendance_rate)            * 0.032 # missing class
        + burnout                             * 0.28  # burnout dominant driver
          (100 - attendance_rate)            * 0.032
        + burnout                             * 0.28
        + (360 - mock_test_avg)              * 0.0055
        + (10  - sleep_hours_avg)            * 0.22
        + stress_level                        * 0.16
        + parental_pressure                   * 0.13
        + (100 - assignment_completion_rate) * 0.018
        + peer_comparison_stress              * 0.11
        + np.where(mock_score_trend < -20, 0.45, 0)
        + np.where(burnout >= 9,           0.60, 0)
        + np.random.normal(0, 0.30, n)
    )

    # Guarantee 28–32 % dropout rate via percentile cutoff
    target_rate = np.random.uniform(0.28, 0.32)
    cutoff      = np.percentile(dropout_logit, (1.0 - target_rate) * 100)
    dropout     = (dropout_logit >= cutoff).astype(int)

    # -- Assemble DataFrame -------------------------------------------------
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
        "dropout":                    dropout,
    })


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  JEE ASPIRANT DROPOUT -- DATASET GENERATOR")
    print("=" * 60)

    print(f"\n  Generating {N:,} synthetic JEE student records ...")
    df = generate_jee_dataset(N)

    actual_dropout_rate = df["dropout"].mean() * 100
    print(f"  Dataset created  ->  {len(df):,} rows | {df.shape[1]} columns")
    print(f"  Dropout rate     ->  {actual_dropout_rate:.1f}%  (target 28-32%)")

    # -- Feature summary -----------------------------------------------------
    print(f"\n  Feature ranges (min | mean | max):")
    print(f"    {'Feature':<32} {'Min':>8} {'Mean':>8} {'Max':>8}")
    print("    " + "-" * 58)
    for col in df.columns:
        if col == "dropout":
            continue
        print(
            f"    {col:<32} {df[col].min():>8.1f} "
            f"{df[col].mean():>8.1f} {df[col].max():>8.1f}"
        )

    # -- Save ----------------------------------------------------------------
    abs_path = os.path.abspath(OUTPUT_PATH)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n  Saved -> {abs_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
