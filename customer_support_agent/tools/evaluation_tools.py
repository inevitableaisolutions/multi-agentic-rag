"""Tools for Agent 3: Evaluation Agent.

LLM-as-judge evaluation with the same metrics as RAGAS + DeepEval.
All evaluation is done via Gemini — zero external dependencies.
"""

from google.adk.tools import ToolContext


def evaluate_response(
    faithfulness_score: float,
    answer_relevance_score: float,
    context_relevance_score: float,
    hallucination_detected: bool,
    bias_detected: bool,
    toxicity_detected: bool,
    tone_appropriate: bool,
    pii_in_response: bool,
    overall_score: float,
    decision: str,
    revision_feedback: str,
    tool_context: ToolContext,
) -> dict:
    """Evaluate the quality of a customer support response.

    This implements the same metrics as RAGAS (faithfulness, answer_relevancy,
    context_precision) and DeepEval (hallucination, bias, toxicity) but using
    custom Gemini prompts — zero external dependencies, real-time evaluation.

    Args:
        faithfulness_score: 0.0-1.0 — % of claims supported by retrieved docs.
        answer_relevance_score: 0.0-1.0 — does the response answer the question?
        context_relevance_score: 0.0-1.0 — were retrieved docs actually useful?
        hallucination_detected: True if response contains info not in context.
        bias_detected: True if gender/racial/political bias found.
        toxicity_detected: True if harmful/offensive content found.
        tone_appropriate: True if tone matches customer sentiment.
        pii_in_response: True if PII was leaked in the response.
        overall_score: 0.0-1.0 weighted quality score.
        decision: One of: approve, revise, escalate.
        revision_feedback: Specific feedback if decision is revise.
        tool_context: ADK tool context for session state access.

    Returns:
        Evaluation result dict.
    """
    evaluation = {
        "faithfulness": faithfulness_score,
        "answer_relevance": answer_relevance_score,
        "context_relevance": context_relevance_score,
        "hallucination_detected": hallucination_detected,
        "bias_detected": bias_detected,
        "toxicity_detected": toxicity_detected,
        "tone_appropriate": tone_appropriate,
        "pii_in_response": pii_in_response,
        "overall_score": overall_score,
        "decision": decision,
        "revision_feedback": revision_feedback,
    }

    # Write to session state
    tool_context.state["qa_evaluation"] = evaluation

    return {
        "status": "evaluated",
        "evaluation": evaluation,
    }
