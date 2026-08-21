# Sends a Digest via SMTP (smtplib) as an HTML email to the configured recipient
import smtplib
import os
from email.mime.text import MIMEText

sender = "mariosaleh.ms@gmail.com"
password = os.getenv("GMAIL_APP_PASSWORD")  # Use an app password for Gmail
recipients = ["mariosaleh.ms@gmail.com"]

def send_email_to_self(subject: str, html_body: str) -> None:
    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

if(__name__ == "__main__"):
    send_email_to_self(
        "Test Email",
        "<html><body><p>This is an <b>HTML</b> test email sent from Python.</p></body></html>",
    )