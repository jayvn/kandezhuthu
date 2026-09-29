"""Metric evaluating mandatory statutory disclaimers and 100% clean title guardrails."""

from typing import Any, Dict
from tests.eval.response_quality import evaluate_guardrails


def evaluate(instance: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate_guardrails(instance)
