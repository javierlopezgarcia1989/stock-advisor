import json
from app.config.model_factory import get_llm
from app.prompts.system_prompts import CHIEF_ANALYST_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

def _create_chain(llm) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", CHIEF_ANALYST_PROMPT),
        ("human", "{input}")
    ])
    return prompt | llm

def _format_technical_indicators_table(technicals_data: dict) -> str:
    """
    Formatea los indicadores técnicos en una tabla Markdown clara y profesional.
    """
    if not technicals_data:
        return "No hay datos técnicos disponibles."
    
    # Obtener datos del primer símbolo
    symbol_data = list(technicals_data.values())[0] if technicals_data else {}
    
    if not symbol_data or symbol_data.get("error"):
        return "No se pudieron obtener los indicadores técnicos."
    
    # Crear tabla Markdown
    table = "## 📊 Análisis Técnico - Indicadores Calculados\n\n"
    table += "| Indicador | Valor | Interpretación |\n"
    table += "|-----------|-------|----------------|\n"
    
    # Precio Actual
    current_price = symbol_data.get("current_price", "N/A")
    table += f"| **Precio Actual** | ${current_price} | Precio de cierre más reciente |\n"
    
    # Medias Móviles
    table += "| | | |\n"
    table += "| **📈 MEDIAS MÓVILES** | | |\n"
    
    sma_20 = symbol_data.get("sma_20", "N/A")
    if sma_20 != "N/A" and current_price != "N/A":
        pos_20 = "por encima" if current_price > sma_20 else "por debajo"
        table += f"| SMA 20 días | ${sma_20} | Precio {pos_20} de la media de corto plazo |\n"
    else:
        table += f"| SMA 20 días | {sma_20} | - |\n"
    
    sma_50 = symbol_data.get("sma_50", "N/A")
    if sma_50 != "N/A" and current_price != "N/A":
        pos_50 = "por encima" if current_price > sma_50 else "por debajo"
        table += f"| SMA 50 días | ${sma_50} | Precio {pos_50} de la media de medio plazo |\n"
    else:
        table += f"| SMA 50 días | {sma_50} | - |\n"
    
    sma_200 = symbol_data.get("sma_200")
    if sma_200:
        pos_200 = "por encima" if current_price > sma_200 else "por debajo"
        table += f"| SMA 200 días | ${sma_200} | Precio {pos_200} de la tendencia de largo plazo |\n"
    else:
        table += f"| SMA 200 días | No disponible | Requiere más histórico |\n"
    
    # Distancia a SMA_200
    distance_sma200 = symbol_data.get("distance_sma200")
    if distance_sma200 is not None:
        dist_pct = distance_sma200 * 100
        dist_interp = f"{'+' if dist_pct > 0 else ''}{dist_pct:.2f}% respecto a SMA_200"
        if dist_pct > 10:
            dist_interp += " (muy alcista)"
        elif dist_pct > 0:
            dist_interp += " (alcista)"
        elif dist_pct > -10:
            dist_interp += " (bajista)"
        else:
            dist_interp += " (muy bajista)"
        table += f"| Distancia SMA 200 | {dist_pct:+.2f}% | {dist_interp} |\n"
    
    # Tendencia
    trend_signal = symbol_data.get("trend_signal", "N/A")
    trend_emoji = "🟢" if trend_signal == "bullish" else "🔴" if trend_signal == "bearish" else "⚪"
    trend_text = "Alcista" if trend_signal == "bullish" else "Bajista" if trend_signal == "bearish" else "Neutral"
    table += f"| **Señal de Tendencia** | {trend_emoji} {trend_text.upper()} | Basado en posición de SMAs |\n"
    
    # Momentum
    table += "| | | |\n"
    table += "| **⚡ MOMENTUM** | | |\n"
    
    rsi = symbol_data.get("rsi", "N/A")
    if rsi != "N/A":
        if rsi > 70:
            rsi_interp = "Sobrecompra (posible corrección)"
        elif rsi < 30:
            rsi_interp = "Sobreventa (posible rebote)"
        else:
            rsi_interp = "Zona neutral"
        table += f"| RSI (14) | {rsi:.2f} | {rsi_interp} |\n"
    else:
        table += f"| RSI (14) | {rsi} | - |\n"
    
    macd = symbol_data.get("macd", "N/A")
    macd_signal = symbol_data.get("macd_signal", "N/A")
    macd_histogram = symbol_data.get("macd_histogram", "N/A")
    macd_trend = symbol_data.get("macd_trend", "N/A")
    if macd != "N/A":
        macd_emoji = "🟢" if macd_trend == "bullish" else "🔴"
        table += f"| MACD | {macd:.4f} | {macd_emoji} {macd_trend.capitalize()} |\n"
        table += f"| MACD Señal | {macd_signal:.4f} | Línea de señal |\n"
        table += f"| MACD Histograma | {macd_histogram:.4f} | Diferencia MACD-Señal |\n"
    
    momentum_5d = symbol_data.get("momentum_5d")
    if momentum_5d is not None:
        mom_pct = momentum_5d * 100
        mom_dir = "subió" if mom_pct > 0 else "bajó"
        table += f"| Momentum 5 días | {mom_pct:+.2f}% | El precio {mom_dir} {abs(mom_pct):.2f}% en 5 días |\n"
    
    # Volatilidad
    table += "| | | |\n"
    table += "| **📊 VOLATILIDAD** | | |\n"
    
    bb_upper = symbol_data.get("bb_upper", "N/A")
    bb_lower = symbol_data.get("bb_lower", "N/A")
    bb_position = symbol_data.get("bb_position", "N/A")
    
    if bb_upper != "N/A" and bb_lower != "N/A":
        table += f"| Banda Bollinger Superior | ${bb_upper} | Límite superior de volatilidad |\n"
        table += f"| Banda Bollinger Inferior | ${bb_lower} | Límite inferior de volatilidad |\n"
        
        bb_interp = ""
        if bb_position == "overbought":
            bb_interp = "🔴 Sobrecompra (precio sobre banda superior)"
        elif bb_position == "oversold":
            bb_interp = "🟢 Sobreventa (precio bajo banda inferior)"
        else:
            bb_interp = "⚪ Normal (precio dentro de bandas)"
        table += f"| **Posición en Bandas** | {bb_position.upper()} | {bb_interp} |\n"
    
    atr = symbol_data.get("atr", "N/A")
    if atr != "N/A":
        table += f"| ATR (14) | ${atr} | Volatilidad promedio diaria |\n"
    
    # Volumen
    volume = symbol_data.get("volume", "N/A")
    if volume != "N/A":
        vol_formatted = f"{volume:,}"
        table += f"| Volumen | {vol_formatted} | Acciones negociadas en el último día |\n"
    
    table += "\n---\n\n"
    
    return table


