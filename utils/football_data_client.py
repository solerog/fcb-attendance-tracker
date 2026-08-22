import types
from datetime import date, datetime
from typing import Any, Self

import requests


class FootballDataClient:
    """Client for football-data.org API requests."""

    DEFAULT_BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": self.api_key})

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.session.close()

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.DEFAULT_BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_team_matches_date(
        self,
        team_id: int,
        date_from: str | date | datetime,
        date_to: str | date | datetime,
    ) -> dict[str, Any]:
        """Obté els partits d'un equip dins del rang exacte de dates."""
        date_from_str = (
            date_from.strftime("%Y-%m-%d")
            if isinstance(date_from, (date, datetime))
            else str(date_from)
        )
        date_to_str = (
            date_to.strftime("%Y-%m-%d")
            if isinstance(date_to, (date, datetime))
            else str(date_to)
        )

        return self.get(
            f"teams/{team_id}/matches",
            {"dateFrom": date_from_str, "dateTo": date_to_str},
        )
