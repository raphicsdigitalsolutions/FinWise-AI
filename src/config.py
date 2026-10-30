from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "FinWise AI"
APP_TAGLINE = "Your money, made clearer."
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CURRENCIES = ["PKR", "USD", "GBP", "EUR", "AED", "SAR", "INR", "CAD", "AUD"]
FINANCIAL_GOALS = [
    "Save money", "Build an emergency fund", "Pay off debt",
    "Plan a vacation", "Start a business", "Improve budgeting",
]
# The assignment names nine categories while saying ten. We preserve all nine named categories.
EXPENSE_CATEGORIES = [
    "Housing / Rent", "Food", "Transportation", "Utilities",
    "Education", "Healthcare", "Entertainment", "Loan / Debt", "Other",
]
