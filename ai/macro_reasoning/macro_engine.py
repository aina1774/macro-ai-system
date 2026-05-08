"""
============================================================
AI — Macro Reasoning Engine (Claude API)
============================================================
Génère des analyses macro institutionnelles et des scénarios
probabilistes en utilisant Claude comme cerveau analytique.
"""

import anthropic
import json
from datetime import datetime
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import API_KEYS
from database.models.models import get_session, News, MacroScore, Scenario

SYSTEM_PROMPT = """You are an elite institutional macro economist and market analyst.
Your role is to provide rigorous, objective macroeconomic analysis — NOT trading recommendations.

You analyze:
- Central bank policy signals (hawkish/dovish tone shifts)
- Inflation dynamics and their second-order effects
- Growth trajectory and recession probability
- Market regime changes (risk-on/risk-off)
- Cross-asset correlations and market stress indicators

Your output is always:
1. Factual and evidence-based
2. Probabilistic (assign confidence levels)
3. Multi-scenario (base case + alternatives)
4. Institutionally rigorous

You NEVER suggest specific trades or positions.
Respond in the language of the user's input (French or English).
"""


class MacroReasoningEngine:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=API_KEYS["anthropic"])
        self.model = "claude-sonnet-4-20250514"

    def _call_claude(self, prompt: str, max_tokens: int = 1500) -> str:
        """Appel direct à l'API Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def analyze_news_macro_impact(self, title: str, content: str, category: str) -> dict:
        """
        Analyse l'impact macro d'une news spécifique.

        Returns:
            {
                "interpretation": str,      # Analyse narrative
                "affected_markets": list,   # Marchés impactés
                "usd_impact": str,          # bullish / bearish / neutral
                "rate_expectation": str,    # higher / lower / unchanged
                "risk_bias": str,           # risk-on / risk-off / neutral
                "confidence": float,        # 0.0 → 1.0
            }
        """
        prompt = f"""Analyze this economic news and provide a structured macro interpretation:

CATEGORY: {category}
TITLE: {title}
CONTENT: {content[:800]}

Respond ONLY with a JSON object (no markdown, no explanation) with this structure:
{{
  "interpretation": "2-3 sentence macro interpretation",
  "key_insight": "single most important takeaway",
  "affected_markets": ["USD", "Gold", "Nasdaq", ...],
  "usd_impact": "bullish|bearish|neutral",
  "rate_expectation": "higher|lower|unchanged",
  "risk_bias": "risk-on|risk-off|neutral",
  "confidence": 0.75,
  "reasoning": "brief explanation of the analysis logic"
}}"""

        try:
            response = self._call_claude(prompt, max_tokens=600)
            # Nettoyer la réponse si besoin
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            return {
                "interpretation": f"Analysis unavailable: {e}",
                "affected_markets": [],
                "usd_impact": "neutral",
                "rate_expectation": "unchanged",
                "risk_bias": "neutral",
                "confidence": 0.0,
                "reasoning": "",
            }

    def generate_macro_narrative(self, macro_scores: dict, recent_news: list[dict]) -> str:
        """
        Génère une analyse narrative du contexte macro global.

        Args:
            macro_scores: Dict des scores actuels {usd_strength, inflation_pressure, etc.}
            recent_news: Liste des 10 dernières news importantes
        """
        news_summary = "\n".join([
            f"- [{n.get('category', '')}] {n.get('title', '')} (tone: {n.get('macro_tone', 'neutral')})"
            for n in recent_news[:10]
        ])

        prompt = f"""Based on the following macroeconomic dashboard and recent news, generate a comprehensive macro narrative analysis (3-4 paragraphs).

CURRENT MACRO SCORES:
- USD Strength: {macro_scores.get('usd_strength', 50):.0f}/100
- Inflation Pressure: {macro_scores.get('inflation_pressure', 50):.0f}/100
- Recession Risk: {macro_scores.get('recession_risk', 50):.0f}/100
- Fear Index: {macro_scores.get('fear_index', 50):.0f}/100
- Market Regime: {macro_scores.get('regime', 'Uncertain')}

RECENT NEWS FLOW:
{news_summary}

Write a rigorous institutional macro analysis covering:
1. Current monetary policy environment
2. Inflation and growth dynamics
3. Market sentiment and risk appetite
4. Key risks and uncertainties

Write in French. Be analytical, not sensationalist."""

        try:
            return self._call_claude(prompt, max_tokens=800)
        except Exception as e:
            return f"Analyse macro indisponible: {e}"

    def generate_scenarios(self, context: dict) -> list[dict]:
        """
        Génère 3 scénarios probabilistes (base, bull, bear).

        Args:
            context: Contexte macro actuel

        Returns:
            Liste de scénarios avec probabilités et narratives
        """
        prompt = f"""Generate 3 macroeconomic scenarios based on the current context.

