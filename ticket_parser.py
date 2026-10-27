"""
Ticket parsing service.

* Extracts raw text from PDF, DOCX and TXT ticket files.
* Pulls structured fields out of the ticket text with regex/heuristics
  (customer name, email, phone, order id, amount, subject, device).

Nothing is guessed: when a field cannot be found it is reported as
"Not detected".
"""

import io
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.config import DEVICE_TERMS, NOT_DETECTED, SUBJECT_PREFIXES  # noqa: E402


class TicketParsingError(Exception):
    """Raised when a ticket file cannot be parsed."""


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise TicketParsingError("PyMuPDF is not installed. Run `pip install pymupdf`.") from exc
    try:
        parts = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                parts.append(page.get_text())
        text = "\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001
        raise TicketParsingError("Failed to read PDF file: it may be corrupted.") from exc
    if not text:
        raise TicketParsingError("No extractable text in the PDF (it may be a scanned image).")
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        import docx  # python-docx
    except ImportError as exc:
        raise TicketParsingError("python-docx is not installed. Run `pip install python-docx`.") from exc
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        paragraphs.append(cell.text)
        text = "\n".join(p for p in paragraphs if p and p.strip()).strip()
    except Exception as exc:  # noqa: BLE001
        raise TicketParsingError("Failed to read DOCX file: it may be corrupted.") from exc
    if not text:
        raise TicketParsingError("The DOCX file appears to be empty.")
    return text


def extract_text_from_txt(file_bytes: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            text = file_bytes.decode(enc).strip()
            if text:
                return text
        except UnicodeDecodeError:
            continue
    raise TicketParsingError("The TXT file is empty or uses an unsupported encoding.")


def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if ext == ".docx":
        return extract_text_from_docx(file_bytes)
    if ext == ".txt":
        return extract_text_from_txt(file_bytes)
    raise TicketParsingError(f"Unsupported file type '{ext}'. Only .pdf, .docx and .txt are supported.")


# ---------------------------------------------------------------------------
# Structured field extraction
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?<![\w#])\+?\(?\d[\d\s\-().]{8,17}\d(?!\w)")
ORDER_PATTERNS = [
    re.compile(r"\b(?:order|booking|transaction|txn|invoice|ticket)\s*(?:id|number|no\.?|#)?\s*[:#\-]?\s*([A-Z]{0,4}-?\d{5,12})\b", re.I),
    re.compile(r"#\s?([A-Z]{0,4}-?\d{5,12})\b"),
    re.compile(r"\b(ORD-?\d{4,12})\b", re.I),
]
AMOUNT_PATTERN = re.compile(r"(?:₹|rs\.?|inr|\$|usd|eur|€|£)\s?\d[\d,]*(?:\.\d{1,2})?", re.I)
NAME_PATTERNS = [
    re.compile(r"^\s*(?:name|customer(?: name)?|from)\s*[:\-]\s*([A-Za-z][A-Za-z .'\-]{1,40})\s*$", re.I | re.M),
    re.compile(r"(?:regards|thanks|thank you|sincerely|best|cheers)[,.\s]*\n+\s*([A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){0,2})\s*$", re.I | re.M),
    re.compile(r"\b(?:my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\b"),
]


def extract_email(text: str) -> str:
    m = EMAIL_PATTERN.search(text)
    return m.group(0) if m else NOT_DETECTED


def extract_phone(text: str) -> str:
    # Remove emails and order ids first so their digits are not mistaken for phones.
    scrubbed = EMAIL_PATTERN.sub(" ", text)
    for pat in ORDER_PATTERNS:
        scrubbed = pat.sub(" ", scrubbed)
    for m in PHONE_PATTERN.finditer(scrubbed):
        candidate = m.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 13:
            return candidate
    return NOT_DETECTED


def extract_order_id(text: str) -> str:
    for pat in ORDER_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1).upper()
    return NOT_DETECTED


def extract_amount(text: str) -> str:
    m = AMOUNT_PATTERN.search(text)
    return m.group(0).strip() if m else NOT_DETECTED


def extract_name(text: str) -> str:
    for pat in NAME_PATTERNS:
        m = pat.search(text)
        if m:
            name = m.group(1).strip().rstrip(".")
            if 1 <= len(name.split()) <= 3:
                return name.title() if name.isupper() or name.islower() else name
    return NOT_DETECTED


def extract_subject(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:8]:
        low = line.lower()
        for prefix in SUBJECT_PREFIXES:
            if low.startswith(prefix):
                subject = line[len(prefix):].strip()
                if subject:
                    return subject[:150]
    if lines:
        first = lines[0]
        if len(first) <= 120 and not EMAIL_PATTERN.search(first):
            return first
    return NOT_DETECTED


def extract_device(text: str) -> str:
    low = text.lower()
    found = [t for t in DEVICE_TERMS if re.search(rf"(?<![a-z]){re.escape(t)}(?![a-z])", low)]
    return ", ".join(found[:3]) if found else NOT_DETECTED


def extract_ticket_info(text: str) -> dict:
    """Extracts all structured fields the system reports."""
    return {
        "customer_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "order_id": extract_order_id(text),
        "amount": extract_amount(text),
        "subject": extract_subject(text),
        "device": extract_device(text),
    }
