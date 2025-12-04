"""
Sistema de caché de datos históricos para optimizar velocidad y reducir llamadas a APIs.

Este módulo implementa una estrategia de caché híbrido:
- Almacena datos históricos en SQLite
- Actualiza solo los datos faltantes (incremental)
- Reduce latencia de 3-5s a <500ms en consultas recurrentes
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import yfinance as yf

from app.data.repository import fetch_price_history, upsert_prices

logger = logging.getLogger(__name__)


def get_cached_history(symbol: str, period_days: int = 90) -> pd.DataFrame:
    """
    Obtiene histórico de precios desde caché o actualiza si está desactualizado.
    
    Args:
        symbol: Símbolo bursátil (ej: 'AAPL')
        period_days: Número de días de histórico requeridos
        
    Returns:
        DataFrame con columnas: date, open, high, low, close, volume
    """
    try:
        # 1. Intentar obtener de BD
        cached_data = fetch_price_history(symbol, limit=period_days)
        
        if not cached_data:
            logger.info(f"No hay datos en caché para {symbol}. Descargando histórico completo...")
            return _download_and_cache(symbol, period_days)
        
        # 2. Verificar frescura (última fecha en BD)
        last_date = datetime.fromisoformat(cached_data[-1]['date']).date()
        today = datetime.now().date()
        
        # Si los datos son de hoy, retornar directamente
        if last_date >= today:
            logger.info(f"Datos de {symbol} están actualizados (última fecha: {last_date})")
            return _dict_list_to_dataframe(cached_data)
        
        # 3. Calcular días faltantes
        days_missing = (today - last_date).days
        
        if days_missing <= 0:
            return _dict_list_to_dataframe(cached_data)
        
        logger.info(f"Datos de {symbol} desactualizados por {days_missing} días. Actualizando...")
        
        # 4. Descargar solo días faltantes
        try:
            start_date = last_date + timedelta(days=1)
            ticker = yf.Ticker(symbol)
            new_hist = ticker.history(start=start_date)
            
            if not new_hist.empty:
                _cache_new_data(symbol, new_hist)
                logger.info(f"Actualizados {len(new_hist)} días nuevos para {symbol}")
            
            # 5. Obtener datos actualizados de la BD
            updated_data = fetch_price_history(symbol, limit=period_days)
            return _dict_list_to_dataframe(updated_data)
            
        except Exception as e:
            logger.warning(f"Error actualizando datos incrementales para {symbol}: {e}")
            # Fallback: retornar datos cacheados aunque estén ligeramente desactualizados
            return _dict_list_to_dataframe(cached_data)
    
    except Exception as e:
        logger.exception(f"Error en get_cached_history para {symbol}")
        # Fallback final: descargar directo de yfinance
        return _download_direct(symbol, period_days)


def _download_and_cache(symbol: str, period_days: int) -> pd.DataFrame:
    """Descarga histórico completo y lo almacena en BD."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{period_days}d")
        
        if hist.empty:
            logger.warning(f"No se obtuvieron datos para {symbol}")
            return pd.DataFrame()
        
        _cache_new_data(symbol, hist)
        logger.info(f"Descargados y cacheados {len(hist)} días para {symbol}")
        
        return hist
        
    except Exception as e:
        logger.exception(f"Error descargando datos para {symbol}")
        return pd.DataFrame()


def _cache_new_data(symbol: str, hist: pd.DataFrame):
    """Almacena nuevos datos en la BD."""
    if hist.empty:
        return
    
    rows = []
    for date, row in hist.iterrows():
        rows.append({
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume'])
        })
    
    if rows:
        upsert_prices(rows)
        logger.debug(f"Insertados/actualizados {len(rows)} registros para {symbol}")


def _dict_list_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convierte lista de diccionarios a DataFrame compatible con yfinance."""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Renombrar columnas al formato esperado (mayúsculas)
    df = df.rename(columns={
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Convertir fecha a índice datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    return df


def _download_direct(symbol: str, period_days: int) -> pd.DataFrame:
    """Descarga directa sin caché (fallback)."""
    try:
        logger.warning(f"Usando descarga directa para {symbol} (sin caché)")
        ticker = yf.Ticker(symbol)
        return ticker.history(period=f"{period_days}d")
    except Exception as e:
        logger.exception(f"Error en descarga directa para {symbol}")
        return pd.DataFrame()


def clear_cache_for_symbol(symbol: str):
    """
    Limpia el caché para un símbolo específico (útil para testing).
    
    Args:
        symbol: Símbolo bursátil a limpiar
    """
    from app.data.repository import get_conn
    
    try:
        conn = get_conn()
        conn.execute("DELETE FROM prices WHERE symbol = ?", (symbol,))
        conn.commit()
        conn.close()
        logger.info(f"Caché limpiado para {symbol}")
    except Exception as e:
        logger.exception(f"Error limpiando caché para {symbol}")


def get_cache_stats(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas del caché.
    
    Args:
        symbol: Símbolo específico o None para todas las stats
        
    Returns:
        Dict con estadísticas del caché
    """
    from app.data.repository import get_conn
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        if symbol:
            cur.execute("""
                SELECT 
                    COUNT(*) as record_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM prices 
                WHERE symbol = ?
            """, (symbol,))
            row = cur.fetchone()
            
            return {
                'symbol': symbol,
                'record_count': row[0] if row else 0,
                'earliest_date': row[1] if row else None,
                'latest_date': row[2] if row else None,
                'is_current': row[2] == datetime.now().date().isoformat() if row and row[2] else False
            }
        else:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT symbol) as symbol_count,
                    COUNT(*) as total_records,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM prices
            """)
            row = cur.fetchone()
            
            return {
                'symbol_count': row[0] if row else 0,
                'total_records': row[1] if row else 0,
                'earliest_date': row[2] if row else None,
                'latest_date': row[3] if row else None
            }
        
    except Exception as e:
        logger.exception("Error obteniendo stats del caché")
        return {}
    finally:
        if conn:
            conn.close()

