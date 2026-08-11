#!/usr/bin/env python3
"""Simple checker that fetches a configured Barça page and records whether 'requests' appear."""

import json
import os
from datetime import UTC, datetime

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_settings():
    path = os.path.join(DATA_DIR, "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_status(status):
    out = os.path.join(DATA_DIR, "requests_status.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def check(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        text = r.text.lower()
        keywords = ["sol·licitud", "solicitud", "requests open", "entrades", "entradas"]
        found = any(k in text for k in keywords)
        return {
            "url": url,
            "checked_at": datetime.now(UTC).isoformat() + "Z",
            "found": found,
        }
    except Exception as e:
        return {
            "url": url,
            "checked_at": datetime.now(UTC).isoformat() + "Z",
            "error": str(e),
        }


def main():
    settings = load_settings()
    url = settings.get("barca_request_url")
    if not url:
        print("No barca_request_url set in data/settings.json")
        return
    status = check(url)
    save_status(status)
    print("Wrote data/requests_status.json")


if __name__ == "__main__":
    main()
