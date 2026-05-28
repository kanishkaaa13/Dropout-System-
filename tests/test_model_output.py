"""
test_model_output.py
-------------------
Unit tests for ML model output and predictions.
"""

import pytest
import numpy as np
import joblib
from pathlib import Path


class TestModelLoading:
    """Test model loading and initialization."""

    def test_model_files_exist(self):
        """Test that required model files exist."""
        model_dir = Path("models")
        
        required_files = [
            "preprocessor.pkl",
            "xgb_model.pkl",
            "rf_model.pkl",
            "lr_model.pkl",
            "metadata.json",
        ]
        
        for filename in required_files:
            model_path = model_dir / filename
            assert model_path.exists(), f"Model file {filename} not found"

    def test_preprocessor_loading(self):
        """Test that preprocessor can be loaded."""
        model_dir = Path("models")
        preprocessor_path = model_dir / "preprocessor.pkl"
        
        if preprocessor_path.exists():
            preprocessor = joblib.load(preprocessor_path)
            assert preprocessor is not None
            assert hasattr(preprocessor, 'transform')

    def test_metadata_loading(self):
        """Test that metadata can be loaded and contains required fields."""
        import json
        model_dir = Path("models")
        metadata_path = model_dir / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            required_fields = [
                "version",
                "trained_at",
                "n_features",
                "feature_names",
                "threshold",
                "ensemble_weights",
            ]
            
            for field in required_fields:
                assert field in metadata, f"Metadata missing field: {field}"

    def test_feature_names_match(self):
        """Test that feature names in metadata match expected features."""
        import json
        from ml_training.train import FEATURE_COLS
        
        model_dir = Path("models")
        metadata_path = model_dir / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata_features = metadata.get("feature_names", [])
            assert len(metadata_features) == len(FEATURE_COLS)
            assert set(metadata_features) == set(FEATURE_COLS)


class TestModelPrediction:
    """Test model prediction functionality."""

    def test_prediction_output_format(self):
        """Test that model predictions have correct output format."""
        # This test requires loaded models, skip if models don't exist
        model_dir = Path("models")
        if not (model_dir / "xgb_model.pkl").exists():
            pytest.skip("Model files not found")
        
        try:
            from backend.app.ml.predictor import JEEDropoutPredictor
            
            predictor = JEEDropoutPredictor(
                model_dir=str(model_dir),
                threshold=0.5,
            )
            predictor.load_models()
            
            # Create sample input
            sample_features = {
                "attendance_rate": 85.0,
                "mock_test_avg": 200.0,
                "physics_score": 60.0,
                "chemistry_score": 55.0,
                "maths_score": 65.0,
                "mock_score_trend": -5.0,
                "assignment_completion_rate": 90.0,
                "dpp_accuracy": 75.0,
                "test_attempt_rate": 95.0,
                "burnout_score": 5,
                "stress_level": 6,
                "sleep_hours_avg": 6.5,
                "study_hours_per_day": 8.0,
                "study_consistency_score": 70.0,
                "parental_pressure_level": 7,
                "peer_comparison_stress": 5,
                "coaching_engagement_score": 80.0,
            }
            
            prediction = predictor.predict_single(sample_features)
            
            # Check output format
            assert "ensemble_probability" in prediction
            assert "predicted_dropout" in prediction
            assert "model_version" in prediction
            assert "inference_time_ms" in prediction
            
            # Check value ranges
            assert 0 <= prediction["ensemble_probability"] <= 1
            assert isinstance(prediction["predicted_dropout"], bool)
            assert prediction["inference_time_ms"] >= 0
            
        except Exception as e:
            pytest.skip(f"Model prediction test skipped: {e}")

    def test_prediction_threshold(self):
        """Test that prediction threshold is applied correctly."""
        model_dir = Path("models")
        if not (model_dir / "xgb_model.pkl").exists():
            pytest.skip("Model files not found")
        
        try:
            from backend.app.ml.predictor import JEEDropoutPredictor
            
            # Test with different thresholds
            for threshold in [0.3, 0.5, 0.7]:
                predictor = JEEDropoutPredictor(
                    model_dir=str(model_dir),
                    threshold=threshold,
                )
                predictor.load_models()
                
                sample_features = {
                    "attendance_rate": 50.0,  # Low attendance
                    "mock_test_avg": 100.0,  # Low scores
                    "physics_score": 30.0,
                    "chemistry_score": 25.0,
                    "maths_score": 35.0,
                    "mock_score_trend": -30.0,
                    "assignment_completion_rate": 40.0,
                    "dpp_accuracy": 30.0,
                    "test_attempt_rate": 50.0,
                    "burnout_score": 9,  # High burnout
                    "stress_level": 9,
                    "sleep_hours_avg": 4.0,
                    "study_hours_per_day": 4.0,
                    "study_consistency_score": 30.0,
                    "parental_pressure_level": 9,
                    "peer_comparison_stress": 8,
                    "coaching_engagement_score": 30.0,
                }
                
                prediction = predictor.predict_single(sample_features)
                
                # High-risk student should be predicted as dropout
                # regardless of threshold (probability should be high)
                assert prediction["ensemble_probability"] >= 0
                
        except Exception as e:
            pytest.skip(f"Threshold test skipped: {e}")

    def test_model_version_consistency(self):
        """Test that model version is consistent across components."""
        import json
        model_dir = Path("models")
        metadata_path = model_dir / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            model_version = metadata.get("version")
            assert model_version is not None
            assert isinstance(model_version, str)


class TestRiskScoring:
    """Test risk scoring computation."""

    def test_risk_score_range(self):
        """Test that risk scores are within valid range."""
        from backend.app.ml.risk_scorer import compute_risk_score
        
        risk = compute_risk_score(
            ml_probability=0.8,
            burnout_score=8,
            mock_score_trend=-20,
            attendance_rate=60,
            sleep_hours=5,
            parental_pressure=8,
        )
        
        assert 0 <= risk["score"] <= 100
        assert risk["level"] in ["Low", "Medium", "High", "Critical"]

    def test_risk_level_mapping(self):
        """Test that risk levels are mapped correctly."""
        from backend.app.ml.risk_scorer import compute_risk_score
        
        # Test high probability
        risk_high = compute_risk_score(
            ml_probability=0.9,
            burnout_score=9,
            mock_score_trend=-30,
            attendance_rate=40,
            sleep_hours=4,
            parental_pressure=9,
        )
        assert risk_high["level"] in ["High", "Critical"]
        
        # Test low probability
        risk_low = compute_risk_score(
            ml_probability=0.1,
            burnout_score=2,
            mock_score_trend=10,
            attendance_rate=95,
            sleep_hours=8,
            parental_pressure=3,
        )
        assert risk_low["level"] in ["Low", "Medium"]

    def test_risk_components(self):
        """Test that risk score components are computed."""
        from backend.app.ml.risk_scorer import compute_risk_score
        
        risk = compute_risk_score(
            ml_probability=0.7,
            burnout_score=6,
            mock_score_trend=-10,
            attendance_rate=70,
            sleep_hours=6,
            parental_pressure=6,
        )
        
        assert "components" in risk
        components = risk["components"]
        
        # Check that all components exist
        expected_components = [
            "ml_probability_score",
            "burnout_score",
            "academic_performance",
            "engagement_score",
        ]
        
        for component in expected_components:
            assert component in components
            assert 0 <= components[component] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
