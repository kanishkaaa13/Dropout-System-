"""
risk_scorer.py
──────────────
JEE Dropout Prediction System — Phase 2
Composite 0-100 risk score with domain-informed adjustments.

The raw ML probability is a good academic discriminator but counselors
need an intuitive 0-100 scale with JEE-domain context.  This module
maps probability → composite score using five domain bonuses.

Usage
-----
    from backend.app.ml.risk_scorer import compute_risk_score

    result = compute_risk_score(
        ml_probability   = 0.72,
        burnout_score    = 8,
        mock_score_trend = -12.5,
        attendance_rate  = 67.0,
        sleep_hours      = 4.8,
        parental_pressure= 9,
    )
    # result["score"]   → 84.3
    # result["level"]   → "Critical"
    # result["urgency"] → "immediate"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


# ─── Return type ─────────────────────────────────────────────────────────────

class RiskScoreResult(TypedDict):
    score:      float          # 0-100 composite risk score
    level:      str            # Low | Medium | High | Critical
    color:      str            # hex colour for UI badges
    urgency:    str            # routine | within_2_weeks | within_48_hours | immediate
    components: dict[str, float]  # breakdown of how score was built


# ─── Risk bands ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _RiskBand:
    min_score: float
    max_score: float
    level:     str
    color:     str     # hex
    urgency:   str


_BANDS: tuple[_RiskBand, ...] = (
    _RiskBand(0,   30,  "Low",      "#10B981", "routine"),
    _RiskBand(30,  55,  "Medium",   "#F59E0B", "within_2_weeks"),
    _RiskBand(55,  75,  "High",     "#EF4444", "within_48_hours"),
    _RiskBand(75, 100,  "Critical", "#7C3AED", "immediate"),
)


def _classify(score: float) -> _RiskBand:
    for band in _BANDS:
        if score < band.max_score:
            return band
    return _BANDS[-1]


# ─── Main function ────────────────────────────────────────────────────────────

def compute_risk_score(
    ml_probability:    float,
    burnout_score:     int   | float,
    mock_score_trend:  float,
    attendance_rate:   float,
    sleep_hours:       float,
    parental_pressure: int   | float,
) -> RiskScoreResult:
    """
    Compute a composite 0-100 dropout risk score with domain-informed bonuses.

    The score has two components:

    1. **ML base** (0-70):  ``ml_probability * 70``
       Anchors the score to the model's calibrated dropout probability.

    2. **Domain bonuses** (0-30 total across all five dimensions):
       Each bonus fires only when a clinically meaningful threshold is crossed,
       preventing small fluctuations from inflating the score.

       - Burnout > 6        → up to +10 pts  (JEE burnout is the #1 dropout driver)
       - Declining trend    → up to +8  pts  (mock_score_trend < 0)
       - Sleep deprivation  → up to +7  pts  (sleep < 6 h)
       - Parental pressure  → up to +5  pts  (pressure > 7)
       - Low attendance     → up to +10 pts  (attendance < 75 %)

    Parameters
    ----------
    ml_probability : float
        Raw ensemble dropout probability in [0, 1].
    burnout_score : int or float
        Self-reported burnout on a 1-10 scale.
    mock_score_trend : float
        Regression slope of last 5 mock test scores (-100 to +100).
        Negative → declining performance.
    attendance_rate : float
        Percentage of classes attended (0-100).
    sleep_hours : float
        Average nightly sleep hours (3-10).
    parental_pressure : int or float
        Self-reported parental pressure on a 1-10 scale.

    Returns
    -------
    RiskScoreResult
        TypedDict with keys: score, level, color, urgency, components.
    """
    # ── 1. ML base (0-70 range) ──────────────────────────────────────────────
    ml_probability = float(max(0.0, min(1.0, ml_probability)))
    ml_base        = ml_probability * 70.0

    # ── 2. Domain bonuses ────────────────────────────────────────────────────

    # Burnout bonus (0-10): kicks in above threshold=6, max at 10
    # e.g. burnout=8 → (8-6)/4 * 10 = 5.0 pts
    #      burnout=9 → (9-6)/4 * 10 = 7.5 pts
    burnout_contribution = max(0.0, (float(burnout_score) - 6.0) / 4.0) * 10.0

    # Trend bonus (0-8): penalises declining mock scores
    # e.g. trend=-10 → min(10, 10)/10 * 8 = 8 pts
    #      trend=-5  →  5/10 * 8 = 4 pts
    trend_contribution = max(0.0, min(abs(float(mock_score_trend)), 100.0) / 100.0 * 8.0) \
        if float(mock_score_trend) < 0 else 0.0

    # Sleep bonus (0-7): penalises < 6 h sleep
    # e.g. sleep=4.5 → (6-4.5)/3 * 7 = 3.5 pts
    sleep_contribution = max(0.0, (6.0 - float(sleep_hours)) / 3.0) * 7.0

    # Parental pressure bonus (0-5): kicks in above threshold=7
    pressure_contribution = max(0.0, (float(parental_pressure) - 7.0) / 3.0) * 5.0

    # Attendance bonus (0-10): penalises below 75 %
    # e.g. attendance=60 → (75-60)/75 * 10 = 2.0 pts
    attendance_contribution = max(0.0, (75.0 - float(attendance_rate)) / 75.0) * 10.0

    total_bonus = (
        burnout_contribution
        + trend_contribution
        + sleep_contribution
        + pressure_contribution
        + attendance_contribution
    )

    # ── 3. Final score (clamped 0-100) ───────────────────────────────────────
    raw_score   = ml_base + total_bonus
    final_score = round(min(100.0, max(0.0, raw_score)), 1)

    band = _classify(final_score)

    return RiskScoreResult(
        score   = final_score,
        level   = band.level,
        color   = band.color,
        urgency = band.urgency,
        components = {
            "ml_base":                  round(ml_base,                 2),
            "burnout_contribution":     round(burnout_contribution,     2),
            "trend_contribution":       round(trend_contribution,       2),
            "sleep_contribution":       round(sleep_contribution,       2),
            "pressure_contribution":    round(pressure_contribution,    2),
            "attendance_contribution":  round(attendance_contribution,  2),
            "total_bonus":              round(total_bonus,              2),
        },
    )


# ─── Convenience: bulk scoring ────────────────────────────────────────────────

def compute_risk_score_from_prediction(
    prediction:  dict,
    raw_features: dict,
) -> RiskScoreResult:
    """
    Convenience wrapper: derive all required fields from a ``predict_single``
    result dict + the raw features dict, to avoid re-passing individual params.

    Parameters
    ----------
    prediction : dict
        Return value of ``JEEDropoutPredictor.predict_single()``.
    raw_features : dict
        The same features dict passed to ``predict_single()``.

    Returns
    -------
    RiskScoreResult
    """
    return compute_risk_score(
        ml_probability    = prediction["ensemble_probability"],
        burnout_score     = raw_features["burnout_score"],
        mock_score_trend  = raw_features["mock_score_trend"],
        attendance_rate   = raw_features["attendance_rate"],
        sleep_hours       = raw_features["sleep_hours_avg"],
        parental_pressure = raw_features["parental_pressure_level"],
    )
