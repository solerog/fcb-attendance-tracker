import os
from dataclasses import dataclass
from typing import cast

from utils.db.supabase import supabase
from utils.football_data_client import FootballDataClient
from utils.types import (
    CompetitionDict,
    MatchDict,
    SettingsRow,
    TeamDict,
)


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

    rows = cast(list[SettingsRow], response.data)

    return [
        Settings(
            home_team_id=row["home_team_id"],
            season_id=row["season_id"],
        )
        for row in rows
    ]


def build_competitions(
    raw_matches: list[dict],
) -> list[CompetitionDict]:
    competitions: dict[str, CompetitionDict] = {}

    for match in raw_matches:
        competition = match["competition"]
        code = competition["code"]

        if code in competitions:
            continue

        competitions[code] = {
            "code": code,
            "name": competition["name"],
            "emblem": competition.get("emblem"),
        }

    return list(competitions.values())


def build_teams(
    raw_matches: list[dict],
) -> list[TeamDict]:
    teams: dict[int, TeamDict] = {}

    for match in raw_matches:
        for team in (
            match["homeTeam"],
            match["awayTeam"],
        ):
            team_id = team["id"]

            if team_id in teams:
                continue

            teams[team_id] = {
                "id": team_id,
                "name": team["name"],
                "shortname": team.get("shortName"),
                "tla": team.get("tla") or "",
                "crest": team.get("crest"),
            }

    return list(teams.values())


def build_matches(
    raw_matches: list[dict],
    season_id: int,
) -> list[MatchDict]:
    matches: list[MatchDict] = []

    for match in raw_matches:
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


def upsert_data(
    table: str,
    data: list[dict],
    on_conflict: str,
) -> None:
    if not data:
        return

    (
        supabase.table(table)
        .upsert(
            data,
            on_conflict=on_conflict,
        )
        .execute()
    )


def sync_matches() -> None:
    home_team_id = int(os.environ["HOME_TEAM_ID"])
    api_key = os.environ["FOOTBALL_DATA_API_KEY"]

    settings_list = get_settings(home_team_id)

    if not settings_list:
        raise RuntimeError(f"No settings found for HOME_TEAM_ID={home_team_id}")

    all_competitions: dict[str, CompetitionDict] = {}
    all_teams: dict[int, TeamDict] = {}
    all_matches: dict[int, MatchDict] = {}

    with FootballDataClient(
        api_key=api_key,
    ) as client:
        for settings in settings_list:
            two_digit_year = settings.season_id % 100
            print(
                f"  📖 Llegint partits de la temporada {two_digit_year:02d}/{(two_digit_year + 1):02d}"
            )

            response = client.get_team_matches(
                team_id=settings.home_team_id,
                season=settings.season_id,
            )

            raw_matches = response["matches"]

            for competition in build_competitions(raw_matches):
                all_competitions[competition["code"]] = competition

            for team in build_teams(raw_matches):
                all_teams[team["id"]] = team

            for match in build_matches(
                raw_matches,
                settings.season_id,
            ):
                all_matches[match["id"]] = match

    upsert_data(
        table="competitions",
        data=cast(list[dict], list(all_competitions.values())),
        on_conflict="code",
    )

    upsert_data(
        table="teams",
        data=cast(list[dict], list(all_teams.values())),
        on_conflict="id",
    )

    upsert_data(
        table="matches",
        data=cast(list[dict], list(all_matches.values())),
        on_conflict="id",
    )

    print(
        f"    🥅 {len(all_matches)} partits\n"
        f"    ⚽ {len(all_teams)} equips\n"
        f"    🏆 {len(all_competitions)} competicions\n"
        "  ✅ Sincronització completada"
    )


if __name__ == "__main__":
    sync_matches()
