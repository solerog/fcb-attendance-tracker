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


def save_matches(matches):
    out = os.path.join(DATA_DIR, "matches.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)


def fetch(team_id, season, api_key):
    headers = {}
    if api_key:
        headers["X-Auth-Token"] = api_key
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?season={season}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("matches", [])
    print(items[0] if items else "No items found")
    home_matches = []
    for it in items:
        if it.get("homeTeam", {}).get("id") != team_id:
            continue
        match = {
            "id": it.get("id"),
            "date": it.get("utcDate"),
            "away_name": it.get("awayTeam", {}).get("name"),
            "away_shortname": it.get("awayTeam", {}).get("shortName"),
            "away_tla": it.get("awayTeam", {}).get("tla"),
            "away_crest": it.get("awayTeam", {}).get("crest"),
            "league": it.get("competition", {}).get("name"),
            "matchday": it.get("matchday"),
            "status": it.get("status"),
            "last_updated": it.get("lastUpdated"),
        }
        home_matches.append(match)
    print(home_matches[0] if home_matches else "No home matches found")
    return home_matches


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("FOOTBALL_DATA_KEY")
    if not team_id or not season:
        print("Please set team_id and season in data/settings.json")
        return
    matches = fetch(team_id, season, api_key)
    save_matches(matches)
    print(f"Saved {len(matches)} matches to data/matches.json")


if __name__ == "__main__":
    main()
