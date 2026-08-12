#!/usr/bin/env python3
"""Fetch matches from api-football and write normalized JSON"""

import os

from utils.helper import is_data_updated, load_settings, save_data
from utils.url import FootballDataClient


def extract_competitions(items):
    """Extract unique competitions from matches and build a dictionary."""
    competitions_dict = {}
    for it in items:
        comp = it.get("competition", {})
        comp_id = comp.get("code")
        if not comp_id or comp_id in competitions_dict:
            continue
        competitions_dict[comp_id] = {
            "id": comp_id,
            "name": comp.get("name"),
            "alias": comp.get("name"),  # Will be refined later if needed
            "crest": comp.get("crest"),
        }
    return competitions_dict


def fetch(team_id, season, api_key):
    client = FootballDataClient(api_key=api_key)
    data = client.team_matches(team_id, season)
    items = data.get("matches", [])

    competitions_dict = extract_competitions(items)
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
            "competition_code": it.get("competition", {}).get("code"),
            "matchday": it.get("matchday"),
            "status": it.get("status"),
        }
        home_matches.append(match)
    return home_matches, competitions_dict


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("FOOTBALL_DATA_KEY")
    if not team_id or not season:
        print("Please set team_id and season in data/settings.json")
        return
    matches, competitions = fetch(team_id, season, api_key)
    updated = is_data_updated(matches, "matches.json")
    if updated:
        save_data(matches, "matches.json")
        print(f"Saved {len(matches)} matches to data/matches.json")
    else:
        print("No changes in matches info.")

    # Save competitions regardless of match updates
    if competitions:
        save_data(list(competitions.values()), "competitions.json")
        print(f"Saved {len(competitions)} competitions to data/competitions.json")

    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
        f.write(f"updated={'true' if updated else 'false'}\n")


if __name__ == "__main__":
    main()
