"""
Kestrel Home — Service Request Routing Pipeline
Variant B Production Model & Prediction Generator
"""

import os
import re
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

CANONICAL_TEAMS = [
    "Installs & Demo",
    "Repairs",
    "Filters & Consumables",
    "Billing",
    "Returns & Replacement",
    "Warranty Claims",
    "Product Advice"
]

TEAM_NAME_MAPPING = {
    "Installations": "Installs & Demo",
    "Installs & Demo": "Installs & Demo",
    "Consumables": "Filters & Consumables",
    "Filters & Consumables": "Filters & Consumables",
    "Repairs": "Repairs",
    "Billing": "Billing",
    "Returns & Replacement": "Returns & Replacement",
    "Warranty Claims": "Warranty Claims",
    "Product Advice": "Product Advice"
}

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Clean Zoho encoding quirks
    text = text.replace("Ã¢â‚¬Â¦", "...").replace("urgÃ©nt", "urgent").replace("Ã©", "e")
    text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€\x9d", '"')
    text = text.lower().strip()
    return text

class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for _, row in X.iterrows():
            text = clean_text(row.get("request_text", ""))
            product = str(row.get("product_family", "")).lower()
            warranty = str(row.get("warranty_status", "")).lower()
            channel = str(row.get("channel", "")).lower()
            
            # Policy rules (§3): disambiguate payment mentions in repairs/installs vs genuine payment failures
            has_payment_word = any(w in text for w in ["paid", "payment", "upi", "emi", "card", "invoice", "refund", "coupon"])
            has_breakdown_word = any(w in text for w in ["not working", "blank", "burnt", "noise", "leaking", "broken", "repair", "smoke", "tripping", "scratch", "damaged"])
            has_install_word = any(w in text for w in ["install", "demo", "installer", "slot", "setup", "turn up", "mounting"])
            has_consumable_word = any(w in text for w in ["filter", "blade", "jar", "brush", "spare", "membrane", "candle"])
            
            intent_tag = ""
            if has_breakdown_word:
                intent_tag = "intent_breakdown "
            elif has_install_word:
                intent_tag = "intent_install "
            elif has_consumable_word:
                intent_tag = "intent_consumables "
            elif has_payment_word:
                intent_tag = "intent_billing "
                
            combined = (
                f"product_{product.replace(' ', '_')} "
                f"warranty_{warranty} "
                f"channel_{channel} "
                f"{intent_tag}"
                f"{text}"
            )
            features.append(combined)
        return features

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    print("[*] Loading datasets...")
    df_train = pd.read_csv(os.path.join(data_dir, "train.csv"))
    df_res = pd.read_csv(os.path.join(data_dir, "resolution_log.csv"))
    df_test = pd.read_csv(os.path.join(data_dir, "test_unlabelled.csv"))
    
    # Merge on request_id
    df = pd.merge(df_train, df_res, on="request_id", how="left")
    
    # Standardize team names
    df["ground_truth"] = df["final_team"].map(TEAM_NAME_MAPPING)
    df["bot_first_team"] = df["first_team"].map(TEAM_NAME_MAPPING)
    
    print(f"[*] Training records loaded: {len(df)}")
    print("[*] Target ground truth distribution:")
    print(df["ground_truth"].value_counts())
    
    pipeline = Pipeline([
        ("extractor", TextFeatureExtractor()),
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=30000,
            sublinear_tf=True,
            strip_accents="unicode"
        )),
        ("clf", LogisticRegression(
            C=3.0,
            max_iter=1000,
            class_weight="balanced",
            solver="lbfgs"
        ))
    ])
    
    # 5-Fold Stratified Cross-Validation on True Operational Resolution
    print("\n[*] Evaluating 5-Fold Cross-Validation on Operational Ground Truth (final_team)...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_true = df["ground_truth"].values
    
    cv_preds = cross_val_predict(pipeline, df, y_true, cv=skf, n_jobs=-1)
    
    op_acc = accuracy_score(y_true, cv_preds)
    bot_acc = accuracy_score(y_true, df["bot_first_team"].values)
    agreement_with_bot = accuracy_score(df["bot_first_team"].values, cv_preds)
    
    print(f"\n================ MODEL EVALUATION RESULTS ================")
    print(f"Our Model Operational Resolution Accuracy:  {op_acc * 100:.2f}%")
    print(f"Legacy Vendor Bot Resolution Accuracy:       {bot_acc * 100:.2f}%")
    print(f"Agreement with Legacy Bot Labels:            {agreement_with_bot * 100:.2f}%")
    print(f"==========================================================\n")
    
    print("[*] Detailed Classification Report (True Operational Resolution):")
    print(classification_report(y_true, cv_preds, target_names=CANONICAL_TEAMS, digits=4))
    
    # Fit full model
    print("[*] Training final model on 100% of historical data...")
    pipeline.fit(df, y_true)
    
    # Save model artifact
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(models_dir, "kestrel_router.pkl"))
    print(f"[+] Model saved to {os.path.join(models_dir, 'kestrel_router.pkl')}")
    
    # Predict on test_unlabelled.csv
    print(f"\n[*] Predicting on {len(df_test)} unlabelled test records...")
    preds = pipeline.predict(df_test)
    
    # Verify exact submission format matching sample_submission.csv
    df_preds = pd.DataFrame({
        "request_id": df_test["request_id"],
        "team": preds
    })
    
    pred_path = os.path.join(base_dir, "predictions.csv")
    df_preds.to_csv(pred_path, index=False)
    print(f"[+] Wrote {len(df_preds)} rows to {pred_path}")
    print("[*] Test predictions class distribution:")
    print(df_preds["team"].value_counts())

if __name__ == "__main__":
    main()
