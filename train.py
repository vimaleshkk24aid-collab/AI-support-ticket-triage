"""
Trains the ticket-category classifier.

Pipeline:
    raw ticket text -> preprocessing -> TF-IDF -> {LogisticRegression, LinearSVC}
    -> choose the better model on a held-out split -> save artifacts.

Run from the project root:
    python ml/train.py
"""

import os
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import config  # noqa: E402
from backend.services.text_processor import preprocess  # noqa: E402


def load_dataset() -> pd.DataFrame:
    if not os.path.exists(config.DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found at {config.DATASET_PATH}. Run `python data/generate_dataset.py` "
            "first, or supply your own dataset.csv with 'ticket_text' and 'category' columns."
        )
    df = pd.read_csv(config.DATASET_PATH)
    if "ticket_text" not in df.columns or "category" not in df.columns:
        raise ValueError("dataset.csv must contain 'ticket_text' and 'category' columns.")
    return df.dropna(subset=["ticket_text", "category"])


def main():
    print("Loading dataset...")
    df = load_dataset()
    print(f"Loaded {len(df)} rows across {df['category'].nunique()} categories.")

    print("Preprocessing ticket text...")
    df["clean_text"] = df["ticket_text"].apply(preprocess)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["category"])

    X_train_text, X_val_text, y_train, y_val = train_test_split(
        df["clean_text"], y, test_size=0.2, random_state=42, stratify=y
    )

    print("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train = vectorizer.fit_transform(X_train_text)
    X_val = vectorizer.transform(X_val_text)

    print("Training Logistic Regression...")
    log_reg = LogisticRegression(C=10, max_iter=1000)
    log_reg.fit(X_train, y_train)
    lr_preds = log_reg.predict(X_val)
    lr_acc, lr_f1 = accuracy_score(y_val, lr_preds), f1_score(y_val, lr_preds, average="weighted")

    print("Training Linear SVM...")
    # Calibrated so the dashboard shows real probabilities, not raw SVM scores.
    svm = CalibratedClassifierCV(LinearSVC(), cv=5)
    svm.fit(X_train, y_train)
    svm_preds = svm.predict(X_val)
    svm_acc, svm_f1 = accuracy_score(y_val, svm_preds), f1_score(y_val, svm_preds, average="weighted")

    print(f"\nLogistic Regression -> accuracy: {lr_acc:.3f}, f1: {lr_f1:.3f}")
    print(f"Linear SVM          -> accuracy: {svm_acc:.3f}, f1: {svm_f1:.3f}\n")

    # On a tie prefer Logistic Regression: it gives real class probabilities.
    if svm_f1 > lr_f1:
        best_model, best_name, best_preds = svm, "Linear SVM", svm_preds
    else:
        best_model, best_name, best_preds = log_reg, "Logistic Regression", lr_preds

    print(f"Selected best model: {best_name}")
    print(classification_report(y_val, best_preds, target_names=label_encoder.classes_))

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    joblib.dump(best_model, config.CLASSIFIER_PATH)
    joblib.dump(vectorizer, config.VECTORIZER_PATH)
    joblib.dump(label_encoder, config.LABEL_ENCODER_PATH)
    print(f"\nSaved classifier    -> {config.CLASSIFIER_PATH}")
    print(f"Saved vectorizer    -> {config.VECTORIZER_PATH}")
    print(f"Saved label encoder -> {config.LABEL_ENCODER_PATH}")


if __name__ == "__main__":
    main()
