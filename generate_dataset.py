"""
Generates a synthetic data/dataset.csv (ticket_text, category) for demo
training. In a real project replace dataset.csv with genuine, labelled
support tickets (same two columns).

To make the demo less trivial than "keyword lookup", every ticket mixes:
  * a greeting + 1-3 core sentences from its own category,
  * shared filler / emotional sentences used by ALL categories,
  * with ~12% probability, one sentence borrowed from ANOTHER category
    (customers often mention two problems at once),
  * optional order ids / amounts so numbers don't leak the label.

Run:  python data/generate_dataset.py
"""

import csv
import os
import random

random.seed(42)

CORE = {
    "Billing & Payments": [
        "My payment failed but the money was deducted from my bank account.",
        "I was charged twice for the same order and need the extra amount reversed.",
        "The card was declined even though I have enough balance.",
        "I did not receive an invoice for my last payment.",
        "Please send me a GST invoice for my purchase.",
        "My subscription renewed automatically and I was billed again without notice.",
        "The coupon code is not applying at checkout and I am being charged the full price.",
        "There is a duplicate charge on my credit card statement for this month.",
        "Payment through UPI keeps failing at the last step.",
        "I want to cancel my subscription so I am not billed next month.",
        "The bill amount is higher than the price shown on the website.",
    ],
    "Technical Issue": [
        "The app keeps crashing every time I open the dashboard.",
        "I get an error message saying something went wrong when I try to save.",
        "The website is extremely slow and keeps loading forever.",
        "The page shows a blank screen after the latest update.",
        "The mobile app freezes on the home screen and I have to force close it.",
        "I am seeing error code 500 whenever I upload a file.",
        "Notifications stopped working on my phone after I updated the app.",
        "The search feature returns no results even for items I know exist.",
        "Videos do not play on my laptop and the player just spins.",
        "The app lags badly on my Android phone and takes too long to respond.",
        "Export to CSV fails with an exception and nothing downloads.",
    ],
    "Account Access": [
        "I forgot my password and the reset link is not arriving in my inbox.",
        "I cannot login to my account, it says invalid credentials.",
        "My account got locked after too many failed attempts.",
        "I am not receiving the OTP verification code on my phone.",
        "Please help me change the email address linked to my account.",
        "I am locked out of my account and need access back.",
        "Two-factor authentication code is rejected every time I try to sign in.",
        "I want to update my registered mobile number but cannot verify.",
        "The password reset email link has expired before I could use it.",
        "My account was suspended and I do not know why.",
        "I created a new account but cannot sign in with my details.",
    ],
    "Shipping & Delivery": [
        "My order has not been delivered yet and it is past the promised date.",
        "The tracking page has not updated for four days.",
        "The courier marked my package as delivered but I never received it.",
        "I want to change the delivery address for my order.",
        "My parcel is delayed and I need it urgently this week.",
        "The package arrived damaged with the outer box crushed.",
        "I received the wrong item, a different product from what I ordered.",
        "One item is missing from my order, the box was incomplete.",
        "The delivery agent keeps calling the wrong number and I missed the delivery.",
        "Can you tell me when my shipment will reach my city?",
        "The tracking number shows no movement after it left the warehouse.",
    ],
    "Refund & Return": [
        "I returned the product two weeks ago and I still have not received my refund.",
        "I would like to return this item because it does not fit.",
        "Please process an exchange for a different size.",
        "I want to cancel my order and get my money back.",
        "The refund was promised in five days but nothing has come into my account.",
        "The product is defective and I would like a replacement or refund.",
        "How long does a refund take to reach my card?",
        "The return pickup never happened even though I scheduled it.",
        "I received a partial refund but the full amount was deducted.",
        "Please refund the amount, the item does not match the description.",
        "My return was marked as rejected without any explanation.",
    ],
    "Feature Request": [
        "It would be great if you could add a dark mode to the web app.",
        "I would love to see integration with Google Calendar.",
        "Please add the ability to export reports as PDF.",
        "A feature request: allow multiple users to share one workspace.",
        "Could you add a bulk upload option for products?",
        "My suggestion is to add keyboard shortcuts for common actions.",
        "It would be helpful to have an API so we can connect our own tools.",
        "Please consider adding support for more languages in the app.",
        "I would like a way to customise the dashboard layout.",
        "Can you add a weekly summary email as an optional feature?",
        "Having a mobile widget would make the product much more useful.",
    ],
    "Security & Fraud": [
        "I think my account was hacked, I see orders I never placed.",
        "Someone else logged in to my account from another country.",
        "I received a suspicious email asking for my password, it looks like phishing.",
        "There is an unauthorized transaction on my card linked to your site.",
        "I am worried about a fraudulent charge I did not make.",
        "My personal data may have been compromised, please investigate.",
        "A scam message claiming to be from your company asked for my OTP.",
        "I want to delete all my personal data from your systems.",
        "Please block my account immediately, I suspect identity theft.",
        "I got a security alert about a login from a device I do not own.",
        "A fake website is using your name to collect card details.",
    ],
    "General Inquiry": [
        "What are your support hours and how can I talk to someone?",
        "Can you share the pricing details for the yearly plan?",
        "Do you offer student discounts on your plans?",
        "How does your service work for a small business?",
        "Which payment methods do you accept?",
        "Is there a phone number I can call for customer care?",
        "I would like to know more about what is included in the premium plan.",
        "Do you ship internationally or only within the country?",
        "Where can I find your terms and conditions?",
        "Could you explain the difference between the basic and pro plans?",
        "Do you have an office I can visit in person?",
    ],
}

