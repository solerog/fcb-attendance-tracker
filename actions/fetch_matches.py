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
        headers["x-apisports-key"] = api_key
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&season={season}&next=100"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("response", [])
    matches = []
    for it in items:
        fix = it.get("fixture", {})
        teams = it.get("teams", {})
        league = it.get("league", {})
        match = {
            "id": fix.get("id"),
            "date": fix.get("date"),
            "timestamp": fix.get("timestamp"),
            "home": teams.get("home", {}).get("name"),
            "away": teams.get("away", {}).get("name"),
            "home_id": teams.get("home", {}).get("id"),
            "away_id": teams.get("away", {}).get("id"),
            "venue": fix.get("venue", {}).get("name"),
            "league": league.get("name"),
            "season": season,
            "status": fix.get("status", {}).get("short"),
            "requests_open": False,
        }
        matches.append(match)
    return matches


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("API_FOOTBALL_KEY")
    if not team_id or not season:
        print("Please set team_id and season in data/settings.json")
        return
    matches = fetch(team_id, season, api_key)
    save_matches(matches)
    print(f"Saved {len(matches)} matches to data/matches.json")


if __name__ == "__main__":
    main()
