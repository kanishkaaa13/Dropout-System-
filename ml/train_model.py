"""
train_model.py
--------------
ML training script for JEE Dropout Prediction.

Merges two datasets, applies SMOTE for class imbalance, trains XGBoost and RandomForest
with 5-fold stratified cross-validation, and saves the best model.
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
from pathlib import Path

from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from imblearn.over_sampling import SMOTE
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings('ignore')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Dataset paths
DATASET1_PATH = DATA_DIR / 'JEE_Dropout_After_Class_12.csv'
DATASET2_PATH = DATA_DIR / 'jee_training_data.csv'

print("=" * 80)
print("JEE Dropout Prediction - ML Training Pipeline")
print("=" * 80)

# Load datasets
print("\n[1/7] Loading datasets...")
try:
    df1 = pd.read_csv(DATASET1_PATH)
    print(f"   Dataset 1 loaded: {df1.shape[0]} rows, {df1.shape[1]} columns")
    print(f"   Columns: {list(df1.columns)}")
except FileNotFoundError:
    print(f"   ERROR: Dataset 1 not found at {DATASET1_PATH}")
    df1 = None

try:
    df2 = pd.read_csv(DATASET2_PATH)
    print(f"   Dataset 2 loaded: {df2.shape[0]} rows, {df2.shape[1]} columns")
    print(f"   Columns: {list(df2.columns)}")
except FileNotFoundError:
    print(f"   ERROR: Dataset 2 not found at {DATASET2_PATH}")
    df2 = None

if df1 is None and df2 is None:
    raise ValueError("No datasets found. Please check the file paths.")

# Use Dataset 2 as primary (more features, better aligned with prediction needs)
# Dataset 1 can be used for additional training if needed
print("\n[2/7] Preprocessing data...")

# Use Dataset 2 as primary (has more relevant features for dropout prediction)
df = df2.copy()

# Check for missing values
print(f"   Missing values: {df.isnull().sum().sum()}")
if df.isnull().sum().sum() > 0:
    print("   Filling missing values with median...")
    df = df.fillna(df.median())

# Separate features and target
target_col = 'dropout'
if target_col not in df.columns:
    raise ValueError(f"Target column '{target_col}' not found in dataset")

X = df.drop(columns=[target_col])
y = df[target_col]

print(f"   Features: {X.shape[1]}")
print(f"   Target distribution:")
print(f"   - Class 0 (No Dropout): {sum(y == 0)} ({sum(y == 0)/len(y)*100:.1f}%)")
print(f"   - Class 1 (Dropout): {sum(y == 1)} ({sum(y == 1)/len(y)*100:.1f}%)")

# Save feature names
feature_names = list(X.columns)
print(f"\n[3/7] Saving feature names to artifacts/features.json...")
with open(ARTIFACTS_DIR / 'features.json', 'w') as f:
    json.dump(feature_names, f, indent=2)
print(f"   Features saved: {len(feature_names)} features")

# Apply SMOTE for class imbalance
print("\n[4/7] Applying SMOTE for class balancing...")
smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X, y)

print(f"   Original distribution: Class 0: {sum(y == 0)}, Class 1: {sum(y == 1)}")
print(f"   After SMOTE: Class 0: {sum(y_resampled == 0)}, Class 1: {sum(y_resampled == 1)}")

# Split into train and test sets
print("\n[5/7] Splitting data into train/test sets...")
X_train, X_test, y_train, y_test = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled
)
print(f"   Train set: {X_train.shape[0]} samples")
print(f"   Test set: {X_test.shape[0]} samples")

# Scale features
print("   Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train models with 5-fold stratified cross-validation
print("\n[6/7] Training models with 5-fold stratified cross-validation...")

# XGBoost
print("   Training XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='logloss',
    use_label_encoder=False
)

# 5-fold CV for XGBoost
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
xgb_cv_scores = cross_val_score(xgb_model, X_train_scaled, y_train, cv=cv, scoring='roc_auc')
print(f"   XGBoost 5-fold CV ROC-AUC: {xgb_cv_scores.mean():.4f} (+/- {xgb_cv_scores.std() * 2:.4f})")

# Train XGBoost on full training set
xgb_model.fit(X_train_scaled, y_train)

# RandomForest
print("   Training RandomForest...")
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

# 5-fold CV for RandomForest
rf_cv_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=cv, scoring='roc_auc')
print(f"   RandomForest 5-fold CV ROC-AUC: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std() * 2:.4f})")

# Train RandomForest on full training set
rf_model.fit(X_train_scaled, y_train)

# Evaluate both models on test set
print("\n   Evaluating models on test set...")

# XGBoost predictions
xgb_pred = xgb_model.predict(X_test_scaled)
xgb_pred_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]

xgb_accuracy = accuracy_score(y_test, xgb_pred)
xgb_precision = precision_score(y_test, xgb_pred)
xgb_recall = recall_score(y_test, xgb_pred)
xgb_f1 = f1_score(y_test, xgb_pred)
xgb_roc_auc = roc_auc_score(y_test, xgb_pred_proba)

print(f"\n   XGBoost Test Metrics:")
print(f"   - Accuracy: {xgb_accuracy:.4f}")
print(f"   - Precision: {xgb_precision:.4f}")
print(f"   - Recall: {xgb_recall:.4f}")
print(f"   - F1 Score: {xgb_f1:.4f}")
print(f"   - ROC-AUC: {xgb_roc_auc:.4f}")

# RandomForest predictions
rf_pred = rf_model.predict(X_test_scaled)
rf_pred_proba = rf_model.predict_proba(X_test_scaled)[:, 1]

rf_accuracy = accuracy_score(y_test, rf_pred)
rf_precision = precision_score(y_test, rf_pred)
rf_recall = recall_score(y_test, rf_pred)
rf_f1 = f1_score(y_test, rf_pred)
rf_roc_auc = roc_auc_score(y_test, rf_pred_proba)

print(f"\n   RandomForest Test Metrics:")
print(f"   - Accuracy: {rf_accuracy:.4f}")
print(f"   - Precision: {rf_precision:.4f}")
print(f"   - Recall: {rf_recall:.4f}")
print(f"   - F1 Score: {rf_f1:.4f}")
print(f"   - ROC-AUC: {rf_roc_auc:.4f}")

# Select best model by ROC-AUC
print("\n[7/7] Selecting best model and saving...")
if xgb_roc_auc >= rf_roc_auc:
    best_model = xgb_model
    best_model_name = "XGBoost"
    best_roc_auc = xgb_roc_auc
    print(f"   Selected: XGBoost (ROC-AUC: {xgb_roc_auc:.4f})")
else:
    best_model = rf_model
    best_model_name = "RandomForest"
    best_roc_auc = rf_roc_auc
    print(f"   Selected: RandomForest (ROC-AUC: {rf_roc_auc:.4f})")

# Save best model
import joblib
model_path = ARTIFACTS_DIR / 'model.pkl'
joblib.dump(best_model, model_path)
print(f"   Model saved to: {model_path}")

# Save scaler
scaler_path = ARTIFACTS_DIR / 'scaler.pkl'
joblib.dump(scaler, scaler_path)
print(f"   Scaler saved to: {scaler_path}")

# Save training metadata
metadata = {
    'model_type': best_model_name,
    'roc_auc': float(best_roc_auc),
    'features': feature_names,
    'n_features': len(feature_names),
    'n_samples_train': len(X_train),
    'n_samples_test': len(X_test),
    'xgb_cv_roc_auc_mean': float(xgb_cv_scores.mean()),
    'xgb_cv_roc_auc_std': float(xgb_cv_scores.std()),
    'rf_cv_roc_auc_mean': float(rf_cv_scores.mean()),
    'rf_cv_roc_auc_std': float(rf_cv_scores.std()),
    'test_metrics': {
        'accuracy': float(xgb_accuracy if best_model_name == 'XGBoost' else rf_accuracy),
        'precision': float(xgb_precision if best_model_name == 'XGBoost' else rf_precision),
        'recall': float(xgb_recall if best_model_name == 'XGBoost' else rf_recall),
        'f1': float(xgb_f1 if best_model_name == 'XGBoost' else rf_f1),
        'roc_auc': float(best_roc_auc)
    }
}

metadata_path = ARTIFACTS_DIR / 'metadata.json'
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"   Metadata saved to: {metadata_path}")

print("\n" + "=" * 80)
print("Training Complete!")
print("=" * 80)
print(f"\nBest Model: {best_model_name}")
print(f"Test ROC-AUC: {best_roc_auc:.4f}")
print(f"\nArtifacts saved to: {ARTIFACTS_DIR}")
print("  - model.pkl")
print("  - scaler.pkl")
print("  - features.json")
print("  - metadata.json")
print("\nRun evaluation with: python ml/evaluate.py")
print("=" * 80)
