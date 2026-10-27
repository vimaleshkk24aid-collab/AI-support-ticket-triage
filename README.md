# 🎫 AI Support Ticket Triage & Smart Reply System

An end-to-end AI system that reads a customer support ticket (PDF / DOCX / TXT
or pasted text), **predicts its category**, **scores priority and sentiment**,
**finds the most relevant help-centre articles**, lists the **information the
agent still needs from the customer**, and **drafts a reply** — all through an
interactive Streamlit dashboard backed by a FastAPI REST API.

---

## 1. Project Overview

Support teams lose time reading, sorting and answering repetitive tickets.
This project automates the first-level triage with classical NLP and
Machine Learning:

* A **FastAPI backend** handles file parsing, ML inference and knowledge-base matching.
* A **Streamlit frontend** is a clean dashboard for uploading/pasting a ticket and viewing results.
* All logic lives in dedicated, reusable modules — never inline in the UI.

No database is used. Trained models are stored as `.joblib` files; the
training data and the knowledge base are plain CSV files.

## 2. Problem Statement

Manual ticket triage is slow and inconsistent: urgent issues (fraud, double
charges) can sit in the same queue as simple questions, agents repeatedly ask
customers for the same missing details, and replies depend on who happens to
pick up the ticket.

## 3. Objectives

1. Extract text and structured details from PDF/DOCX/TXT tickets.
2. Predict the ticket category with a trained ML classifier.
3. Determine priority (High / Medium / Low) and customer sentiment.
4. Match the ticket against knowledge-base articles (TF-IDF + cosine similarity).
5. Identify missing information the agent should request.
6. Generate recommendations and an editable draft reply.
7. Present everything in a clear, interactive dashboard.

## 4. Features

- 📄 Upload **PDF, DOCX or TXT** tickets — or paste text directly
- 🧠 ML **category prediction** (8 categories) with confidence chart
- 🚦 Rule-based **priority** detection with human-readable reasons
- 😠 Lexicon-based **sentiment** score with negation handling
- 📚 **Knowledge-base matching** (top 3 articles with step-by-step fixes)
- 🔎 Issue **keyword extraction** from a predefined dictionary
- ❌ **Missing information** detection (order id, email, phone, error details...)
- ✉️ Auto-generated **draft reply** + recommendations
- 📊 **Plotly** visualisations (gauges, bar charts)
- ⬇️ Download the report as TXT or JSON
- 🚫 No database — models and data are plain files

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, Plotly, custom CSS |
| Backend | FastAPI, Uvicorn, Pydantic, python-multipart |
| ML / NLP | scikit-learn, pandas, numpy, TF-IDF, Logistic Regression / calibrated Linear SVM, Joblib |
| Ticket processing | PyMuPDF, python-docx, Regex |
| Storage | CSV (dataset + knowledge base), `.joblib` (models) — **no database** |

## 6. System Architecture

```text
                 STREAMLIT
                FRONTEND/UI
                    │
                    │ HTTP REST API
                    ▼
                 FASTAPI
                 BACKEND
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
  Ticket Processing       ML / NLP Engine
          │                    │
          ▼                    ▼
  Text Extraction      Category Model (TF-IDF + Classifier)
  Field Extraction             │
          │                    │
          └─────────┬──────────┘
                    ▼
     Priority · Sentiment · Keywords
                    │
                    ▼
     Knowledge-Base Matching (cosine similarity)
                    │
                    ▼
     Missing Info · Recommendations · Draft Reply
                    │
                    ▼
                 FASTAPI  ──►  STREAMLIT DASHBOARD
```

## 7. Project Structure

```text
ai-support-ticket-triage/
│
├── frontend/
│   └── streamlit_app.py          # Streamlit dashboard (UI only)
│
├── backend/
│   ├── main.py                   # FastAPI app entrypoint
│   ├── schemas.py                # Pydantic request/response models
│   │
│   ├── routes/
│   │   ├── pipeline.py           # Shared upload validation + analysis pipeline
│   │   ├── prediction.py         # POST /predict
│   │   └── analysis.py           # POST /analyze-ticket, /match-kb, /full-analysis
│   │
│   └── services/
│       ├── ticket_parser.py      # PDF/DOCX/TXT text + field extraction
│       ├── text_processor.py     # Cleaning, tokenisation, stopwords, light stemming
│       ├── keyword_extractor.py  # Issue-keyword dictionary extraction
│       ├── analyzer.py           # Priority + sentiment rules
│       └── matcher.py            # KB TF-IDF index, missing info, reply drafting
│
├── ml/
│   ├── train.py                  # Trains and saves the classifier
│   ├── predict.py                # Loads models once, exposes predict()
│   └── models/                   # classifier / vectorizer / label encoder (.joblib)
│
├── data/
│   ├── dataset.csv               # Training data (ticket_text, category)
│   ├── generate_dataset.py       # Generates the synthetic demo dataset
│   ├── knowledge_base.csv        # Help-centre articles used for matching
│   └── make_knowledge_base.py    # Regenerates the demo knowledge base
│
├── samples/                      # Ready-to-upload demo tickets (TXT/DOCX/PDF)
├── utils/config.py               # Paths, constants, dictionaries, rules
├── tests_smoke.py                # End-to-end smoke test (no server needed)
├── requirements.txt
├── README.md
└── .gitignore
```

## 8. ML Methodology

1. **Preprocessing** (`text_processor.py`): lowercase, strip URLs/emails/punctuation/numbers,
   tokenise, remove stopwords, light suffix stemming. Pure Python — no NLTK downloads needed,
   and the same function is used for training and inference.
