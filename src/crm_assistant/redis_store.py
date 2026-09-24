import logging
import os

import redis
from dotenv import load_dotenv
from langchain_core.load import dumps, loads

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_SECONDS = 60 * 60 * 24  # sessions expire after 24h of inactivity

_client = redis.from_url(REDIS_URL, decode_responses=True)


def _key(session_id: str) -> str:
    return f"chat:session:{session_id}"


def load_history(session_id: str) -> list:
    """Load a session's message history from Redis. Returns [] if none exists
    or if Redis can't be reached - a down Redis degrades chat to no-memory,
    it doesn't take the whole endpoint down."""
    try:
        raw = _client.get(_key(session_id))
    except Exception as e:
        logger.error("Could not reach Redis to load session %s: %s", session_id, e)
        return []
    if not raw:
        return []
    try:
        return loads(raw, allowed_objects="messages")
    except Exception as e:
        logger.error("Failed to deserialize session %s, starting fresh: %s", session_id, e)
        return []


def save_history(session_id: str, messages: list) -> None:
    """Save a session's full message history to Redis with a TTL."""
    try:
        _client.set(_key(session_id), dumps(messages), ex=SESSION_TTL_SECONDS)
    except Exception as e:
        logger.error("Failed to save session %s to Redis: %s", session_id, e)