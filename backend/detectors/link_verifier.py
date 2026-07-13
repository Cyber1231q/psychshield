"""Link verifier — checks URLs against known phishing databases.

Cross-references extracted URLs with the PhishTank CSV dataset and
performs structural URL analysis (typosquatting, suspicious TLDs,
IP-based hostnames, encoded characters, excessive URL length).
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import dns.exception
import dns.resolver
import whois as _whois_module
from Levenshtein import distance as levenshtein_distance

from data.loaders.phishtank_loader import is_phishing_domain, is_phishing_url
from models.schemas import LinkVerificationResult, SenderVerification, URLFlag

logger = logging.getLogger("psychshield")

_DNS_TIMEOUT_SECONDS = 3.0

# python-whois can make several sequential socket connections per lookup
# (root registry server, then a referral to the registrar's own WHOIS
# server) — each one respects its own internal timeout, so the *total*
# wall-clock time isn't actually bounded by any single-socket timeout
# setting. A thread pool + future.result(timeout=...) gives a real,
# enforced deadline on the whole call regardless of how many hops happen
# inside it, which is what actually matters for request latency.
_WHOIS_TIMEOUT_SECONDS = 3.0
_whois_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="whois")

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


def verify_links(body: str, sender: str = "") -> LinkVerificationResult:  # noqa: ARG001
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

    if not url_flags:
        link_reason = "No URLs found in email body"
    elif max_risk == 0.0:
        link_reason = "Link risk: 0/100 — no suspicious indicators detected"
    else:
        top_flag = max(url_flags, key=lambda u: u.riskLevel == "High")
        detail = ", ".join(top_flag.flags[:2]).lower() if top_flag.flags else "suspicious structure"
        link_reason = f"Link risk: {round(max_risk * 100)}/100 — {detail}"

    return LinkVerificationResult(
        model="PhishTank + Structural Analysis",
        linkScore=round(max_risk, 3),
        urls=url_flags,
        linkReason=link_reason,
    )


def _txt_records(domain: str) -> list[str]:
    """Resolve TXT records for a domain, returning an empty list on any failure."""
    try:
        answers = dns.resolver.resolve(domain, "TXT", lifetime=_DNS_TIMEOUT_SECONDS)
        return [b"".join(r.strings).decode("utf-8", errors="ignore") for r in answers]
    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        return []
    except Exception as exc:  # pragma: no cover - defensive, DNS libs can raise oddly
        logger.warning("DNS TXT lookup failed for %s: %s", domain, exc)
        return []


def _check_spf_record(domain: str) -> str:
    """Check whether the domain publishes an SPF policy.

    This confirms the domain *has* an SPF record configured — legitimate
    organizations almost always do, and many throwaway phishing domains
    don't. It cannot confirm that *this specific email* passed SPF, since
    that requires the sending server's IP address, which isn't available
    for pasted or uploaded email text (only real message delivery — e.g.
    Gmail — carries that). Returns PASS/FAIL/UNKNOWN.
    """
    if not domain:
        return "UNKNOWN"
    records = _txt_records(domain)
    if not records:
        return "UNKNOWN"
    return "PASS" if any(r.lower().startswith("v=spf1") for r in records) else "FAIL"


def _check_dmarc_record(domain: str) -> str:
    """Check whether the domain publishes a DMARC policy at _dmarc.<domain>."""
    if not domain:
        return "UNKNOWN"
    records = _txt_records(f"_dmarc.{domain}")
    if not records:
        return "UNKNOWN"
    return "PASS" if any(r.lower().startswith("v=dmarc1") for r in records) else "FAIL"


def _check_domain_age(domain: str) -> Optional[int]:
    """Look up how many days ago `domain` was registered via WHOIS.

    Returns None — never raises, never blocks past _WHOIS_TIMEOUT_SECONDS
    — if the lookup fails, times out, or the registry doesn't expose a
    creation date. That's common enough (rate limiting, privacy-protected
    registrations, unsupported TLDs) that "unavailable" must never be
    treated as "suspicious" by itself; see _sender_risk_score in
    risk_scorer.py, which weighs None the same as an UNKNOWN SPF/DKIM/DMARC
    result rather than as evidence of anything.
    """
    if not domain:
        return None
    try:
        future = _whois_executor.submit(_whois_module.whois, domain)
        record = future.result(timeout=_WHOIS_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        logger.warning(
            "WHOIS lookup for %s exceeded %.1fs — abandoning it", domain, _WHOIS_TIMEOUT_SECONDS
        )
        return None
    except Exception as exc:  # noqa: BLE001 - whois libs raise all sorts of things
        logger.warning("WHOIS lookup failed for %s: %s", domain, exc)
        return None

    created = record.creation_date
    if isinstance(created, list):
        created = created[0] if created else None
    if created is None:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - created).days
    return max(age_days, 0)


def verify_sender(sender_email: str, check_dns: bool = True) -> SenderVerification:
    """Verify sender identity based on email address analysis.

    Args:
        sender_email: The sender's email address.
        check_dns: If True (default), look up live SPF/DMARC DNS records
            and the domain's WHOIS registration age. Callers that already
            have a more authoritative per-message verdict (e.g. Gmail's
            own Authentication-Results header) should pass False and
            apply their own SPF/DKIM/DMARC values instead — and skip the
            WHOIS lookup too, since it's a blocking network call and
            those callers typically loop over many messages per request
            (see routers/gmail.py's scan loop), where paying a WHOIS
            round-trip per message would add real latency for a signal
            Gmail's own header doesn't cover anyway.

    Returns:
        SenderVerification with domain checks and authentication status.
        SPF/DKIM/DMARC are set to FAIL outright for typosquatted domains.
        DKIM is never checked here — verifying a DKIM signature requires
        the DKIM-Signature header (selector + domain) and the actual
        signed message bytes, neither of which are available from a bare
        sender address; it stays UNKNOWN unless overridden by a caller
        with access to a real per-message verdict. domainAgeDays is None
        whenever check_dns=False or the WHOIS lookup fails/times out —
        never treated as evidence of anything by the risk scorer.
    """
    parts = sender_email.split("@")
    domain = parts[1] if len(parts) == 2 else ""
    display_name = parts[0] if parts else sender_email
    squatted, _brand = is_typosquatted(domain)

    if squatted:
        spf = dkim = dmarc = "FAIL"
        domain_age_days = None
    elif check_dns:
        spf = _check_spf_record(domain)
        dmarc = _check_dmarc_record(domain)
        dkim = "UNKNOWN"
        domain_age_days = _check_domain_age(domain)
    else:
        spf = dkim = dmarc = "UNKNOWN"
        domain_age_days = None

    return SenderVerification(
        **{"from": sender_email},
        displayName=display_name,
        domain=domain,
        typosquatted=squatted,
        spf=spf,
        dkim=dkim,
        dmarc=dmarc,
        domainAgeDays=domain_age_days,
    )
