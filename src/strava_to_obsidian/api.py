"""Strava API client."""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator, Optional

import requests

from strava_to_obsidian.auth import ensure_valid_token
from strava_to_obsidian.config import Config

STRAVA_API_BASE = "https://www.strava.com/api/v3"


@dataclass
class RateLimitInfo:
    """Rate limit information from API response."""

    limit_15min: int = 100
    usage_15min: int = 0
    limit_daily: int = 1000
    usage_daily: int = 0

    @property
    def remaining_15min(self) -> int:
        return self.limit_15min - self.usage_15min

    @property
    def remaining_daily(self) -> int:
        return self.limit_daily - self.usage_daily

    def is_limited(self) -> bool:
        return self.usage_15min >= self.limit_15min or self.usage_daily >= self.limit_daily


class StravaAPIError(Exception):
    """Strava API error."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class StravaClient:
    """Client for Strava API."""

    def __init__(self, config: Config):
        self.config = config
        self.rate_limit = RateLimitInfo()
        self._session = requests.Session()

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.config.strava.access_token}"}

    def _update_rate_limits(self, response: requests.Response) -> None:
        """Update rate limit info from response headers."""
        limit_header = response.headers.get("X-RateLimit-Limit", "")
        usage_header = response.headers.get("X-RateLimit-Usage", "")

        if limit_header and usage_header:
            try:
                limits = limit_header.split(",")
                usages = usage_header.split(",")
                self.rate_limit.limit_15min = int(limits[0])
                self.rate_limit.limit_daily = int(limits[1])
                self.rate_limit.usage_15min = int(usages[0])
                self.rate_limit.usage_daily = int(usages[1])
            except (IndexError, ValueError):
                pass

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Any:
        """Make an API request with error handling and rate limiting."""
        # Ensure we have a valid token
        if not ensure_valid_token(self.config):
            raise StravaAPIError("Not authenticated. Run 'strava-to-obsidian auth' first.")

        url = f"{STRAVA_API_BASE}{endpoint}"

        try:
            response = self._session.request(
                method,
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30,
            )
            self._update_rate_limits(response)

            if response.status_code == 429:
                # Rate limited - wait and retry
                if retry_count < 3:
                    wait_time = 60 * (2**retry_count)  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._request(method, endpoint, params, retry_count + 1)
                raise StravaAPIError("Rate limit exceeded. Try again later.", 429)

            if response.status_code == 401:
                raise StravaAPIError("Authentication failed. Run 'strava-to-obsidian auth'.", 401)

            if response.status_code == 403:
                raise StravaAPIError("Access forbidden. Check API permissions.", 403)

            if response.status_code == 404:
                raise StravaAPIError("Resource not found.", 404)

            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            if retry_count < 3:
                time.sleep(5)
                return self._request(method, endpoint, params, retry_count + 1)
            raise StravaAPIError("Request timed out.")

        except requests.RequestException as e:
            raise StravaAPIError(f"Request failed: {e}")

    def get_athlete(self) -> dict[str, Any]:
        """Get authenticated athlete profile."""
        return self._request("GET", "/athlete")

    def get_activities(
        self,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        per_page: int = 200,
    ) -> Iterator[dict[str, Any]]:
        """
        Get all activities with pagination.

        Args:
            after: Only return activities after this date
            before: Only return activities before this date
            per_page: Number of activities per page (max 200)

        Yields:
            Activity summary dictionaries
        """
        page = 1
        params: dict[str, Any] = {"per_page": min(per_page, 200)}

        if after:
            params["after"] = int(after.timestamp())
        if before:
            params["before"] = int(before.timestamp())

        while True:
            params["page"] = page
            activities = self._request("GET", "/athlete/activities", params)

            if not activities:
                break

            yield from activities

            if len(activities) < per_page:
                break

            page += 1

    def get_activity_detail(self, activity_id: int) -> dict[str, Any]:
        """Get detailed activity information."""
        return self._request("GET", f"/activities/{activity_id}")

    def get_rate_limit_status(self) -> str:
        """Get human-readable rate limit status."""
        return (
            f"Rate limits: {self.rate_limit.usage_15min}/{self.rate_limit.limit_15min} (15 min), "
            f"{self.rate_limit.usage_daily}/{self.rate_limit.limit_daily} (daily)"
        )
