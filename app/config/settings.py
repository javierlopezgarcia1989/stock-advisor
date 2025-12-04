import os
from dotenv import load_dotenv

load_dotenv()

BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")
DEFAULT_MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# --- Decision thresholds & defaults ---
ACTION_BUY_THRESHOLD = float(os.getenv("ACTION_BUY_THRESHOLD", "70"))
ACTION_SELL_THRESHOLD = float(os.getenv("ACTION_SELL_THRESHOLD", "40"))
SCORE_DELTA_MIN = float(os.getenv("SCORE_DELTA_MIN", "5"))
SCORE_DELTA_STRONG = float(os.getenv("SCORE_DELTA_STRONG", "8"))
PRICE_CHANGE_BUY_BONUS = float(os.getenv("PRICE_CHANGE_BUY_BONUS", "0.02"))
PRICE_CHANGE_SELL_TRIGGER = float(os.getenv("PRICE_CHANGE_SELL_TRIGGER", "-0.04"))
DEFAULT_TICKERS = os.getenv("DEFAULT_TICKERS", "AAPL,MSFT,GOOGL,AMZN,TSLA").split(",")

