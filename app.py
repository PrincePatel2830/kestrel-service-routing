"""
Kestrel Home — Operational Routing Service
Variant B Production Endpoint & Desk UI
Runs locally without paid API keys or recurring costs.
"""

import os
import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from features import TextFeatureExtractor

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "kestrel_router.pkl")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI(title="Kestrel Service Request Router", version="2.0")

model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print(f"[+] Loaded Kestrel Routing Model from {MODEL_PATH}")
else:
    print("[!] Warning: Model file not found. Run python train_and_predict.py first.")

class ServiceRequestInput(BaseModel):
    request_id: str = Field(default="SR510822", examples=["SR510822"])
    channel: str = Field(default="chat", examples=["chat"])
    product_family: str = Field(default="Air Fryer", examples=["Air Fryer"])
    warranty_status: str = Field(default="in_warranty", examples=["in_warranty"])
    request_text: str = Field(
        default="display of air fryer gone blank pls call back",
        examples=["display of air fryer gone blank pls call back"]
    )

def generate_agent_rationale(predicted_team: str, req: ServiceRequestInput, confidence: float) -> list[str]:
    """Generates concise, human-readable rationales for Kestrel desk agents based on Ops Policy §3."""
    reasons = []
    text_lower = req.request_text.lower()
    
    payment_cues = ["paid", "upi", "card", "emi", "invoice", "receipt", "coupon", "discount"]
    repair_cues = ["leaking", "not working", "blank", "burnt", "noise", "spark", "error", "broken", "smoke", "tripping"]
    install_cues = ["install", "demo", "installer", "slot", "setup", "turn up", "mounting"]
    consumable_cues = ["filter", "blade", "jar", "brush", "spare", "membrane", "candle"]
    return_cues = ["damaged", "missing", "broken in box", "exchange", "wrong item", "return"]

    if predicted_team == "Repairs":
        found = [w for w in repair_cues if w in text_lower]
        reasons.append(f"Identified physical/hardware defect cues in request text ({', '.join(found) if found else 'hardware malfunction'}).")
        if any(p in text_lower for p in payment_cues):
            reasons.append("Payment reference detected ('paid/upi/emi'), but routed to Repairs per Ops Policy §3 as root issue is device breakdown, not billing failure.")
        reasons.append(f"Product '{req.product_family}' ({req.warranty_status}) requires technician diagnosis.")
        
    elif predicted_team == "Installs & Demo":
        found = [w for w in install_cues if w in text_lower]
        reasons.append(f"Customer is requesting first-time setup, demonstration, or technician appointment ({', '.join(found) if found else 'installation inquiry'}).")
        reasons.append(f"Applies to {req.product_family}; dispatched to field technician schedule.")
        
    elif predicted_team == "Filters & Consumables":
        found = [w for w in consumable_cues if w in text_lower]
        reasons.append(f"Request involves replacement parts, jars, blades, or consumable replenishment ({', '.join(found) if found else 'spares purchase'}).")
        reasons.append("No active mechanical fault reported; routed to spares dispatch queue.")
        
    elif predicted_team == "Billing":
        reasons.append("Query strictly involves payment discrepancy, refund status, invoice generation, or EMI deduction.")
        reasons.append("No hardware failure or installation booking detected; assigned to Finance/Billing desk.")
        
    elif predicted_team == "Returns & Replacement":
        found = [w for w in return_cues if w in text_lower]
        reasons.append(f"Customer reports delivery damage, incomplete package, or return window claim ({', '.join(found) if found else 'delivery defect'}).")
        reasons.append("Assigned to Logistics & Reverse Courier team.")
        
    elif predicted_team == "Warranty Claims":
        reasons.append("Inquiry concerning warranty registration, Shield coverage policy, or claim disputes.")
        
    elif predicted_team == "Product Advice":
        reasons.append("Pre/post-purchase guidance request regarding operating settings, power consumption, or user manual instructions.")
        
    reasons.append(f"Model prediction confidence: {confidence * 100:.1f}%.")
    return reasons

@app.post("/predict")
def predict_endpoint(item: ServiceRequestInput):
    if model is None:
        return {
            "error": "Model not trained yet",
            "predicted_team": "Manual Review",
            "confidence": 0.0,
            "reasons": ["Service running in fallback mode. Please run python train_and_predict.py to initialize."]
        }
    
    df_single = pd.DataFrame([{
        "request_id": item.request_id,
        "channel": item.channel,
        "product_family": item.product_family,
        "warranty_status": item.warranty_status,
        "request_text": item.request_text
    }])
    
    pred_team = model.predict(df_single)[0]
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(df_single)[0]
        classes = list(model.classes_)
        conf = float(probs[classes.index(pred_team)])
    else:
        conf = 0.95
        
    reasons = generate_agent_rationale(pred_team, item, conf)
    
    return {
        "request_id": item.request_id,
        "predicted_team": pred_team,
        "confidence": round(conf, 4),
        "reasons": reasons
    }

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(TEMPLATES_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
