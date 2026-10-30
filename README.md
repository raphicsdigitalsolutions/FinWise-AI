# FinWise AI — Smart Budget Intelligence

An educational Streamlit prototype for the **AI-Powered Personal Financial Analysis and Smart Budget Assistant** assignment. It combines deterministic Python calculations with LangChain-powered structured financial education.

## Safety and privacy
FinWise AI is an educational prototype, not financial, investment, tax, or legal advice. It does not connect to bank accounts, execute transactions, guarantee outcomes, or recommend specific investments. Every screen includes a disclaimer. Consult a qualified financial professional for important decisions. Use fictional data in demonstrations; never enter bank credentials or account numbers.

AI requests send the entered budget figures to OpenAI through the configured API key. The SQLite cache stores prompts and responses in plaintext. Use fictional demonstration data and keep `.env`, Streamlit secrets, and `data/*.db` out of GitHub.

## Features
- Monthly income, nine named expense categories, current savings, goal, and currency.
- Deterministic totals, remaining balance, savings ratio, expense ratio, debt ratio, and transparent preliminary score.
- Rule-based risk indicator separate from the AI assessment.
- LangChain `ChatOpenAI`, reusable `LLMChain`, `PromptTemplate`, `ChatPromptTemplate`, and System/Human/AI message example.
- Validated structured JSON output and friendly error handling.
- Live recommendation streaming via `llm.stream()` and `st.write_stream()`.
- Off, in-memory, and SQLite cache modes.
- Premium dark Streamlit dashboard with animated 3D-inspired hero orb, metrics, and interactive spending chart.

## Requirements
- Python 3.10+
- OpenAI API key for model-based analysis
- Internet access for package installation and API calls

## Windows setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```
Set your own key in `.env`:
```dotenv
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```
Then run:
```powershell
streamlit run app.py
```

## Streamlit Community Cloud
Deploy the GitHub repository and add `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in **App settings → Secrets**. Never commit `.env` or `secrets.toml`. Visitors should not be asked to expose personal API keys unless they trust the deployment.

## Python vs AI
Python deterministically computes totals, ratios, and a transparent preliminary score. The LLM interprets the supplied figures and generates educational narrative and recommendations. The AI score is not the same as the Python score and is not a regulated financial assessment.

## Caching
- **Off:** no LangChain cache.
- **In-memory:** process memory; cleared when the app process restarts.
- **SQLite:** persists to `data/langchain_cache.db`; prompts and responses are stored in plaintext. Never use real sensitive financial data with SQLite caching.

## Testing
```powershell
python -m pip install pytest
python -m pytest -q
```

## Assignment note
The assignment states “ten expense categories” but explicitly names nine: housing/rent, food, transportation, utilities, education, healthcare, entertainment, loan/debt, and other. This implementation includes the nine named categories rather than inventing an unspecified tenth category.

## Project structure
See `src/` for modular calculation, prompts, chains, cache, and JSON parsing; `tests/` for automated unit tests.
