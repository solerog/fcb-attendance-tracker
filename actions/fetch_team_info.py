#!/usr/bin/env python3
"""Fetch matches from api-football and write normalized JSON"""

import json
import os

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_settings():
    path = os.path.join(DATA_DIR, "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_info(info):
    out = os.path.join(DATA_DIR, "fcb.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def fetch(team_id, season, api_key):
    headers = {}
    if api_key:
        headers["X-Auth-Token"] = api_key
    url = f"https://api.football-data.org/v4/teams/{team_id}?season={season}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    info = {
        "id": data.get("id"),
        "name": data.get("name"),
        "shortname": data.get("shortName"),
        "tla": data.get("tla"),
        "crest": data.get("crest"),
    }
    print(info if info else "No team info found")
    return info


def is_info_updated(new_info):
    """Check if the new info is different from the existing info in fcb.json"""
    path = os.path.join(DATA_DIR, "fcb.json")
    if not os.path.exists(path):
        return True
    with open(path, "r", encoding="utf-8") as f:
        try:
            existing_info = json.load(f)
        except json.JSONDecodeError:
            return True
    return existing_info != new_info


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("FOOTBALL_DATA_KEY")
    if not team_id or not season:
        print("Please set team_id and season in data/settings.json")
        return
    team_info = fetch(team_id, season, api_key)
    if is_info_updated(team_info):
        save_info(team_info)
        print(f"Saved {len(team_info)} team info to data/fcb.json")
    else:
        print("No changes in team info.")


if __name__ == "__main__":
    main()
