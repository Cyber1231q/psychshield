"""Link verifier — checks URLs against known phishing databases.

Cross-references extracted URLs with the PhishTank CSV dataset and
performs structural URL analysis (typosquatting, suspicious TLDs,
IP-based hostnames, encoded characters, excessive URL length).
"""

import re
from urllib.parse import urlparse

from Levenshtein import distance as levenshtein_distance

from data.loaders.phishtank_loader import is_phishing_domain, is_phishing_url
from models.schemas import LinkVerificationResult, SenderVerification, URLFlag

BRANDS: list[str] = [
    "paypal", "google", "microsoft", "apple", "amazon",
    "facebook", "netflix", "instagram", "linkedin", "dropbox",
    "chase", "gmail", "outlook", "yahoo", "twitter", "whatsapp",
    "citibank", "wellsfargo", "barclays", "hsbc",
]

SUSPICIOUS_TLDS: list[str] = [
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".click", ".loan",
]

LEGIT_DOMAINS: set[str] = {
    "google.com", "gmail.com", "youtube.com", "microsoft.com",
    "outlook.com", "office.com", "apple.com", "icloud.com",
    "amazon.com", "aws.amazon.com", "facebook.com", "instagram.com",
    "twitter.com", "linkedin.com", "github.com", "stackoverflow.com",
    "paypal.com", "stripe.com", "netflix.com", "spotify.com",
    "dropbox.com", "zoom.us", "slack.com", "notion.so",
    "calebuniversity.edu.ng",
}


def extract_urls(text: str) -> list[str]:
    """Extract HTTP/HTTPS URLs including malformed variants."""
    normalized = re.sub(r'https?:{2,}//', 'http://', text)
    normalized = re.sub(r'hxxps?://', 'http://', normalized, flags=re.IGNORECASE)
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, normalized)


def is_typosquatted(domain: str) -> tuple[bool, str]:
    """Check if a domain is a typosquat of a known brand.

    Args:
        domain: The domain name to check (e.g. "paypa1-support.com").

    Returns:
        Tuple of (is_typosquatted, matched_brand). The brand string is
        empty if no match is found.
    """
    clean = domain.lower().replace("www.", "").split(".")[0]
    # Check the full subdomain label
    for brand in BRANDS:
        dist = levenshtein_distance(clean, brand)
        if 0 < dist <= 2:
            return True, brand
    # Also check segments split by hyphens/underscores
    for segment in re.split(r"[-_]", clean):
        if len(segment) < 3:
            continue
        for brand in BRANDS:
            dist = levenshtein_distance(segment, brand)
            if 0 < dist <= 2:
                return True, brand
    return False, ""


def analyze_url(url: str) -> tuple[list[str], float]:
    """Analyze a single URL for phishing indicators.

    Args:
        url: The full URL to analyze.

    Returns:
        Tuple of (flags, risk_score) where risk_score is 0.0–1.0.
    """
    flags: list[str] = []
    risk: float = 0.0
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if is_phishing_url(url):
        flags.append("Listed on PhishTank database")
        risk = max(risk, 0.95)

    if is_phishing_domain(hostname):
        flags.append("Domain listed on PhishTank")
        risk = max(risk, 0.90)

    squatted, brand = is_typosquatted(hostname)
    if squatted:
        flags.append(f"Typosquatting detected — mimics {brand}")
        risk = max(risk, 0.85)

    if re.match(r"^\d+\.\d+\.\d+\.\d+$", hostname):
        flags.append("IP address used as hostname")
        risk = max(risk, 0.70)

    if any(url.lower().endswith(tld) or f"{tld}/" in url.lower() for tld in SUSPICIOUS_TLDS):
        flags.append("Suspicious top-level domain")
        risk = max(risk, 0.60)

    if len(url) > 100:
        flags.append(f"Excessively long URL ({len(url)} chars)")
        risk = max(risk, 0.40)

    if re.search(r"%[0-9a-fA-F]{2}", parsed.path):
        flags.append("Encoded characters in URL path")
        risk = max(risk, 0.35)

    return flags, risk


def verify_links(body: str, sender: str = "") -> LinkVerificationResult:
    """Verify all links found in the email body.

    Args:
        body: The full email body text.
        sender: Optional sender email address for additional domain checks.

    Returns:
        LinkVerificationResult with per-URL flags and an overall link score.
    """
    urls = extract_urls(body)
    url_flags: list[URLFlag] = []
    max_risk: float = 0.0

    for url in urls:
        flags, risk = analyze_url(url)
        level = "High" if risk > 0.7 else "Medium" if risk > 0.4 else "Low"
        url_flags.append(URLFlag(url=url, flags=flags, riskLevel=level))
        max_risk = max(max_risk, risk)

    return LinkVerificationResult(
        model="PhishTank + Structural Analysis",
        linkScore=round(max_risk, 3),
        urls=url_flags,
    )


def verify_sender(sender_email: str) -> SenderVerification:
    """Verify sender identity based on email address analysis.

    Args:
        sender_email: The sender's email address.

    Returns:
        SenderVerification with domain checks and authentication status.
        SPF/DKIM/DMARC are set to FAIL for typosquatted domains.
    """
    parts = sender_email.split("@")
    domain = parts[1] if len(parts) == 2 else ""
    display_name = parts[0] if parts else sender_email
    squatted, _brand = is_typosquatted(domain)
    _is_legit = domain.lower() in LEGIT_DOMAINS

    return SenderVerification(
        **{"from": sender_email},
        displayName=display_name,
        domain=domain,
        typosquatted=squatted,
        spf="FAIL" if squatted else "UNKNOWN",
        dkim="FAIL" if squatted else "UNKNOWN",
        dmarc="FAIL" if squatted else "UNKNOWN",
        domainAgeDays=None,
    )
