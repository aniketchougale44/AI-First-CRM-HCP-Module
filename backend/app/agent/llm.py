from langchain_groq import ChatGroq

from app.config import settings


def get_llm(temperature: float = 0.2):
    """
    Returns a ChatGroq LLM instance.
    Primary model: gemma2-9b-it (fast, cheap - good for structured extraction).
    Fallback model (llama-3.3-70b-versatile) can be swapped in for tasks
    needing stronger reasoning (e.g. conversational follow-up suggestions).
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
    )


def get_llm_reasoning(temperature: float = 0.3):
    """Stronger model for reasoning-heavy tasks (follow-up suggestions, chat)."""
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL_FALLBACK,
        temperature=temperature,
    )
