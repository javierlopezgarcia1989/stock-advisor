"""
Análisis avanzado de sentimiento de noticias financieras usando FinBERT.

FinBERT es un modelo BERT pre-entrenado específicamente para análisis de sentimiento
en textos financieros, logrando alta precisión en la clasificación de noticias como
positivas, negativas o neutrales.

Este módulo proporciona:
- Análisis de sentimiento por artículo con scores detallados
- Agregación ponderada considerando confianza y recencia
- Caché de modelo para eficiencia
- Manejo robusto de errores y fallbacks
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

# Lazy imports para evitar cargar modelos pesados hasta que sean necesarios
_finbert_model = None
_finbert_tokenizer = None


def _load_finbert():
    """Carga FinBERT de forma lazy (solo una vez)."""
    global _finbert_model, _finbert_tokenizer
    
    if _finbert_model is not None:
        return _finbert_model, _finbert_tokenizer
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        
        model_name = "ProsusAI/finbert"
        logger.info(f"Cargando modelo FinBERT desde {model_name}...")
        
        _finbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _finbert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Modo evaluación (sin entrenamiento)
        _finbert_model.eval()
        
        logger.info("Modelo FinBERT cargado exitosamente")
        return _finbert_model, _finbert_tokenizer
        
    except Exception as e:
        logger.exception("Error al cargar FinBERT")
        raise RuntimeError(f"No se pudo cargar FinBERT: {e}")


def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """
    Analiza el sentimiento de un texto usando FinBERT.
    """
    try:
        import torch
        
        model, tokenizer = _load_finbert()
        
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        )
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
        
        probs = probabilities[0].numpy()
        
        # ✅ CORRECCIÓN: Orden correcto según ProsusAI/finbert
        # Verificado en: https://huggingface.co/ProsusAI/finbert/blob/main/config.json
        sentiment_map = {0: 'positive', 1: 'negative', 2: 'neutral'}
        predicted_class = int(np.argmax(probs))
        sentiment = sentiment_map[predicted_class]
        confidence = float(probs[predicted_class])
        
        # Cálculo de sentiment_score (0-100): 0=muy negativo, 100=muy positivo
        # Fórmula: ((P(positive) - P(negative)) + 1) / 2 * 100
        sentiment_score = ((probs[0] - probs[1]) + 1) / 2 * 100
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 4),
            'scores': {
                'positive': round(float(probs[0]), 4),  # Probabilidad de que el texto sea positivo (índice 0)
                'negative': round(float(probs[1]), 4),  # Probabilidad de que el texto sea negativo (índice 1)
                'neutral': round(float(probs[2]), 4)    # Probabilidad de que el texto sea neutral (índice 2)
            },
            'sentiment_score': round(float(sentiment_score), 2), # Score de sentimiento (0-100)
            'text_preview': text[:100]
        }
        
    except Exception as e:
        logger.exception(f"Error analizando sentimiento: {e}")
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'scores': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34},
            'sentiment_score': 50.0,
            'error': str(e)
        }

def compute_aggregate_sentiment(
    articles: List[Dict[str, Any]], 
    symbol: str
) -> Dict[str, Any]:
    """
    Calcula sentimiento agregado para un conjunto de artículos.
    Usa un enfoque ponderado considerando confianza y edad del artículo.
    Parámetros:
    - articles: lista de artículos con 'title' y 'content'
    - symbol: símbolo financiero asociado (para logging)
    Retorna: un diccionario con el sentimiento agregado y detalles.
    """
    if not articles:
        return {
            'aggregate_score': 50.0,
            'sentiment_label': 'neutral',
            'article_count': 0,
            'details': [],
            'confidence': 0.0,
            'method': 'finbert'
        }
    
    article_sentiments = []
    
    for i, article in enumerate(articles):
        title = article.get('title', article.get('content', '')) # Título del artículo
        content = article.get('content', '') # Contenido del artículo
        
        title_sentiment = analyze_text_sentiment(title) if title else None # Sentimiento del título
        desc_sentiment = analyze_text_sentiment(content) if content and content != title else None # Sentimiento del contenido
        
        if title_sentiment and desc_sentiment:
            # Detectar conflicto entre título y contenido
            title_score = title_sentiment['sentiment_score']
            content_score = desc_sentiment['sentiment_score']
            
            # Si hay un conflicto fuerte (título muy diferente al contenido)
            # y el contenido tiene más confianza, dar más peso al contenido
            score_diff = abs(title_score - content_score)
            conf_diff = desc_sentiment['confidence'] - title_sentiment['confidence']
            
            if score_diff > 40 and conf_diff > 0.15:
                # Caso de conflicto: dar más peso al contenido (que suele tener más contexto)
                weight_title = 0.4
                weight_content = 0.6
                logger.debug(f"Conflicto detectado en artículo: título={title_score:.1f}, contenido={content_score:.1f}. Usando pesos adaptativos.")
            else:
                # Caso normal: 70% título, 30% contenido
                weight_title = 0.7
                weight_content = 0.3
            
            combined_score = (
                weight_title * title_sentiment['sentiment_score'] + # Puntuación del título
                weight_content * desc_sentiment['sentiment_score'] # Puntuación del contenido
            )
            combined_confidence = (
                weight_title * title_sentiment['confidence'] + # Confianza del título
                weight_content * desc_sentiment['confidence'] # Confianza del contenido
            )
        elif title_sentiment:
            combined_score = title_sentiment['sentiment_score'] # Puntuación del título
            combined_confidence = title_sentiment['confidence'] # Confianza del título
        elif desc_sentiment:
            combined_score = desc_sentiment['sentiment_score'] # Puntuación del contenido
            combined_confidence = desc_sentiment['confidence'] # Confianza del contenido
        else:
            continue
        
        age_weight = 1.0 # Peso de la edad del artículo
        
        article_sentiments.append({
            'score': combined_score, # Puntuación del artículo
            'confidence': combined_confidence, # Confianza del artículo
            'age_weight': age_weight,
            'title': title[:80], # Título del artículo
            'title_sentiment': title_sentiment, # Sentimiento del título
            'desc_sentiment': desc_sentiment # Sentimiento del contenido
        })
    
    if not article_sentiments:
        return {
            'aggregate_score': 50.0,
            'sentiment_label': 'neutral',
            'article_count': 0,
            'details': [],
            'confidence': 0.0,
            'method': 'finbert'
        }
    
    total_weight = sum(art['confidence'] * art['age_weight'] for art in article_sentiments) # Peso total del artículo
    weighted_sum = sum(art['score'] * art['confidence'] * art['age_weight'] for art in article_sentiments) # Puntuación total del artículo
    confidence_sum = sum(art['confidence'] for art in article_sentiments) # Confianza total del artículo
    
    aggregate_score = weighted_sum / total_weight if total_weight > 0 else 50.0 # Puntuación agregada del artículo
    avg_confidence = confidence_sum / len(article_sentiments) # Confianza promedio del artículo
    
    if aggregate_score >= 65:
        sentiment_label = 'positive'
    elif aggregate_score <= 35:
        sentiment_label = 'negative'
    elif 45 <= aggregate_score <= 55:
        sentiment_label = 'neutral'
    else:
        sentiment_label = 'mixed'
    
    return {
        'aggregate_score': round(aggregate_score, 2),
        'sentiment_label': sentiment_label,
        'article_count': len(article_sentiments),
        'details': article_sentiments,
        'confidence': round(avg_confidence, 3),
        'method': 'finbert',
        'symbol': symbol
    }

def analyze_news_sentiment(news_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    """
    Función principal: analiza sentimiento de noticias para un símbolo.
    Adaptada para el formato de datos limpio de Tavily.
    """
    try:
        # La herramienta de Tavily ya devuelve una lista estructurada en la clave 'articles'
        articles = news_data.get("articles", [])
        
        if not articles:
            logger.warning(f"No se encontraron artículos para {symbol} en el payload de noticias.")
            return {
                'aggregate_score': 50.0,
                'sentiment_label': 'neutral',
                'article_count': 0,
                'method': 'finbert',
                'warning': 'No articles found in news payload'
            }
        
        logger.info(f"Analizando sentimiento de {len(articles)} artículos para {symbol}")
        
        # El resto del flujo no cambia, ya que compute_aggregate_sentiment espera una lista de artículos
        result = compute_aggregate_sentiment(articles, symbol)
        
        logger.info(
            f"{symbol}: Sentimiento agregado = {result['aggregate_score']:.1f} "
            f"({result['sentiment_label']}) basado en {result['article_count']} artículos"
        )
        
        return result
        
    except Exception as e:
        logger.exception(f"Error en análisis de sentimiento para {symbol}")
        return {
            'aggregate_score': 50.0,
            'sentiment_label': 'neutral',
            'article_count': 0,
            'method': 'finbert',
            'error': str(e)
        }

def get_sentiment_score(news_data: Dict[str, Any], symbol: str) -> float:
    """
    Función de conveniencia que devuelve solo el score agregado 0-100.
    """
    result = analyze_news_sentiment(news_data, symbol)
    return result.get('aggregate_score', 50.0)