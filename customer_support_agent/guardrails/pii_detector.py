"""PII detection and redaction using regex patterns.

Detects: SSN, credit cards, phone numbers, emails, IP addresses.
Redacts by replacing with tokens like [REDACTED_SSN].
"""

import re


# PII patterns: (name, regex, replacement token)
PII_PATTERNS = [
    (
        "SSN",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[REDACTED_SSN]",
    ),
    (
        "CREDIT_CARD",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "[REDACTED_CREDIT_CARD]",
    ),
    (
        "PHONE",
        re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "[REDACTED_PHONE]",
    ),
    (
        "EMAIL",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        "IP_ADDRESS",
        re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        "[REDACTED_IP]",
    ),
]


def detect_and_redact_pii(text: str) -> dict:
    """Detect and redact PII from text using regex patterns.

    Returns:
        dict with:
            - sanitized_query: str with PII replaced by tokens
            - pii_types: list of PII types found (e.g., ["SSN", "EMAIL"])
            - pii_count: int total PII instances found
            - original_had_pii: bool
    """
    sanitized = text
    pii_types_found = []
    total_count = 0

    for pii_name, pattern, replacement in PII_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            pii_types_found.append(pii_name)
            total_count += len(matches)
            sanitized = pattern.sub(replacement, sanitized)

    return {
        "sanitized_query": sanitized,
        "pii_types": pii_types_found,
        "pii_count": total_count,
        "original_had_pii": total_count > 0,
    }
