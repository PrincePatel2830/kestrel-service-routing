# Kestrel Home — Service Request Routing Engine (Variant B)

Zero-cost, offline, policy-compliant routing service for Kestrel Home Appliances.
Replaces the ₹3.2L/year vendor bot with 83.2% operational resolution accuracy and ₹0 recurring API costs.

---

### Prerequisites
- Python 3.9+
- Standard virtual environment (no GPU required)

---

### Quickstart (Clean Machine Setup)

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_URL>
   cd kestrel_routing
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train model and regenerate `predictions.csv` (Optional - pre-trained model and predictions are included):**
   ```bash
   python train_and_predict.py
   ```
   *Trains the model against resolution ground truth in ~4 seconds and writes 2,178 predictions to `predictions.csv`.*

5. **Start the local service:**
   ```bash
   python app.py
   ```
   Open your browser to: **`http://localhost:8000`**

---

### API Usage

#### `POST /predict`
Takes a single service request JSON payload and returns the destination team, confidence score, and human-readable desk agent reasoning.

**Example Request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "SR510822",
    "channel": "chat",
    "product_family": "Air Fryer",
    "warranty_status": "in_warranty",
    "request_text": "display of air fryer gone blank pls call back"
  }'
```

**Example Response:**
```json
{
  "request_id": "SR510822",
  "predicted_team": "Repairs",
  "confidence": 0.9421,
  "reasons": [
    "Identified physical/hardware defect cues in request text (blank).",
    "Product 'Air Fryer' (in_warranty) requires technician diagnosis.",
    "Model prediction confidence: 94.2%."
  ]
}
```

---

### Key Deliverables in this Repository
- `predictions.csv`: 2,178 test request predictions matching `sample_submission.csv` format (`request_id,team`).
- `train_and_predict.py`: Full training, cross-validation, and prediction pipeline.
- `app.py`: FastAPI server with single-record `/predict` endpoint and agent rationale generator.
- `templates/index.html`: Interactive single-screen UI for Kestrel service desk agents.
- `memo.md`: 1-page non-technical executive memo to Ritu Deshpande.
- `walkthrough_script.md`: 3-minute video walkthrough script.
- `submission_form_answers.md`: Complete answers to all 11 evaluation prompts.
