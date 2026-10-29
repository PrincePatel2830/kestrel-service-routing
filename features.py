"""
Feature extraction and domain cleaning transformers for Kestrel Home routing.
"""

from sklearn.base import BaseEstimator, TransformerMixin

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
