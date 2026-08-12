#!/usr/bin/env python3
"""Fetch matches from api-football and write normalized JSON"""

import os

from utils.helper import (
    is_list_dicts_updated,
    load_settings,
    save_data,
)
from utils.url import FootballDataClient


def fetch(team_id: int, season: int, api_key: str) -> tuple[list[dict], list[dict]]:
    client = FootballDataClient(api_key=api_key)
    data = client.team_matches(team_id, season)
    items = data.get("matches", [])

    competitions_dict: dict[str, dict] = {}
    home_matches: list[dict] = []

    for it in items:
        if it.get("homeTeam", {}).get("id") != team_id:
            continue
        comp_code = it.get("competition", {}).get("code")
        if comp_code and comp_code not in competitions_dict:
            competitions_dict[comp_code] = {
                "code": comp_code,
                "name": it.get("competition", {}).get("name"),
                "crest": it.get("competition", {}).get("crest"),
            }
        match = {
            "id": it.get("id"),
            "date": it.get("utcDate"),
            "away_name": it.get("awayTeam", {}).get("name"),
            "away_shortname": it.get("awayTeam", {}).get("shortName"),
            "away_tla": it.get("awayTeam", {}).get("tla"),
            "away_crest": it.get("awayTeam", {}).get("crest"),
            "competition_code": comp_code,
            "matchday": it.get("matchday"),
            "status": it.get("status"),
        }
        home_matches.append(match)
    competitions: list[dict] = list(competitions_dict.values())
    return home_matches, competitions


def main():
    settings = load_settings()
    team_id = settings.get("team_id")
    season = settings.get("season")
    api_key = os.environ.get("FOOTBALL_DATA_KEY")

    if not team_id or not season:
        raise ValueError("Set team_id and season in data/settings.json")
    if not api_key:
        raise ValueError("Set FOOTBALL_DATA_KEY in your environment variables")

    matches, competitions = fetch(team_id, season, api_key)

    matches_updated = is_list_dicts_updated(matches, "matches.json")
    if matches_updated:
        save_data(matches, "matches.json")
        print(f"Saved {len(matches)} matches to data/matches.json")
    else:
        print("No changes in matches info.")

    comp_updated = is_list_dicts_updated(competitions, "competitions.json")
    if comp_updated:
        save_data(competitions, "competitions.json")
        print(f"Saved {len(competitions)} competitions to data/competitions.json")

    with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
        f.write(f"updated={'true' if matches_updated or comp_updated else 'false'}\n")


if __name__ == "__main__":
    main()
