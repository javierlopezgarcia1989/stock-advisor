import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'research.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn = get_conn()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def ensure_analysis_columns():
    """Ensure extended columns exist (idempotent)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(analyses)")
        cols = {r[1] for r in cur.fetchall()}
        alter_statements = []
        wanted = {
            "previous_action": "TEXT",
            "previous_aggregate_score": "REAL",
            "price_change_pct": "REAL",
            "news_sentiment": "REAL",
            "action_reason": "TEXT",
            "changed": "INTEGER",
            "close_price": "REAL",
            "rsi14": "REAL",
            "distance_sma200": "REAL",
            "sentiment_label": "TEXT",
            "sentiment_confidence": "REAL",
            "sentiment_article_count": "INTEGER",
            "sentiment_details": "TEXT"
        }
        for name, ctype in wanted.items():
            if name not in cols:
                alter_statements.append(f"ALTER TABLE analyses ADD COLUMN {name} {ctype}")
        for stmt in alter_statements:
            cur.execute(stmt)
        if alter_statements:
            conn.commit()
    finally:
        conn.close()


def upsert_prices(rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.executemany(
            """INSERT OR REPLACE INTO prices(symbol, date, open, high, low, close, volume)
                 VALUES(:symbol, :date, :open, :high, :low, :close, :volume)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def fetch_price_history(symbol: str, limit: int = 260) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT date, open, high, low, close, volume FROM prices WHERE symbol=? ORDER BY date DESC LIMIT ?",
            (symbol, limit),
        )
        rows = cur.fetchall()
        return [
            {"symbol": symbol, "date": r[0], "open": r[1], "high": r[2], "low": r[3], "close": r[4], "volume": r[5]} for r in rows
        ][::-1]  # oldest first
    finally:
        conn.close()


def insert_analysis(record: Dict[str, Any]):
    conn = get_conn()
    try:
        record = {**record, "run_timestamp": record.get("run_timestamp") or datetime.utcnow().isoformat()}
        
        # Serializar sentiment_details si existe
        sentiment_details_json = None
        if record.get("sentiment_details"):
            sentiment_details_json = json.dumps(record["sentiment_details"], ensure_ascii=False)
        
        conn.execute(
            """INSERT INTO analyses(symbol, run_timestamp, action, aggregate_score, fundamental_score, technical_score, 
                 risk_score, news_score, previous_action, previous_aggregate_score, price_change_pct, news_sentiment, 
                 action_reason, changed, close_price, rsi14, distance_sma200, explanation,
                 sentiment_label, sentiment_confidence, sentiment_article_count, sentiment_details)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record["symbol"],
                record["run_timestamp"],
                record["action"],
                record.get("aggregate_score"),
                record.get("fundamental_score"),
                record.get("technical_score"),
                record.get("risk_score"),
                record.get("news_score"),
                record.get("previous_action"),
                record.get("previous_aggregate_score"),
                record.get("price_change_pct"),
                record.get("news_sentiment"),
                record.get("action_reason"),
                record.get("changed"),
                record.get("close_price"),
                record.get("rsi14"),
                record.get("distance_sma200"),
                record.get("explanation"),
                record.get("sentiment_label"),
                record.get("sentiment_confidence"),
                record.get("sentiment_article_count"),
                sentiment_details_json,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_last_analysis(symbol: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT symbol, run_timestamp, action, aggregate_score, fundamental_score, technical_score, risk_score, news_score,
                      previous_action, previous_aggregate_score, price_change_pct, news_sentiment, action_reason, changed, 
                      close_price, rsi14, distance_sma200, explanation, sentiment_label, sentiment_confidence, 
                      sentiment_article_count, sentiment_details
                 FROM analyses WHERE symbol=? ORDER BY run_timestamp DESC LIMIT 1""",
            (symbol,),
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = [
            "symbol","run_timestamp","action","aggregate_score","fundamental_score","technical_score","risk_score","news_score",
            "previous_action","previous_aggregate_score","price_change_pct","news_sentiment","action_reason","changed",
            "close_price","rsi14","distance_sma200","explanation","sentiment_label","sentiment_confidence",
            "sentiment_article_count","sentiment_details"
        ]
        result = {k: row[i] for i, k in enumerate(keys)}
        
        # Deserializar sentiment_details si existe
        if result.get("sentiment_details"):
            try:
                result["sentiment_details"] = json.loads(result["sentiment_details"])
            except:
                pass
        
        return result
    finally:
        conn.close()


# Initialize on import
init_db()
ensure_analysis_columns()
