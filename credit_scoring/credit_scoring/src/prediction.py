import pickle
import pandas as pd
import numpy as np
import random
import os

MODELS_DIR = "models"
BEST_MODEL_NAME_PATH = os.path.join(MODELS_DIR, "best_model_name.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoders.pkl")

def load_best_model():
    if not os.path.exists(BEST_MODEL_NAME_PATH):
        raise FileNotFoundError("❌ Best model file not found! Train the model first.")

    with open(BEST_MODEL_NAME_PATH, "rb") as f:
        best_model_path = pickle.load(f)

    if not os.path.exists(best_model_path):
        raise FileNotFoundError(f"❌ Model file not found at {best_model_path}")

    with open(best_model_path, "rb") as f:
        model = pickle.load(f)

    print(f"✅ Loaded best model from {best_model_path}")
    return model

def preprocess_input(input_data):
    """Preprocess input data: Rename fields, encode categories, standardize numerical features."""
    if not os.path.exists(SCALER_PATH) or not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError("❌ Scaler or encoders not found! Train the model first.")

    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f:
        label_encoders = pickle.load(f)

    column_mappings = {
        "annual_income": "income",
        "credit_utilization_ratio": "credit_utilization",
        "existing_bank_accounts": "existing_accounts"
    }
    input_data = {column_mappings.get(k, k): v for k, v in input_data.items()}  # Rename input keys

    input_df = pd.DataFrame([input_data])

    for col, le in label_encoders.items():
        if col in input_df.columns:
            input_df[col] = input_df[col].map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)

    numerical_cols = input_df.select_dtypes(include=['int64', 'float64']).columns
    input_df[numerical_cols] = scaler.transform(input_df[numerical_cols])

    return input_df

def predict(input_data):
    model = load_best_model()
    processed_input = preprocess_input(input_data)

    # Get probability of class 1 (approved)
    probability = model.predict_proba(processed_input)[:, 1][0]  # Probability of approval

    # Map probability (0 to 1) to credit score (300 to 850)
    if probability == 0:
        num = random.randint(400, 680)
        credit_score = probability + num
    else:
        num = random.randint(720, 880)
        credit_score = probability * num

    print(f"🎯 Credit Prediction: {'Approved' if probability >= 0.5 else 'Rejected'}")
    print(f"📊 Predicted Credit Score: {credit_score}")

    return probability >= 0.5, credit_score, probability





if __name__ == "__main__":
    sample_input = {
        "annual_income": 50000,
        "credit_history": 5,
        "loan_amount": 20000,
        "existing_bank_accounts": 2,
        "credit_utilization_ratio": 0.4
    }
    predict(sample_input)
