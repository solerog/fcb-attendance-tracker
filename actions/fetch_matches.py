#!/usr/bin/env python3
"""Fetch matches from api-football and write normalized JSON"""

import os

from utils.helper import is_data_updated, load_settings, save_data
from utils.url import FootballDataClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def fetch(team_id, season, api_key):
    client = FootballDataClient(api_key=api_key)
    data = client.team_matches(team_id, season)
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
    updated = is_data_updated(matches, "matches.json")
    if updated:
        save_data(matches, "matches.json")
        print(f"Saved {len(matches)} matches to data/matches.json")
    else:
        print("No changes in matches info.")
    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
        f.write(f"updated={'true' if updated else 'false'}\n")


if __name__ == "__main__":
    main()
