import json
import os
import logging
from app.config.model_factory import get_llm
from app.prompts.system_prompts import NEWS_ANALYST_PROMPT
from app.features.news_sentiment import analyze_news_sentiment
from app.features.sentiment_exporter import export_sentiment_analysis
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)

# Configuración de exportación automática
EXPORT_SENTIMENT = os.getenv("EXPORT_SENTIMENT_ANALYSIS", "true").lower() == "true"

def _create_chain(llm) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", NEWS_ANALYST_PROMPT),
        ("human", "{input}")
    ])
    return prompt | llm

def run_news_analysis(state: dict) -> dict:
    """
    Invoca al agente de análisis de noticias para procesar noticias y sentimiento.
    """
    print(f"--- AGENTE: Analista de Noticias y Sentimiento INPUT ---")
    llm = get_llm()
    chain = _create_chain(llm)
    
    news_data = state.get("news", {})
    if not news_data:
        return {"news_report": "No se encontraron noticias para el análisis."}

    reports = []
    for symbol, news_block in news_data.items():
        if news_block.get("error"):
            reports.append(f"No se pudieron obtener noticias para {symbol}.")
            continue

        try:
            # 1. Analizar sentimiento con FinBERT
            sentiment_analysis = analyze_news_sentiment(news_block, symbol)
            
            # 2. Exportar resultados si está habilitado
            if EXPORT_SENTIMENT and sentiment_analysis.get("article_count", 0) > 0:
                try:
                    exported_files = export_sentiment_analysis(
                        sentiment_analysis,
                        symbol
                    )
                    logger.info(f"Análisis de sentimiento exportado para {symbol}: {exported_files}")
                    print(f"✅ Sentimiento exportado: {exported_files}")
                except Exception as export_error:
                    logger.warning(f"No se pudo exportar análisis de sentimiento: {export_error}")
            
            # 3. Preparar contexto para el LLM
            context = {
                "symbol": symbol,
                "sentiment": sentiment_analysis,
                "articles": news_block.get("articles", [])[:5] # Limitar a 5 artículos para no exceder el contexto
            }
            input_str = json.dumps(context, indent=2, ensure_ascii=False)
            
            # 4. Invocar al LLM para el resumen cualitativo
            response = chain.invoke({"input": input_str})
            print(f"--- RESPONSE from NEWS ANALYST for {symbol} --- {response.content}")
            reports.append(f"--- Análisis de Noticias para {symbol} ---\n{response.content}")

        except Exception as e:
            print(f"Error en el agente de análisis de noticias para {symbol}: {e}")
            reports.append(f"[FALLBACK] No se pudo generar el informe de noticias para {symbol}.")

    print("--- AGENTE: Analista de Noticias y Sentimiento OUTPUT ---")
    print("\n\n".join(reports))
    return {
        "news_report": "\n\n".join(reports),
        "progress": 55.0,
        "current_step": "Analizando noticias y sentimiento..."
    }
