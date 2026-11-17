import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
import seaborn as sns
import matplotlib.pyplot as plt

# Paths for saving transformations
LABEL_ENCODERS_PATH = "models/label_encoders.pkl"
SCALER_PATH = "models/scaler.pkl"

def load_data(file_path):
    """Load dataset from CSV file."""
    return pd.read_csv(file_path)

def preprocess_data(df, training=True):
    """
    Clean and preprocess the dataset.

    - If training=True, fit & save encoders/scaler.
    - If training=False, load existing encoders/scaler & apply transformation.
    """
    # Fill missing values with median
    df = df.fillna(df.median())

    # Separate features & target
    target_col = "credit_status"
    if target_col in df.columns:
        y = df[target_col]
        X = df.drop(columns=[target_col])
    else:
        X, y = df, None  # For test data

    # Encode categorical variables
    label_encoders = {}
    categorical_cols = X.select_dtypes(include=['object']).columns

    if training:
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le
        joblib.dump(label_encoders, LABEL_ENCODERS_PATH)
    else:
        if os.path.exists(LABEL_ENCODERS_PATH):
            label_encoders = joblib.load(LABEL_ENCODERS_PATH)
            for col in categorical_cols:
                if col in label_encoders:
                    X[col] = X[col].apply(lambda s: label_encoders[col].transform([s])[0] if s in label_encoders[col].classes_ else -1)
        else:
            print("⚠️ Warning: Label encoders not found! Categories may be misaligned.")

    # Standardize numerical features (excluding target)
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns
    scaler = StandardScaler()

    if training:
        X[numerical_cols] = scaler.fit_transform(X[numerical_cols])
        joblib.dump(scaler, SCALER_PATH)
    else:
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
            X[numerical_cols] = scaler.transform(X[numerical_cols])
        else:
            print("⚠️ Warning: Scaler not found! Model may produce incorrect results.")

    return X, y, label_encoders, scaler

def visualize_data(df):
    """Perform exploratory data analysis."""
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Feature Correlation Heatmap")
    plt.show()

if __name__ == "__main__":
    df = load_data("data/credit_data.csv")
    X, y, encoders, scaler = preprocess_data(df, training=True)
    visualize_data(df)
    print("✅ Processed Data Sample:")
    print(X.head())
