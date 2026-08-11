from urllib.parse import urljoin

import requests


class FootballDataClient:
    """Client for football-data.org API requests."""

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.timeout = timeout
        self.headers = {}
        if api_key:
            self.headers["X-Auth-Token"] = api_key

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        endpoint = endpoint.lstrip("/")
        url = urljoin(self.BASE_URL + "/", endpoint)
        response = requests.get(
            url,
            headers=self.headers,
            params=params or {},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def team_info(self, team_id: int, season: int) -> dict:
        return self.get(f"teams/{team_id}", {"season": season})

    def team_matches(self, team_id: int, season: int) -> dict:
        return self.get(f"teams/{team_id}/matches", {"season": season})
