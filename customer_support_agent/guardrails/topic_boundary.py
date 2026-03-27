"""Topic boundary enforcement for customer support queries.

Ensures queries are related to customer support topics:
billing, technical, account management, or general product questions.

Blocks: code generation, personal advice, harmful content, unrelated topics.
"""

import re

# Off-topic patterns (case-insensitive)
_REDIRECT = "I'm a customer support assistant for CloudSync Pro. I can help with billing, technical issues, account management, or general product questions. How can I assist you?"

OFF_TOPIC_PATTERNS = [
    # Code generation
    (re.compile(r"write\s+(me\s+)?(a\s+)?(\w+\s+)?(code|script|program|function)", re.IGNORECASE), _REDIRECT),
    # Hacking / security abuse
    (re.compile(r"(hack|exploit|crack|ddos|phish|leak|breach|dump)", re.IGNORECASE), "I can only assist with customer support inquiries. For security concerns, please contact our security team."),
    # Personal advice
    (re.compile(r"(dating|relationship|medical|legal|financial)\s+advice", re.IGNORECASE), _REDIRECT),
    # Entertainment
    (re.compile(r"(tell\s+me\s+a\s+joke|sing|poem|story|creative\s+writing)", re.IGNORECASE), _REDIRECT),
    # Asking about AI/projects (not customer support)
    (re.compile(r"(what\s+(are\s+)?your\s+projects|what\s+have\s+you\s+(done|built|made)|real.?time\s+projects)", re.IGNORECASE), _REDIRECT),
    # Generic greetings with no support question
    (re.compile(r"^(hi|hello|hey|wassup|sup|yo|what's up|whats up|howdy)\s*[!?.]*$", re.IGNORECASE), None),  # None = allow through but flag
    # Adversarial probing
    (re.compile(r"(you'?re\s+leaking|expose|reveal|show\s+me\s+(the|your)\s+(data|secret|key|token|password|credential))", re.IGNORECASE), "I can only assist with customer support inquiries. I don't have access to any sensitive data."),
    # Asking the AI to be something else
    (re.compile(r"(you\s+are\s+(a|an|my)|act\s+as|role\s*play|pretend)", re.IGNORECASE), _REDIRECT),
]

# On-topic keywords — if ANY of these are present, the query is likely on-topic
ON_TOPIC_KEYWORDS = [
    "account", "password", "login", "sign in", "billing", "charge", "payment",
    "refund", "subscription", "plan", "upgrade", "downgrade", "cancel",
    "error", "bug", "issue", "problem", "not working", "broken", "fix",
    "help", "support", "how to", "how do i", "setup", "install", "configure",
    "feature", "update", "pricing", "invoice", "receipt",
    "api", "integration", "connect", "sync", "data", "export", "import",
    "delete", "remove", "change", "reset", "access", "permission",
    "slow", "performance", "timeout", "crash", "outage",
    "2fa", "two factor", "security", "privacy", "gdpr",
]


def check_topic_boundary(query: str) -> dict:
    """Check if a query is within customer support topic boundaries.

    Returns:
        dict with:
            - is_on_topic: bool
            - suggested_response: str (pre-written response if off-topic)
            - confidence: float
    """
    query_lower = query.lower()

    # Check for explicit off-topic patterns first
    for pattern, response in OFF_TOPIC_PATTERNS:
        if pattern.search(query):
            if response is None:
                # Greeting — allow through (agents can handle greetings)
                return {
                    "is_on_topic": True,
                    "suggested_response": "",
                    "confidence": 0.7,
                }
            return {
                "is_on_topic": False,
                "suggested_response": response,
                "confidence": 0.95,
            }

    # Check for on-topic keywords
    for keyword in ON_TOPIC_KEYWORDS:
        if keyword in query_lower:
            return {
                "is_on_topic": True,
                "suggested_response": "",
                "confidence": 0.9,
            }

    # If no strong signal either way, default to on-topic
    # (better to answer a borderline query than block a legitimate one)
    return {
        "is_on_topic": True,
        "suggested_response": "",
        "confidence": 0.5,
    }
