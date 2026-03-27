"""Input guardrails — PII redaction, prompt injection detection, topic boundary."""

from customer_support_agent.guardrails.pii_detector import detect_and_redact_pii
from customer_support_agent.guardrails.injection_detector import detect_injection
from customer_support_agent.guardrails.topic_boundary import check_topic_boundary


def run_guardrails(query: str) -> dict:
    """Run all input guardrails on a query.

    Returns:
        dict with keys:
            - sanitized_query: str (PII redacted)
            - is_safe: bool (passed all checks)
            - blocked_reason: str | None (why it was blocked)
            - pii_detected: list[str] (types of PII found)
            - details: dict (full guardrail results)
    """
    # Step 1: PII detection and redaction
    pii_result = detect_and_redact_pii(query)
    sanitized_query = pii_result["sanitized_query"]

    # Step 2: Prompt injection detection (on sanitized query)
    injection_result = detect_injection(sanitized_query)
    if not injection_result["is_safe"]:
        return {
            "sanitized_query": sanitized_query,
            "is_safe": False,
            "blocked_reason": f"Prompt injection detected: {injection_result['reason']}",
            "pii_detected": pii_result["pii_types"],
            "details": {"pii": pii_result, "injection": injection_result},
        }

    # Step 3: Topic boundary check (on sanitized query)
    topic_result = check_topic_boundary(sanitized_query)
    if not topic_result["is_on_topic"]:
        return {
            "sanitized_query": sanitized_query,
            "is_safe": False,
            "blocked_reason": f"Off-topic query: {topic_result['suggested_response']}",
            "pii_detected": pii_result["pii_types"],
            "details": {"pii": pii_result, "topic": topic_result},
        }

    return {
        "sanitized_query": sanitized_query,
        "is_safe": True,
        "blocked_reason": None,
        "pii_detected": pii_result["pii_types"],
        "details": {"pii": pii_result, "injection": injection_result, "topic": topic_result},
    }
