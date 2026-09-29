import os
import smtplib
from email.message import EmailMessage


def send_lead_emails(lead: dict) -> list[tuple[str, bool, str]]:
    host, username, password = (os.getenv(k, "").strip() for k in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"))
    sales = os.getenv("SALES_EMAIL", "").strip()
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        return [("email", False, "SMTP_PORT must be a number")]
    if not all((host, username, password, sales)):
        return [("welcome_email", False, "SMTP configuration incomplete; welcome email not sent."),
                ("sales_notification", False, "SMTP configuration incomplete; sales notification not sent.")]
    welcome = EmailMessage()
    welcome["Subject"] = "Thanks for contacting us"
    welcome["From"] = username
    welcome["To"] = lead["email"]
    welcome.set_content(f"Hi {lead['name']},\n\nThanks for contacting us. We have received your request and our team will get back to you soon.\n\nBest regards,\nSales Team")
    notice = EmailMessage()
    notice["Subject"] = f"New Lead: {lead['name']}"
    notice["From"] = username
    notice["To"] = sales
    notice.set_content("New lead received\n\n" + "\n".join(f"{k.title()}: {lead[k]}" for k in ("name", "email", "company", "message", "source")))
    results = []
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(username, password)
            for action, message in (("welcome_email", welcome), ("sales_notification", notice)):
                try:
                    server.send_message(message)
                    results.append((action, True, "Email sent."))
                except Exception as exc:
                    results.append((action, False, f"Email send failed: {exc}"))
    except Exception as exc:
        results.extend((action, False, f"SMTP connection failed: {exc}") for action in ("welcome_email", "sales_notification"))
    return results
