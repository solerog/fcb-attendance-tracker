#!/usr/bin/env python3
"""Send email reminders for home matches within 7 days using Gmail SMTP."""

import json
import os
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")


def load_json(name, default):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_upcoming_home(matches, days=7):
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)
    res = []
    for m in matches:
        try:
            dt = datetime.fromisoformat(m["date"].replace("Z", "+00:00"))
        except Exception:
            continue
        if m.get("home") and dt >= now and dt <= cutoff:
            res.append(m)
    return res


def send_mail(subject, body, recipients):
    user = os.environ.get("MAIL_USER")
    pwd = os.environ.get("MAIL_PASS")
    if not user or not pwd:
        print("MAIL_USER and MAIL_PASS must be set in environment")
        return False
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(msg)
    return True


def main():
    matches = load_json("matches.json", [])
    settings = load_json("settings.json", {})
    members = settings.get("members", [])
    upcoming = find_upcoming_home(matches, days=7)
    if not upcoming:
        print("No upcoming home matches within 7 days")
        return
    for m in upcoming:
        subj = (
            f"Recordatori: partit {m.get('home')} vs {m.get('away')} - demana entrades"
        )
        body = f"Recordatori: el partit {m.get('home')} vs {m.get('away')} és el {m.get('date')}. Cal demanar entrades 7 dies abans."
        ok = send_mail(subj, body, members)
        print("Sent" if ok else "Failed", subj)


if __name__ == "__main__":
    main()
