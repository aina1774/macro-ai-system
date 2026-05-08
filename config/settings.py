"""
============================================================
AI MACRO INTELLIGENCE SYSTEM — Configuration Centrale
============================================================
Modifie ce fichier pour adapter le système à ton environnement.
"""

import os
from pathlib import Path

# ─── Répertoires ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

# ─── Base de données ────────────────────────────────────────
DATABASE = {
    "engine": "sqlite",                        # "sqlite" ou "postgresql"
    "sqlite_path": BASE_DIR / "database" / "macro_ai.db",

    # PostgreSQL (Phase 2+)
    "pg_host": os.getenv("PG_HOST", "localhost"),
    "pg_port": os.getenv("PG_PORT", 5432),
    "pg_name": os.getenv("PG_NAME", "macro_ai"),
    "pg_user": os.getenv("PG_USER", "postgres"),
    "pg_password": os.getenv("PG_PASSWORD", ""),
}

# ─── APIs Clés ──────────────────────────────────────────────
# Mets tes clés ici OU utilise des variables d'environnement (.env)
API_KEYS = {
    "fred":         os.getenv("FRED_API_KEY", "YOUR_FRED_KEY"),
    "newsapi":      os.getenv("NEWSAPI_KEY", "YOUR_NEWSAPI_KEY"),
    "finnhub":      os.getenv("FINNHUB_KEY", "YOUR_FINNHUB_KEY"),
    "alphavantage": os.getenv("ALPHAVANTAGE_KEY", "YOUR_AV_KEY"),
    "anthropic":    os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY"),
}

# ─── Collecte de données ────────────────────────────────────
COLLECTION = {
    "interval_minutes": 60,          # Fréquence de collecte automatique
    "max_news_per_source": 50,       # Nombre max d'articles par source
    "lookback_days": 7,              # Historique à récupérer au démarrage
    "dedup_threshold_hours": 24,     # Fenêtre de déduplication
}

# ─── FRED — Séries économiques à suivre ────────────────────
FRED_SERIES = {
    "CPIAUCSL":   "CPI (Inflation)",
    "FEDFUNDS":   "Fed Funds Rate",
    "GDP":        "GDP",
    "UNRATE":     "Unemployment Rate",
    "DGS10":      "10Y Treasury Yield",
    "DGS2":       "2Y Treasury Yield",
    "T10Y2Y":     "Yield Curve (10Y-2Y)",
    "DCOILWTICO": "WTI Oil Price",
    "VIXCLS":     "VIX",
    "DTWEXBGS":   "USD Trade Weighted Index",
    "M2SL":       "M2 Money Supply",
    "PAYEMS":     "Nonfarm Payrolls",
}

# ─── NewsAPI — Requêtes de recherche ────────────────────────
NEWS_QUERIES = [
    "Federal Reserve interest rates",
    "CPI inflation data",
    "GDP economic growth",
    "ECB monetary policy",
    "Bank of Japan BOJ",
    "nonfarm payrolls jobs report",
    "recession risk economic outlook",
    "dollar DXY currency",
    "Treasury yields bonds",
    "oil price OPEC",
]

# ─── Finnhub — Symboles marchés ─────────────────────────────
MARKET_SYMBOLS = {
    "forex": ["OANDA:EUR_USD", "OANDA:GBP_USD", "OANDA:USD_JPY"],
    "crypto": ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"],
    "indices": ["^GSPC", "^NDX", "^DJI"],    # Via Yahoo Finance fallback
}

# ─── NLP / FinBERT ──────────────────────────────────────────
NLP = {
    "model": "ProsusAI/finbert",              # Modèle FinBERT HuggingFace
    "max_length": 512,
    "batch_size": 16,
    "device": "cpu",                          # "cuda" si GPU disponible
    "confidence_threshold": 0.65,            # Score minimum pour accepter
}

# ─── Scores Macro — Pondérations ────────────────────────────
MACRO_WEIGHTS = {
    "usd_strength": {
        "fed_hawkish_sentiment": 0.35,
        "yield_spread": 0.25,
        "cpi_surprise": 0.20,
        "risk_sentiment": 0.20,
    },
    "inflation_pressure": {
        "cpi_yoy": 0.40,
        "ppi_yoy": 0.25,
        "oil_price": 0.20,
        "m2_growth": 0.15,
    },
    "recession_risk": {
        "yield_curve": 0.35,
        "unemployment_trend": 0.25,
        "gdp_growth": 0.25,
        "pmi_composite": 0.15,
    },
    "fear_index": {
        "vix_level": 0.40,
        "news_negative_sentiment": 0.30,
        "bond_flight": 0.30,
    },
}

# ─── Seuils d'alertes ───────────────────────────────────────
ALERT_THRESHOLDS = {
    "usd_strength_high": 75,
    "inflation_pressure_high": 70,
    "recession_risk_high": 65,
    "fear_index_high": 70,
    "sentiment_shift_delta": 20,     # Changement de score en % pour déclencher alerte
    "vix_spike": 30,
}

# ─── Dashboard ──────────────────────────────────────────────
DASHBOARD = {
    "refresh_interval_seconds": 300,  # Auto-refresh toutes les 5 min
    "max_news_displayed": 20,
    "chart_lookback_days": 30,
    "theme": "dark",
}

# ─── Logging ────────────────────────────────────────────────
LOGGING = {
    "level": "INFO",
    "file": LOGS_DIR / "macro_ai.log",
    "max_size_mb": 50,
    "backup_count": 5,
}
