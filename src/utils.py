from __future__ import annotations
import json
from typing import Any

REQUIRED_KEYS = {
    "financial_summary", "financial_health_score", "spending_analysis", "risk_level",
    "top_priorities", "budget_recommendations", "savings_strategy", "next_month_action_plan",
}

def parse_financial_json(raw: Any) -> dict:
    """Parse and validate the expected JSON shape; tolerate fenced JSON but reject malformed data."""
    if isinstance(raw, dict):
        data = raw
    else:
        text = str(raw or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("The AI response was not valid JSON. Please try again.") from exc
    if not isinstance(data, dict):
        raise ValueError("The AI response must be a JSON object.")
    missing = REQUIRED_KEYS - set(data)
    if missing:
        raise ValueError(f"The AI response is missing required fields: {', '.join(sorted(missing))}")
    if not isinstance(data["financial_summary"], str):
        raise ValueError("financial_summary must be text.")
    try:
        score = int(data["financial_health_score"])
    except (TypeError, ValueError) as exc:
        raise ValueError("financial_health_score must be an integer.") from exc
    if not 0 <= score <= 100:
        raise ValueError("financial_health_score must be between 0 and 100.")
    if str(data["risk_level"]).upper() not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("risk_level must be LOW, MEDIUM, or HIGH.")
    list_fields = ["spending_analysis", "top_priorities", "budget_recommendations", "savings_strategy", "next_month_action_plan"]
    for key in list_fields:
        if not isinstance(data[key], list):
            raise ValueError(f"{key} must be a list.")
    for item in data["spending_analysis"]:
        if not isinstance(item, dict) or not all(k in item for k in ("category", "observation", "recommendation")):
            raise ValueError("Each spending_analysis item must contain category, observation, and recommendation.")
    data["financial_health_score"] = score
    data["risk_level"] = str(data["risk_level"]).upper()
    return data
