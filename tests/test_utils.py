import pytest
from src.utils import parse_financial_json

VALID = {
    "financial_summary": "A sample summary.",
    "financial_health_score": 72,
    "spending_analysis": [{"category": "Food", "observation": "High share", "recommendation": "Plan meals"}],
    "risk_level": "LOW",
    "top_priorities": ["Track food spending"],
    "budget_recommendations": ["Set a weekly limit"],
    "savings_strategy": ["Automate a small transfer"],
    "next_month_action_plan": ["Review spending weekly"],
}

def test_parses_valid_dict():
    assert parse_financial_json(VALID)["financial_health_score"] == 72

def test_parses_fenced_json():
    import json
    assert parse_financial_json("```json\n" + json.dumps(VALID) + "\n```")["risk_level"] == "LOW"

def test_rejects_missing_fields():
    with pytest.raises(ValueError):
        parse_financial_json({"financial_summary": "incomplete"})

def test_rejects_out_of_range_score():
    bad = dict(VALID, financial_health_score=120)
    with pytest.raises(ValueError):
        parse_financial_json(bad)
