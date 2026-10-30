from __future__ import annotations
from typing import Mapping

def calculate_financial_metrics(
    monthly_income: float,
    expenses: Mapping[str, float],
    current_savings: float,
) -> dict:
    """Deterministic financial calculations. No AI or external services are used."""
    income = max(float(monthly_income), 0.0)
    savings = max(float(current_savings), 0.0)
    clean_expenses = {str(k): max(float(v or 0), 0.0) for k, v in expenses.items()}
    total_expenses = sum(clean_expenses.values())
    remaining_income = income - total_expenses
    savings_ratio = (savings / income * 100) if income > 0 else 0.0
    expense_ratio = (total_expenses / income * 100) if income > 0 else (100.0 if total_expenses > 0 else 0.0)
    debt = clean_expenses.get("Loan / Debt", 0.0)
    debt_ratio = (debt / income * 100) if income > 0 else (100.0 if debt > 0 else 0.0)

    # Transparent heuristic: savings 35%, remaining balance 30%, expense ratio 25%, debt 10%.
    if income <= 0:
        score = 0
    else:
        savings_component = min(savings_ratio / 20.0, 1.0) * 35
        leftover_ratio = max(remaining_income / income, 0.0)
        leftover_component = min(leftover_ratio / 0.30, 1.0) * 30
        expense_component = max(0.0, 1.0 - max(expense_ratio - 50.0, 0.0) / 100.0) * 25
        debt_component = max(0.0, 1.0 - debt_ratio / 50.0) * 10
        score = round(max(0.0, min(100.0, savings_component + leftover_component + expense_component + debt_component)))

    return {
        "monthly_income": round(income, 2),
        "total_expenses": round(total_expenses, 2),
        "remaining_income": round(remaining_income, 2),
        "current_savings": round(savings, 2),
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
        "debt_ratio": round(debt_ratio, 2),
        "preliminary_score": int(score),
        "expense_breakdown": clean_expenses,
    }

def score_band(score: int) -> str:
    if score >= 80: return "Strong"
    if score >= 60: return "Generally healthy"
    if score >= 40: return "Needs improvement"
    return "High attention"

def risk_band(metrics: dict) -> str:
    if metrics["remaining_income"] < 0 or metrics["expense_ratio"] > 100 or metrics["debt_ratio"] >= 50:
        return "HIGH"
    if metrics["remaining_income"] == 0 or metrics["expense_ratio"] >= 80 or metrics["debt_ratio"] >= 30:
        return "MEDIUM"
    return "LOW"