OPENERS = [
    "Hello team,", "Hi support,", "Dear customer care,", "Good morning,",
    "Hi,", "Hello,", "To whom it may concern,", "",
]
# Shared by ALL categories so they carry no label information.
FILLER = [
    "I have been a customer for about a year.",
    "I contacted you earlier but did not get a clear answer.",
    "Please let me know what I should do next.",
    "I would appreciate a quick response.",
    "I am using the service for my work every day.",
    "Kindly look into this at the earliest.",
    "This is the first time I am facing something like this.",
    "I tried again this morning and nothing changed.",
    "A friend recommended your service to me.",
    "I am writing from my personal account.",
]
EMOTION_NEG = [
    "This is really frustrating.", "I am very disappointed with this experience.",
    "This is unacceptable.", "I am quite upset about this.",
]
EMOTION_POS = [
    "Thanks for your help so far.", "I really like your product otherwise.",
    "I appreciate your support team.",
]
CLOSERS = ["Thanks,", "Regards,", "Thank you,", "Best,", ""]
NAMES = ["Arun", "Priya", "Karthik", "Divya", "Rahul", "Sneha", "Vikram", "Meena", "Ravi", "Anitha", "John", "Sara"]


def make_ticket(category: str) -> str:
    parts = []
    opener = random.choice(OPENERS)
    if opener:
        parts.append(opener)

    core = random.sample(CORE[category], k=random.choice([1, 2, 2, 3]))
    parts.extend(core)

    if random.random() < 0.12:
        other = random.choice([c for c in CORE if c != category])
        parts.append(random.choice(CORE[other]))

    if random.random() < 0.55:
        parts.append(random.choice(FILLER))
    if random.random() < 0.3:
        parts.append(random.choice(EMOTION_NEG))
    elif random.random() < 0.2:
        parts.append(random.choice(EMOTION_POS))
    if random.random() < 0.4:
        parts.append(f"My order number is ORD-{random.randint(10000, 99999)}.")
    if random.random() < 0.2:
        parts.append(f"The amount is Rs. {random.randint(199, 9999)}.")

    closer = random.choice(CLOSERS)
    if closer:
        parts.append(f"{closer} {random.choice(NAMES)}")
    return " ".join(parts)


def main():
    rows = []
    per_category = 70
    for category in CORE:
        for _ in range(per_category):
            rows.append({"ticket_text": make_ticket(category), "category": category})
    random.shuffle(rows)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket_text", "category"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
