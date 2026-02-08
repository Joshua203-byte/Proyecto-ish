"""
Test Script for Epochly GPU Jobs
This script loads a CSV from the dataset and does basic ML training.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import os

print("🚀 Starting Epochly Test Job...")
print(f"Python version: {os.sys.version}")

# Load dataset from the data folder
DATA_PATH = "data/sample_data.csv"

if os.path.exists(DATA_PATH):
    print(f"✅ Found dataset at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"📊 Dataset shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    
    # Simple ML example
    X = df[['feature_1', 'feature_2', 'feature_3']]
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("🤖 Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print(f"✅ Model trained successfully!")
    print(f"📈 Accuracy: {accuracy:.2%}")
    
    # Save results
    os.makedirs("output", exist_ok=True)
    results = pd.DataFrame({
        'actual': y_test,
        'predicted': predictions
    })
    results.to_csv("output/predictions.csv", index=False)
    print("💾 Results saved to output/predictions.csv")
    
else:
    print(f"⚠️ No dataset found at {DATA_PATH}")
    print("Running without dataset - generating synthetic data...")
    
    # Generate synthetic data
    np.random.seed(42)
    X = np.random.randn(1000, 3)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    
    print(f"📊 Generated synthetic data: {X.shape}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"✅ Model trained on synthetic data!")
    print(f"📈 Accuracy: {accuracy:.2%}")

print("\n🎉 Job completed successfully!")
