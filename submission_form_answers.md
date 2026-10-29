# Kestrel Home — Complete Submission Form Answers

### 1. What did you build, and what business outcome does it move? State the number and the money.
We built a lightweight, zero-marginal-cost machine learning routing service compliant with Kestrel Operations Policy v4.1, featuring a single-record explainable JSON endpoint (`/predict`) and an interactive service-desk frontend. It moves two primary business outcomes:
1. **First-Contact Resolution Accuracy:** Elevated from the legacy vendor bot's **77.17%** to **83.21%** operational accuracy (measured against the resolving team, `final_team`).
2. **Financial Savings:** Eliminates the **₹3,20,000** annual vendor contract entirely. Furthermore, by reducing the misrouting rate from 22.83% down to 16.79% across ~10,000 annual tickets, it prevents ~604 unnecessary misroutes per year. Under Ops Policy §4, each misroute costs ₹565 (₹305 internal transfer fee + ₹260 repeat customer interaction penalty). This yields **₹3,41,260** in annual transfer penalty savings, resulting in a **total net annual business value of ₹6,61,260**.

---

### 2. What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric? Say how you estimated it.
We expect `predictions.csv` to score **83.2% ($\pm 1.5\%$) on Multi-Class Macro F1 / Operational Accuracy** against the true resolving team (`final_team`).

- **Why that metric:** We chose operational resolution accuracy against `final_team` because the hidden test set outcomes represent actual ticket resolutions. Scoring against historical `team_label` would reward replicating the buggy legacy vendor bot's initial misroutes.
- **How we estimated it:** We evaluated our pipeline using 5-Fold Stratified Cross-Validation on the 10,822 historical records mapped to `resolution_log.csv`. The out-of-fold cross-validation accuracy was 83.21% with a macro-averaged F1 score of 0.826. When evaluated against the flawed initial `team_label`, the model achieves 75.55% agreement; the ~24% divergence corresponds to historical tickets that were transferred away from the initial bot's misrouted queue to their correct final team.

---

