"""
============================================================
ORCHESTRATEUR PRINCIPAL — Pipeline de collecte automatique
============================================================
Lance tous les collecteurs, analyse le sentiment,
calcule les scores macro et génère les scénarios.

Usage:
    python main.py --init          # Initialise la DB
    python main.py --collect       # Collecte une fois
    python main.py --analyze       # Analyse le sentiment
    python main.py --scores        # Calcule les scores
    python main.py --scenarios     # Génère des scénarios IA
    python main.py --run           # Pipeline complet
    python main.py --scheduler     # Boucle automatique (prod)
    python main.py --dashboard     # Lance Streamlit
"""

import argparse
import time
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import COLLECTION, LOGGING
from database.models.models import init_db
from api_clients.fred.fred_client import FREDClient
from api_clients.newsapi.newsapi_client import NewsAPIClient
from ai.sentiment.sentiment_analyzer import SentimentAnalyzer
from ai.macro_reasoning.macro_engine import MacroReasoningEngine
from engines.sentiment_engine.macro_score_engine import MacroScoreEngine

# ─── Logging ──────────────────────────────────────────────────
os.makedirs(str(LOGGING["file"].parent), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOGGING["level"]),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOGGING["file"])),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("macro_ai")


# ──────────────────────────────────────────────────────────────
def step_init():
    """Étape 0 — Initialisation de la base de données."""
    logger.info("=" * 60)
    logger.info("🚀 INITIALISATION DU SYSTÈME")
    logger.info("=" * 60)
    init_db()


def step_collect_fred():
    """Étape 1a — Collecte des données FRED."""
    logger.info("📡 [FRED] Collecte des séries économiques...")
    client = FREDClient()

    series_data = client.fetch_all_series(lookback_days=COLLECTION["lookback_days"] * 10)
    total_saved = 0

    for series_id, df in series_data.items():
        saved = client.save_to_db(series_id, df)
        total_saved += saved

    logger.info(f"✅ FRED: {total_saved} observations sauvegardées")
    return total_saved


def step_collect_news():
    """Étape 1b — Collecte des news économiques."""
    logger.info("📰 [NewsAPI] Collecte des articles macro...")
    client = NewsAPIClient()

    articles = client.fetch_all_macro_news()
    saved = client.save_to_db(articles)

    logger.info(f"✅ NewsAPI: {saved} articles sauvegardés")
    return saved


def step_analyze_sentiment():
    """Étape 2 — Analyse NLP des articles non traités."""
    logger.info("🧠 [FinBERT] Analyse du sentiment...")
    analyzer = SentimentAnalyzer()

    processed = analyzer.process_unanalyzed_news(batch_size=50)
    logger.info(f"✅ Sentiment: {processed} articles analysés")
    return processed


def step_calculate_scores():
    """Étape 3 — Calcul des scores macro."""
    logger.info("📊 [Engine] Calcul des scores macro...")
    engine = MacroScoreEngine()

    scores = engine.compute_all_scores()
    if scores:
        logger.info(f"✅ Scores calculés — Régime: {scores.regime}")
    else:
        logger.warning("⚠️  Pas assez de données pour calculer les scores")
    return scores


def step_generate_scenarios():
    """Étape 4 — Génération des scénarios IA."""
    logger.info("🎯 [Claude] Génération des scénarios probabilistes...")

    score_engine = MacroScoreEngine()
    latest = score_engine.get_latest_scores()

    if not latest:
        logger.warning("⚠️  Aucun score disponible pour générer des scénarios")
        return

    reasoning_engine = MacroReasoningEngine()
    scenarios = reasoning_engine.generate_scenarios({
        "usd_strength": latest.get("usd_strength", 50),
        "inflation_pressure": latest.get("inflation_pressure", 50),
        "recession_risk": latest.get("recession_risk", 50),
        "dominant_tone": "hawkish" if (latest.get("hawkish_pct", 0) > latest.get("dovish_pct", 0)) else "dovish",
        "recent_events": f"Régime: {latest.get('regime', 'Unknown')}",
    })

    for scenario in scenarios:
        reasoning_engine.save_scenario_to_db(scenario)
        logger.info(
            f"  📋 [{scenario.get('type', '?').upper()}] "
            f"{scenario.get('title', '')} "
            f"— P={scenario.get('probability', 0):.0%}"
        )

    logger.info(f"✅ {len(scenarios)} scénarios générés et sauvegardés")


def run_full_pipeline():
    """Pipeline complet — collecte, analyse, scores, scénarios."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🔄 PIPELINE COMPLET — {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        step_collect_fred()
    except Exception as e:
        logger.error(f"❌ FRED: {e}")

    try:
        step_collect_news()
    except Exception as e:
        logger.error(f"❌ NewsAPI: {e}")

    try:
        step_analyze_sentiment()
    except Exception as e:
        logger.error(f"❌ Sentiment: {e}")

    try:
        step_calculate_scores()
    except Exception as e:
        logger.error(f"❌ Scores: {e}")

    try:
        step_generate_scenarios()
    except Exception as e:
        logger.error(f"❌ Scénarios: {e}")

    elapsed = (datetime.now() - start).seconds
    logger.info(f"✅ Pipeline terminé en {elapsed}s")


def run_scheduler():
    """Boucle automatique pour la production."""
    interval = COLLECTION["interval_minutes"] * 60
    logger.info(f"⏰ Scheduler démarré — intervalle: {COLLECTION['interval_minutes']} min")

    # Premier run immédiat
    run_full_pipeline()

    while True:
        logger.info(f"💤 Prochain cycle dans {COLLECTION['interval_minutes']} minutes...")
        time.sleep(interval)
        run_full_pipeline()


def launch_dashboard():
    """Lance le dashboard Streamlit."""
    logger.info("🖥️  Lancement du dashboard...")
    os.system("streamlit run app/dashboard/dashboard.py --server.port 8501")


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Macro Intelligence System")
    parser.add_argument("--init",       action="store_true", help="Initialise la base de données")
    parser.add_argument("--collect",    action="store_true", help="Collecte les données")
    parser.add_argument("--analyze",    action="store_true", help="Analyse le sentiment NLP")
    parser.add_argument("--scores",     action="store_true", help="Calcule les scores macro")
    parser.add_argument("--scenarios",  action="store_true", help="Génère les scénarios IA")
    parser.add_argument("--run",        action="store_true", help="Pipeline complet (une fois)")
    parser.add_argument("--scheduler",  action="store_true", help="Boucle automatique (prod)")
    parser.add_argument("--dashboard",  action="store_true", help="Lance Streamlit")

    args = parser.parse_args()

    if args.init:
        step_init()
    elif args.collect:
        step_collect_fred()
        step_collect_news()
    elif args.analyze:
        step_analyze_sentiment()
    elif args.scores:
        step_calculate_scores()
    elif args.scenarios:
        step_generate_scenarios()
    elif args.run:
        run_full_pipeline()
    elif args.scheduler:
        run_scheduler()
    elif args.dashboard:
        launch_dashboard()
    else:
        print(__doc__)
        parser.print_help()