2. **Features**: `TfidfVectorizer` (unigrams + bigrams, max 5,000 features).
3. **Modelling**: `LogisticRegression` and a calibrated `LinearSVC` are trained; the one with
   the better weighted F1 on a held-out split is saved (ties go to Logistic Regression).
4. **Persistence**: classifier, vectorizer and label encoder saved with Joblib.
5. **Inference**: `ml/predict.py` loads the artefacts **once** (module-level singleton).

### Rule-based components (transparent, easy to edit in `utils/config.py`)

| Component | How it works |
|---|---|
| Priority | High/medium urgency phrases + negative sentiment + per-category minimum (e.g. fraud is never Low) |
| Sentiment | Positive/negative word lexicon with negation look-back → score from -1 to +1 |
| Keywords | Word-boundary regex over `ISSUE_KEYWORDS` |
| Missing info | `REQUIRED_INFO_BY_CATEGORY` vs. fields found in the ticket |

### Knowledge-base matching

The KB articles are vectorised once at startup (TF-IDF, unigrams + bigrams). Each ticket is
transformed with the same vectoriser and ranked by cosine similarity. The relevance gauge
shows the best article's score: **≥35% strong**, **15–35% partial**, **<15% weak**.

## 9. Dataset

`data/dataset.csv` has two columns:

| Column | Description |
|---|---|
| `ticket_text` | Raw ticket / customer message |
| `category` | One of the 8 categories |

```text
Billing & Payments, Technical Issue, Account Access, Shipping & Delivery,
Refund & Return, Feature Request, Security & Fraud, General Inquiry
```

> ⚠️ **The bundled dataset is synthetic** (560 tickets built from sentence templates), so the
> ~98% validation accuracy is optimistic — the same sentences appear in both the train and
> validation splits. For real use, replace `data/dataset.csv` with genuine labelled tickets
> (same two columns) and re-run `python ml/train.py`. Expect lower, more honest scores.

## 10. Model Training

```bash
python ml/train.py
```

Loads the dataset, preprocesses it, fits TF-IDF, trains both classifiers, prints a
classification report, and saves the best model into `ml/models/`.

## 11. FastAPI API Documentation

Base URL: `http://localhost:8000` — interactive docs at `/docs`.

Endpoints that analyse a ticket accept **either** a multipart `file` **or** a `ticket_text` form field.

### `GET /health`
```json
{ "status": "healthy", "model_loaded": true, "knowledge_base_loaded": true }
```

### `POST /predict`
Returns `category`, `confidence`, `category_probabilities`.

### `POST /analyze-ticket`
Returns extracted ticket info, category, priority, sentiment and issue keywords.

### `POST /match-kb`
JSON body: `{ "ticket_text": "..." }` → relevance score + top articles with steps.

### `POST /full-analysis`
The complete report:

```json
{
  "ticket_info": { "customer_name": "Priya Raman", "email": "priya.r@example.com",
                   "phone": "+91 98765 43210", "order_id": "84521", "amount": "Rs. 2,499",
                   "subject": "Charged twice for order #84521", "device": "android" },
  "category": "Billing & Payments",
  "confidence": 0.66,
  "priority": { "level": "High", "reasons": ["urgency / risk terms: urgently, charged twice"] },
  "sentiment": { "label": "Negative", "score": -1.0 },
  "keywords": ["Double Charge", "Refund"],
  "match_score": 37.2,
  "suggested_articles": [ { "article_id": "KB-102", "title": "I was charged twice for one order", "score": 37.2, "steps": ["..."] } ],
  "matching_keywords": ["Double Charge"],
  "missing_info": [],
  "recommendations": ["Escalate: assign to a senior agent and respond within 1 hour.", "..."],
  "draft_reply": "Hi Priya Raman, ..."
}
```

Example with curl:
```bash
curl -X POST http://localhost:8000/full-analysis -F "file=@samples/ticket_security_hacked.txt"
curl -X POST http://localhost:8000/full-analysis -F "ticket_text=My app keeps crashing with error 500"
```

## 12. Streamlit Setup

The Streamlit app is purely a frontend: it calls the FastAPI backend with `requests` and never
touches the models or file parsing. The backend URL is set in `utils/config.py`
(`API_BASE_URL`, default `http://localhost:8000`, override with the `TICKET_API_URL` env variable).

## 13. How to Run the Project (VS Code)

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) regenerate data and retrain — trained models are already included
python data/generate_dataset.py
python data/make_knowledge_base.py
python ml/train.py

# 5. Start the backend (terminal 1)
uvicorn backend.main:app --reload

# 6. Start the frontend (terminal 2, venv activated)
streamlit run frontend/streamlit_app.py
```

Then open the Streamlit link (usually http://localhost:8501) and upload a file from `samples/`.

Quick check without starting any server:
```bash
python tests_smoke.py
```

## 14. Example

**Input** (`samples/ticket_billing_double_charge.txt`): a customer charged twice for order #84521, writing urgently.

**Output:** Category *Billing & Payments*, **High** priority, **Negative** sentiment, best article
*"I was charged twice for one order"*, and a draft reply with the article's steps.

## 15. Future Enhancements

- Train on a large real-world labelled ticket dataset.
- Replace TF-IDF with Sentence-BERT embeddings for semantic article matching.
- Batch triage: upload many tickets, rank them by priority.
- Add multilingual support (Tamil, Hindi, etc.).
- Integrate with Zendesk / Freshdesk / email inbox APIs.
- Add authentication and ticket history (would introduce a database).
- Use an LLM to polish the draft reply.

## License

Provided as a learning/demo scaffold — adapt it freely.
