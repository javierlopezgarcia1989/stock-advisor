import json
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


def get_stock_price(symbol: str) -> str:
    try:
        stock = yf.Ticker(symbol)
        info = stock.info # Información de la empresa
        hist = stock.history(period="1d") # Historial de precios de la acción
        if hist.empty:
            return json.dumps({"error": f"No data for {symbol}"}) # Retorna un error si no hay historial de precios
        current_price = hist['Close'].iloc[-1] # Precio actual de la acción (Close)
        result = {
            "symbol": symbol, # Símbolo de la acción
            "current_price": round(current_price, 2), # Precio actual de la acción (Close)
            "company_name": info.get('longName', symbol), # Nombre de la empresa
            "market_cap": info.get('marketCap', 0), # Capitalización de mercado
            "pe_ratio": info.get('trailingPE', 'N/A'), # Ratio precio/beneficio
            "52_week_high": info.get('fiftyTwoWeekHigh', 0), # Precio más alto en los últimos 52 semanas
            "52_week_low": info.get('fiftyTwoWeekLow', 0) # Precio más bajo en los últimos 52 semanas
        }
        return json.dumps(result) # Retorna el resultado en formato JSON
    except Exception as e:
        logger.exception("get_stock_price failed")
        return json.dumps({"error": str(e)})
