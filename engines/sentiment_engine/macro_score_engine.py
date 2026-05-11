"""
============================================================
ENGINE — Calcul des Scores Macro
============================================================
Calcule les scores USD, Inflation, Recession Risk, Fear Index
en combinant données FRED + sentiment NLP des news.
"""

from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import MACRO_WEIGHTS, ALERT_THRESHOLDS
from database.models.models import get_session, News, MacroScore, FredData, Alert


class MacroScoreEngine:

    def __init__(self):
        self.db = None

    def _get_recent_news_stats(self, hours: int = 48) -> dict:
        """Calcule les statistiques de sentiment sur les N dernières heures."""
        db = get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = db.query(News).filter(
                News.published_at >= cutoff,
                News.is_processed == True,
            ).all()

            if not recent:
                return {
                    "count": 0,
                    "hawkish_pct": 0.33,
                    "dovish_pct": 0.33,
                    "neutral_pct": 0.34,
                    "avg_sentiment": 0.0,
                    "negative_pct": 0.33,
                }

            total = len(recent)
            hawkish = sum(1 for n in recent if n.macro_tone in ["hawkish", "slightly-hawkish"])
            dovish  = sum(1 for n in recent if n.macro_tone in ["dovish", "slightly-dovish"])
            riskoff = sum(1 for n in recent if n.macro_tone == "risk-off")
            negative = sum(1 for n in recent if n.sentiment_label == "negative")

            avg_macro_score = sum((n.macro_score or 0) for n in recent) / total

            return {
                "count": total,
                "hawkish_pct": hawkish / total,
                "dovish_pct": dovish / total,
                "risk_off_pct": riskoff / total,
                "neutral_pct": max(0, 1 - hawkish/total - dovish/total),
                "avg_sentiment": avg_macro_score,
                "negative_pct": negative / total,
            }
        finally:
            db.close()

    def _get_fred_value(self, series_id: str) -> Optional[float]:
        """Récupère la dernière valeur FRED depuis la DB."""
        db = get_session()
        try:
            row = (
                db.query(FredData)
                .filter_by(series_id=series_id)
                .order_by(FredData.date.desc())
                .first()
            )
            return row.value if row else None
        finally:
            db.close()

    def _normalize(self, value: float, min_val: float, max_val: float, invert: bool = False) -> float:
        """Normalise une valeur entre 0 et 100."""
        if max_val == min_val:
            return 50.0
        normalized = (value - min_val) / (max_val - min_val) * 100
        normalized = max(0, min(100, normalized))
        return (100 - normalized) if invert else normalized

    def calculate_usd_strength(self, news_stats: dict) -> tuple[float, str]:
        """
        Score USD Strength (0→100, 50=neutre, >50=haussier).

        Facteurs:
        - Sentiment hawkish des news FED (35%)
        - Écart de taux 10Y-2Y (25%)
        - Surprise CPI (20%)
        - Risk sentiment général (20%)
        """
        weights = MACRO_WEIGHTS["usd_strength"]

        # Hawkish sentiment → USD haussier
        hawkish_score = news_stats["hawkish_pct"] * 100 * weights["fed_hawkish_sentiment"]

        # Yield spread (T10Y2Y) — spread positif = normale = USD neutre
        yield_spread = self._get_fred_value("T10Y2Y") or 0
        yield_score = self._normalize(yield_spread, -1.5, 2.0) * weights["yield_spread"]

        # CPI — si haut = pression sur FED = USD haussier potentiel
        cpi = self._get_fred_value("CPIAUCSL") or 3.0
        cpi_score = self._normalize(cpi, 1.0, 6.0) * weights["cpi_surprise"]

        # Risk-off → USD refuge → haussier
        risk_off_contribution = news_stats.get("risk_off_pct", 0) * 100
        risk_score = risk_off_contribution * weights["risk_sentiment"]

        # Base 50 + ajustements
        raw_score = 50 + (hawkish_score - 25) + (yield_score - 12.5) + (cpi_score - 10) + (risk_score - 10)
        score = max(0, min(100, raw_score))

        if score >= 70:
            label = "Strongly Bullish"
        elif score >= 58:
            label = "Bullish"
        elif score <= 30:
            label = "Strongly Bearish"
        elif score <= 42:
            label = "Bearish"
        else:
            label = "Neutral"

        return round(score, 1), label

    def calculate_inflation_pressure(self, news_stats: dict) -> tuple[float, str]:
        """
        Score Inflation Pressure (0→100, >70=High).
        """
        cpi = self._get_fred_value("CPIAUCSL") or 3.0
        oil = self._get_fred_value("DCOILWTICO") or 70.0

        cpi_score = self._normalize(cpi, 0.5, 7.0) * 0.50
        oil_score = self._normalize(oil, 40.0, 120.0) * 0.25
        hawkish_news = news_stats["hawkish_pct"] * 100 * 0.25

        score = cpi_score + oil_score + hawkish_news
        score = max(0, min(100, score))

        if score >= 75:
            label = "Very High"
        elif score >= 55:
            label = "High"
        elif score >= 35:
            label = "Moderate"
        else:
            label = "Low"

        return round(score, 1), label

    def calculate_recession_risk(self, news_stats: dict) -> tuple[float, str]:
        """
        Score Recession Risk (0→100, >65=High Risk).
        """
        yield_curve = self._get_fred_value("T10Y2Y") or 0.5
        unemployment = self._get_fred_value("UNRATE") or 4.0

        # Yield curve inversée (négative) = signe de récession
        yield_risk = self._normalize(yield_curve, -1.5, 2.0, invert=True) * 0.35

        # Chômage élevé = risque récession
        unemp_risk = self._normalize(unemployment, 3.0, 8.0) * 0.25

        # Sentiment dovish/risk-off dans les news
        dovish_risk = news_stats["dovish_pct"] * 100 * 0.25
        riskoff_risk = news_stats.get("risk_off_pct", 0) * 100 * 0.15

        score = yield_risk + unemp_risk + dovish_risk + riskoff_risk
        score = max(0, min(100, score))

        if score >= 65:
            label = "High"
        elif score >= 45:
            label = "Moderate"
        elif score >= 25:
            label = "Low"
        else:
            label = "Very Low"

        return round(score, 1), label

    def calculate_fear_index(self, news_stats: dict) -> tuple[float, str]:
        """
        Score Fear Index (0=Extreme Greed → 100=Extreme Fear).
        """
        vix = self._get_fred_value("VIXCLS") or 18.0

        vix_score = self._normalize(vix, 10.0, 45.0) * 0.45
        news_fear = news_stats["negative_pct"] * 100 * 0.30
        riskoff = news_stats.get("risk_off_pct", 0) * 100 * 0.25

        score = vix_score + news_fear + riskoff
        score = max(0, min(100, score))

        if score >= 75:
            label = "Extreme Fear"
        elif score >= 60:
            label = "Fear"
        elif score <= 25:
            label = "Extreme Greed"
        elif score <= 40:
            label = "Greed"
        else:
            label = "Neutral"

        return round(score, 1), label

    def determine_regime(self, usd: float, inflation: float, recession: float, fear: float) -> str:
        """Détermine le régime macro dominant."""
        if inflation >= 65 and recession <= 35:
            return "Inflation / Hawkish Cycle"
        elif recession >= 60 and fear >= 60:
            return "Risk-Off / Recession Fear"
        elif fear >= 70:
            return "Extreme Risk-Off / Crisis"
        elif usd >= 65 and inflation >= 60:
            return "Stagflation Risk"
        elif recession <= 30 and fear <= 35:
            return "Risk-On / Growth"
        elif inflation <= 35 and recession <= 35:
            return "Goldilocks / Soft Landing"
        else:
            return "Mixed / Transitional"

    def compute_all_scores(self) -> Optional[MacroScore]:
        """
        Calcule tous les scores macro et les sauvegarde en DB.

        Returns:
            MacroScore object ou None si erreur.
        """
        print("📊 Calcul des scores macro...")
        news_stats = self._get_recent_news_stats(hours=48)

        if news_stats["count"] == 0:
            print("⚠️  Pas assez de news pour calculer les scores.")
            # return None  # disabled

        usd_score, usd_label = self.calculate_usd_strength(news_stats)
        inf_score, inf_label = self.calculate_inflation_pressure(news_stats)
        rec_score, rec_label = self.calculate_recession_risk(news_stats)
        fear_score, fear_label = self.calculate_fear_index(news_stats)
        regime = self.determine_regime(usd_score, inf_score, rec_score, fear_score)

        macro = MacroScore(
            usd_strength=usd_score,
            usd_label=usd_label,
            inflation_pressure=inf_score,
            inflation_label=inf_label,
            recession_risk=rec_score,
            recession_label=rec_label,
            fear_index=fear_score,
            fear_label=fear_label,
            risk_sentiment=100 - fear_score,
            regime=regime,
            news_count=news_stats["count"],
            hawkish_pct=news_stats["hawkish_pct"] * 100,
            dovish_pct=news_stats["dovish_pct"] * 100,
            neutral_pct=news_stats["neutral_pct"] * 100,
        )

        db = get_session()
        try:
            db.add(macro)
            db.commit()
            db.refresh(macro)

            print(f"  💵 USD Strength:       {usd_score:.0f}/100 — {usd_label}")
            print(f"  🔥 Inflation Pressure: {inf_score:.0f}/100 — {inf_label}")
            print(f"  📉 Recession Risk:     {rec_score:.0f}/100 — {rec_label}")
            print(f"  😱 Fear Index:         {fear_score:.0f}/100 — {fear_label}")
            print(f"  🌍 Regime:             {regime}")

            self._check_and_create_alerts(macro)
            return macro

        except Exception as e:
            db.rollback()
            print(f"❌ Erreur: {e}")
            return None
        finally:
            db.close()

    def _check_and_create_alerts(self, macro: MacroScore):
        """Génère des alertes si des seuils sont dépassés."""
        db = get_session()
        alerts_to_create = []

        thresholds = ALERT_THRESHOLDS

        if macro.fear_index and macro.fear_index >= thresholds["fear_index_high"]:
            alerts_to_create.append(Alert(
                level="warning",
                category="score_threshold",
                title=f"⚠️ Fear Index élevé: {macro.fear_index:.0f}/100",
                message=f"Le Fear Index a atteint {macro.fear_index:.0f}/100 ({macro.fear_label}). Régime: {macro.regime}",
            ))

        if macro.recession_risk and macro.recession_risk >= thresholds["recession_risk_high"]:
            alerts_to_create.append(Alert(
                level="critical",
                category="score_threshold",
                title=f"🔴 Risque de récession élevé: {macro.recession_risk:.0f}/100",
                message=f"Le risque de récession a atteint {macro.recession_risk:.0f}/100 ({macro.recession_label}).",
            ))

        if macro.inflation_pressure and macro.inflation_pressure >= thresholds["inflation_pressure_high"]:
            alerts_to_create.append(Alert(
                level="warning",
                category="score_threshold",
                title=f"🔥 Pression inflationniste: {macro.inflation_pressure:.0f}/100",
                message=f"La pression inflationniste est à {macro.inflation_pressure:.0f}/100 ({macro.inflation_label}).",
            ))

        try:
            for alert in alerts_to_create:
                db.add(alert)
            db.commit()
            if alerts_to_create:
                print(f"  🚨 {len(alerts_to_create)} alertes générées.")
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def get_latest_scores(self) -> Optional[dict]:
        """Récupère le dernier snapshot de scores depuis la DB."""
        db = get_session()
        try:
            latest = db.query(MacroScore).order_by(MacroScore.timestamp.desc()).first()
            if not latest:
                return None
            return {
                "timestamp": latest.timestamp,
                "usd_strength": latest.usd_strength,
                "usd_label": latest.usd_label,
                "inflation_pressure": latest.inflation_pressure,
                "inflation_label": latest.inflation_label,
                "recession_risk": latest.recession_risk,
                "recession_label": latest.recession_label,
                "fear_index": latest.fear_index,
                "fear_label": latest.fear_label,
                "regime": latest.regime,
                "hawkish_pct": latest.hawkish_pct,
                "dovish_pct": latest.dovish_pct,
                "news_count": latest.news_count,
            }
        finally:
            db.close()
