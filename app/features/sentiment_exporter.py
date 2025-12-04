"""
Exportador de resultados de análisis de sentimiento.

Permite guardar los resultados detallados del análisis de sentimiento en formato JSON para análisis posterior,
auditoría y generación de reportes.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Directorio para exportaciones
EXPORT_DIR = Path("exports/sentiment")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_sentiment_analysis(
    sentiment_data: Dict[str, Any],
    symbol: str
) -> str:
    """
    Exporta el análisis de sentimiento completo a un archivo.
    
    Args:
        sentiment_data: Resultado de analyze_news_sentiment()
        symbol: Símbolo de la acción analizada
    
    Returns:
        str: Ruta(s) del archivo(s) generado(s)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{symbol}_sentiment_{timestamp}"
    
    exported_files = []
    
    try:
        json_file = _export_to_json(sentiment_data, symbol, base_filename)
        exported_files.append(json_file)
        
        logger.info(f"Análisis de sentimiento exportado: {', '.join(exported_files)}")
        return ", ".join(exported_files)
    
    except Exception as e:
        logger.exception(f"Error exportando análisis de sentimiento: {e}")
        return f"Error: {str(e)}"


def _export_to_json(sentiment_data: Dict[str, Any], symbol: str, base_filename: str) -> str:
    """
    Exporta a formato JSON estructurado.
    """
    filepath = EXPORT_DIR / f"{base_filename}.json"
    
    export_data = {
        "metadata": {
            "symbol": symbol,
            "export_timestamp": datetime.now().isoformat(),
            "analysis_method": sentiment_data.get("method", "finbert"),
            "version": "1.0"
        },
        "summary": {
            "aggregate_score": sentiment_data.get("aggregate_score", 0),
            "sentiment_label": sentiment_data.get("sentiment_label", "unknown"),
            "article_count": sentiment_data.get("article_count", 0),
            "average_confidence": sentiment_data.get("confidence", 0)
        },
        "articles": []
    }
    
    # Añadir detalles de cada artículo
    for i, detail in enumerate(sentiment_data.get("details", []), 1):
        article_data = {
            "article_number": i,
            "title": detail.get("title", ""),
            "combined_score": detail.get("score", 0),
            "combined_confidence": detail.get("confidence", 0),
            "age_weight": detail.get("age_weight", 1.0),
            "title_sentiment": {
                "sentiment": detail.get("title_sentiment", {}).get("sentiment", ""),
                "confidence": detail.get("title_sentiment", {}).get("confidence", 0),
                "scores": detail.get("title_sentiment", {}).get("scores", {}),
                "sentiment_score": detail.get("title_sentiment", {}).get("sentiment_score", 0)
            }
        }
        
        # Añadir sentimiento de contenido si existe
        if detail.get("desc_sentiment"):
            article_data["content_sentiment"] = {
                "sentiment": detail.get("desc_sentiment", {}).get("sentiment", ""),
                "confidence": detail.get("desc_sentiment", {}).get("confidence", 0),
                "scores": detail.get("desc_sentiment", {}).get("scores", {}),
                "sentiment_score": detail.get("desc_sentiment", {}).get("sentiment_score", 0)
            }
        
        export_data["articles"].append(article_data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exportado a JSON: {filepath}")
    return str(filepath)


def export_article_details(
    articles: List[Dict[str, Any]],
    symbol: str,
    sentiment_results: List[Dict[str, Any]],
    format: str = "json"
) -> str:
    """
    Exporta detalles completos de artículos incluyendo URLs y contenido original.
    
    Args:
        articles: Lista de artículos originales (con título, contenido, url)
        symbol: Símbolo de la acción
        sentiment_results: Resultados del análisis de sentimiento por artículo
    
    Returns:
        str: Ruta del archivo generado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_articles_detailed_{timestamp}.{format}"
    filepath = EXPORT_DIR / filename
    
    combined_data = []
    
    for i, (article, sentiment) in enumerate(zip(articles, sentiment_results), 1):
        combined_data.append({
            "article_number": i,
            "symbol": symbol,
            "title": article.get("title", ""),
            "content": article.get("content", "")[:500],  # Primeros 500 caracteres
            "url": article.get("url", ""),
            "sentiment_analysis": sentiment
        })
    
    if format == "json":
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "symbol": symbol,
                    "export_timestamp": datetime.now().isoformat(),
                    "article_count": len(combined_data)
                },
                "articles": combined_data
            }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Detalles de artículos exportados: {filepath}")
    return str(filepath)


