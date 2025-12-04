import json
import logging
import os

from langchain_tavily import TavilySearch

from app.tools.mocks.news_mocks import ALL_MOCKS

logger = logging.getLogger(__name__)

# --- TAVILY TOOL ---
# Inicializar Tavily solo si hay API key
_tavily_tool = None
if os.getenv("TAVILY_API_KEY"):
    try:
        if os.getenv("TAVILY_API_KEY"):
            _tavily_tool = TavilySearch(max_results=5)
    except Exception as e:
        logger.warning(f"No se pudo inicializar Tavily: {e}")


def search_financial_news(company_name: str, symbol: str) -> str:
    """
    Busca noticias financieras recientes sobre una empresa.
    Utiliza datos mock si USE_MOCK_NEWS está configurado.
    
    La configuración mock se lee dinámicamente en cada llamada para permitir
    testing flexible sin reiniciar el sistema.
    """
    # Configuración
    use_mock_data = os.getenv("USE_MOCK_NEWS", "false").lower() == "true"
    mock_scenario = os.getenv("MOCK_NEWS_SCENARIO", "DEFAULT").upper()
    
    logger.debug(f"USE_MOCK_NEWS={use_mock_data}, MOCK_SCENARIO={mock_scenario}")
    
    if use_mock_data:
        logger.warning(f"Usando datos MOCK para la búsqueda de noticias de {symbol}.")
        
        mock_data = ALL_MOCKS.get(mock_scenario, ALL_MOCKS["DEFAULT"])
        
        # Devuelve los datos mock si el símbolo coincide, sino un error simulado.
        if symbol == mock_data["symbol"]:
            return json.dumps(mock_data, ensure_ascii=False)
        else:
            # Si el símbolo no coincide, busca un mock que sí lo haga.
            for scenario, data in ALL_MOCKS.items():
                if data["symbol"] == symbol:
                    logger.warning(f"Símbolo '{symbol}' no coincide con el escenario '{mock_scenario}'. Usando escenario '{scenario}'.")
                    return json.dumps(data, ensure_ascii=False)
            
            # Si no se encuentra ningún mock para el símbolo, devuelve un aviso.
            return json.dumps({
                "warning": f"Datos MOCK no encontrados para el símbolo '{symbol}'.",
                "symbol": symbol,
                "articles": []
            })

    if not _tavily_tool:
        return json.dumps({
            "error": "La API key de Tavily (TAVILY_API_KEY) no está configurada y el modo mock está desactivado.",
            "symbol": symbol,
            "articles": [],
        })

    try:
        query = f"financial news and analysis for {company_name} ({symbol})"
        logger.info(f"Buscando noticias con Tavily: {query}")

        results = _tavily_tool.invoke(query)

        if not isinstance(results, list):
            logger.warning(f"Tavily no devolvió una lista para {symbol}. Resultado: {results}")
            results = []

        logger.info(f"Encontrados {len(results)} artículos para {symbol} a través de Tavily.")

        return json.dumps(
            {
                "symbol": symbol,
                "company": company_name,
                "query": query,
                "articles": results,
                "article_count": len(results),
            },
            ensure_ascii=False,
        )

    except Exception as e:
        logger.exception("La herramienta de búsqueda de noticias (Tavily) falló.")
        return json.dumps({"error": str(e), "symbol": symbol, "articles": []})