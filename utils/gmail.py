"""Utilitats per a la connexió i enviament de correus amb Gmail (IMAP i SMTP)."""

import imaplib
import os
import smtplib
from collections.abc import Generator
from contextlib import contextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_gmail_credentials() -> tuple[str, str]:
    """Obté l'usuari i la contrasenya d'aplicació de Gmail."""
    user = os.environ.get("GMAIL_USER", "")
    password = os.environ.get("GMAIL_PASSWORD") or os.environ.get(
        "GMAIL_APP_PASSWORD", ""
    )
    if not user or not password:
        raise ValueError(
            "Cal definir GMAIL_USER i GMAIL_PASSWORD a les variables d'entorn."
        )
    return user, password


@contextmanager
def get_imap_connection(mailbox: str = "INBOX") -> Generator[imaplib.IMAP4_SSL]:
    """Context manager per a connexions IMAP segures que tanca la sessió automàticament."""
    user, password = get_gmail_credentials()
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        mail.login(user, password)
        mail.select(mailbox)
        yield mail
    finally:
        mail.close()
        mail.logout()


def send_email(
    recipients: list[str],
    subject: str,
    body_text: str,
    body_html: str | None = None,
    sender_name: str = "FCB Attendance Tracker",
) -> None:
    """Envia un correu electrònic via SMTP SSL."""
    if not recipients:
        return

    user, password = get_gmail_credentials()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{user}>"
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
