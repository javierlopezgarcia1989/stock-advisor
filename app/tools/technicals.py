import json
import logging
import pandas as pd

from app.services.data_cache import get_cached_history

logger = logging.getLogger(__name__)


def get_technical_indicators(symbol: str, period_days: int = 180) -> str:
    """
    Calcula indicadores técnicos usando datos cacheados para mayor velocidad.
    
    Periodo por defecto: 180 días (6 meses) para poder calcular SMA_200 si hay suficientes datos.
    
    Indicadores calculados:
    - SMA_20, SMA_50, SMA_200: Medias móviles simples
    - RSI: Relative Strength Index (14 períodos)
    - MACD: Moving Average Convergence Divergence con señal e histograma
    - Bandas de Bollinger: Upper, Lower y posición
    - ATR: Average True Range (volatilidad)
    
    Args:
        symbol: Símbolo bursátil
        period_days: Días de histórico necesarios (default 180)
        
    Returns:
        JSON con todos los indicadores técnicos
    """
    try:
        # Usar caché para obtener datos históricos
        hist = get_cached_history(symbol, period_days=period_days)
        
        if hist.empty:
            return json.dumps({"error": f"No historical data for {symbol}"})
        
        # === MEDIAS MÓVILES SIMPLES ===
        hist["SMA_20"] = hist["Close"].rolling(window=20).mean() # Simple Moving Average de 20 días
        hist["SMA_50"] = hist["Close"].rolling(window=50).mean() # Simple Moving Average de 50 días
        hist["SMA_200"] = hist["Close"].rolling(window=200).mean() # Simple Moving Average de 200 días
        
        # === RSI (Relative Strength Index) ===
        delta = hist["Close"].diff() # Diferencia entre el precio actual y el precio anterior
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean() # Ganancia promedio
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean() # Pérdida promedio
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)) # Relative Strength Index
        
        # === MACD (Moving Average Convergence Divergence) ===
        exp1 = hist["Close"].ewm(span=12, adjust=False).mean() # Exponential Moving Average de 12 días
        exp2 = hist["Close"].ewm(span=26, adjust=False).mean() # Exponential Moving Average de 26 días
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean() # Exponential Moving Average de 9 días
        histogram = macd - signal
        
        # === BANDAS DE BOLLINGER ===
        sma20 = hist["Close"].rolling(window=20).mean() # Simple Moving Average de 20 días
        std20 = hist["Close"].rolling(window=20).std() # Desviación estándar de 20 días
        bb_upper = sma20 + (std20 * 2) # Banda superior de Bollinger
        bb_lower = sma20 - (std20 * 2) # Banda inferior de Bollinger 
        
        # === ATR (Average True Range) - Volatilidad ===
        high_low = hist["High"] - hist["Low"] # Diferencia entre el precio más alto y el precio más bajo
        high_close = abs(hist["High"] - hist["Close"].shift()) # Diferencia entre el precio más alto y el precio actual
        low_close = abs(hist["Low"] - hist["Close"].shift()) # Diferencia entre el precio más bajo y el precio actual
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean() # Average True Range
        
        # === OBTENER ÚLTIMOS VALORES ===
        latest = hist.iloc[-1]
        latest_rsi = float(rsi.iloc[-1]) # RSI del último precio
        latest_macd = float(macd.iloc[-1]) # MACD del último precio
        latest_signal = float(signal.iloc[-1]) # Señal del último precio
        latest_histogram = float(histogram.iloc[-1]) # Histograma del último precio 
        
        # === SEÑALES DE TENDENCIA ===
        trend_signal = "neutral" # Tendencia neutral
        if pd.notna(latest["SMA_20"]) and pd.notna(latest["SMA_50"]):
            if latest["Close"] > latest["SMA_20"] > latest["SMA_50"]:
                trend_signal = "bullish" # Tendencia alcista
            elif latest["Close"] < latest["SMA_20"] < latest["SMA_50"]:
                trend_signal = "bearish" # Tendencia bajista
        
        # Posición en Bandas de Bollinger
        bb_position = "normal" # Posición normal
        if pd.notna(bb_upper.iloc[-1]) and pd.notna(bb_lower.iloc[-1]):
            if latest["Close"] > bb_upper.iloc[-1]:
                bb_position = "overbought" # Sobrecompra
            elif latest["Close"] < bb_lower.iloc[-1]:
                bb_position = "oversold" # Sobreventa
        
        # MACD Signal
        macd_signal = "bullish" if latest_macd > latest_signal else "bearish" # Tendencia del MACD
        
        # === INDICADORES ADICIONALES (de price_features.py) ===
        
        # Momentum de corto plazo (5 días) - Cambio porcentual
        momentum_5d = None
        if len(hist) >= 6:
            try:
                momentum_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6]) - 1.0
            except (ZeroDivisionError, IndexError):
                momentum_5d = None
        
        # Distancia porcentual a SMA_200 (indicador de tendencia de largo plazo)
        distance_sma200 = None
        if pd.notna(latest["SMA_200"]) and latest["SMA_200"] > 0:
            distance_sma200 = (latest["Close"] / latest["SMA_200"]) - 1.0
        
        # === RESULTADO COMPLETO ===
        result = {
            "symbol": symbol, # Símbolo de la acción
            "current_price": round(float(latest["Close"]), 2), # Precio actual de la acción (Close)
            "sma_20": round(float(latest["SMA_20"]), 2) if pd.notna(latest["SMA_20"]) else None, # Simple Moving Average de 20 días
            "sma_50": round(float(latest["SMA_50"]), 2) if pd.notna(latest["SMA_50"]) else None, # Simple Moving Average de 50 días
            "sma_200": round(float(latest["SMA_200"]), 2) if pd.notna(latest["SMA_200"]) else None, # Simple Moving Average de 200 días
            "rsi": round(latest_rsi, 2) if pd.notna(latest_rsi) else None, # Relative Strength Index del último precio
            "macd": round(latest_macd, 4), # MACD del último precio
            "macd_signal": round(latest_signal, 4), # Señal del último precio
            "macd_histogram": round(latest_histogram, 4), # Histograma del último precio
            "macd_trend": macd_signal, # Tendencia del MACD
            "bb_upper": round(float(bb_upper.iloc[-1]), 2) if pd.notna(bb_upper.iloc[-1]) else None, # Banda superior de Bollinger
            "bb_lower": round(float(bb_lower.iloc[-1]), 2) if pd.notna(bb_lower.iloc[-1]) else None, # Banda inferior de Bollinger  
            "bb_position": bb_position, # Posición en Bandas de Bollinger
            "atr": round(float(atr.iloc[-1]), 2) if pd.notna(atr.iloc[-1]) else None, # Average True Range del último precio
            "volume": int(latest["Volume"]), # Volumen de la acción
            "trend_signal": trend_signal, # Tendencia de la acción
            "momentum_5d": round(momentum_5d, 4) if momentum_5d is not None else None, # Momentum de 5 días (% cambio)
            "distance_sma200": round(distance_sma200, 4) if distance_sma200 is not None else None, # Distancia % a SMA_200
        }
        
        logger.info(f"Indicadores técnicos calculados para {symbol}: RSI={result['rsi']}, MACD={macd_signal}, Trend={trend_signal}, Momentum_5d={result['momentum_5d']}, Dist_SMA200={result['distance_sma200']}")
        return json.dumps(result)
        
    except Exception as e:
        logger.exception(f"get_technical_indicators failed for {symbol}")
        return json.dumps({"error": str(e)})
