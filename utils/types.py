from datetime import datetime
from typing import TypedDict

# ==========================================
# MODELS DE BASE DE DADES / SUPABASE
# ==========================================


class SettingsRow(TypedDict):
    home_team_id: int
    season_id: int


class PersonRow(TypedDict):
    id: int
    name: str
    first_surname: str
    second_surname: str
    clau_soci: int | None


class SeatRow(TypedDict):
    id: int
    owner_id: int
    clau_soci: int | None


class MatchRow(TypedDict):
    id: int
    date: str
    away_team_name: str | None
    away_team_shortname: str | None
    season_id: int


class ProcessedEmailRow(TypedDict):
    locator: str
    match_id: int | None
    registration_date: str | None
    processed_at: str


class AttendanceInsert(TypedDict):
    match_id: int
    seat_id: int
    person_id: int


# ==========================================
# MODELS D'APIS I PARSING (Football-Data / Email)
# ==========================================


class CompetitionDict(TypedDict):
    code: str
    name: str
    emblem: str | None


class TeamDict(TypedDict):
    id: int
    name: str
    shortname: str | None
    tla: str
    crest: str | None


class MatchDict(TypedDict):
    id: int
    season_id: int
    competition_code: str
    home_team_id: int
    away_team_id: int
    date: str
    status: str
    matchday: int | None


class AssistantInfo(TypedDict):
    name: str
    first_surname: str
    clau_soci: int | None


class ParsedEmail(TypedDict):
    locator: str | None
    rival: str | None
    registration_dt: datetime | None
    assistants: list[AssistantInfo]
