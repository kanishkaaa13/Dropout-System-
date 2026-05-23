"""
ML MODEL TRAINING SCRIPT
Trains Random Forest, Gradient Boosting, and Neural Network models
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os

print("="*70)
print("  🤖 TRAINING DROPOUT PREDICTION MODELS")
print("="*70)

# Create ML directory
os.makedirs('ml', exist_ok=True)

# Generate synthetic training data
print("\n📊 Generating training data...")
np.random.seed(42)
n_samples = 5000

data = {
    'attendance': np.random.normal(80, 15, n_samples).clip(0, 100),
    'gpa': np.random.normal(7, 1.5, n_samples).clip(0, 10),
    'assignments_completed': np.random.normal(75, 20, n_samples).clip(0, 100),
    'test_scores': np.random.normal(70, 15, n_samples).clip(0, 100),
    'previous_failures': np.random.poisson(0.3, n_samples),
    'extracurricular': np.random.poisson(2, n_samples),
    'library_visits': np.random.poisson(5, n_samples),
    'online_engagement': np.random.normal(70, 20, n_samples).clip(0, 100),
    'parental_education': np.random.choice([1, 2, 3, 4, 5], n_samples),
    'financial_stress': np.random.choice([1, 2, 3, 4, 5], n_samples),
    'family_support': np.random.choice([1, 2, 3, 4, 5], n_samples),
    'health_issues': np.random.choice([1, 2, 3, 4, 5], n_samples),
    'stress_level': np.random.choice([1, 2, 3, 4, 5], n_samples),
    'sleep_hours': np.random.normal(6, 1.5, n_samples).clip(3, 10),
    'age': np.random.normal(20, 2, n_samples).clip(17, 30),
    'commute_time': np.random.exponential(30, n_samples).clip(0, 120),
    'part_time_job': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
}

df = pd.DataFrame(data)

# Calculate dropout risk
dropout_prob = (
    (100 - df['attendance']) * 0.3 +
    (10 - df['gpa']) * 10 * 0.25 +
    (100 - df['assignments_completed']) * 0.15 +
    df['previous_failures'] * 15 +
    df['financial_stress'] * 5 +
    (6 - df['family_support']) * 3 +
    df['stress_level'] * 3
) / 100

dropout_prob = dropout_prob.clip(0, 1)
df['dropout'] = (dropout_prob > np.random.uniform(0.3, 0.6, n_samples)).astype(int)

print(f"✅ Generated {n_samples} samples")
print(f"   Dropout rate: {df['dropout'].mean()*100:.1f}%")

# Prepare features and target
X = df.drop('dropout', axis=1)
y = df['dropout']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n📦 Data split:")
print(f"   Training: {len(X_train)} samples")
print(f"   Testing: {len(X_test)} samples")

# Scale features
print("\n🔧 Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Random Forest
print("\n🌲 Training Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=10,
    min_samples_leaf=4,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train_scaled, y_train)
rf_pred = rf_model.predict(X_test_scaled)
rf_acc = accuracy_score(y_test, rf_pred)
print(f"   ✅ Random Forest Accuracy: {rf_acc*100:.2f}%")

# Train Gradient Boosting
print("\n⚡ Training Gradient Boosting...")
gb_model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=10,
    min_samples_leaf=4,
    random_state=42
)
gb_model.fit(X_train_scaled, y_train)
gb_pred = gb_model.predict(X_test_scaled)
gb_acc = accuracy_score(y_test, gb_pred)
print(f"   ✅ Gradient Boosting Accuracy: {gb_acc*100:.2f}%")

# Train Neural Network
print("\n🧠 Training Neural Network...")
mlp_model = MLPClassifier(
    hidden_layer_sizes=(64, 32, 16),
    activation='relu',
    solver='adam',
    max_iter=500,
    random_state=42,
    early_stopping=True
)
mlp_model.fit(X_train_scaled, y_train)
mlp_pred = mlp_model.predict(X_test_scaled)
mlp_acc = accuracy_score(y_test, mlp_pred)
print(f"   ✅ Neural Network Accuracy: {mlp_acc*100:.2f}%")

# Ensemble prediction
print("\n🎯 Creating Ensemble Model...")
rf_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
gb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
mlp_proba = mlp_model.predict_proba(X_test_scaled)[:, 1]

ensemble_proba = rf_proba * 0.4 + gb_proba * 0.35 + mlp_proba * 0.25
ensemble_pred = (ensemble_proba > 0.5).astype(int)
ensemble_acc = accuracy_score(y_test, ensemble_pred)

print(f"   ✅ Ensemble Accuracy: {ensemble_acc*100:.2f}%")

# Save models
print("\n💾 Saving models...")
joblib.dump(scaler, 'ml/scaler.pkl')
joblib.dump(rf_model, 'ml/rf_model.pkl')
joblib.dump(gb_model, 'ml/gb_model.pkl')
joblib.dump(mlp_model, 'ml/mlp_model.pkl')

print("\n✅ Model files saved:")
print("   ml/scaler.pkl")
print("   ml/rf_model.pkl")
print("   ml/gb_model.pkl")
print("   ml/mlp_model.pkl")

# Summary
print("\n" + "="*70)
print("  📊 TRAINING SUMMARY")
print("="*70)
print(f"  Random Forest:      {rf_acc*100:.2f}%")
print(f"  Gradient Boosting:  {gb_acc*100:.2f}%")
print(f"  Neural Network:     {mlp_acc*100:.2f}%")
print(f"  Ensemble:           {ensemble_acc*100:.2f}%")
print("="*70)
print("\n✅ TRAINING COMPLETE! Models ready to use.")
print("   Run: python app.py")
print("="*70 + "\n")
