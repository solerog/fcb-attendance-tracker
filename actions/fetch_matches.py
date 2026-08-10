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
    matches = []
    for it in items:
        match = {
            "id": it.get("id"),
            "date": it.get("utcDate"),
            "timestamp": None,
            "home": it.get("homeTeam", {}).get("name"),
            "away": it.get("awayTeam", {}).get("name"),
            "home_id": it.get("homeTeam", {}).get("id"),
            "away_id": it.get("awayTeam", {}).get("id"),
            "venue": it.get("venue"),
            "league": it.get("competition", {}).get("name"),
            "competition_code": it.get("competition", {}).get("code"),
            "season": it.get("season", {}).get("startDate") or season,
            "season_end": it.get("season", {}).get("endDate"),
            "matchday": it.get("matchday"),
            "status": it.get("status"),
            "last_updated": it.get("lastUpdated"),
            "requests_open": False,
        }
        matches.append(match)
    return matches


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
