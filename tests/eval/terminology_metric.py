"""Metric evaluating accurate Kerala property and Malayalam legal terminology."""

from typing import Any, Dict
from tests.eval.response_quality import evaluate_terminology


def evaluate(instance: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate_terminology(instance)
