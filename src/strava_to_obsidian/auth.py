"""OAuth 2.0 authentication for Strava API."""

import http.server
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Optional

import requests

from strava_to_obsidian.config import Config

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
REDIRECT_PORT = 8080
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


@dataclass
class TokenResponse:
    """OAuth token response from Strava."""

    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: int
    athlete_name: str


class AuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""

    authorization_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth callback."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            AuthCallbackHandler.authorization_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Strava Authorization</title></head>
                <body style="font-family: system-ui; text-align: center; padding: 50px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        elif "error" in params:
            AuthCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: system-ui; text-align: center; padding: 50px;">
                    <h1>Authorization Failed</h1>
                    <p>{AuthCallbackHandler.error}</p>
                </body>
                </html>
            """.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


def get_authorization_url(client_id: str) -> str:
    """Generate Strava authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read,activity:read_all",
    }
    return f"{STRAVA_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    client_id: str, client_secret: str, code: str
) -> TokenResponse:
    """Exchange authorization code for access tokens."""
    response = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    athlete = data.get("athlete", {})
    return TokenResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=data["expires_at"],
        athlete_id=athlete.get("id", 0),
        athlete_name=f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
    )


def refresh_access_token(config: Config) -> bool:
    """Refresh the access token using refresh token."""
    if not config.strava.refresh_token:
        return False

    try:
        response = requests.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": config.strava.client_id,
                "client_secret": config.strava.client_secret,
                "refresh_token": config.strava.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        config.save_tokens(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
        )
        return True
    except requests.RequestException:
        return False


def is_token_expired(config: Config) -> bool:
    """Check if the access token is expired or will expire soon."""
    # Add 5 minute buffer
    return time.time() > (config.strava.token_expires_at - 300)


def ensure_valid_token(config: Config) -> bool:
    """Ensure we have a valid access token, refreshing if needed."""
    if not config.has_tokens():
        return False

    if is_token_expired(config):
        return refresh_access_token(config)

    return True


def authenticate(config: Config) -> Optional[TokenResponse]:
    """Run the full OAuth authentication flow."""
    if not config.has_valid_credentials():
        raise ValueError(
            "Missing Strava API credentials. Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET "
            "environment variables."
        )

    # Reset any previous state
    AuthCallbackHandler.authorization_code = None
    AuthCallbackHandler.error = None

    # Start local server to capture callback
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), AuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()

    # Open browser for authorization
    auth_url = get_authorization_url(config.strava.client_id)
    print(f"\nOpening browser for Strava authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if AuthCallbackHandler.error:
        raise ValueError(f"Authorization failed: {AuthCallbackHandler.error}")

    if not AuthCallbackHandler.authorization_code:
        raise ValueError("Authorization timed out. Please try again.")

    # Exchange code for tokens
    tokens = exchange_code_for_tokens(
        config.strava.client_id,
        config.strava.client_secret,
        AuthCallbackHandler.authorization_code,
    )

    # Save tokens
    config.save_tokens(tokens.access_token, tokens.refresh_token, tokens.expires_at)

    return tokens
