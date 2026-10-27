"""Creates sample ticket files (TXT, DOCX, PDF) in samples/ for quick demos."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TICKETS = {
    "ticket_billing_double_charge": """Subject: Charged twice for order #84521
Name: Priya Raman

Hi team,
I was charged twice for my order #84521 (Rs. 2,499) and this is unacceptable.
Please refund the extra amount urgently.
My email is priya.r@example.com and my phone is +91 98765 43210.
I used the Android app.

Regards,
Priya Raman
""",
    "ticket_security_hacked": """Subject: Someone hacked my account!
Name: Karthik S

Hello,
I think my account was hacked. I see orders I never placed and an unauthorized
transaction on my card. Please block my account immediately.
Email: karthik.s@example.com

Thanks,
Karthik S
""",
    "ticket_shipping_delay": """Subject: Order not delivered yet
Hi, my order ORD-55231 has not been delivered and the tracking page has not
updated for four days. It is delayed and I need it this week.
I am a bit worried. Please let me know when it will arrive.

Thanks,
Divya
""",
    "ticket_feature_request": """Subject: Feature request - dark mode
Hi team, I really like your product. It would be great if you could add a dark
mode to the web app. Thanks for your help so far!
meena@example.com

Best,
Meena
""",
}


def main():
    import docx
    import fitz  # PyMuPDF

    for name, body in TICKETS.items():
        with open(os.path.join(HERE, f"{name}.txt"), "w", encoding="utf-8") as f:
            f.write(body)

    # One DOCX and one PDF so every upload type has a demo file.
    d = docx.Document()
    for line in TICKETS["ticket_shipping_delay"].splitlines():
        d.add_paragraph(line)
    d.save(os.path.join(HERE, "ticket_shipping_delay.docx"))

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 60), TICKETS["ticket_billing_double_charge"], fontsize=11)
    pdf.save(os.path.join(HERE, "ticket_billing_double_charge.pdf"))
    pdf.close()
    print("Sample tickets written to", HERE)


if __name__ == "__main__":
    main()
