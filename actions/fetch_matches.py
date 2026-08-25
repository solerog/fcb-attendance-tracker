#!/usr/bin/env python3
"""Sincronitza els partits des de Football-Data cap a Supabase utilitzant rangs de dates (15-Jul al 14-Jul)."""

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from dotenv import load_dotenv

from utils.db.supabase import supabase
from utils.football_data_client import FootballDataClient
from utils.types import (
    CompetitionDict,
    MatchDict,
    SettingsRow,
    TeamDict,
)

load_dotenv()


@dataclass(frozen=True)
class Settings:
    home_team_id: int
    season_id: int


def get_settings(home_team_id: int) -> list[Settings]:
    response = (
        supabase.table("settings")
        .select("home_team_id, season_id")
        .eq("home_team_id", home_team_id)
        .order("season_id")
        .execute()
    )

    rows = cast(list[SettingsRow], response.data or [])

    return [
        Settings(
            home_team_id=row["home_team_id"],
            season_id=row["season_id"],
        )
        for row in rows
    ]


def get_season_dates(season_id: int) -> tuple[date, date]:
    """Retorna l'inici (15 de juliol) i final (14 de juliol de l'any següent)."""
    return date(season_id, 7, 15), date(season_id, 7, 14).replace(year=season_id + 1)


def get_season_id_for_date(match_date_str: str, settings_list: list[Settings]) -> int:
    """Calcula el season_id d'un partit a partir de la seva data."""
    match_dt = datetime.fromisoformat(match_date_str)
    match_date = match_dt.date()

    for s in settings_list:
        d_from, d_to = get_season_dates(s.season_id)
        if d_from <= match_date <= d_to:
            return s.season_id

    # Per defecte si no encaixa exactament
    return match_dt.year if match_dt.month >= 7 else match_dt.year - 1


def build_competitions(raw_matches: list[dict[str, Any]]) -> list[CompetitionDict]:
    competitions: dict[str, CompetitionDict] = {}
    for match in raw_matches:
        comp = match["competition"]
        code = comp["code"]
        if code not in competitions:
            competitions[code] = {
                "code": code,
                "name": comp["name"],
                "emblem": comp.get("emblem"),
            }
    return list(competitions.values())


def build_teams(raw_matches: list[dict[str, Any]]) -> list[TeamDict]:
    teams: dict[int, TeamDict] = {}
    for match in raw_matches:
        for team in (match["homeTeam"], match["awayTeam"]):
            team_id = team["id"]
            if team_id not in teams:
                teams[team_id] = {
                    "id": team_id,
                    "name": team["name"],
                    "shortname": team.get("shortName"),
                    "tla": team.get("tla") or "",
                    "crest": team.get("crest"),
                }
    return list(teams.values())


def build_matches(
    raw_matches: list[dict[str, Any]], settings_list: list[Settings]
) -> list[MatchDict]:
    matches: list[MatchDict] = []
    for match in raw_matches:
        season_id = get_season_id_for_date(match["utcDate"], settings_list)
        matches.append(
            {
                "id": match["id"],
                "season_id": season_id,
                "competition_code": match["competition"]["code"],
                "home_team_id": match["homeTeam"]["id"],
                "away_team_id": match["awayTeam"]["id"],
                "date": match["utcDate"],
                "status": match["status"],
                "matchday": match.get("matchday"),
            }
        )
    return matches


def upsert_data(table: str, data: list[dict[str, Any]], on_conflict: str) -> None:
    if not data:
        return
    supabase.table(table).upsert(data, on_conflict=on_conflict).execute()


def sync_matches(full_fetch: bool = False) -> None:
    home_team_id = int(os.environ["HOME_TEAM_ID"])
    api_key = os.environ["FOOTBALL_DATA_API_KEY"]

    settings_list = get_settings(home_team_id)
    if not settings_list:
        raise RuntimeError(
            f"No s'han trobat paràmetres a settings per a HOME_TEAM_ID={home_team_id}"
        )

    target_settings = (
        settings_list if full_fetch else [max(settings_list, key=lambda s: s.season_id)]
    )

    all_ranges = [get_season_dates(s.season_id) for s in target_settings]
    min_date_from = min(r[0] for r in all_ranges)
    max_date_to = max(r[1] for r in all_ranges)

    if not full_fetch:
        min_date_from = datetime.now(UTC).date() - timedelta(days=2)

    all_raw_matches: list[dict[str, Any]] = []

    with FootballDataClient(api_key=api_key) as client:
        print(
            f"  📅 Consultant: {min_date_from.strftime('%Y-%m-%d')} -> {max_date_to.strftime('%Y-%m-%d')}"
        )

        response = client.get_team_matches_date(
            team_id=home_team_id,
            date_from=min_date_from,
            date_to=max_date_to,
        )

        all_raw_matches.extend(response.get("matches", []))

    # 3. Processar i estructurar les dades
    competitions = build_competitions(all_raw_matches)
    teams = build_teams(all_raw_matches)
    matches = build_matches(all_raw_matches, settings_list)

    # 4. Guardar a Supabase
    upsert_data("competitions", cast(list[dict[str, Any]], competitions), "code")
    upsert_data("teams", cast(list[dict[str, Any]], teams), "id")
    upsert_data("matches", cast(list[dict[str, Any]], matches), "id")

    print(
        f"    🥅 {len(matches)} partits sincronitzats\n"
        f"    ⚽ {len(teams)} equips\n"
        f"    🏆 {len(competitions)} competicions\n"
        "  ✅ Sincronització completada"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sincronitza partits des de Football-Data cap a Supabase mitjançant rangs de dates."
    )
    parser.add_argument(
        "-f",
        "--full",
        "--full-fetch",
        dest="full_fetch",
        action="store_true",
        default=False,
        help="Si s'activa, sincronitza totes les temporades registrades des del 15 de juliol inicial.",
    )

    args = parser.parse_args()
    sync_matches(full_fetch=args.full_fetch)
