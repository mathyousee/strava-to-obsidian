"""Configuration management for Strava to Obsidian exporter."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class StravaConfig:
    """Strava API configuration."""

    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""
    refresh_token: str = ""
    token_expires_at: int = 0


@dataclass
class Config:
    """Main configuration for the exporter."""

    strava: StravaConfig = field(default_factory=StravaConfig)
    output_dir: Path = field(default_factory=lambda: Path("./activities"))

    # Token file location
    token_file: Path = field(default_factory=lambda: Path(".strava_tokens.json"))

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file and environment variables."""
        # Load .env file if it exists (looks in current dir and parents)
        load_dotenv()

        config = cls()

        # Load from environment variables (including those from .env)
        config.strava.client_id = os.environ.get("STRAVA_CLIENT_ID", "")
        config.strava.client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")

        # Load tokens from token file if it exists
        token_file = config_path.parent / ".strava_tokens.json" if config_path else config.token_file
        if token_file.exists():
            try:
                with open(token_file) as f:
                    tokens = json.load(f)
                    config.strava.access_token = tokens.get("access_token", "")
                    config.strava.refresh_token = tokens.get("refresh_token", "")
                    config.strava.token_expires_at = tokens.get("expires_at", 0)
            except (json.JSONDecodeError, OSError):
                pass

        return config

    def save_tokens(self, access_token: str, refresh_token: str, expires_at: int) -> None:
        """Save OAuth tokens to file."""
        self.strava.access_token = access_token
        self.strava.refresh_token = refresh_token
        self.strava.token_expires_at = expires_at

        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }

        # Create parent directory if needed
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

        # Write with restricted permissions
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)

        # Set file permissions to user-only (Unix)
        try:
            os.chmod(self.token_file, 0o600)
        except OSError:
            pass  # Windows doesn't support chmod the same way

    def has_valid_credentials(self) -> bool:
        """Check if we have valid Strava API credentials."""
        return bool(self.strava.client_id and self.strava.client_secret)

    def has_tokens(self) -> bool:
        """Check if we have OAuth tokens."""
        return bool(self.strava.access_token and self.strava.refresh_token)
