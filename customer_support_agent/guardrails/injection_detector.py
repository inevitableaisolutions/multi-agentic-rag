"""Prompt injection detection using pattern matching.

Detects attempts to manipulate the AI system:
- "Ignore previous instructions"
- "You are now a..."
- "Reveal your system prompt"
- DAN-style jailbreaks
"""

import re

# Known injection patterns (case-insensitive)
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"show\s+(me\s+)?(your\s+)?system\s+(prompt|instructions)", re.IGNORECASE),
    re.compile(r"what\s+(are|is)\s+your\s+(system\s+)?instructions", re.IGNORECASE),
    re.compile(r"do\s+anything\s+now", re.IGNORECASE),  # DAN
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"bypass\s+(your\s+)?(safety|content|filter)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+you\s+are|a)\s+", re.IGNORECASE),
    re.compile(r"from\s+now\s+on\s+you\s+(will|are|must)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?(rules|guidelines|instructions)", re.IGNORECASE),
]


def detect_injection(query: str) -> dict:
    """Detect prompt injection attempts using pattern matching.

    Returns:
        dict with:
            - is_safe: bool (True if no injection detected)
            - reason: str (which pattern matched, if any)
            - confidence: float (1.0 for pattern match)
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(query)
        if match:
            return {
                "is_safe": False,
                "reason": f"Matched injection pattern: '{match.group()}'",
                "confidence": 1.0,
            }

    return {
        "is_safe": True,
        "reason": "No injection patterns detected",
        "confidence": 1.0,
    }
