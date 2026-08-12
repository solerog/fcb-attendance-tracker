#!/usr/bin/env python3
"""Check open ticket request windows for Barça matches and map them to local fixtures."""

import os
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from utils.helper import is_list_dicts_updated, load_matches, load_settings, save_data

LOCAL_TZ = ZoneInfo("Europe/Madrid")


def parse_match_local_datetime(date_text, time_text):
    normalized_time = time_text.strip().replace(".", ":")
    if ":" not in normalized_time:
        normalized_time = f"{normalized_time}:00"
    return datetime.strptime(
        f"{date_text} {normalized_time}", "%d/%m/%y %H:%M"
    ).replace(tzinfo=LOCAL_TZ)


def parse_deadline(date_text, time_text):
    return parse_match_local_datetime(date_text, time_text)


def match_fixture(page_match, fixtures):
    page_dt = parse_match_local_datetime(
        page_match["date_text"], page_match["time_text"]
    )
    page_dt_utc = page_dt.astimezone(UTC)

    best_match = None
    best_diff = None
    for fixture in fixtures:
        fixture_iso = fixture.get("date")
        if not fixture_iso:
            continue
        fixture_dt = datetime.fromisoformat(fixture_iso).astimezone(UTC)
        diff = abs((page_dt_utc - fixture_dt).total_seconds())
        if best_diff is None or diff < best_diff:
            best_match = fixture
            best_diff = diff

    if best_match is None:
        return None

    fixture_iso = best_match.get("date")
    fixture_dt = datetime.fromisoformat(fixture_iso).astimezone(UTC)
    is_time_correct = abs((page_dt_utc - fixture_dt).total_seconds()) <= 1800

    return {
        "match_id": best_match.get("id"),
        "away_name": best_match.get("away_name"),
        "away_shortname": best_match.get("away_shortname"),
        "fixture_date_utc": fixture_iso,
        "fixture_date_local": fixture_dt.astimezone(LOCAL_TZ).isoformat(),
        "page_match_datetime_local": page_dt.isoformat(),
        "page_match_datetime_utc": page_dt_utc.isoformat(),
        "is_time_correct": is_time_correct,
    }


def extract_open_matches(html):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("div.article__content.js-article-body.js-text-share-body")
    if not article:
        return []

    entries = []
    current = None

    for block in article.find_all(["h3", "p", "div"], recursive=True):
        if block.name == "h3":
            title = block.get_text(" ", strip=True)
            match = re.search(
                r"FC BARCELONA-\s*(.+?)\s*-\s*(\d{2}/\d{2}/\d{2})\s*-\s*([\d.]+)\s*H",
                title,
                flags=re.IGNORECASE,
            )
            if match:
                current = {
                    "rival": match.group(1).strip(),
                    "date_text": match.group(2).strip(),
                    "time_text": match.group(3).strip(),
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


def check(url, fixtures=None):
    fixtures = fixtures or []

    r = requests.get(url, timeout=30)
    r.raise_for_status()
    page_matches = extract_open_matches(r.text)

    result = []
    for match in page_matches:
        fixture = match_fixture(match, fixtures)
        if not fixture:
            continue
        result.append(
            {
                "match_id": fixture.get("match_id"),
                "request_deadline_local": match.get("deadline"),
            }
        )

    return result


def main():
    settings = load_settings()
    url = settings.get("barca_request_url")
    if not url:
        print("No barca_request_url set in data/settings.json")
        return

    matches = load_matches()
    status = check(url, matches)

    requests_updated = is_list_dicts_updated(status, "open_ticket_requests.json")
    if requests_updated:
        save_data(status, "open_ticket_requests.json")
        print(
            f"Saved {len(status)} open ticket requests to data/open_ticket_requests.json"
        )
    else:
        print("No changes in open ticket requests info.")

    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
        f.write(f"updated={'true' if requests_updated else 'false'}\n")


if __name__ == "__main__":
    main()
