"""
============================================================
DATABASE — Modèles & Initialisation
============================================================
Gère SQLite (dev) et PostgreSQL (prod) via SQLAlchemy.
"""

from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Text, DateTime, Boolean, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE

Base = declarative_base()


# ──────────────────────────────────────────────────────────────
# TABLE 1 : News économiques
# ──────────────────────────────────────────────────────────────
class News(Base):
    __tablename__ = "news"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    title           = Column(Text, nullable=False)
    content         = Column(Text)
    summary         = Column(Text)
    source          = Column(String(100))
    url             = Column(Text)
    author          = Column(String(200))
    published_at    = Column(DateTime)
    collected_at    = Column(DateTime, default=datetime.utcnow)

    # NLP Results
    sentiment_label = Column(String(50))   # positive / negative / neutral
    sentiment_score = Column(Float)        # 0.0 → 1.0
    macro_tone      = Column(String(50))   # hawkish / dovish / neutral / risk-on / risk-off
    macro_score     = Column(Float)        # -1.0 → +1.0
    impact_level    = Column(String(20))   # low / medium / high / critical

    # Catégorisation
    category        = Column(String(100))  # CPI / FED / GDP / NFP / etc.
    keywords        = Column(Text)         # JSON list
    entities        = Column(Text)         # JSON list (banques centrales, etc.)

    # Déduplication
    content_hash    = Column(String(64), unique=True)
    is_processed    = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_news_published", "published_at"),
        Index("idx_news_source", "source"),
        Index("idx_news_sentiment", "macro_tone"),
        Index("idx_news_category", "category"),
    )

    def __repr__(self):
        return f"<News id={self.id} source={self.source} tone={self.macro_tone}>"


# ──────────────────────────────────────────────────────────────
# TABLE 2 : Scores Macro (snapshot périodique)
# ──────────────────────────────────────────────────────────────
class MacroScore(Base):
    __tablename__ = "macro_scores"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    timestamp           = Column(DateTime, default=datetime.utcnow, index=True)

    # Scores principaux (0 → 100)
    usd_strength        = Column(Float)
    inflation_pressure  = Column(Float)
    recession_risk      = Column(Float)
    fear_index          = Column(Float)
    risk_sentiment      = Column(Float)   # 0=extreme fear, 100=extreme greed

    # Labels qualitatifs
    usd_label           = Column(String(50))    # Bearish / Neutral / Bullish
    inflation_label     = Column(String(50))    # Low / Moderate / High / Very High
    recession_label     = Column(String(50))    # Low / Moderate / High
    fear_label          = Column(String(50))    # Greed / Neutral / Fear / Extreme Fear

    # Contexte macro global
    regime              = Column(String(100))   # Risk-On / Risk-Off / Stagflation / etc.
    dominant_narrative  = Column(Text)          # Résumé IA du contexte

    # Sources du calcul
    news_count          = Column(Integer)
    hawkish_pct         = Column(Float)
    dovish_pct          = Column(Float)
    neutral_pct         = Column(Float)

    def __repr__(self):
        return f"<MacroScore ts={self.timestamp} usd={self.usd_strength:.1f} inf={self.inflation_pressure:.1f}>"


# ──────────────────────────────────────────────────────────────
# TABLE 3 : Données de marché
# ──────────────────────────────────────────────────────────────
class MarketData(Base):
    __tablename__ = "market_data"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    symbol      = Column(String(50), nullable=False)
    name        = Column(String(100))
    asset_class = Column(String(50))   # forex / equity / bond / commodity / crypto
    timestamp   = Column(DateTime, default=datetime.utcnow)

    open        = Column(Float)
    high        = Column(Float)
    low         = Column(Float)
    close       = Column(Float)
    volume      = Column(Float)
    change_pct  = Column(Float)

    source      = Column(String(50))

    __table_args__ = (
        Index("idx_market_symbol_ts", "symbol", "timestamp"),
    )


# ──────────────────────────────────────────────────────────────
# TABLE 4 : Données FRED (séries économiques)
# ──────────────────────────────────────────────────────────────
class FredData(Base):
    __tablename__ = "fred_data"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    series_id   = Column(String(50), nullable=False)
    series_name = Column(String(200))
    date        = Column(DateTime, nullable=False)
    value       = Column(Float)
    units       = Column(String(100))
    collected_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_fred_series_date", "series_id", "date"),
    )


# ──────────────────────────────────────────────────────────────
# TABLE 5 : Corrélations détectées
# ──────────────────────────────────────────────────────────────
class Correlation(Base):
    __tablename__ = "correlations"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    timestamp       = Column(DateTime, default=datetime.utcnow)
    asset_a         = Column(String(50))
    asset_b         = Column(String(50))
    correlation     = Column(Float)      # -1.0 → +1.0
    period_days     = Column(Integer)    # Fenêtre de calcul
    interpretation  = Column(Text)       # Ex: "DXY ↑ → Gold ↓ (correlation: -0.82)"


# ──────────────────────────────────────────────────────────────
# TABLE 6 : Alertes générées
# ──────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    level       = Column(String(20))    # info / warning / critical
    category    = Column(String(50))    # sentiment_shift / score_threshold / regime_change
    title       = Column(String(200))
    message     = Column(Text)
    is_read     = Column(Boolean, default=False)


# ──────────────────────────────────────────────────────────────
# TABLE 7 : Scénarios IA générés
# ──────────────────────────────────────────────────────────────
class Scenario(Base):
    __tablename__ = "scenarios"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    generated_at    = Column(DateTime, default=datetime.utcnow)
    trigger_event   = Column(Text)          # News/event qui a déclenché le scénario
    scenario_type   = Column(String(50))    # base / bull / bear / tail_risk
    probability     = Column(Float)         # 0.0 → 1.0
    title           = Column(String(200))
    narrative       = Column(Text)          # Analyse narrative complète (Claude)
    market_impacts  = Column(Text)          # JSON: impacts estimés par marché
    horizon_weeks   = Column(Integer)       # Horizon temporel du scénario


# ──────────────────────────────────────────────────────────────
# Initialisation de la base
# ──────────────────────────────────────────────────────────────
def get_engine():
    if DATABASE["engine"] == "postgresql":
        url = (
            f"postgresql://{DATABASE['pg_user']}:{DATABASE['pg_password']}"
            f"@{DATABASE['pg_host']}:{DATABASE['pg_port']}/{DATABASE['pg_name']}"
        )
    else:
        db_path = DATABASE["sqlite_path"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        url = f"sqlite:///{db_path}"

    return create_engine(url, echo=False)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Crée toutes les tables si elles n'existent pas."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("✅ Base de données initialisée avec succès.")
    return engine


if __name__ == "__main__":
    init_db()
