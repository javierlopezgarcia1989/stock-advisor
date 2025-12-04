import gradio as gr
from app.graph.builder import build_graph
from langgraph.graph.graph import CompiledGraph

# Variable global para cachear el grafo compilado
_GRAPH: CompiledGraph | None = None

def _get_graph() -> CompiledGraph:
    """Compila el grafo si no está en caché y lo devuelve."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH

def run_analysis_pipeline(query: str):
    """
    Ejecuta el grafo de análisis completo con la consulta del usuario, 
    emitiendo actualizaciones de progreso.
    """
    if not query or not query.strip():
        yield "Por favor, introduzca una consulta.", gr.update(value=0), gr.update(value="Esperando consulta...")
        return

    # Mostrar controles de progreso
    yield "Iniciando análisis...", gr.update(visible=True, value=0), gr.update(visible=True, value="0% - Iniciando...")

    graph = _get_graph()
    initial_state = {"query": query, "progress": 0.0, "current_step": ""}
    final_state = None

    try:
        # Usar `stream` para obtener actualizaciones en tiempo real
        for state_update in graph.stream(initial_state):
            # state_update es un dict donde las claves son los nombres de los nodos
            # y los valores son las actualizaciones parciales del estado
            for node_name, node_update in state_update.items():
                progress = node_update.get('progress', 0.0)
                current_step = node_update.get('current_step', '')
                
                if current_step:  # Solo actualizar si hay un paso actual definido
                    yield f"**{current_step}**\n\nPor favor, espere...", gr.update(value=progress), gr.update(value=f"{int(progress)}% - {current_step}")
                
                # Guardar el último estado (acumular todos los campos)
                if final_state is None:
                    final_state = {}
                final_state.update(node_update)

        # Comprueba si hubo un error manejado en el grafo
        if final_state and (error_message := final_state.get("error")):
            final_report = f"ERROR EN EL ANÁLISIS: {error_message}"
        elif final_state:
            final_report = final_state.get("final_report", "No se pudo generar un informe final.")
        else:
            final_report = "El análisis no produjo un resultado final."

        # Actualización final al completar
        yield final_report, gr.update(value=100), gr.update(value="100% - Análisis completado")

    except Exception as e:
        error_message = f"Ocurrió un error inesperado: {e}"
        yield error_message, gr.update(value=0), gr.update(value="Error")
    finally:
        # Opcional: Ocultar la barra de progreso después de un tiempo
        # En este caso, la mantenemos visible con el resultado final.
        pass

def create_interface():
    """
    Crea y configura la interfaz de usuario con Gradio.
    """
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Stock Advisor") as demo:
        gr.Markdown("""
        #  AI Stock Advisor
        Introduce un símbolo bursátil (ticker) para obtener un análisis multi-agente.
        """)
        
        with gr.Row():
            query_input = gr.Textbox(
                lines=2,
                label="Consulta", 
                placeholder="Ej: ¿Debería invertir en NVIDIA (NVDA)?",
                scale=4
            )
            run_button = gr.Button("Analizar", variant="primary", scale=1)

        with gr.Column() as progress_column:
            progress_label = gr.Label(label="Progreso del Análisis", value="Esperando para iniciar...", visible=False)
            progress_bar = gr.Slider(label="", minimum=0, maximum=100, value=0, interactive=False, visible=False)
        
        output_report = gr.Markdown(label="Informe de Inversión")

        run_button.click(
            fn=run_analysis_pipeline, 
            inputs=[query_input], 
            outputs=[output_report, progress_bar, progress_label]
        )
        
        gr.Examples(
            examples = [
                "Analyze the current state of Microsoft (MSFT)", 
                "Is now a good time to buy Apple (AAPL) stock?", 
                "I want a report on Tesla (TSLA)", 
                "I want a report on Google (GOOGL)" 
            ],
            inputs=query_input
        )

    return demo