"""
services/ml_service.py
─────────────────────
ML service with model caching for dropout prediction.
Loads models once at startup and provides prediction methods.
"""

from __future__ import annotations

import logging
import os
import pickle
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class MLService:
    """
    ML service with model caching.
    Loads models once at startup and provides prediction methods.
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.is_loaded = False
        self.metadata = {}

    def load_models(self) -> bool:
        """
        Load ML models from disk.
        Returns True if successful, False otherwise.
        """
        try:
            model_path = settings.MODEL_PATH
            scaler_path = settings.MODEL_PATH.replace(".pkl", "_scaler.pkl")
            
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            # Load model
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            
            # Load scaler
            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
            else:
                logger.warning(f"Scaler file not found: {scaler_path}")
                self.scaler = StandardScaler()
            
            # Set feature columns (adjust based on your actual features)
            self.feature_cols = [
                "attendance_rate", "mock_test_avg", "physics_score",
                "chemistry_score", "maths_score", "mock_score_trend",
                "assignment_completion_rate", "dpp_accuracy", "test_attempt_rate",
                "burnout_score", "stress_level", "sleep_hours_avg",
                "study_hours_per_day", "study_consistency_score",
                "parental_pressure_level", "peer_comparison_stress"
            ]
            
            self.metadata = {
                "version": "1.0.0",
                "n_features": len(self.feature_cols),
                "threshold": settings.PREDICTION_THRESHOLD,
                "trained_at": "2024-01-01",  # Update with actual training date
            }
            
            self.is_loaded = True
            logger.info(f"ML models loaded successfully from {model_path}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to load ML models: {exc}")
            self.is_loaded = False
            return False

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Make a prediction using the loaded model.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_loaded or self.model is None:
            logger.warning("ML models not loaded, returning default prediction")
            return {
                "ensemble_probability": 0.5,
                "predicted_dropout": False,
                "model_version": "unknown",
                "inference_time_ms": 0,
            }
        
        try:
            # Extract features in correct order
            feature_values = [features.get(col, 0) for col in self.feature_cols]
            feature_array = np.array(feature_values).reshape(1, -1)
            
            # Scale features if scaler is available
            if self.scaler:
                feature_array = self.scaler.transform(feature_array)
            
            # Make prediction
            import time
            start_time = time.time()
            probability = self.model.predict_proba(feature_array)[0, 1]
            inference_time = (time.time() - start_time) * 1000
            
            predicted_dropout = probability >= settings.PREDICTION_THRESHOLD
            
            return {
                "ensemble_probability": float(probability),
                "predicted_dropout": predicted_dropout,
                "model_version": self.metadata.get("version", "unknown"),
                "inference_time_ms": round(inference_time, 2),
            }
            
        except Exception as exc:
            logger.error(f"Prediction failed: {exc}")
            return {
                "ensemble_probability": 0.5,
                "predicted_dropout": False,
                "model_version": "unknown",
                "inference_time_ms": 0,
            }

    def validate_features(self, features: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate input features before prediction.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_features = self.feature_cols or []
        
        for feature in required_features:
            if feature not in features:
                return False, f"Missing required feature: {feature}"
            
            value = features[feature]
            if value is None:
                return False, f"Feature {feature} cannot be None"
            
            # Type validation
            if not isinstance(value, (int, float)):
                return False, f"Feature {feature} must be numeric"
        
        return True, ""


# Global ML service instance
ml_service = MLService()
