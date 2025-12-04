from langchain_ollama import ChatOllama
from .settings import (
    DEFAULT_MODEL_PROVIDER,
    OLLAMA_MODEL,
    LM_STUDIO_MODEL,
    LM_STUDIO_BASE_URL,
    TEMPERATURE,
)


def get_llm(provider: str | None = None):
    """Return an LLM client based on provider.

    ChatOpenAI se importa de forma diferida solo si se solicita lm_studio
    para evitar coste de inicialización SSL cuando solo usamos Ollama.
    """
    provider = provider or DEFAULT_MODEL_PROVIDER
    if provider == "lm_studio":
        # Lazy import to speed up cold start when not needed
        from langchain_openai import ChatOpenAI  # type: ignore
        return ChatOpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key="lm-studio",
            model=LM_STUDIO_MODEL,
            temperature=TEMPERATURE,
        )
    return ChatOllama(model=OLLAMA_MODEL, temperature=TEMPERATURE, num_predict=4096)