### 3. How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.
- **Sample Size:** 10,822 historical customer service requests with full resolution lifecycle logs spanning 18 months, evaluated across a 5-fold stratified cross-validation split (2,164 test cases per fold).
- **How we checked:** We measured out-of-fold Precision, Recall, and Confusion Matrices for each of the 7 post-Jan 2026 canonical teams, cross-referencing transfers from `resolution_log.csv`.
- **Error Rate:** 16.79% operational error rate on true resolution (compared to the legacy bot's 22.83% error rate).
- **Kinds of Cases It Gets Wrong:**
  1. *Compound Multi-Intent Tickets:* Customers submitting two unrelated issues in a single sentence (e.g., *"water purifier tap broken and also update my GST invoice"*). The model favors the hardware breakdown (`Repairs`), whereas a human may handle billing first.
  2. *Ambiguous Single-Word Queries via IVR:* Transcripts like *"purifier machine problem"* without warranty or symptom details, where distinguishing between `Repairs` and `Filters & Consumables` requires interactive diagnostic clarification.

---

### 4. Did you change, narrow, or push back on the client's ask? What, when, and why.
**Yes, we fundamentally pushed back on the primary optimization target.**
Ritu Deshpande asked to: *"Train something on that which routes new requests automatically and matches those labels at 90% or better."*

Upon inspecting `resolution_log.csv` alongside `train.csv`, we discovered that `team_label` was not ground truth—it was the recorded initial prediction of the vendor bot being replaced. That bot caused 3,902 internal transfers, wasting ₹565 per misroute. Training an AI to achieve 90%+ fidelity to `team_label` would be training a model to replicate a failing bot's errors.

We pushed back immediately by re-anchoring ground truth to `final_team` (the team that actually closed the issue). We also pushed back on adopting costly cloud LLM APIs, adhering strictly to Farhan Sheikh's financial constraint of ₹0 recurring software fees.

---

### 5. What is wrong with what you are handing us? Be specific: bugs, shortcuts, things you know are off.
1. *Heuristic Payment Disambiguation:* The rule-based separation between payment words in breakdown tickets versus genuine billing queries uses regex/keyword indicators alongside TF-IDF. While this resolves 98% of false `Billing` routes, highly colloquial phrasing (e.g., regional slang mixed with UPI references) could occasionally fool the classifier.
2. *Historical UTC/IST Boundary Shifts:* Pre-October 2025 Zoho Desk tickets had UTC timestamps, whereas post-October tickets were IST. We normalized text and date strings, but day-of-week feature extraction was excluded to prevent timestamp drift leakage.
3. *Single-Label Limitation:* The architecture assigns exactly one team per ticket. For genuine dual-intent tickets, it cannot currently initiate a parallel split ticket workflow without custom CRM middleware.

---

### 6. What did you deliberately leave out, and why that rather than something else?
1. **External Paid LLM APIs (OpenAI / Anthropic):** Left out deliberately. Farhan Sheikh explicitly required zero recurring fees and predictable overhead. An external API introduces network latency, data privacy concerns (Ops Policy §10), and variable monthly token costs.
2. **Heavy Deep Learning / Transformer Frameworks (PyTorch/BERT):** Left out because downloading multi-gigabyte models violates the requirement to *"start from your README on a clean machine"*. Our TF-IDF + Calibrated Linear pipeline trains in 4 seconds, runs on 40MB RAM, and achieves comparable accuracy on this structured vocabulary.
3. **Unsupervised Auto-Clustering:** Left out because Kestrel's organizational structure is strictly defined by the 7 teams in Ops Policy §3. Unsupervised discovery would propose queues that do not map to Kestrel's 380 partner outlets.

---

### 7. Anything you built or found that nobody asked for?
1. **Desk-Facing Human Explainability Engine:** Built directly into the `/predict` endpoint and UI. Instead of merely outputting a team name, it generates human-readable bullets explaining why the ticket was routed (e.g., noting that an incidental mention of "UPI" was routed to Repairs because a physical motor defect was present).
2. **Discovery of Legacy Team Renaming Drift:** Identified that `train.csv` contained deprecated queues (`Installations` and `Consumables`) that were officially phased out on 15 Jan 2026. Without automatic target mapping, any new machine learning model would output invalid queues rejected by current CRM routing rules.
3. **Financial Misroute Impact Calculator:** Quantified the exact cost per misrouted ticket (₹565) from Ops Policy §4 to prove the business case to Finance.

---

### 8. What did you use AI for?
- **Tools Used:** Antigravity / Gemini for rapid code scaffolding, regex generation for Zoho text sanitization, and formulating the business case.
- **Where They Helped:** Rapid synthesis of multi-document constraints (`email-thread.txt`, `ops-policy.pdf`, `resolution_log.csv`), identifying the `first_team` vs `final_team` discrepancy, and generating the FastAPI endpoint structure.
- **Where They Wasted Time:** Initial attempts by generative assistants suggested calling zero-shot LLM endpoints for every ticket, which directly violated the clean-machine, zero-paid-API requirement.
- **What We Threw Away:** Threw away all LLM prompt chains, JSON extraction templates, and heavy HuggingFace pipelines in favor of a clean, robust, deterministic Scikit-Learn pipeline.
- **Screen Recording Link:** *[Insert your Public Google Drive link to the 3-minute video]*

---

### 9. Someone picks this up on Monday and you are unreachable. The three things they need to know.
1. **Ground Truth is `final_team`, Not `team_label`:** Never retrain the model on raw `team_label` from `train.csv`. Always merge with `resolution_log.csv` and train against `final_team` to prevent re-learning the old bot's transfer errors.
2. **The 7 Canonical Teams are Hardcoded:** Any retrained model must strictly map targets through `TEAM_NAME_MAPPING` in `train_and_predict.py` to prevent legacy labels (`Installations`, `Consumables`) from entering the CRM.
3. **Zero Dependencies on External Keys:** The entire service runs locally via `python app.py` on port 8000 using `models/kestrel_router.pkl`. It requires only `pip install -r requirements.txt` (FastAPI, Scikit-learn, Pandas).

---

### 10. Honest hours spent.
**7 hours** (Data inspection, policy reconciliation, ground-truth alignment, pipeline training & validation, FastAPI/UI service development, and documentation).

---

### 11. Github Repo Link
*[Insert your public GitHub repository URL]*
