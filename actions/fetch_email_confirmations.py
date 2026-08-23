#!/usr/bin/env python3
"""Llegeix correus de confirmació del Barça, crea noves persones automàticament i mapeja seients i rivals de forma robusta amb primer i segon cognom."""

import email
import email.utils
import imaplib
import os
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from utils.db.supabase import supabase
from utils.gmail import get_imap_connection
from utils.types import (
    AssistantInfo,
    AttendanceInsert,
    MatchRow,
    ParsedEmail,
    PersonRow,
    ProcessedEmailRow,
    SeatRow,
    SettingsRow,
)

load_dotenv()

LOCAL_TZ = ZoneInfo("Europe/Madrid")

# Àlies d'equips per normalitzar noms internacionals o diferències de grafia
TEAM_ALIASES: dict[str, str] = {
    "copenhagen": "kobenhavn",
    "fc copenhagen": "kobenhavn",
    "copenhague": "kobenhavn",
    "atletico de madrid": "atletico madrid",
    "atletico": "atletico madrid",
    "inter milan": "internazionale",
    "inter de mila": "internazionale",
    "estrella roja": "crvena zvezda",
    "shakhtar": "shakhtar donetsk",
    "sporting lisboa": "sporting cp",
    "sporting de portugal": "sporting cp",
}

# Àlies de persones (variants de nom que mapegen a un person_id existent)
PERSON_ALIASES: dict[str, int] = {
    "m.lluisa sole palacin": 5,
    "m. lluisa sole palacin": 5,
    "m lluisa sole palacin": 5,
    "m.lluisa sole": 5,
    "m lluisa sole": 5,
    "maria lluisa sole palacin": 5,
    "marisa sole palacin": 5,
}

# Diccionari de caràcters especials no coberts per NFKD
SPECIAL_CHAR_MAP = {
    "ø": "o",
    "Ø": "o",
    "æ": "ae",
    "Æ": "ae",
    "å": "a",
    "Å": "a",
    "ß": "ss",
}


def get_gmail_connection() -> imaplib.IMAP4_SSL:
    user = os.environ["GMAIL_USER"]
    password = os.environ.get("GMAIL_PASSWORD") or os.environ.get(
        "GMAIL_APP_PASSWORD", ""
    )

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(user, password)
    return mail


def remove_accents(text: str) -> str:
    """Elimina accents, caràcters nòrdics (ø, æ), tags HTML i converteix a minúscules."""
    if not text:
        return ""
    clean_text = re.sub(r"<[^>]+>", "", text)
    clean_text = clean_text.replace("&nbsp;", " ").replace(".", " ")

    # Reemplacem caràcters especials tipus ø -> o
    for char, replacement in SPECIAL_CHAR_MAP.items():
        clean_text = clean_text.replace(char, replacement)

    normalized = unicodedata.normalize("NFKD", clean_text)
    return (
        "".join(c for c in normalized if not unicodedata.combining(c)).strip().lower()
    )


def to_title_case(text: str) -> str:
    """Converteix cadenes en majúscules a format Capitalized (Title Case)."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()
    return " ".join(word.capitalize() for word in clean.split())


def clean_html_field(text: str) -> str:
    """Neteja etiquetes HTML i espais en blanc."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.replace("&nbsp;", " ").strip()


