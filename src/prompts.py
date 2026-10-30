from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

JSON_SCHEMA = {
    "financial_summary": "string",
    "financial_health_score": 0,
    "spending_analysis": [{"category": "string", "observation": "string", "recommendation": "string"}],
    "risk_level": "LOW | MEDIUM | HIGH",
    "top_priorities": ["string"],
    "budget_recommendations": ["string"],
    "savings_strategy": ["string"],
    "next_month_action_plan": ["string"],
}

SYSTEM_INSTRUCTIONS = """You are FinWise AI, an educational personal budgeting assistant.
You are NOT a financial adviser. Provide general informational budgeting education only.
Never guarantee returns, recommend specific investments, execute transactions, or claim certainty.
Do not ask for bank credentials or account numbers. Use only the supplied synthetic or user-entered
figures. Explain uncertainty and encourage a qualified financial professional for important decisions.
Return valid JSON only, matching exactly this schema:
{{
 "financial_summary": "string",
 "financial_health_score": 0,
 "spending_analysis": [{"category":"string","observation":"string","recommendation":"string"}],
 "risk_level": "LOW | MEDIUM | HIGH",
 "top_priorities": ["string"],
 "budget_recommendations": ["string"],
 "savings_strategy": ["string"],
 "next_month_action_plan": ["string"]
}}
Score must be an integer from 0 to 100. Do not claim the score is a regulated or clinical measure.
Keep recommendations practical, respectful, and grounded in the provided numbers."""

FINANCIAL_PROMPT = PromptTemplate(
    input_variables=[
        "monthly_income", "total_expenses", "remaining_income", "savings",
        "savings_ratio", "expense_ratio", "financial_goal", "expense_breakdown",
    ],
    template="""Create a personalized educational monthly budget analysis.
Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Financial goal: {financial_goal}
Expense breakdown: {expense_breakdown}
Return the required JSON only. Clearly identify the largest spending categories and propose
actions that fit the numbers. Do not invent missing facts."""
)

NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTIONS + "\nWrite a concise plain-language explanation of the analysis. Do not add investment advice."),
    ("human", """Income: {monthly_income}
Expenses: {total_expenses}
Remaining: {remaining_income}
Savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Goal: {financial_goal}
Breakdown: {expense_breakdown}
Explain the key takeaway and 3 practical budgeting actions."""),
])

def message_demo(financial_data: str):
    """Explicit SystemMessage/HumanMessage/AIMessage example for the assignment."""
    return [
        SystemMessage(content="You are an educational budgeting assistant. No investment advice."),
        HumanMessage(content=financial_data),
        AIMessage(content="I will explain the provided budget figures for educational purposes."),
    ]
