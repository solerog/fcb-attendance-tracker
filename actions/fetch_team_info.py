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
    data = client.team_info(team_id, season)
    info = {
        "id": data.get("id"),
        "name": data.get("name"),
        "shortname": data.get("shortName"),
        "tla": data.get("tla"),
        "crest": data.get("crest"),
    }
    print(info if info else "No team info found")
    return info


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("FOOTBALL_DATA_KEY")
    if not team_id or not season:
        print("Please set team_id and season in data/settings.json")
        return
    team_info = fetch(team_id, season, api_key)
    updated = is_data_updated(team_info, "fcb.json")
    if updated:
        save_data(team_info, "fcb.json")
        print("Saved team info to data/fcb.json")
    else:
        print("No changes in team info.")
    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
        f.write(f"updated={'true' if updated else 'false'}\n")


if __name__ == "__main__":
    main()