def split_surnames(raw_surnames: str) -> tuple[str, str | None]:
    """Separa el bloc de cognoms en primer i segon cognom."""
    parts = clean_html_field(raw_surnames).split()
    if not parts:
        return "", None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def get_latest_processed_date() -> datetime | None:
    response = (
        supabase.table("processed_emails")
        .select("processed_at")
        .order("processed_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = cast(list[ProcessedEmailRow], response.data or [])
    if rows:
        raw_date = rows[0]["processed_at"]
        return datetime.fromisoformat(raw_date)
    return None


def get_all_processed_locators() -> set[str]:
    response = supabase.table("processed_emails").select("locator").execute()
    rows = cast(list[ProcessedEmailRow], response.data or [])
    return {row["locator"] for row in rows}


def parse_email_body(raw_text: str) -> ParsedEmail:
    # 1. Localitzador
    locator_match = re.search(
        r"Localitzador:\s*([A-Z0-9]+)", raw_text, flags=re.IGNORECASE
    )
    locator = clean_html_field(locator_match.group(1)) if locator_match else None

    # 2. Data d'inscripció
    reg_date_match = re.search(
        r"Hora de la inscripci[oó]:\s*([\d-]+(?:\s+[\d:]+)?)",
        raw_text,
        flags=re.IGNORECASE,
    )
    registration_dt = None
    if reg_date_match:
        try:
            cleaned_date = clean_html_field(reg_date_match.group(1))
            registration_dt = datetime.fromisoformat(cleaned_date).replace(
                tzinfo=LOCAL_TZ
            )
        except ValueError:
            pass

    # 3. Rival
    match_rival = re.search(
        r"Partit:\s*Fc Barcelona\s*-\s*(.+?)(?:\r?\n|<br|\.|$)",
        raw_text,
        flags=re.IGNORECASE,
    )
    rival_name = clean_html_field(match_rival.group(1)) if match_rival else None

    # 4. Assistents
    assistants: list[AssistantInfo] = []
    blocks = re.split(r"\[Assistent(?:\s+\d+)?\]", raw_text, flags=re.IGNORECASE)

    for block in blocks[1:]:
        nom = re.search(r"Nom:\s*(.+?)(?:\r?\n|<br|$)", block, flags=re.IGNORECASE)
        cognoms = re.search(
            r"Cognoms:\s*(.+?)(?:\r?\n|<br|$)", block, flags=re.IGNORECASE
        )
        clau = re.search(r"Clau(?:\s+de)?\s+soci:\s*(\d+)", block, flags=re.IGNORECASE)

        if nom and cognoms:
            assistants.append(
                {
                    "name": clean_html_field(nom.group(1)),
                    "first_surname": clean_html_field(cognoms.group(1)),
                    "clau_soci": int(clau.group(1).strip()) if clau else None,
                }
            )

    return {
        "locator": locator,
        "rival": rival_name,
        "registration_dt": registration_dt,
        "assistants": assistants,
    }


def find_match_id(
    rival_text: str,
    home_team_id: int,
    ref_date: datetime | None = None,
) -> int | None:
    """Cerca el partit local contra el rival a partir de la data d'inscripció."""
    query = (
        supabase.table("match_details")
        .select("id, date, away_team_name, away_team_shortname, season_id")
        .eq("home_team_id", home_team_id)
    )

    if ref_date:
        min_date = ref_date - timedelta(days=1)
        max_date = ref_date + timedelta(days=35)
        query = query.gte("date", min_date.isoformat()).lte(
            "date", max_date.isoformat()
        )

    response = query.order("date").execute()
    matches = cast(list[MatchRow], response.data or [])

    rival_norm = remove_accents(rival_text)

    # Aplicar àlies si existeix
    for alias_key, alias_val in TEAM_ALIASES.items():
        if alias_key in rival_norm:
            rival_norm = alias_val
            break

    # Paraules clau significatives del rival (ignorant 'fc', 'club', 'de', etc.)
    stop_words = {"fc", "club", "de", "the", "cf", "ud", "cd"}
    rival_tokens = [w for w in rival_norm.split() if w not in stop_words and len(w) > 2]

    for match in matches:
        away_name = remove_accents(match.get("away_team_name") or "")
        away_short = remove_accents(match.get("away_team_shortname") or "")

        if (
            away_name in rival_norm
            or away_short in rival_norm
            or rival_norm in away_name
            or rival_norm in away_short
        ):
            return match["id"]

        if any(token in away_name or token in away_short for token in rival_tokens):
            return match["id"]

    return None


def get_or_create_person(
    name: str, surnames_raw: str, people_cache: list[PersonRow]
) -> int:
    """Cerca la persona a la BD per nom i primer/segon cognom o la crea si és nova."""
    full_name_clean = remove_accents(f"{name} {surnames_raw}")

    # 1. Comprovar si està al diccionari d'àlies
    for alias_key, person_id in PERSON_ALIASES.items():
        if alias_key in full_name_clean or full_name_clean in alias_key:
            return person_id

    # 2. Cerca a la llista existent de persones
    ast_name_norm = remove_accents(name)
    first_surname_raw, second_surname_raw = split_surnames(surnames_raw)
    ast_first_norm = remove_accents(first_surname_raw)
    ast_second_norm = remove_accents(second_surname_raw or "")

    for p in people_cache:
        p_name_norm = remove_accents(p["name"])
        p_first_norm = remove_accents(p.get("first_surname") or "")
        p_second_norm = remove_accents(p.get("second_surname") or "")

        # Coincidència de nom
        name_match = p_name_norm in ast_name_norm or ast_name_norm in p_name_norm

        # Coincidència de cognoms (primer obligatori, segon si existeix)
        first_match = (
            (p_first_norm in ast_first_norm or ast_first_norm in p_first_norm)
            if p_first_norm and ast_first_norm
            else False
        )

        second_match = True
        if p_second_norm and ast_second_norm:
            second_match = (
                p_second_norm in ast_second_norm or ast_second_norm in p_second_norm
            )

        if name_match and first_match and second_match:
            return p["id"]

    # 3. Si no existeix, la creem a Supabase
    next_id = max((p["id"] for p in people_cache), default=0) + 1
    new_person: PersonRow = {
        "id": next_id,
        "name": to_title_case(name),
        "first_surname": to_title_case(first_surname_raw),
        "second_surname": to_title_case(second_surname_raw)
        if second_surname_raw
        else "",
        "clau_soci": None,
        "email": None,
    }

    supabase.table("people").insert(cast(dict[str, Any], new_person)).execute()
    people_cache.append(new_person)
    full_display = f"{new_person['name']} {new_person['first_surname']}" + (
        f" {new_person['second_surname']}" if new_person["second_surname"] else ""
    )
    print(
        f"  👤 Nova persona afegida a la base de dades: {full_display} (ID: {next_id})"
    )

    return next_id


def process_confirmations() -> None:
    settings_res = (
        supabase.table("settings")
        .select("home_team_id, season_id")
        .order("season_id", desc=True)
        .limit(1)
        .execute()
    )
    settings_rows = cast(list[SettingsRow], settings_res.data or [])

    if not settings_rows:
        print("No s'han trobat paràmetres a la taula settings.")
        return

    home_team_id = settings_rows[0]["home_team_id"]

    people_res = (
        supabase.table("people")
        .select("id, name, first_surname, second_surname, clau_soci")
        .execute()
    )
    people = cast(list[PersonRow], people_res.data or [])

    seats_res = (
        supabase.table("seat_details")
        .select("id, owner_id, clau_soci")
        .order("id")
        .execute()
    )
    seats = cast(list[SeatRow], seats_res.data or [])

    processed_locators = get_all_processed_locators()
    latest_processed = get_latest_processed_date()

    with get_imap_connection("INBOX") as mail:
        search_query = '(FROM "info.tickets@fcbarcelona.cat" SUBJECT "temporada"'
        if latest_processed:
            since_date = (latest_processed - timedelta(days=1)).strftime("%d-%b-%Y")
            search_query += f' SINCE "{since_date}"'
        search_query += ")"

        print(f"Cercant a Gmail amb criteri: {search_query}")
        status, messages = mail.search(None, search_query)

        if status != "OK" or not messages[0]:
            print("No s'han trobat nous correus per processar.")
            return

        email_ids = messages[0].split()
        print(f"Correus trobats pel filtre: {len(email_ids)}")

        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            if not msg_data or not msg_data[0] or not isinstance(msg_data[0], tuple):
                continue

            raw_email_bytes = cast(bytes, msg_data[0][1])
            msg = email.message_from_bytes(raw_email_bytes)

            email_date_raw = msg.get("Date", "")
            email_date_tuple = (
                email.utils.parsedate_to_datetime(email_date_raw).astimezone(LOCAL_TZ)
                if email_date_raw
                else datetime.now(LOCAL_TZ)
            )

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body = payload.decode(errors="ignore")
                        break
            else:
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body = payload.decode(errors="ignore")

            parsed = parse_email_body(body)
            locator = parsed["locator"]

            if not locator:
                print("⚠️ No s'ha trobat cap localitzador al correu. S'omet.")
                continue

            if locator in processed_locators:
                print(f"⏩ Localitzador {locator} ja processat anteriorment. Ometent.")
                continue

            if not parsed["rival"] or not parsed["assistants"]:
                continue

            ref_dt = parsed["registration_dt"] or email_date_tuple

            match_id = find_match_id(
                rival_text=parsed["rival"],
                home_team_id=home_team_id,
                ref_date=ref_dt,
            )

            if not match_id:
                print(
                    f"⚠️ No s'ha trobat partit per al rival: {parsed['rival']} "
                    f"(Inscripció: {ref_dt.strftime('%Y-%m-%d')})."
                )
                continue

            attendance_rows: list[AttendanceInsert] = []

            for assistant in parsed["assistants"]:
                seat_id: int | None = None
                if assistant["clau_soci"]:
                    s_match = next(
                        (
                            s
                            for s in seats
                            if s.get("clau_soci") == assistant["clau_soci"]
                        ),
                        None,
                    )
                    if s_match:
                        seat_id = s_match["id"]

                if not seat_id:
                    print(
                        f"⚠️ No s'ha trobat cap seient per a la clau de soci {assistant['clau_soci']}."
                    )
                    continue

                person_id = get_or_create_person(
                    name=assistant["name"],
                    surnames_raw=assistant["first_surname"],
                    people_cache=people,
                )

                attendance_rows.append(
                    {
                        "match_id": match_id,
                        "seat_id": seat_id,
                        "person_id": person_id,
                    }
                )

            if attendance_rows:
                supabase.table("attendance").upsert(
                    cast(list[dict[str, Any]], attendance_rows),
                    on_conflict="match_id,seat_id",
                ).execute()

            supabase.table("matches").update({"tickets_requested": True}).eq(
                "id", match_id
            ).execute()

            supabase.table("processed_emails").insert(
                {
                    "locator": locator,
                    "match_id": match_id,
                    "registration_date": ref_dt.isoformat(),
                }
            ).execute()

            processed_locators.add(locator)
            print(
                f"✅ Localitzador {locator} processat amb èxit (Partit ID: "
                f"{match_id}, {len(attendance_rows)} seients)."
            )


if __name__ == "__main__":
    process_confirmations()
