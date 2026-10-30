from __future__ import annotations
from pathlib import Path
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_community.cache import SQLiteCache

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "langchain_cache.db"

def configure_cache(mode: str):
    """Register the selected LangChain cache. Personal financial data should remain fictional."""
    normalized = mode.lower()
    if normalized == "off":
        set_llm_cache(None)
        return "Cache is off."
    if normalized == "in-memory":
        set_llm_cache(InMemoryCache())
        return "In-memory cache is active for this Python process."
    if normalized == "sqlite":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=str(DB_PATH)))
        return f"SQLite cache is active at {DB_PATH}."
    raise ValueError("Cache mode must be Off, In-memory, or SQLite.")
