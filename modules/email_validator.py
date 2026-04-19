"""
Email Validation Module
-----------------------
Two levels of validation:

Level 1 — Format check
  Checks structure: has @, has domain, has extension, no spaces,
  no invalid characters, proper length etc.

Level 2 — Domain DNS check
  Checks if the email domain actually exists on the internet
  by looking up its MX (mail exchange) records.
  e.g. abc@xyz123fake.com → domain doesn't exist → rejected
       abc@gmail.com      → domain exists → accepted
"""

import re
import socket


# ── Known valid domains (fast check — skip DNS for these) ─────────────
KNOWN_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "protonmail.com", "rediffmail.com", "ymail.com",
    "live.com", "msn.com", "me.com", "aol.com",
}

# ── Disposable/temp email domains to block ────────────────────────────
BLOCKED_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "throwam.com", "yopmail.com", "sharklasers.com",
    "trashmail.com", "fakeinbox.com", "dispostable.com",
    "maildrop.cc", "spam4.me", "getairmail.com",
}


def _check_format(email: str) -> tuple[bool, str]:
    """
    Level 1: Validate email format strictly.
    Returns (valid, error_message)
    """
    email = email.strip()

    if not email:
        return False, "Email address cannot be empty."

    if " " in email:
        return False, "Email address cannot contain spaces."

    if email.count("@") != 1:
        return False, "Email address must contain exactly one '@' symbol."

    local, domain = email.split("@")

    if not local:
        return False, "Please enter something before the '@' symbol."

    if len(local) > 64:
        return False, "The part before '@' is too long."

    if not domain:
        return False, "Please enter a domain after '@' (e.g. gmail.com)."

    if "." not in domain:
        return False, "Email domain must contain a '.' (e.g. gmail.com, yahoo.com)."

    parts = domain.split(".")
    if any(len(p) == 0 for p in parts):
        return False, "Invalid domain format in email address."

    tld = parts[-1]
    if len(tld) < 2:
        return False, "Email domain extension is too short (e.g. .com, .in, .org)."

    # Regex for overall format
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format. Please use a format like name@example.com"

    return True, ""


def _check_domain(domain: str) -> tuple[bool, str]:
    """
    Level 2: Check if domain actually exists using DNS lookup.
    Returns (valid, error_message)
    """
    # Skip DNS for known domains (faster)
    if domain.lower() in KNOWN_DOMAINS:
        return True, ""

    # Block disposable email services
    if domain.lower() in BLOCKED_DOMAINS:
        return False, f"Disposable/temporary email addresses are not allowed. Please use a real email."

    # DNS lookup — check if domain resolves
    try:
        socket.getaddrinfo(domain, None)
        return True, ""
    except socket.gaierror:
        return False, f"The email domain '@{domain}' does not exist. Please check and try again."
    except Exception:
        # If DNS check fails for network reasons, allow it through
        # (don't block user just because of network issue)
        return True, ""


def validate_email(email: str, check_domain: bool = True) -> tuple[bool, str]:
    """
    Full email validation — format + optional domain check.

    Args:
        email:        The email string to validate
        check_domain: If True, also checks if the domain exists via DNS

    Returns:
        (is_valid: bool, message: str)
        message is empty string if valid, error message if invalid
    """
    email = email.strip().lower()

    # Level 1 — format
    fmt_ok, fmt_msg = _check_format(email)
    if not fmt_ok:
        return False, fmt_msg

    if not check_domain:
        return True, ""

    # Extract domain
    domain = email.split("@")[1]

    # Level 2 — domain existence
    dns_ok, dns_msg = _check_domain(domain)
    if not dns_ok:
        return False, dns_msg

    return True, ""


def get_email_suggestion(email: str) -> str | None:
    """
    Suggests correction for common typos in email domains.
    e.g. 'user@gmial.com' → suggests 'user@gmail.com'
    Returns suggestion string or None.
    """
    common_typos = {
        "gmial.com":    "gmail.com",
        "gmai.com":     "gmail.com",
        "gmail.co":     "gmail.com",
        "gmail.cm":     "gmail.com",
        "gmailcom":     "gmail.com",
        "yahooo.com":   "yahoo.com",
        "yaho.com":     "yahoo.com",
        "yahoo.co":     "yahoo.com",
        "hotmial.com":  "hotmail.com",
        "hotmail.co":   "hotmail.com",
        "outlok.com":   "outlook.com",
        "outloo.com":   "outlook.com",
        "redifmail.com":"rediffmail.com",
    }

    if "@" not in email:
        return None

    local, domain = email.strip().lower().split("@", 1)
    suggestion = common_typos.get(domain)
    if suggestion:
        return f"{local}@{suggestion}"
    return None