MACRO CONTEXT:
- USD Strength: {context.get('usd_strength', 50):.0f}/100
- Inflation Pressure: {context.get('inflation_pressure', 50):.0f}/100
- Recession Risk: {context.get('recession_risk', 50):.0f}/100
- Dominant Tone: {context.get('dominant_tone', 'neutral')}
- Recent Events: {context.get('recent_events', 'No major events')}

Respond ONLY with a JSON array (no markdown) with exactly 3 scenarios:
[
  {{
    "type": "base",
    "title": "Scenario title",
    "probability": 0.55,
    "horizon_weeks": 8,
    "narrative": "2-3 sentence scenario description",
    "key_conditions": ["condition 1", "condition 2"],
    "market_impacts": {{
      "USD": "bullish/bearish/neutral",
      "Gold": "bullish/bearish/neutral",
      "Nasdaq": "bullish/bearish/neutral",
      "Bonds": "bullish/bearish/neutral"
    }}
  }},
  {{
    "type": "bull",
    "probability": 0.25,
    ...
  }},
  {{
    "type": "bear",
    "probability": 0.20,
    ...
  }}
]

Probabilities must sum to 1.0."""

        try:
            response = self._call_claude(prompt, max_tokens=1000)
            response = response.strip()
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            print(f"❌ Erreur génération scénarios: {e}")
            return []

    def detect_regime_change(self, current_scores: dict, previous_scores: dict) -> Optional[dict]:
        """
        Détecte un changement de régime macro entre deux périodes.

        Returns:
            None si pas de changement, sinon dict avec description du changement.
        """
        if not previous_scores:
            return None

        changes = {}
        threshold = 15  # Changement significatif si > 15 points

        for metric in ["usd_strength", "inflation_pressure", "recession_risk", "fear_index"]:
            curr = current_scores.get(metric, 50)
            prev = previous_scores.get(metric, 50)
            delta = curr - prev

            if abs(delta) >= threshold:
                changes[metric] = {
                    "previous": prev,
                    "current": curr,
                    "delta": delta,
                    "direction": "↑" if delta > 0 else "↓",
                }

        if not changes:
            return None

        # Demander à Claude d'interpréter le changement
        changes_text = "\n".join([
            f"- {k}: {v['previous']:.0f} → {v['current']:.0f} ({v['direction']} {abs(v['delta']):.0f} pts)"
            for k, v in changes.items()
        ])

        prompt = f"""A significant macro regime shift has been detected:

{changes_text}

In 2 sentences, describe what this regime change means for the macro environment.
Respond in French."""

        interpretation = self._call_claude(prompt, max_tokens=200)

        return {
            "detected_at": datetime.utcnow().isoformat(),
            "changes": changes,
            "interpretation": interpretation,
            "severity": "high" if len(changes) >= 3 else "medium",
        }

    def save_scenario_to_db(self, scenario: dict, trigger_event: str = ""):
        """Sauvegarde un scénario généré en base de données."""
        db = get_session()
        try:
            s = Scenario(
                trigger_event=trigger_event,
                scenario_type=scenario.get("type", "base"),
                probability=scenario.get("probability", 0.33),
                title=scenario.get("title", ""),
                narrative=scenario.get("narrative", ""),
                market_impacts=json.dumps(scenario.get("market_impacts", {})),
                horizon_weeks=scenario.get("horizon_weeks", 4),
            )
            db.add(s)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur sauvegarde scénario: {e}")
        finally:
            db.close()


# ──────────────────────────────────────────────────────────────
# Test rapide
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = MacroReasoningEngine()

    print("🧠 Test analyse news...")
    result = engine.analyze_news_macro_impact(
        title="US CPI rises 3.5% above expectations, Fed may delay rate cuts",
        content="The Consumer Price Index rose more than expected in March, suggesting the Federal Reserve may need to keep interest rates higher for longer.",
        category="CPI/Inflation"
    )
    print(json.dumps(result, indent=2))

    print("\n📊 Test génération scénarios...")
    scenarios = engine.generate_scenarios({
        "usd_strength": 72,
        "inflation_pressure": 68,
        "recession_risk": 35,
        "dominant_tone": "hawkish",
        "recent_events": "CPI surprise, strong NFP",
    })
    for s in scenarios:
        print(f"\n[{s.get('type', '?').upper()}] {s.get('title', '')} — P={s.get('probability', 0):.0%}")
        print(f"  {s.get('narrative', '')}")
