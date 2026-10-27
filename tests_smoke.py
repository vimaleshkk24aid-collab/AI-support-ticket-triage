"""
Quick end-to-end smoke test (no server needed):  python tests_smoke.py
Exercises every endpoint, every upload type and the main error paths.
"""
import glob
import os

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
failures = 0


def check(name, cond, extra=""):
    global failures
    print(("PASS " if cond else "FAIL ") + name, extra)
    failures += 0 if cond else 1


check("health", client.get("/health").json()["model_loaded"])

expected = {
    "ticket_billing_double_charge": "Billing & Payments",
    "ticket_security_hacked": "Security & Fraud",
    "ticket_shipping_delay": "Shipping & Delivery",
    "ticket_feature_request": "Feature Request",
}
for path in sorted(glob.glob("samples/ticket_*")):
    base, ext = os.path.splitext(os.path.basename(path))
    with open(path, "rb") as f:
        r = client.post("/full-analysis", files={"file": (os.path.basename(path), f.read())})
    ok = r.status_code == 200
    d = r.json() if ok else {}
    check(f"full-analysis {base}{ext}", ok and d["category"] == expected[base],
          f"-> {d.get('category')} / {d.get('priority', {}).get('level')} / kb {d.get('match_score')}")

r = client.post("/predict", data={"ticket_text": "my app crashes with error 500"})
check("predict text", r.status_code == 200 and r.json()["category"] == "Technical Issue")
r = client.post("/analyze-ticket", data={"ticket_text": "Please add dark mode"})
check("analyze-ticket", r.status_code == 200 and "Dark Mode" in r.json()["keywords"])
r = client.post("/match-kb", json={"ticket_text": "where is my parcel tracking"})
check("match-kb", r.status_code == 200 and r.json()["suggested_articles"])

check("empty request -> 400", client.post("/full-analysis").status_code == 400)
check("bad extension -> 400", client.post("/full-analysis", files={"file": ("a.exe", b"x")}).status_code == 400)
check("empty file -> 400", client.post("/full-analysis", files={"file": ("a.txt", b"")}).status_code == 400)
check("corrupt pdf -> 400", client.post("/full-analysis", files={"file": ("a.pdf", b"notapdf")}).status_code == 400)
check("empty match-kb -> 400", client.post("/match-kb", json={"ticket_text": "  "}).status_code == 400)
check("gibberish ok", client.post("/full-analysis", data={"ticket_text": "zzzz qqqq"}).status_code == 200)

print("\nALL PASSED" if not failures else f"\n{failures} FAILED")
raise SystemExit(failures)
