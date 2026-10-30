from src.financial_calculator import calculate_financial_metrics, score_band, risk_band

def test_calculates_income_expenses_and_ratios():
    result = calculate_financial_metrics(8000, {"Food": 1000, "Housing / Rent": 1000}, 1200)
    assert result["total_expenses"] == 2000
    assert result["remaining_income"] == 6000
    assert result["savings_ratio"] == 15
    assert result["expense_ratio"] == 25
    assert 0 <= result["preliminary_score"] <= 100

def test_zero_income_does_not_divide_by_zero():
    result = calculate_financial_metrics(0, {"Food": 100}, 0)
    assert result["savings_ratio"] == 0
    assert result["expense_ratio"] == 100
    assert result["preliminary_score"] == 0

def test_negative_remaining_means_high_risk():
    result = calculate_financial_metrics(2000, {"Food": 2600}, 0)
    assert result["remaining_income"] == -600
    assert risk_band(result) == "HIGH"

def test_score_bands_match_assignment():
    assert score_band(85) == "Strong"
    assert score_band(70) == "Generally healthy"
    assert score_band(50) == "Needs improvement"
    assert score_band(25) == "High attention"
