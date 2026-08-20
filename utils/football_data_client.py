from urllib.parse import urljoin

import requests


class FootballDataClient:
    """Client for football-data.org API requests."""

    DEFAULT_BASE_URL = "https://api.football-data.org/v4"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Auth-Token": api_key,
            }
        )

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        endpoint = endpoint.lstrip("/")

        url = urljoin(
            f"{self.base_url}/",
            endpoint,
        )

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()

    def get_team_info(
        self,
        team_id: int,
        season: int,
    ) -> dict:
        return self.get(
            f"teams/{team_id}",
            {"season": season},
        )

    def get_team_matches(
        self,
        team_id: int,
        season: int,
    ) -> dict:
        return self.get(
            f"teams/{team_id}/matches",
            {"season": season},
        )

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
