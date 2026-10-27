"""
Writes data/knowledge_base.csv -- a small demo help-centre used for
ticket <-> article matching. Replace it with your company's real FAQ /
help articles (same columns: article_id,title,category,content,steps).
Steps are separated with the '|' character.

Run:  python data/make_knowledge_base.py
"""

import csv
import os

ARTICLES = [
    # --- Billing & Payments ---------------------------------------------
    ("KB-101", "Why was my payment declined or failed?", "Billing & Payments",
     "Payments can fail when the card has insufficient funds, the billing address does not match the bank record, the card has expired, or your bank blocks online transactions. Failed payments are not charged.",
     "Check the card number, expiry date and CVV|Confirm the billing address matches your bank records|Try another card or UPI / net banking|Ask your bank to allow online transactions"),
    ("KB-102", "I was charged twice for one order", "Billing & Payments",
     "A duplicate charge is usually a temporary authorisation hold that is released automatically within 5 to 7 working days. If both amounts are fully debited, we reverse the extra charge once the transaction id is verified.",
     "Share both transaction ids and the debit dates|Wait 5-7 working days for pending holds to release|We reverse confirmed duplicate debits to the original payment method"),
    ("KB-103", "How to download an invoice or receipt", "Billing & Payments",
     "Invoices are generated after every successful payment. You can download a PDF invoice from your order history, and GST invoices can be requested with your business tax details.",
     "Open Account > Orders|Select the order and click Download Invoice|For a GST invoice, add your GST number and request again"),
    ("KB-104", "Manage, pause or cancel a subscription", "Billing & Payments",
     "Subscriptions renew automatically on the billing date. You can pause or cancel any time from billing settings; access continues until the end of the paid period and no further renewals are charged.",
     "Go to Settings > Billing > Subscription|Choose Pause or Cancel plan|Check the confirmation email for the end date"),

    # --- Technical Issue ----------------------------------------------------
    ("KB-201", "The app crashes or closes unexpectedly", "Technical Issue",
     "Crashes are commonly caused by an outdated app version, low device storage or corrupted cache. Updating the app and clearing the cache fixes most crashes.",
     "Update to the latest app version|Clear the app cache and restart the device|Free up at least 1 GB of storage|Reinstall the app if the crash continues"),
    ("KB-202", "Troubleshooting error messages and error codes", "Technical Issue",
     "When you see an error code or a something went wrong message, note the exact code, the time it happened and what you were doing. Most errors are temporary server or network issues.",
     "Refresh the page or restart the app|Check your internet connection|Try a different browser or device|Send us the exact error code with a screenshot"),
    ("KB-203", "The website or app is slow or loading forever", "Technical Issue",
     "Slow loading can be caused by a weak network, too many open tabs, an outdated browser or heavy browser extensions. Switching networks and clearing browser data usually helps.",
     "Switch between Wi-Fi and mobile data|Clear browser cache and cookies|Disable heavy browser extensions|Update your browser to the latest version"),
    ("KB-204", "Notifications or emails are not arriving", "Technical Issue",
     "If notifications or emails are missing, check app notification permissions and your spam folder. Add our sender address to your contacts so messages are not filtered.",
     "Enable notifications in phone settings|Check spam and promotions folders|Add our sender address to contacts"),

    # --- Account Access ---------------------------------------------------
    ("KB-301", "How to reset a forgotten password", "Account Access",
     "Use the Forgot password link on the login page. A reset link is sent to your registered email and stays valid for 30 minutes. Check spam if it does not arrive.",
     "Click Forgot password on the login page|Enter your registered email|Open the reset link within 30 minutes|Choose a new strong password"),
    ("KB-302", "My account is locked or suspended", "Account Access",
     "Accounts are locked automatically after several failed login attempts to keep them safe. The lock lifts after 30 minutes, or you can unlock it immediately by verifying your identity.",
     "Wait 30 minutes and try again|Or use Unlock account and verify with an OTP|Contact support if the account stays suspended"),
    ("KB-303", "I am not receiving the OTP or verification code", "Account Access",
     "Verification codes can be delayed by network issues or blocked by do-not-disturb filters. Codes expire in 10 minutes and a new one can be requested after 60 seconds.",
     "Check phone signal and DND settings|Wait 60 seconds and request a new code|Make sure your registered phone number is correct"),
    ("KB-304", "Change the email address or phone number on my account", "Account Access",
     "You can change your email or phone number from profile settings after verifying with a one-time code sent to the current contact detail.",
     "Open Profile > Contact details|Enter the new email or phone number|Verify using the code sent to the current detail"),

    # --- Shipping & Delivery -------------------------------------------
    ("KB-401", "Where is my order? Tracking and delivery delays", "Shipping & Delivery",
     "Use the tracking id from your shipping confirmation to follow your parcel. Delays can occur due to weather, high demand or an incorrect address. Most delayed parcels arrive within 3 working days of the promised date.",
     "Open Orders > Track order or use the tracking id|Check the courier site for the latest scan|Contact us if there is no movement for 3 days"),
    ("KB-402", "Marked delivered but I did not receive my package", "Shipping & Delivery",
     "If a parcel shows delivered but is missing, check with neighbours, building security and the delivery location. We open an investigation with the courier within 48 hours.",
     "Check neighbours, reception and safe places|Wait 24 hours as scans may be early|Report it so we can raise a courier investigation"),
    ("KB-403", "Change the delivery address after ordering", "Shipping & Delivery",
     "The address can be changed only before the order is shipped. After dispatch, contact the courier with your tracking id to request a redirect.",
     "Open the order and choose Edit address if available|After dispatch, contact the courier with the tracking id|Contact support for urgent changes"),
    ("KB-404", "Package arrived damaged or with an item missing", "Shipping & Delivery",
     "Report damaged, wrong or missing items within 7 days of delivery with photos of the product and the outer packaging. We arrange a free replacement or a refund after verification.",
     "Take photos of the item, label and outer box|Report within 7 days of delivery|Choose replacement or refund"),

    # --- Refund & Return ----------------------------------------------------
    ("KB-501", "Refund status and timelines", "Refund & Return",
     "Refunds are issued to the original payment method after the returned item passes quality checks. Cards take 5 to 7 working days, UPI and wallets 1 to 3 working days.",
     "Open Orders > Refund status|Allow 5-7 working days for cards|Share the order id if the refund is overdue"),
    ("KB-502", "How to return or exchange a product", "Refund & Return",
     "Most products can be returned or exchanged within 10 days of delivery if unused and in original packaging. Pickup is scheduled automatically once you raise the return request.",
     "Open the order and click Return or Exchange|Select the reason and pickup slot|Pack the item in its original packaging"),
    ("KB-503", "Cancel an order before it ships", "Refund & Return",
     "Orders can be cancelled free of charge until they are shipped. Prepaid amounts are refunded automatically after cancellation.",
     "Open Orders and select Cancel order|Choose the reason|Refund is initiated automatically for prepaid orders"),
    ("KB-504", "Refund not received after return pickup", "Refund & Return",
     "If the refund is delayed past the stated time, it is often waiting for the bank to post the credit. We can share an acquirer reference number to help your bank trace it.",
     "Confirm the item was picked up and received at our warehouse|Request the refund reference number|Show it to your bank to trace the credit"),

    # --- Feature Request ----------------------------------------------------
    ("KB-601", "How to submit a feature request", "Feature Request",
     "We read every suggestion. Describe the problem you want solved and how you would use the feature. Popular requests are reviewed monthly by the product team and added to the public roadmap.",
     "Describe the problem and your use case|Vote for similar existing requests|Follow the public roadmap for updates"),
    ("KB-602", "Dark mode and display customisation", "Feature Request",
     "Dark mode is available on mobile apps from Settings > Appearance. Web dark mode and further theme customisation are planned on the roadmap.",
     "Open Settings > Appearance|Choose Dark or System default|Follow the roadmap for web dark mode"),
    ("KB-603", "API access, integrations and data export", "Feature Request",
     "Public API keys and webhooks are available on the Business plan. Data can be exported as CSV from Settings > Data. Additional integrations are prioritised based on customer votes.",
     "Create an API key in Settings > Developer|Use Settings > Data > Export for CSV files|Vote for the integration you need"),

    # --- Security & Fraud --------------------------------------------------
    ("KB-701", "My account was hacked or accessed without permission", "Security & Fraud",
     "If you see logins or orders you did not make, secure your account immediately. We can log out all devices, lock the account and investigate suspicious activity.",
     "Reset your password right away|Log out of all devices from Security settings|Enable two-factor authentication|Report the activity so we can lock and investigate"),
    ("KB-702", "Report a phishing email or scam message", "Security & Fraud",
     "We never ask for passwords, OTPs or card PINs by email, SMS or phone. Do not click suspicious links. Forward the message to our security mailbox so we can block the sender.",
     "Do not click links or share OTPs|Forward the email to the security mailbox|Delete the message and report it as spam"),
    ("KB-703", "Unauthorised or fraudulent transaction on my card", "Security & Fraud",
     "If you see a payment you did not authorise, contact your bank to block the card, then share the transaction details with us. We freeze the order and investigate with the payment partner.",
     "Block or freeze the card with your bank|Share the transaction id, date and amount|We freeze the order and open an investigation"),
    ("KB-704", "Privacy requests: view or delete my personal data", "Security & Fraud",
     "You can request a copy of your personal data or ask for deletion from Settings > Privacy. Requests are completed within 30 days and confirmed by email.",
     "Open Settings > Privacy|Choose Download my data or Delete my data|Confirm via the email we send"),

    # --- General Inquiry ----------------------------------------------------
    ("KB-801", "Pricing, plans and what is included", "General Inquiry",
     "Pricing depends on the plan. The pricing page lists monthly and yearly costs, what each plan includes and any available discounts for students and non-profits.",
     "Open the pricing page|Compare plans|Contact sales for custom or bulk pricing"),
    ("KB-802", "Support hours and how to contact us", "General Inquiry",
     "Our support team is available Monday to Saturday from 9 AM to 8 PM IST. You can reach us via chat, email or the callback option in the Help section.",
     "Use chat for the fastest reply|Email us any time and we reply within 24 hours|Request a callback in the Help section"),
    ("KB-803", "General questions about how the service works", "General Inquiry",
     "The help centre has getting-started guides, FAQs and video tutorials that explain how to use the service and answer common general questions.",
     "Visit the Help Centre|Search the FAQ|Watch the getting-started tutorials"),
]


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["article_id", "title", "category", "content", "steps"])
        w.writerows(ARTICLES)
    print(f"Wrote {len(ARTICLES)} articles to {out}")


if __name__ == "__main__":
    main()
