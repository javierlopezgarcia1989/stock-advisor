-- Schema inicial para almacenamiento histórico
CREATE TABLE IF NOT EXISTS prices (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL, -- ISO YYYY-MM-DD
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  PRIMARY KEY(symbol, date)
);

CREATE TABLE IF NOT EXISTS analyses (
  symbol TEXT NOT NULL,
  run_timestamp TEXT NOT NULL, -- ISO datetime
  action TEXT NOT NULL, -- BUY/SELL/HOLD
  aggregate_score REAL, -- Puntuación agregada de la acción
  fundamental_score REAL, -- Puntuación fundamental de la acción
  technical_score REAL, -- Puntuación técnica de la acción
  risk_score REAL, -- Puntuación de riesgo de la acción
  news_score REAL, -- Puntuación de noticias de la acción
  -- Campos extendidos para comparación diaria y trazabilidad de decisión
  previous_action TEXT, -- Acción anterior
  previous_aggregate_score REAL, -- Puntuación agregada de la acción anterior
  price_change_pct REAL, -- variación diaria respecto al cierre previo (0.05 = +5%)
  news_sentiment REAL,   -- 0-100 puntuación FinBERT agregada
  action_reason TEXT,    -- explicación breve del cambio de acción
  changed INTEGER,       -- 1 si cambió la acción respecto al día previo
  close_price REAL,      -- cierre del día analizado
  rsi14 REAL, -- Relative Strength Index de 14 días
  distance_sma200 REAL, -- Distancia a la Simple Moving Average de 200 días
  explanation TEXT, -- Explicación breve de la acción
  -- Campos adicionales para análisis FinBERT detallado
  sentiment_label TEXT,  -- 'positive', 'negative', 'neutral', 'mixed'
  sentiment_confidence REAL, -- confianza promedio del modelo FinBERT
  sentiment_article_count INTEGER, -- número de artículos analizados
  sentiment_details TEXT, -- JSON con análisis detallado por artículo
  PRIMARY KEY(symbol, run_timestamp) -- Clave primaria compuesta por símbolo y fecha de ejecución
);

-- Tabla opcional para histórico de artículos individuales
CREATE TABLE IF NOT EXISTS news_articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  analyzed_at TEXT NOT NULL, -- ISO datetime
  title TEXT,
  description TEXT,
  url TEXT,
  age TEXT, -- "2 hours ago", "1 day ago"
  sentiment TEXT, -- 'positive', 'negative', 'neutral'
  sentiment_score REAL, -- 0-100
  confidence REAL, -- 0-1
  method TEXT DEFAULT 'finbert'
);
