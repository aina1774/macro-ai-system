"""
============================================================
AI — Sentiment Analysis avec FinBERT
============================================================
Détecte le sentiment financier et le ton macro (hawkish/dovish)
des articles économiques en utilisant FinBERT.
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from typing import Optional
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import NLP
from database.models.models import get_session, News


# ──────────────────────────────────────────────────────────────
# Règles de détection Hawkish / Dovish
# ──────────────────────────────────────────────────────────────
HAWKISH_SIGNALS = [
    "rate hike", "interest rate increase", "tighten", "tightening",
    "inflation above", "inflation remains high", "persistent inflation",
    "higher for longer", "restrictive", "quantitative tightening", "qt",
    "fed may raise", "rate increase", "hike rates", "combat inflation",
    "price stability", "above target", "overshoot", "hot inflation",
    "strong jobs", "labor market tight", "wages rising",
]

DOVISH_SIGNALS = [
    "rate cut", "interest rate cut", "lower rates", "ease", "easing",
    "pivot", "pause", "hold rates", "rate reduction", "accommodation",
    "quantitative easing", "qe", "stimulus", "support economy",
    "below target", "disinflation", "deflation risk", "recession risk",
    "slowdown", "weak jobs", "unemployment rising", "soft landing",
    "dovish", "gradual approach", "patient",
]

RISK_ON_SIGNALS = [
    "risk appetite", "risk-on", "rally", "bull market", "optimism",
    "strong growth", "beat expectations", "better than expected",
    "soft landing achieved", "disinflation progress",
]

RISK_OFF_SIGNALS = [
    "risk-off", "flight to safety", "sell-off", "bear market",
    "recession", "crisis", "fear", "panic", "uncertainty",
    "worse than expected", "miss expectations", "default",
    "banking stress", "contagion", "systemic risk",
]


class SentimentAnalyzer:

    def __init__(self):
        self.model_name = NLP["model"]
        self.device = NLP["device"]
        self.tokenizer = None
        self.model = None
        self._loaded = False

    def load_model(self):
        """Charge FinBERT (lazy loading — seulement quand nécessaire)."""
        if self._loaded:
            return

        print(f"🤖 Chargement de {self.model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        self._loaded = True
        print("✅ FinBERT chargé.")

    def analyze_finbert(self, text: str) -> dict:
        """
        Analyse le sentiment financier avec FinBERT.

        Returns:
            {
                "label": "positive" | "negative" | "neutral",
                "score": float,          # Confidence 0→1
                "positive": float,
                "negative": float,
                "neutral": float,
            }
        """
        self.load_model()

        # Tronquer le texte si nécessaire
        text = text[:1000].strip()
        if not text:
            return {"label": "neutral", "score": 0.5, "positive": 0.33, "negative": 0.33, "neutral": 0.34}

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=NLP["max_length"],
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)[0]

        # FinBERT labels: positive=0, negative=1, neutral=2
        labels = ["positive", "negative", "neutral"]
        scores = {label: probs[i].item() for i, label in enumerate(labels)}
        best_label = max(scores, key=scores.get)

        return {
            "label": best_label,
            "score": scores[best_label],
            **scores,
        }

    def detect_macro_tone(self, text: str) -> dict:
        """
        Détecte le ton macro économique (hawkish/dovish/risk-on/risk-off).
        Basé sur des règles expertes + FinBERT.

        Returns:
            {
                "tone": "hawkish" | "dovish" | "risk-on" | "risk-off" | "neutral",
                "score": float,     # -1.0 (très dovish) → +1.0 (très hawkish)
                "signals": list,    # Signaux détectés
            }
        """
        text_lower = text.lower()

        hawkish_count = sum(1 for s in HAWKISH_SIGNALS if s in text_lower)
        dovish_count = sum(1 for s in DOVISH_SIGNALS if s in text_lower)
        risk_on_count = sum(1 for s in RISK_ON_SIGNALS if s in text_lower)
        risk_off_count = sum(1 for s in RISK_OFF_SIGNALS if s in text_lower)

        signals_detected = (
            [f"hawkish: {s}" for s in HAWKISH_SIGNALS if s in text_lower][:3] +
            [f"dovish: {s}" for s in DOVISH_SIGNALS if s in text_lower][:3]
        )

        total = hawkish_count + dovish_count
        if total > 0:
            hawkish_score = (hawkish_count - dovish_count) / total
        else:
            hawkish_score = 0.0

        # Détermination du ton dominant
        if hawkish_count > dovish_count and hawkish_count >= 2:
            tone = "hawkish"
        elif dovish_count > hawkish_count and dovish_count >= 2:
            tone = "dovish"
        elif risk_off_count > risk_on_count and risk_off_count >= 2:
            tone = "risk-off"
        elif risk_on_count > risk_off_count and risk_on_count >= 2:
            tone = "risk-on"
        elif hawkish_count == 1 and dovish_count == 0:
            tone = "slightly-hawkish"
        elif dovish_count == 1 and hawkish_count == 0:
            tone = "slightly-dovish"
        else:
            tone = "neutral"

        return {
            "tone": tone,
            "score": round(hawkish_score, 3),
            "hawkish_signals": hawkish_count,
            "dovish_signals": dovish_count,
            "risk_on_signals": risk_on_count,
            "risk_off_signals": risk_off_count,
            "signals": signals_detected,
        }

    def detect_impact_level(self, text: str, category: str) -> str:
        """Estime l'impact d'une news sur les marchés."""
        HIGH_IMPACT_CATEGORIES = ["FOMC/FED", "CPI/Inflation", "NFP/Jobs", "GDP"]
        HIGH_IMPACT_KEYWORDS = [
            "surprise", "unexpected", "shock", "above expectations",
            "below expectations", "crisis", "emergency", "urgent",
            "historic", "record high", "record low", "pivot",
        ]

        if category in HIGH_IMPACT_CATEGORIES:
            base = "high"
        else:
            base = "medium"

        text_lower = text.lower()
        if any(kw in text_lower for kw in HIGH_IMPACT_KEYWORDS):
            if base == "high":
                return "critical"
            return "high"

        if category in ["Markets", "General/Macro"]:
            return "low"

        return base

    def analyze_article(self, title: str, content: str = "", category: str = "") -> dict:
        """
        Analyse complète d'un article : sentiment + tone + impact.

        Returns:
            dict avec tous les scores pour mise à jour en DB.
        """
        full_text = f"{title}. {content}"[:1500]

        # Sentiment FinBERT
        sentiment = self.analyze_finbert(full_text)

        # Tone macro (règles expertes)
        macro = self.detect_macro_tone(full_text)

        # Impact
        impact = self.detect_impact_level(full_text, category)

        return {
            "sentiment_label": sentiment["label"],
            "sentiment_score": round(sentiment["score"], 3),
            "macro_tone": macro["tone"],
            "macro_score": macro["score"],
            "impact_level": impact,
        }

    def process_unanalyzed_news(self, batch_size: int = 50) -> int:
        """
        Analyse les articles non traités en base de données.
        Retourne le nombre d'articles traités.
        """
        self.load_model()
        db = get_session()
        processed = 0

        try:
            unprocessed = (
                db.query(News)
                .filter(News.is_processed == False)
                .limit(batch_size)
                .all()
            )

            print(f"📊 Analyse de {len(unprocessed)} articles...")

            for article in unprocessed:
                try:
                    analysis = self.analyze_article(
                        article.title,
                        article.content or "",
                        article.category or "",
                    )

                    article.sentiment_label = analysis["sentiment_label"]
                    article.sentiment_score = analysis["sentiment_score"]
                    article.macro_tone = analysis["macro_tone"]
                    article.macro_score = analysis["macro_score"]
                    article.impact_level = analysis["impact_level"]
                    article.is_processed = True

                    processed += 1

                except Exception as e:
                    print(f"  ❌ Article {article.id}: {e}")

            db.commit()
            print(f"✅ {processed} articles analysés.")

        except Exception as e:
            db.rollback()
            print(f"❌ Erreur: {e}")
        finally:
            db.close()

        return processed


# ──────────────────────────────────────────────────────────────
# Test rapide
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    test_texts = [
        "Federal Reserve raises interest rates by 25 basis points to combat persistent inflation",
        "Fed signals rate cuts ahead as inflation eases toward target",
        "Markets rally on strong jobs data and positive economic outlook",
        "Recession fears mount as yield curve inverts and PMI falls below 50",
    ]

    print("🧪 Test d'analyse de sentiment:\n")
    for text in test_texts:
        result = analyzer.analyze_article(text)
        print(f"TEXT: {text[:70]}...")
        print(f"  → Sentiment: {result['sentiment_label']} ({result['sentiment_score']:.2f})")
        print(f"  → Tone: {result['macro_tone']} (score: {result['macro_score']:+.2f})")
        print(f"  → Impact: {result['impact_level']}")
        print()
