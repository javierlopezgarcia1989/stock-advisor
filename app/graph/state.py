from typing import TypedDict, List, Dict, Any, Optional, Annotated

def max_progress(left: float, right: float) -> float:
    """Reducer que toma el valor máximo de progreso."""
    return max(left or 0.0, right or 0.0)

def last_non_empty(left: str, right: str) -> str:
    """Reducer que toma el último valor no vacío."""
    return right if right else left

class GraphState(TypedDict, total=False):
    """
    Define el estado que se pasa entre los nodos del grafo de análisis.
    """
    query: str
    symbols: List[str]
    
    # Datos brutos de las herramientas
    market_data: Dict[str, Any]
    technicals: Dict[str, Any]
    news: Dict[str, Any]
    
    # Informes generados por los agentes analistas
    technical_report: str
    news_report: str
    
    # Informe final y recomendación del agente jefe
    final_report: str
    
    # Estado de la interfaz - usar Annotated con reducers para manejar valores paralelos
    progress: Annotated[float, max_progress]  # Porcentaje de completado (0-100)
    current_step: Annotated[str, last_non_empty]  # Descripción del paso actual

    # Manejo de errores
    error: Optional[str]