def run_chief_analyst(state: dict) -> dict:
    """
    Invoca al Analista Jefe para sintetizar todos los informes y generar la recomendación final.
    """
    print("--- AGENTE: Analista Jefe de Inversiones ---")
    llm = get_llm()
    chain = _create_chain(llm)
    
    # Recopilar todos los informes y datos relevantes del estado
    news_data = state.get("news", {})
    relevant_news_content = []
    for symbol, news_block in news_data.items():
        if news_block.get("articles"):
            # Tomar los primeros 5 artículos (los más relevantes según Tavily)
            for article in news_block["articles"][:5]:
                title = article.get('title', 'Sin título')
                url = article.get('url', '#')
                content = article.get('content', 'Sin contenido')
                # Truncar contenido si es muy largo (primeras 200 caracteres)
                content_preview = content[:200] + "..." if len(content) > 200 else content
                relevant_news_content.append(f"- [{title}]({url}): {content_preview}")

    context = {
        "original_query": state.get("query"),
        "symbols": state.get("symbols"),
        "technical_report": state.get("technical_report"),
        "news_report": state.get("news_report"),
        "Noticias Relevantes": "\n".join(relevant_news_content) if relevant_news_content else "No hay contenido de noticias disponible."
    }
    
    input_str = json.dumps(context, indent=2, ensure_ascii=False)
    
    try:
        response = chain.invoke({"input": input_str})
        final_report = response.content
    except Exception as e:
        print(f"Error en el agente Analista Jefe: {e}")
        final_report = "[FALLBACK] No se pudo generar el informe final."

    # Agregar tabla de indicadores técnicos al final del informe
    technicals_data = state.get("technicals", {})
    technical_table = _format_technical_indicators_table(technicals_data)
    
    # Combinar el informe del LLM con la tabla técnica
    final_report_with_table = f"{final_report}\n\n{technical_table}"

    print("--- AGENTE: Analista Jefe de Inversiones OUTPUT ---")
    print(final_report_with_table)    
    return {
        "final_report": final_report_with_table,
        "progress": 90.0,
        "current_step": "Generando informe final..."
    }
