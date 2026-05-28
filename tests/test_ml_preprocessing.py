"""
test_ml_preprocessing.py
------------------------
Unit tests for ML preprocessing pipeline.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from imblearn.over_sampling import SMOTE


class TestPreprocessingPipeline:
    """Test the preprocessing pipeline components."""

    def test_pipeline_creation(self):
        """Test that the preprocessing pipeline can be created."""
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ])
        assert pipeline is not None
        assert len(pipeline.steps) == 2

    def test_pipeline_fit_transform(self):
        """Test that the pipeline can fit and transform data."""
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ])
        
        # Create sample data with missing values
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, np.nan, 6.0],
            [7.0, 8.0, 9.0],
        ])
        
        X_transformed = pipeline.fit_transform(X)
        
        assert X_transformed.shape == X.shape
        assert not np.isnan(X_transformed).any()
        assert np.isfinite(X_transformed).all()

    def test_imputer_strategy(self):
        """Test that the imputer uses median strategy correctly."""
        imputer = SimpleImputer(strategy="median")
        
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, np.nan, 6.0],
            [7.0, 8.0, 9.0],
        ])
        
        X_imputed = imputer.fit_transform(X)
        
        # Check that missing value was replaced with median
        assert not np.isnan(X_imputed).any()
        # Median of column 1 is (2.0 + 8.0) / 2 = 5.0
        assert X_imputed[1, 1] == 5.0

    def test_scaler_output_range(self):
        """Test that RobustScaler produces reasonable output range."""
        scaler = RobustScaler()
        
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ])
        
        X_scaled = scaler.fit_transform(X)
        
        # RobustScaler doesn't bound to [0,1] like MinMaxScaler
        # but should produce centered data
        assert np.isfinite(X_scaled).all()
        assert X_scaled.shape == X.shape


class TestSMOTE:
    """Test SMOTE oversampling for class imbalance."""

    def test_smote_application(self):
        """Test that SMOTE can be applied to imbalanced data."""
        X = np.array([
            [1.0, 2.0],
            [1.5, 2.5],
            [2.0, 3.0],
            [10.0, 20.0],  # minority class
        ])
        y = np.array([0, 0, 0, 1])
        
        smote = SMOTE(sampling_strategy='auto', random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        # After SMOTE, classes should be balanced
        unique, counts = np.unique(y_resampled, return_counts=True)
        assert len(unique) == 2
        assert counts[0] == counts[1]  # Balanced classes
        assert X_resampled.shape[0] > X.shape[0]  # More samples

    def test_smote_with_balanced_data(self):
        """Test SMOTE with already balanced data."""
        X = np.array([
            [1.0, 2.0],
            [2.0, 3.0],
            [10.0, 20.0],
            [11.0, 21.0],
        ])
        y = np.array([0, 0, 1, 1])
        
        smote = SMOTE(sampling_strategy='auto', random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        # Should remain balanced
        unique, counts = np.unique(y_resampled, return_counts=True)
        assert counts[0] == counts[1]

    def test_smote_feature_preservation(self):
        """Test that SMOTE preserves feature dimensions."""
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, 12.0],
        ])
        y = np.array([0, 0, 1, 1])
        
        smote = SMOTE(sampling_strategy='auto', random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        # Number of features should remain the same
        assert X_resampled.shape[1] == X.shape[1]


class TestFeatureEngineering:
    """Test feature engineering logic."""

    def test_feature_columns_exist(self):
        """Test that required feature columns are defined."""
        from ml_training.train import FEATURE_COLS
        
        required_features = [
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
        
        assert len(FEATURE_COLS) == 17
        for feature in required_features:
            assert feature in FEATURE_COLS

    def test_feature_data_types(self):
        """Test that feature data types are appropriate."""
        # Create sample feature data
        features = {
            "attendance_rate": 85.5,
            "mock_test_avg": 200.0,
            "physics_score": 60.0,
            "chemistry_score": 55.0,
            "maths_score": 65.0,
            "mock_score_trend": -10.0,
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
        
        # All values should be numeric
        for key, value in features.items():
            assert isinstance(value, (int, float))

    def test_feature_range_validation(self):
        """Test that feature values are within reasonable ranges."""
        features = {
            "attendance_rate": 85.5,  # 0-100
            "mock_test_avg": 200.0,  # 0-360
            "physics_score": 60.0,  # 0-120
            "burnout_score": 5,  # 1-10
            "stress_level": 6,  # 1-10
        }
        
        assert 0 <= features["attendance_rate"] <= 100
        assert 0 <= features["mock_test_avg"] <= 360
        assert 0 <= features["physics_score"] <= 120
        assert 1 <= features["burnout_score"] <= 10
        assert 1 <= features["stress_level"] <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
