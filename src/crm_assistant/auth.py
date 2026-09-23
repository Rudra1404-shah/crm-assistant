import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"

_access_token: str | None = None
_expires_at: float = 0.0


def _refresh_access_token() -> str:
    global _access_token, _expires_at
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": os.getenv("ZOHO_CLIENT_ID"),
                "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
                "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        _access_token = data["access_token"]
        _expires_at = time.time() + data["expires_in"] - 60
        logger.info("Zoho access token refreshed (valid ~%ss)", data["expires_in"])
        return _access_token
    except requests.RequestException as e:
        logger.error("Failed to refresh Zoho access token: %s", e)
        raise


def get_access_token(force_refresh: bool = False) -> str:
    global _access_token
    if force_refresh or _access_token is None or time.time() >= _expires_at:
        return _refresh_access_token()
    return _access_token