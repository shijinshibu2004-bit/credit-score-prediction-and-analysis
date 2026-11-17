import pandas as pd
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

MODELS_DIR = "models"
BEST_MODEL_NAME_PATH = os.path.join(MODELS_DIR, "best_model_name.pkl")
os.makedirs(MODELS_DIR, exist_ok=True)

def load_data(file_path):
    return pd.read_csv(file_path)

def preprocess_data(df):
    """Preprocess data: Rename columns, encode categories, standardize numerical features."""
    column_mappings = {
        "annual_income": "income",
        "credit_utilization_ratio": "credit_utilization",
        "existing_bank_accounts": "existing_accounts"
    }
    df.rename(columns=column_mappings, inplace=True)

    # Drop credit_status from features
    target_column = "credit_status"
    if target_column in df.columns:
        y = df[target_column]
        X = df.drop(columns=[target_column])
    else:
        y = None
        X = df

    label_encoders = {}
    categorical_cols = X.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        label_encoders[col] = le

    scaler = StandardScaler()
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns
    X[numerical_cols] = scaler.fit_transform(X[numerical_cols])

    with open(os.path.join(MODELS_DIR, "label_encoders.pkl"), "wb") as f:
        pickle.dump(label_encoders, f)
    with open(os.path.join(MODELS_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)

    return X, y, label_encoders, scaler

def train_models():
    df = load_data("data/credit_data.csv")
    X, y, label_encoders, scaler = preprocess_data(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    smote = SMOTE(random_state=42)
    X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)

    with open(os.path.join(MODELS_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "label_encoders.pkl"), "wb") as f:
        pickle.dump(label_encoders, f)

    models = {
        "logistic_regression": LogisticRegression(),
        "decision_tree": DecisionTreeClassifier(max_depth=5),
        "random_forest": RandomForestClassifier(n_estimators=100, max_depth=10)
    }

    best_model = None
    best_accuracy = 0
    best_model_path = None

    for name, model in models.items():
        print(f"\n🚀 Training {name}...")
        model.fit(X_train_bal, y_train_bal)
        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        print(f"{name} Accuracy: {accuracy:.2f}")
        print(classification_report(y_test, y_pred))

        model_path = os.path.join(MODELS_DIR, f"{name}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = model_path

    print(f"\n🏆 Best model saved: {best_model}")

    with open(BEST_MODEL_NAME_PATH, "wb") as f:
        pickle.dump(best_model, f)

if __name__ == "__main__":
    train_models()
