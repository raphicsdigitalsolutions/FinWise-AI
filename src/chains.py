from __future__ import annotations
import json
from langchain_openai import ChatOpenAI
from langchain_classic.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from .prompts import SYSTEM_INSTRUCTIONS, FINANCIAL_PROMPT, NARRATIVE_CHAT_TEMPLATE
from .utils import parse_financial_json

def build_llm(api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.2):
    if not api_key or not api_key.strip():
        raise ValueError("An OpenAI API key is required for AI analysis.")
    return ChatOpenAI(api_key=api_key.strip(), model=model, temperature=temperature, timeout=60, max_retries=2)

def build_analysis_chain(llm):
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_INSTRUCTIONS),
        ("human", FINANCIAL_PROMPT.template),
    ])
    return LLMChain(llm=llm, prompt=prompt, output_key="analysis_json")

def run_analysis(llm, inputs: dict) -> dict:
    chain = build_analysis_chain(llm)
    result = chain.invoke(inputs)
    raw = result.get("analysis_json", "")
    return parse_financial_json(raw)

def stream_recommendations(llm, inputs: dict):
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        content = chunk.content
        if isinstance(content, str) and content:
            yield content
