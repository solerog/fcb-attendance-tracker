#!/usr/bin/env python3
"""Comprova partits amb sol·licituds obertes pendents i envia recordatoris per correu."""

import os
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, cast
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from utils.db.supabase import supabase
from utils.gmail import send_email
from utils.types import PersonRow

load_dotenv()

LOCAL_TZ = ZoneInfo("Europe/Madrid")


def send_email_notification(
    recipients: list[str],
    subject: str,
    body_text: str,
    body_html: str,
) -> None:
    user = os.environ["GMAIL_USER"]
    password = os.environ.get("GMAIL_PASSWORD") or os.environ.get(
        "GMAIL_APP_PASSWORD", ""
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"FCB Attendance Tracker <{user}>"
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())


def main() -> None:
    # 1. Obtenir persones amb correu registrat
    people_res = (
        supabase.table("people")
        .select("id, name, first_surname, email")
        .not_.is_("email", "null")
        .execute()
    )
    people = cast(list[PersonRow], people_res.data or [])
    recipients: list[str] = [cast(str, p["email"]) for p in people if p.get("email")]

    if not recipients:
        print("ℹ️ No hi ha cap persona amb correu electrònic a la base de dades.")
        return

    # 2. Obtenir partits oberts no demanats
    # Consulta a match_details (vista amb dades del rival) o matches
    matches_res = (
        supabase.table("match_details")
        .select(
            "id, date, away_team_name, away_team_shortname, request_deadline, tickets_open, tickets_requested"
        )
        .eq("tickets_open", True)
        .eq("tickets_requested", False)
        .not_.is_("request_deadline", "null")
        .execute()
    )
    matches = cast(list[dict[str, Any]], matches_res.data or [])

    if not matches:
        print("ℹ️ No hi ha partits amb sol·licituds obertes i pendents de demanar.")
        return

    now = datetime.now(UTC)

    for match in matches:
        deadline_raw = match.get("request_deadline")
        if not deadline_raw:
            continue

        deadline_dt = datetime.fromisoformat(deadline_raw)
        time_diff = (deadline_dt - now).total_seconds()

        # Avaluar si queden menys de 24h o menys de 48h
        if 0 < time_diff <= 86400:
            urgency_tag = "AVUI"
            subject_prefix = "🚨 ÚLTIM DIA: AVUI acaba el termini"
        elif 86400 < time_diff <= 172800:
            urgency_tag = "DEMÀ"
            subject_prefix = "⚠️ RECORDATORI: DEMÀ acaba el termini"
        else:
            # Més de 2 dies o termini ja superat
            continue

        rival = (
            match.get("away_team_name") or match.get("away_team_shortname") or "Rival"
        )

        # Formatar dates en hora local
        match_dt_local = datetime.fromisoformat(match["date"]).astimezone(LOCAL_TZ)
        deadline_dt_local = deadline_dt.astimezone(LOCAL_TZ)

        match_date_str = match_dt_local.strftime("%d/%m/%Y a les %H:%M h")
        deadline_str = deadline_dt_local.strftime("%d/%m/%Y a les %H:%M h")

        subject = f"{subject_prefix} per demanar entrades vs {rival}"

        body_text = f"""Hola!

{urgency_tag} finalitza el període per sol·licitar les entrades per al següent partit:

⚽ Partit: FC Barcelona vs {rival}
📅 Data del partit: {match_date_str}
⏰ Data límit de sol·licitud: {deadline_str}

Recorda fer la petició a la web del soci abans que venci el termini.
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; }}
    .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ font-size: 1.25rem; font-weight: 700; color: #004d98; margin-bottom: 12px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.75rem; background: #fee2e2; color: #b91c1c; margin-bottom: 16px; }}
    .info-row {{ margin: 10px 0; font-size: 0.95rem; }}
    .info-label {{ font-weight: 600; color: #64748b; }}
    .footer {{ margin-top: 24px; font-size: 0.8rem; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">{urgency_tag} TANCAMENT DE SOL·LICITUDS</div>
    <div class="header">FC Barcelona vs {rival}</div>
    <p>Recordatori automàtic: les entrades per a aquest partit encara estan <strong>pendents de demanar</strong>.</p>
    
    <div class="info-row"><span class="info-label">📅 Data del partit:</span> {match_date_str}</div>
    <div class="info-row"><span class="info-label">⏰ Termini:</span> <strong>{deadline_str}</strong></div>
    
    <div class="footer">FCB Attendance Tracker · Notificació automàtica</div>
  </div>
</body>
</html>
"""

        print(f"📧 Enviant recordatori per al partit vs {rival} ({urgency_tag})...")
        send_email(
            recipients=recipients,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )
        print(f"  ✅ Correu enviat a {len(recipients)} destinataris.")


if __name__ == "__main__":
    main()
