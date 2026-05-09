"""
REAL-TIME SCHEDULER — AI Macro Intelligence System
Frequences :
  News (NewsAPI)      toutes les 15 min
  Marches (Finnhub)   toutes les 5 min
  FRED                toutes les 6h
  Sentiment NLP       apres chaque batch de news
  Scores Macro        apres chaque cycle news
"""

import schedule
import time
import threading
import logging
import argparse
import signal
import sys
import os
from datetime import datetime
from collections import defaultdict

# Fix Windows UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import COLLECTION, LOGGING

# Logging
os.makedirs(str(LOGGING["file"].parent), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(str(LOGGING["file"]), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")

stats = defaultdict(lambda: {
    "runs": 0,
    "errors": 0,
    "last_run": None,
    "last_status": "pending",
    "last_duration_s": 0,
})

_lock = threading.Lock()
_running = True


def job(name: str, fn, exclusive: bool = False):
    def wrapper():
        if exclusive and _lock.locked():
            return
        start = datetime.now()
        logger.info(f"[START] {name}")
        try:
            if exclusive:
                with _lock:
                    fn()
            else:
                fn()
            duration = (datetime.now() - start).seconds
            with threading.Lock():
                stats[name]["runs"] += 1
                stats[name]["last_run"] = datetime.now()
                stats[name]["last_status"] = "OK"
                stats[name]["last_duration_s"] = duration
            logger.info(f"[OK] {name} termine en {duration}s")
        except Exception as e:
            duration = (datetime.now() - start).seconds
            with threading.Lock():
                stats[name]["errors"] += 1
                stats[name]["last_run"] = datetime.now()
                stats[name]["last_status"] = f"ERREUR: {str(e)[:60]}"
                stats[name]["last_duration_s"] = duration
            logger.error(f"[ERREUR] {name}: {e}", exc_info=True)
    return wrapper


def collect_news():
    from api_clients.newsapi.newsapi_client import NewsAPIClient
    client = NewsAPIClient()
    articles = client.fetch_all_macro_news()
    saved = client.save_to_db(articles)
    logger.info(f"News: {saved} nouveaux articles")


def collect_fred():
    from api_clients.fred.fred_client import FREDClient
    client = FREDClient()
    series_data = client.fetch_all_series(lookback_days=30)
    total = sum(client.save_to_db(sid, df) for sid, df in series_data.items())
    logger.info(f"FRED: {total} nouvelles observations")


def collect_markets():
    try:
        from api_clients.finnhub.finnhub_client import FinnhubClient
        client = FinnhubClient()
        client.fetch_and_save_all()
    except ImportError:
        pass


def analyze_sentiment():
    from ai.sentiment.sentiment_analyzer import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    processed = analyzer.process_unanalyzed_news(batch_size=30)
    logger.info(f"Sentiment: {processed} articles analyses")


def calculate_scores():
    from engines.sentiment_engine.macro_score_engine import MacroScoreEngine
    engine = MacroScoreEngine()
    scores = engine.compute_all_scores()
    if scores:
        logger.info(
            f"Scores - USD:{scores.usd_strength:.0f} "
            f"INF:{scores.inflation_pressure:.0f} "
            f"REC:{scores.recession_risk:.0f} "
            f"FEAR:{scores.fear_index:.0f} "
            f"| {scores.regime}"
        )


def news_then_sentiment():
    collect_news()
    analyze_sentiment()
    calculate_scores()


def print_status():
    logger.info("=" * 60)
    logger.info("STATUS DU SCHEDULER")
    logger.info("=" * 60)
    for name, s in stats.items():
        last = s["last_run"].strftime("%H:%M:%S") if s["last_run"] else "jamais"
        logger.info(
            f"  {name:<30} | runs:{s['runs']:>4} | err:{s['errors']:>3} "
            f"| last:{last} | {s['last_status']}"
        )
    logger.info("=" * 60)


def setup_schedule():
    schedule.every(15).minutes.do(
        job("news+sentiment+scores", news_then_sentiment, exclusive=True)
    )
    schedule.every(5).minutes.do(
        job("markets", collect_markets)
    )
    schedule.every(6).hours.do(
        job("fred", collect_fred)
    )
    schedule.every(1).hours.do(print_status)

    logger.info("Schedule configure:")
    logger.info("  News + Sentiment + Scores  -> toutes les 15 min")
    logger.info("  Marches                    -> toutes les 5 min")
    logger.info("  FRED                       -> toutes les 6h")


def run_initial_pipeline():
    logger.info("Premier cycle de demarrage...")
    for name, fn in [
        ("fred", collect_fred),
        ("news+sentiment+scores", news_then_sentiment),
        ("markets", collect_markets),
    ]:
        job(name, fn, exclusive=False)()
        time.sleep(2)
    logger.info("Cycle initial termine - scheduler actif")


def handle_signal(sig, frame):
    global _running
    logger.info("Arret du scheduler...")
    print_status()
    _running = False
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def run_scheduler():
    logger.info("=" * 60)
    logger.info("AI MACRO INTELLIGENCE - REAL-TIME SCHEDULER")
    logger.info(f"Demarre le {datetime.now().strftime('%Y-%m-%d a %H:%M:%S')}")
    logger.info("Ctrl+C pour arreter")
    logger.info("=" * 60)
    setup_schedule()
    run_initial_pipeline()
    while _running:
        schedule.run_pending()
        time.sleep(30)


def run_once():
    logger.info("Mode --once : cycle unique")
    collect_fred()
    news_then_sentiment()
    collect_markets()
    print_status()
    logger.info("Cycle termine.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Macro - Real-Time Scheduler")
    parser.add_argument("--once",   action="store_true", help="Un seul cycle complet")
    parser.add_argument("--status", action="store_true", help="Affiche le statut")
    args = parser.parse_args()

    if args.once:
        run_once()
    elif args.status:
        logger.info("Lance: python scheduler.py pour voir les stats en live")
    else:
        run_scheduler()
