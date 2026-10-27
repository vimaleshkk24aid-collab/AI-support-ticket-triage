"""
Central configuration for the AI Support Ticket Triage & Smart Reply System.
All paths, constants and dictionaries live here so the rest of the code
stays clean and easy to change.
"""

import os

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
DATASET_PATH = os.path.join(DATA_DIR, "dataset.csv")
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "knowledge_base.csv")

ML_DIR = os.path.join(BASE_DIR, "ml")
MODELS_DIR = os.path.join(ML_DIR, "models")
CLASSIFIER_PATH = os.path.join(MODELS_DIR, "classifier.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib")
LABEL_ENCODER_PATH = os.path.join(MODELS_DIR, "label_encoder.joblib")

# ---------------------------------------------------------------------------
# API settings
# ---------------------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 8000
API_BASE_URL = os.environ.get("TICKET_API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Upload constraints
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TEXT_CHARS = 20000          # limit for pasted ticket text
TOP_K_ARTICLES = 3              # how many knowledge-base articles to return

# ---------------------------------------------------------------------------
# Ticket categories supported by the classifier
# ---------------------------------------------------------------------------
TICKET_CATEGORIES = [
    "Billing & Payments",
    "Technical Issue",
    "Account Access",
    "Shipping & Delivery",
    "Refund & Return",
    "Feature Request",
    "Security & Fraud",
    "General Inquiry",
]

NOT_DETECTED = "Not detected"

# ---------------------------------------------------------------------------
# Issue keyword dictionary (rule-based "issue term" extractor).
# canonical label -> surface forms matched case-insensitively.
# ---------------------------------------------------------------------------
ISSUE_KEYWORDS = {
    "Payment Failed": ["payment failed", "payment declined", "transaction failed", "card declined"],
    "Double Charge": ["charged twice", "double charged", "duplicate charge", "billed twice"],
    "Invoice": ["invoice", "receipt", "bill"],
    "Subscription": ["subscription", "plan renewal", "auto renewal", "auto-renewal"],
    "Coupon / Discount": ["coupon", "promo code", "discount code", "voucher"],
    "App Crash": ["crash", "crashes", "crashing", "keeps closing", "force close"],
    "Error Message": ["error", "exception", "error code", "something went wrong"],
    "Slow Performance": ["slow", "lag", "lagging", "loading forever", "takes too long"],
    "Login Problem": ["cannot login", "can't login", "unable to login", "login failed", "sign in"],
    "Password Reset": ["password reset", "reset password", "forgot password", "reset link"],
    "Two-Factor Auth": ["2fa", "two-factor", "two factor", "otp", "verification code"],
    "Account Locked": ["account locked", "locked out", "account suspended", "account blocked"],
    "Email Change": ["change email", "update email", "change my email"],
    "Delivery Delay": ["delayed", "not delivered", "late delivery", "still not arrived", "not received"],
    "Tracking": ["tracking", "tracking number", "track my order", "tracking id"],
    "Wrong Item": ["wrong item", "wrong product", "incorrect item", "received the wrong"],
    "Damaged Product": ["damaged", "broken", "defective", "cracked", "torn"],
    "Missing Item": ["missing item", "item missing", "missing from my order", "package empty"],
    "Refund": ["refund", "money back", "reimburse"],
    "Return / Exchange": ["return", "exchange", "replacement", "replace"],
    "Cancellation": ["cancel", "cancellation", "cancelled", "canceled"],
    "Feature Request": ["feature request", "would love to see", "please add", "it would be great if", "suggestion"],
    "Dark Mode": ["dark mode", "night mode"],
    "Integration": ["integration", "integrate", "api access", "webhook"],
    "Export / Import": ["export", "import", "download data", "csv"],
    "Phishing": ["phishing", "suspicious email", "suspicious link", "scam"],
    "Unauthorized Access": ["unauthorized", "unauthorised", "hacked", "compromised", "someone else logged"],
    "Fraud": ["fraud", "fraudulent", "stolen card", "identity theft"],
    "Privacy / Data": ["privacy", "personal data", "data breach", "gdpr", "delete my data"],
    "Pricing Info": ["pricing", "price", "cost", "how much"],
    "Business Hours": ["business hours", "opening hours", "working hours", "support hours"],
    "Contact Info": ["contact", "phone number", "customer care", "talk to someone"],
}

# ---------------------------------------------------------------------------
# Priority rules
# ---------------------------------------------------------------------------
HIGH_PRIORITY_TERMS = [
    "urgent", "urgently", "immediately", "asap", "emergency", "critical",
    "hacked", "unauthorized", "unauthorised", "fraud", "fraudulent",
    "stolen", "data breach", "outage", "down for", "charged twice",
    "double charged", "lost money", "legal action", "lawyer", "chargeback",
    "cannot access", "can't access", "locked out",
]
MEDIUM_PRIORITY_TERMS = [
    "not working", "failed", "error", "crash", "broken", "damaged", "delayed",
    "not received", "wrong item", "refund", "waiting", "still", "again",
    "problem", "issue", "unable",
]
# Categories that never drop below the given priority.
CATEGORY_MIN_PRIORITY = {
    "Security & Fraud": "High",
    "Billing & Payments": "Medium",
    "Account Access": "Medium",
}
PRIORITY_ORDER = ["Low", "Medium", "High"]

# ---------------------------------------------------------------------------
# Sentiment lexicon (small, transparent, rule-based)
# ---------------------------------------------------------------------------
NEGATIVE_WORDS = {
    "angry", "annoyed", "terrible", "horrible", "worst", "awful", "bad", "poor",
    "disappointed", "disappointing", "frustrated", "frustrating", "unacceptable",
    "ridiculous", "useless", "waste", "never", "pathetic", "disgusted", "upset",
    "furious", "scam", "fraud", "broken", "damaged", "late", "delayed", "failed",
    "worried", "stuck", "unhappy", "rude", "slow", "cheated", "problem",
}
POSITIVE_WORDS = {
    "thanks", "thank", "great", "good", "love", "awesome", "excellent", "happy",
    "appreciate", "appreciated", "helpful", "wonderful", "amazing", "pleased",
    "satisfied", "perfect", "nice", "fantastic", "grateful",
}
NEGATIONS = {"not", "no", "never", "don't", "doesn't", "didn't", "isn't", "wasn't", "can't", "cannot", "won't"}

# ---------------------------------------------------------------------------
# Information an agent normally needs to resolve a ticket.
# Used to report "missing information" (the analogue of missing skills).
# ---------------------------------------------------------------------------
REQUIRED_INFO_BY_CATEGORY = {
    "Billing & Payments": ["order_id", "email", "amount"],
    "Technical Issue": ["email", "error_details", "device"],
    "Account Access": ["email", "phone"],
    "Shipping & Delivery": ["order_id", "email", "phone"],
    "Refund & Return": ["order_id", "email", "amount"],
    "Feature Request": ["email"],
    "Security & Fraud": ["email", "phone", "order_id"],
    "General Inquiry": ["email"],
}
INFO_LABELS = {
    "order_id": "Order / transaction ID",
    "email": "Customer email address",
    "phone": "Contact phone number",
    "amount": "Amount involved",
    "error_details": "Exact error message or what happened",
    "device": "Device / browser / app version",
}
DEVICE_TERMS = [
    "android", "iphone", "ios", "windows", "mac", "macos", "linux", "chrome",
    "firefox", "safari", "edge", "browser", "desktop", "mobile", "tablet", "app version",
]

# Section-ish headers sometimes present in ticket documents.
SUBJECT_PREFIXES = ["subject:", "re:", "ticket:", "title:"]
