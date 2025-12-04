from dotenv import load_dotenv


# Cargar variables de entorno desde el archivo .env
load_dotenv()

import logging
from app.ui.interface import create_interface

logging.basicConfig(level=logging.INFO)

def main():
    """Punto de entrada principal de la aplicación."""
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
