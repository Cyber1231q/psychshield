"""Sliding-window rate limiter — Redis-backed when available, in-memory
fallback otherwise.

The in-memory implementation (a per-process dict) works fine for local
dev and a single-instance deployment, but resets on every restart and
can't be shared across multiple backend instances behind a load
balancer — an attacker who gets load-balanced across instances effectively
gets max_attempts * instance_count tries instead of max_attempts.

Setting REDIS_URL makes rate limits durable and shared across instances.
Leaving it unset (or Redis being unreachable) keeps the previous
zero-dependency behavior automatically — callers don't need to know or
care which backend is active; the interface (check/record/clear) is the
same either way.
"""

import logging
import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger("psychshield")

REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

_redis_client = None
if REDIS_URL:
    try:
        import redis as _redis_module

        _redis_client = _redis_module.from_url(
            REDIS_URL, socket_connect_timeout=2, socket_timeout=2
        )
        _redis_client.ping()
        logger.info("Rate limiting backed by Redis at %s", REDIS_URL)
    except Exception as exc:  # noqa: BLE001 - any import/connect failure just falls back
        logger.warning(
            "REDIS_URL is set but Redis isn't reachable (%s) — "
            "falling back to in-memory rate limiting.",
            exc,
        )
        _redis_client = None

_memory_store: dict[str, list[float]] = defaultdict(list)


def _prune_memory(key: str, window_seconds: int) -> list[float]:
    window_start = time.time() - window_seconds
    attempts = [t for t in _memory_store[key] if t > window_start]
    _memory_store[key] = attempts
    return attempts


def _count(key: str, window_seconds: int) -> int:
    if _redis_client is not None:
        try:
            window_start = time.time() - window_seconds
            _redis_client.zremrangebyscore(key, 0, window_start)
            return _redis_client.zcard(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Redis rate-limit read failed (%s) — using in-memory for this call.",
                exc,
            )
    return len(_prune_memory(key, window_seconds))


def check(key: str, max_attempts: int, window_seconds: int) -> None:
    """Raise HTTP 429 if `key` already has >= max_attempts within the window."""
    if _count(key, window_seconds) >= max_attempts:
        raise HTTPException(
            status_code=429, detail="Too many attempts. Try again later."
        )


def check_bool(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Same check as check(), but returns False instead of raising.

    Used by endpoints (like forgot-password) that must return a normal
    response either way, to avoid leaking whether an email is registered.
    """
    return _count(key, window_seconds) < max_attempts


def record(key: str, window_seconds: int) -> None:
    """Record one attempt for `key` right now."""
    now = time.time()
    if _redis_client is not None:
        try:
            _redis_client.zadd(key, {f"{now}:{os.urandom(4).hex()}": now})
            _redis_client.expire(key, window_seconds)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Redis rate-limit write failed (%s) — using in-memory for this call.",
                exc,
            )
    _memory_store[key].append(now)


def clear(key: str) -> None:
    """Reset a key's attempt history (e.g. after a successful login)."""
    if _redis_client is not None:
        try:
            _redis_client.delete(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis rate-limit clear failed (%s)", exc)
    _memory_store.pop(key, None)
