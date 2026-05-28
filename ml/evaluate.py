"""
evaluate.py
-----------
Model evaluation script for JEE Dropout Prediction.

Loads the saved model and prints comprehensive evaluation metrics.
"""

import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("WARNING: seaborn/matplotlib not installed. Confusion matrix plot will be skipped.")

# Paths
ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
DATA_DIR = Path(__file__).parent.parent / 'data'
DATASET_PATH = DATA_DIR / 'jee_training_data.csv'

print("=" * 80)
print("JEE Dropout Prediction - Model Evaluation")
print("=" * 80)

# Load model and artifacts
print("\n[1/5] Loading model and artifacts...")
try:
    model = joblib.load(ARTIFACTS_DIR / 'model.pkl')
    print(f"   Model loaded successfully")
except FileNotFoundError:
    print(f"   ERROR: Model not found at {ARTIFACTS_DIR / 'model.pkl'}")
    exit(1)

try:
    scaler = joblib.load(ARTIFACTS_DIR / 'scaler.pkl')
    print(f"   Scaler loaded successfully")
except FileNotFoundError:
    print(f"   ERROR: Scaler not found at {ARTIFACTS_DIR / 'scaler.pkl'}")
    exit(1)

try:
    with open(ARTIFACTS_DIR / 'features.json', 'r') as f:
        feature_names = json.load(f)
    print(f"   Feature names loaded: {len(feature_names)} features")
except FileNotFoundError:
    print(f"   ERROR: Features not found at {ARTIFACTS_DIR / 'features.json'}")
    exit(1)

try:
    with open(ARTIFACTS_DIR / 'metadata.json', 'r') as f:
        metadata = json.load(f)
    print(f"   Metadata loaded")
except FileNotFoundError:
    print(f"   WARNING: Metadata not found")
    metadata = {}

# Load test data
print("\n[2/5] Loading test data...")
try:
    df = pd.read_csv(DATASET_PATH)
    print(f"   Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
except FileNotFoundError:
    print(f"   ERROR: Dataset not found at {DATASET_PATH}")
    exit(1)

# Separate features and target
target_col = 'dropout'
if target_col not in df.columns:
    raise ValueError(f"Target column '{target_col}' not found in dataset")

X = df[feature_names]
y = df[target_col]

# Fill missing values
X = X.fillna(X.median())

# Scale features
print("\n[3/5] Scaling features...")
X_scaled = scaler.transform(X)

# Make predictions
print("\n[4/5] Making predictions...")
y_pred = model.predict(X_scaled)
y_pred_proba = model.predict_proba(X_scaled)[:, 1]

# Calculate metrics
print("\n[5/5] Calculating evaluation metrics...")

accuracy = accuracy_score(y, y_pred)
precision = precision_score(y, y_pred)
recall = recall_score(y, y_pred)
f1 = f1_score(y, y_pred)
roc_auc = roc_auc_score(y, y_pred_proba)

print("\n" + "=" * 80)
print("EVALUATION RESULTS")
print("=" * 80)

print(f"\nModel Type: {metadata.get('model_type', 'Unknown')}")
print(f"Training ROC-AUC: {metadata.get('roc_auc', 'N/A'):.4f}" if metadata.get('roc_auc') else "Training ROC-AUC: N/A")

print("\n--- Test Set Metrics ---")
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")
print(f"ROC-AUC:   {roc_auc:.4f}")

print("\n--- Confusion Matrix ---")
cm = confusion_matrix(y, y_pred)
print(f"True Negatives:  {cm[0, 0]}")
print(f"False Positives: {cm[0, 1]}")
print(f"False Negatives: {cm[1, 0]}")
print(f"True Positives:  {cm[1, 1]}")

print("\n--- Classification Report ---")
print(classification_report(y, y_pred, target_names=['No Dropout', 'Dropout']))

# Plot confusion matrix (if seaborn is available)
if HAS_SEABORN:
    print("\nGenerating confusion matrix plot...")
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['No Dropout', 'Dropout'],
                yticklabels=['No Dropout', 'Dropout'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / 'confusion_matrix.png', dpi=150, bbox_inches='tight')
    print(f"   Confusion matrix saved to: {ARTIFACTS_DIR / 'confusion_matrix.png'}")
else:
    print("\nSkipping confusion matrix plot (seaborn not installed)")

print("\n" + "=" * 80)
print("Evaluation Complete!")
print("=" * 80)
