"""Tests for the link verifier module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.loaders.phishtank_loader import load_phishtank
from detectors.link_verifier import verify_links, extract_urls, is_typosquatted


def test_phishtank_loads():
    urls, domains = load_phishtank()
    assert len(urls) > 0 or len(domains) > 0


def test_typosquatted_domain_detected():
    result = verify_links("https://paypa1-support.com/verify", "")
    assert result.linkScore > 0.5


def test_legitimate_url_no_flags():
    result = verify_links("Visit https://calebuniversity.edu.ng for info", "")
    assert result.linkScore < 0.5


def test_ip_url_flagged():
    result = verify_links("Click http://192.168.1.1/login", "")
    assert result.linkScore > 0


def test_suspicious_tld_flagged():
    result = verify_links("Go to https://example.xyz/verify", "")
    assert result.linkScore > 0


def test_no_urls_scores_zero():
    result = verify_links("No links in this email at all", "")
    assert result.linkScore == 0
    assert len(result.urls) == 0


def test_extract_urls_finds_links():
    urls = extract_urls("Visit https://example.com and http://test.org/path")
    assert len(urls) == 2


def test_extract_urls_ignores_non_urls():
    urls = extract_urls("Just plain text, no links here")
    assert len(urls) == 0


def test_typosquatted_paypal():
    is_typo, brand = is_typosquatted("paypa1.com")
    assert is_typo is True
    assert brand == "paypal"


def test_legitimate_domain_not_typosquatted():
    is_typo, _ = is_typosquatted("google.com")
    assert is_typo is False


def test_link_score_between_zero_and_one():
    result = verify_links("https://evil.xyz/phish http://1.2.3.4/bad", "")
    assert 0 <= result.linkScore <= 1.0


def test_multiple_urls_scored():
    result = verify_links(
        "Link1: https://paypa1.com/a Link2: https://g00gle.xyz/b", ""
    )
    assert len(result.urls) == 2
