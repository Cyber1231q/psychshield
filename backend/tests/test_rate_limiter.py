"""Tests for the shared rate limiter (utils/rate_limiter.py).

Runs against the in-memory fallback, since no Redis server is expected to
be running for local test execution — REDIS_URL is unset in the test
environment, so the module never attempts a connection.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException
import pytest

from utils import rate_limiter


def _key() -> str:
    """A fresh, collision-free key per test."""
    return f"test:{uuid.uuid4().hex}"


def test_check_allows_under_limit():
    key = _key()
    rate_limiter.record(key, window_seconds=60)
    rate_limiter.check(key, max_attempts=3, window_seconds=60)  # should not raise


def test_check_blocks_at_limit():
    key = _key()
    for _ in range(3):
        rate_limiter.record(key, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        rate_limiter.check(key, max_attempts=3, window_seconds=60)
    assert exc_info.value.status_code == 429


def test_clear_resets_the_window():
    key = _key()
    for _ in range(3):
        rate_limiter.record(key, window_seconds=60)
    rate_limiter.clear(key)
    rate_limiter.check(key, max_attempts=3, window_seconds=60)  # should not raise


def test_check_bool_returns_false_at_limit():
    key = _key()
    for _ in range(2):
        rate_limiter.record(key, window_seconds=60)
    assert rate_limiter.check_bool(key, max_attempts=2, window_seconds=60) is False


def test_check_bool_returns_true_under_limit():
    key = _key()
    assert rate_limiter.check_bool(key, max_attempts=2, window_seconds=60) is True


def test_different_keys_are_independent():
    key_a, key_b = _key(), _key()
    for _ in range(5):
        rate_limiter.record(key_a, window_seconds=60)
    rate_limiter.check(key_b, max_attempts=1, window_seconds=60)  # unaffected by key_a
