import json
from app.config.model_factory import get_llm
from app.prompts.system_prompts import TECHNICAL_ANALYST_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

def _create_chain(llm) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", TECHNICAL_ANALYST_PROMPT),
        ("human", "{input}")
    ])
    return prompt | llm

def run_technical_analysis(state: dict) -> dict:
    """
    Invoca al agente de análisis técnico para interpretar indicadores, tendencias y patrones de precio.
    """
    print("--- AGENTE: Analista Técnico INPUT ---")
    llm = get_llm()
    chain = _create_chain(llm)
    
    technicals_data = state.get("technicals", {})
    if not technicals_data:
        return {"technical_report": "No se dispuso de datos técnicos para el análisis."}

    # Preparar la entrada para el LLM
    input_str = json.dumps(technicals_data, indent=2, ensure_ascii=False)
    
    try:
        response = chain.invoke({"input": input_str})
        report = response.content
    except Exception as e:
        print(f"Error en el agente de análisis técnico: {e}")
        report = "[FALLBACK] No se pudo generar el informe técnico."
        
    print("--- AGENTE: Analista Técnico OUTPUT ---")
    print(report)

    return {
        "technical_report": report,
        "progress": 50.0,
        "current_step": "Analizando datos técnicos..."
    }
