"""PhishTank loader — reads and indexes the PhishTank CSV for fast URL lookups.

Loads data/phishtank/online-valid.csv into a set of known phishing URLs
and a set of phishing domains for O(1) membership checks during link
verification.
"""

import logging
import os
from urllib.parse import urlparse

import pandas as pd

logger = logging.getLogger(__name__)

_CSV_PATH: str = os.getenv(
    "PHISHTANK_CSV_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "phishtank", "online-valid.csv"),
)

_phishtank_urls: set[str] = set()
_phishtank_domains: set[str] = set()
_loaded: bool = False


def load_phishtank() -> tuple[set[str], set[str]]:
    """Load the PhishTank CSV and populate URL and domain sets.

    Returns:
        Tuple of (phishing_urls, phishing_domains). Both are empty sets
        if the CSV file is missing or unreadable.
    """
    global _phishtank_urls, _phishtank_domains, _loaded

    if _loaded:
        return _phishtank_urls, _phishtank_domains

    csv_path = os.path.normpath(_CSV_PATH)

    try:
        df = pd.read_csv(csv_path, usecols=["url"])
        raw_urls = df["url"].dropna().astype(str)

        for raw in raw_urls:
            url = raw.strip().lower()
            if not url:
                continue
            _phishtank_urls.add(url)
            try:
                parsed = urlparse(url)
                domain = parsed.hostname
                if domain:
                    _phishtank_domains.add(domain)
            except Exception:
                continue

        _loaded = True
        logger.info(
            "PhishTank loaded: %d URLs, %d domains from %s",
            len(_phishtank_urls),
            len(_phishtank_domains),
            csv_path,
        )
    except FileNotFoundError:
        logger.warning("PhishTank CSV not found at %s — running with empty dataset", csv_path)
        _loaded = True
    except Exception as exc:
        logger.warning("Failed to load PhishTank CSV: %s — running with empty dataset", exc)
        _loaded = True

    return _phishtank_urls, _phishtank_domains


def is_phishing_url(url: str) -> bool:
    """Check if a URL is in the PhishTank phishing URL set."""
    return url.strip().lower() in _phishtank_urls


def is_phishing_domain(domain: str) -> bool:
    """Check if a domain is in the PhishTank phishing domain set."""
    return domain.strip().lower() in _phishtank_domains


def get_phishtank_stats() -> dict:
    """Return loading statistics for health checks and diagnostics."""
    return {
        "total_urls": len(_phishtank_urls),
        "total_domains": len(_phishtank_domains),
        "loaded": _loaded,
    }


# Auto-load on import
load_phishtank()
