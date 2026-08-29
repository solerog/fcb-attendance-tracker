#!/usr/bin/env python3
"""Comprova les sol·licituds d'entrades obertes al web del Barça i actualitza el termini a Supabase."""

import os
import re
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils.db.supabase import supabase
from utils.types import MatchRow, SettingsRow

load_dotenv()

LOCAL_TZ = ZoneInfo("Europe/Madrid")


def parse_match_local_datetime(date_text: str, time_text: str) -> datetime:
    normalized_time = time_text.strip().replace(".", ":")
    if ":" not in normalized_time:
        normalized_time = f"{normalized_time}:00"
    return datetime.strptime(
        f"{date_text} {normalized_time}", "%d/%m/%y %H:%M"
    ).replace(tzinfo=LOCAL_TZ)


def parse_deadline(date_text: str, time_text: str) -> datetime:
    return parse_match_local_datetime(date_text, time_text)


def match_fixture(
    page_match: dict[str, Any], fixtures: list[MatchRow]
) -> dict[str, Any] | None:
    page_dt = parse_match_local_datetime(
        page_match["date_text"], page_match["time_text"]
    )
    page_dt_utc = page_dt.astimezone(UTC)

    best_match: MatchRow | None = None
    best_diff: float | None = None

    for fixture in fixtures:
        fixture_iso = fixture.get("date")
        if not fixture_iso:
            continue
        fixture_dt = datetime.fromisoformat(fixture_iso).astimezone(UTC)
        diff = abs((page_dt_utc - fixture_dt).total_seconds())

        if best_diff is None or diff < best_diff:
            best_match = fixture
            best_diff = diff

    # Tolerància de 36 hores (129.600 segons) per cobrir ajustos d'horari
    if best_match is None or (best_diff is not None and best_diff > 129600):
        return None

    fixture_iso = best_match.get("date", "")
    fixture_dt = datetime.fromisoformat(fixture_iso).astimezone(LOCAL_TZ)

    return {
        "match_id": best_match.get("id"),
        "away_name": best_match.get("away_team_name"),
        "away_shortname": best_match.get("away_team_shortname"),
        "fixture_date_utc": fixture_iso,
        "fixture_date_local": fixture_dt.isoformat(),
        "page_match_datetime_local": page_dt.isoformat(),
    }


def extract_open_matches(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("div.article__content.js-article-body.js-text-share-body")
    if not article:
        return []

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    # Busquem tant spans amb data-teams="true" com h3, p i div
    for block in article.find_all(["span", "h3", "p", "div"], recursive=True):
        is_title_block = False
        title_text = ""

        # Format 1: <span data-teams="true">RIVAL. DD/MM/YY- HH.MM h</span>
        if (
            block.name == "span"
            and block.get("data-teams") == "true"
            or block.name == "h3"
        ):
            is_title_block = True
            title_text = block.get_text(" ", strip=True)

        if is_title_block:
            # Regex flexible per capturar data (DD/MM/YY) i hora (HH.MM o HH:MM)
            match = re.search(
                r"(\d{2}/\d{2}/\d{2})\s*[-–]\s*([\d.]+)\s*h?",
                title_text,
                flags=re.IGNORECASE,
            )
            if match:
                current = {
                    "raw_title": title_text,
                    "date_text": match.group(1).strip(),
                    "time_text": match.group(2).strip(),
                    "deadline": None,
                    "deadline_text": None,
                    "button_url": None,
                    "open": False,
                }
                entries.append(current)
            continue

        if current is None:
            continue

        text = block.get_text(" ", strip=True)
        if "tancament formulari" in text.lower():
            deadline_match = re.search(
                r"tancament formulari:\s*(\d{2}/\d{2}/\d{2})\s*a\s*les\s*([\d.]+)\s*h?",
                text,
                flags=re.IGNORECASE,
            )
            if deadline_match:
                current["deadline_text"] = text
                deadline_dt = parse_deadline(
                    deadline_match.group(1), deadline_match.group(2)
                )
                current["deadline"] = deadline_dt.isoformat()

        if block.name == "div":
            link = block.select_one("a.button.button--primary")
            if link:
                current["button_url"] = link.get("href")
                current["open"] = True

    return entries


def check_open_requests(url: str, fixtures: list[MatchRow]) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    page_matches = extract_open_matches(response.text)
    results: list[dict[str, Any]] = []

    for match in page_matches:
        fixture = match_fixture(match, fixtures)
        if not fixture:
            continue
        results.append(
            {
                "match_id": fixture["match_id"],
                "request_deadline": match.get("deadline"),
                "is_open": match.get("open", False),
            }
        )

    return results


def main() -> None:
    home_team_id = int(os.environ.get("HOME_TEAM_ID", "81"))

    # 1. Obtenir configuració de la temporada actual amb open_requests_url
    settings_res = (
        supabase.table("settings")
        .select("home_team_id, season_id, open_requests_url")
        .eq("home_team_id", home_team_id)
        .order("season_id", desc=True)
        .limit(1)
        .execute()
    )
    settings_rows = cast(list[SettingsRow], settings_res.data or [])

    if not settings_rows:
        print(f"❌ No s'han trobat paràmetres a settings per a l'equip {home_team_id}.")
        return

    current_settings = settings_rows[0]
    season_id = current_settings["season_id"]
    url = current_settings.get("open_requests_url")

    if not url:
        print(
            f"⚠️ No s'ha definit cap URL a open_requests_url per a la temporada {season_id}."
        )
        return

    # 2. Obtenir tots els partits de casa de la temporada
    matches_res = (
        supabase.table("match_details")
        .select(
            "id, date, away_team_name, away_team_shortname, season_id, tickets_open"
        )
        .eq("home_team_id", home_team_id)
        .eq("season_id", season_id)
        .execute()
    )
    fixtures = cast(list[MatchRow], matches_res.data or [])

    print(f"🔍 Comprovant sol·licituds obertes a: {url}")
    open_requests = check_open_requests(url, fixtures)

    # 3. Conjunt dels IDs dels partits que ACTUALMENT estan oberts al web
    currently_open_match_ids = {
        req["match_id"]
        for req in open_requests
        if req.get("match_id") and req.get("is_open", True)
    }

    # 4. Actualitzar a TRUE els partits oberts (i el seu deadline si s'ha trobat)
    updated_open_count = 0
    for req in open_requests:
        match_id = req["match_id"]
        deadline = req["request_deadline"]

        if not match_id:
            continue

        update_dict: dict[str, Any] = {"tickets_open": True}
        if deadline:
            update_dict["request_deadline"] = deadline

        supabase.table("matches").update(update_dict).eq("id", match_id).execute()
        updated_open_count += 1
        print(f"  ✅ Entrades obertes per al partit ID {match_id}")

    # 5. Actualitzar a FALSE els partits que estaven oberts a la BD però ja no ho estan al web
    matches_to_close = [
        m["id"]
        for m in fixtures
        if m.get("tickets_open") is True and m["id"] not in currently_open_match_ids
    ]

    for match_id in matches_to_close:
        supabase.table("matches").update({"tickets_open": False}).eq(
            "id", match_id
        ).execute()
        print(
            f"  🔒 Formulari tancat: Partit ID {match_id} marcat amb tickets_open = false"
        )

    print(
        f"✨ Sincronització completada: {updated_open_count} partits oberts, "
        f"{len(matches_to_close)} partits tancats."
    )


if __name__ == "__main__":
    main()
