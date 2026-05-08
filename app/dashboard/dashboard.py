"""
============================================================
DASHBOARD — AI Macro Intelligence System
============================================================
Interface Streamlit professionnelle pour visualiser
les analyses macro en temps réel.

Usage: streamlit run app/dashboard/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import DASHBOARD
from database.models.models import get_session, News, MacroScore, Alert, Scenario, FredData

# ─── Configuration Page ──────────────────────────────────────
st.set_page_config(
    page_title="AI Macro Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS Custom ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: #0a0e1a;
        color: #e0e6f0;
    }

    .main-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.6rem;
        font-weight: 600;
        color: #4fc3f7;
        letter-spacing: 0.05em;
        border-bottom: 1px solid #1e2d4a;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #0d1b2e 0%, #112240 100%);
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }

    .metric-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #7a9bbf;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.4rem;
    }

    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        line-height: 1;
    }

    .metric-label-text {
        font-size: 0.8rem;
        margin-top: 0.3rem;
        font-weight: 600;
    }

    .regime-badge {
        background: #1a2f4e;
        border: 1px solid #2e5077;
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #4fc3f7;
        display: inline-block;
        margin: 0.3rem 0;
    }

    .news-item {
        background: #0d1b2e;
        border-left: 3px solid #1e3a5f;
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }

    .news-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #ccd6f6;
        margin-bottom: 0.2rem;
    }

    .news-meta {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #5a7a9e;
    }

    .tone-hawkish  { color: #ef5350 !important; border-left-color: #ef5350 !important; }
    .tone-dovish   { color: #26c6da !important; border-left-color: #26c6da !important; }
    .tone-riskoff  { color: #ffa726 !important; border-left-color: #ffa726 !important; }
    .tone-riskon   { color: #66bb6a !important; border-left-color: #66bb6a !important; }
    .tone-neutral  { color: #7a9bbf !important; }

    .alert-critical { border-left: 4px solid #ef5350; background: #1a0a0a; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }
    .alert-warning  { border-left: 4px solid #ffa726; background: #1a1200; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }
    .alert-info     { border-left: 4px solid #4fc3f7; background: #001a2a; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }

    .scenario-card {
        background: #0d1b2e;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    .stDataFrame { background: #0d1b2e; }
    div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Helpers de couleur
# ──────────────────────────────────────────────────────────────
def score_color(score: float) -> str:
    if score >= 70: return "#ef5350"
    elif score >= 55: return "#ffa726"
    elif score <= 30: return "#26c6da"
    elif score <= 45: return "#66bb6a"
    return "#7a9bbf"

def tone_color(tone: str) -> str:
    colors = {
        "hawkish": "#ef5350", "slightly-hawkish": "#ff7043",
        "dovish": "#26c6da",  "slightly-dovish": "#4dd0e1",
        "risk-off": "#ffa726","risk-on": "#66bb6a",
        "neutral": "#7a9bbf",
    }
    return colors.get(tone, "#7a9bbf")

def gauge_chart(value: float, title: str, color: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 12, "color": "#7a9bbf", "family": "IBM Plex Mono"}},
        number={"font": {"size": 32, "color": color, "family": "IBM Plex Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#2e4a6a", "tickfont": {"size": 8}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#0d1b2e",
            "bordercolor": "#1e3a5f",
            "steps": [
                {"range": [0, 33],  "color": "#051020"},
                {"range": [33, 66], "color": "#0a1828"},
                {"range": [66, 100],"color": "#0f2035"},
            ],
            "threshold": {
                "line": {"color": "#4fc3f7", "width": 2},
                "thickness": 0.8,
                "value": 50,
            },
        },
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font={"color": "#e0e6f0"},
    )
    return fig


# ──────────────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=DASHBOARD["refresh_interval_seconds"])
def load_latest_scores():
    db = get_session()
    try:
        row = db.query(MacroScore).order_by(MacroScore.timestamp.desc()).first()
        if not row:
            return None
        return {
            "timestamp": row.timestamp,
            "usd_strength": row.usd_strength or 50,
            "usd_label": row.usd_label or "N/A",
            "inflation_pressure": row.inflation_pressure or 50,
            "inflation_label": row.inflation_label or "N/A",
            "recession_risk": row.recession_risk or 50,
            "recession_label": row.recession_label or "N/A",
            "fear_index": row.fear_index or 50,
            "fear_label": row.fear_label or "N/A",
            "regime": row.regime or "Unknown",
            "hawkish_pct": row.hawkish_pct or 0,
            "dovish_pct": row.dovish_pct or 0,
            "news_count": row.news_count or 0,
        }
    finally:
        db.close()

@st.cache_data(ttl=120)
def load_recent_news(limit: int = 20):
    db = get_session()
    try:
        rows = (
            db.query(News)
            .filter(News.published_at >= datetime.utcnow() - timedelta(days=3))
            .order_by(News.published_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "id": r.id,
            "title": r.title,
            "source": r.source,
            "published_at": r.published_at,
            "macro_tone": r.macro_tone or "neutral",
            "sentiment_label": r.sentiment_label or "neutral",
            "impact_level": r.impact_level or "low",
            "category": r.category or "General",
        } for r in rows]
    finally:
        db.close()

@st.cache_data(ttl=300)
def load_score_history(days: int = 30):
    db = get_session()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(MacroScore)
            .filter(MacroScore.timestamp >= cutoff)
            .order_by(MacroScore.timestamp.asc())
            .all()
        )
        return pd.DataFrame([{
            "timestamp": r.timestamp,
            "USD Strength": r.usd_strength,
            "Inflation Pressure": r.inflation_pressure,
            "Recession Risk": r.recession_risk,
            "Fear Index": r.fear_index,
        } for r in rows])
    finally:
        db.close()

@st.cache_data(ttl=120)
def load_alerts(limit: int = 10):
    db = get_session()
    try:
        rows = (
            db.query(Alert)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "level": r.level,
            "title": r.title,
            "message": r.message,
            "created_at": r.created_at,
        } for r in rows]
    finally:
        db.close()

@st.cache_data(ttl=300)
def load_scenarios(limit: int = 6):
    db = get_session()
    try:
        rows = (
            db.query(Scenario)
            .order_by(Scenario.generated_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "type": r.scenario_type,
            "title": r.title,
            "probability": r.probability,
            "narrative": r.narrative,
            "horizon_weeks": r.horizon_weeks,
            "generated_at": r.generated_at,
        } for r in rows]
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# DASHBOARD LAYOUT
# ──────────────────────────────────────────────────────────────
def render_dashboard():

    # ─── Header
    col_title, col_time = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="main-title">⚡ AI MACRO INTELLIGENCE SYSTEM</div>', unsafe_allow_html=True)
    with col_time:
        st.markdown(f"""
            <div style="text-align:right; font-family:'IBM Plex Mono'; font-size:0.75rem; color:#5a7a9e; margin-top:0.5rem;">
            {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
            </div>
        """, unsafe_allow_html=True)

    # ─── Load data
    scores = load_latest_scores()
    alerts = load_alerts()
    news = load_recent_news()
    history = load_score_history()
    scenarios = load_scenarios()

    # ─── ALERTES CRITIQUES (en haut si présentes)
    critical = [a for a in alerts if a["level"] == "critical"]
    if critical:
        for alert in critical[:2]:
            st.markdown(f"""
                <div class="alert-critical">
                    <strong>{alert['title']}</strong><br>
                    <span style="font-size:0.8rem; color:#ffcdd2;">{alert['message']}</span>
                </div>
            """, unsafe_allow_html=True)

    # ─── RÉGIME MACRO
    if scores:
        st.markdown(f"""
            <div style="text-align:center; margin-bottom:1rem;">
                <span class="regime-badge">🌍 RÉGIME: {scores['regime'].upper()}</span>
                <span style="font-family:'IBM Plex Mono'; font-size:0.7rem; color:#5a7a9e; margin-left:1rem;">
                    Basé sur {scores['news_count']} articles analysés
                </span>
            </div>
        """, unsafe_allow_html=True)

    # ─── GAUGES MACRO
    st.markdown("### Scores Macro Temps Réel")
    if scores:
        g1, g2, g3, g4 = st.columns(4)

        with g1:
            st.plotly_chart(
                gauge_chart(scores["usd_strength"], "💵 USD STRENGTH", score_color(scores["usd_strength"])),
                use_container_width=True, key="gauge_usd"
            )
            col_v = score_color(scores['usd_strength'])
            st.markdown(f"<div style='text-align:center; font-size:0.8rem; color:{col_v};'>{scores['usd_label']}</div>", unsafe_allow_html=True)

        with g2:
            st.plotly_chart(
                gauge_chart(scores["inflation_pressure"], "🔥 INFLATION", score_color(scores["inflation_pressure"])),
                use_container_width=True, key="gauge_inf"
            )
            col_v = score_color(scores['inflation_pressure'])
            st.markdown(f"<div style='text-align:center; font-size:0.8rem; color:{col_v};'>{scores['inflation_label']}</div>", unsafe_allow_html=True)

        with g3:
            st.plotly_chart(
                gauge_chart(scores["recession_risk"], "📉 RECESSION RISK", score_color(scores["recession_risk"])),
                use_container_width=True, key="gauge_rec"
            )
            col_v = score_color(scores['recession_risk'])
            st.markdown(f"<div style='text-align:center; font-size:0.8rem; color:{col_v};'>{scores['recession_label']}</div>", unsafe_allow_html=True)

        with g4:
            st.plotly_chart(
                gauge_chart(scores["fear_index"], "😱 FEAR INDEX", score_color(scores["fear_index"])),
                use_container_width=True, key="gauge_fear"
            )
            col_v = score_color(scores['fear_index'])
            st.markdown(f"<div style='text-align:center; font-size:0.8rem; color:{col_v};'>{scores['fear_label']}</div>", unsafe_allow_html=True)

    else:
        st.info("⚠️ Aucun score disponible. Lance `python main.py --run` pour initialiser.")

    st.divider()

    # ─── LIGNE 2 : Sentiment Tone + Chart historique
    col_tone, col_chart = st.columns([1, 2])

    with col_tone:
        st.markdown("#### 🎯 Distribution des Tons")
        if scores:
            hawkish = scores.get("hawkish_pct", 0)
            dovish  = scores.get("dovish_pct", 0)
            neutral = max(0, 100 - hawkish - dovish)

            fig_tone = go.Figure(go.Bar(
                x=["Hawkish", "Dovish", "Neutral"],
                y=[hawkish, dovish, neutral],
                marker_color=["#ef5350", "#26c6da", "#5a7a9e"],
                text=[f"{v:.0f}%" for v in [hawkish, dovish, neutral]],
                textposition="auto",
            ))
            fig_tone.update_layout(
                height=250,
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a",
                font={"color": "#e0e6f0", "family": "IBM Plex Mono"},
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                yaxis=dict(gridcolor="#1e2d4a"),
                xaxis=dict(gridcolor="#1e2d4a"),
            )
            st.plotly_chart(fig_tone, use_container_width=True, key="tone_bar")

    with col_chart:
        st.markdown("#### 📈 Évolution des Scores (30j)")
        if not history.empty:
            fig_hist = go.Figure()
            colors = {
                "USD Strength": "#4fc3f7",
                "Inflation Pressure": "#ef5350",
                "Recession Risk": "#ffa726",
                "Fear Index": "#ab47bc",
            }
            for col, color in colors.items():
                if col in history.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=history["timestamp"],
                        y=history[col],
                        name=col,
                        line=dict(color=color, width=1.5),
                        mode="lines",
                    ))
            fig_hist.update_layout(
                height=250,
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a",
                font={"color": "#e0e6f0", "family": "IBM Plex Mono", "size": 10},
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=-0.3, font={"size": 9}),
                yaxis=dict(range=[0, 100], gridcolor="#1e2d4a"),
                xaxis=dict(gridcolor="#1e2d4a"),
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="hist_chart")
        else:
            st.info("Historique disponible après plusieurs cycles de collecte.")

    st.divider()

    # ─── LIGNE 3 : News + Scénarios
    col_news, col_scenarios = st.columns([3, 2])

    with col_news:
        st.markdown("#### 📰 News Macro Live")
        if news:
            for article in news[:15]:
                tone = article["macro_tone"]
                tone_cls = f"tone-{tone.replace('-', '')}" if tone else "tone-neutral"
                impact_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(article["impact_level"], "⚪")
                published = article["published_at"]
                time_str = published.strftime("%H:%M") if published else "?"

                st.markdown(f"""
                    <div class="news-item {tone_cls}">
                        <div class="news-title">{impact_emoji} {article['title'][:100]}</div>
                        <div class="news-meta">
                            {article['source']} · {time_str} · 
                            <span style="color:{tone_color(tone)};">{tone}</span> · 
                            {article['category']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune news disponible. Lance `python main.py --collect`")

    with col_scenarios:
        st.markdown("#### 🎯 Scénarios Probabilistes IA")
        if scenarios:
            type_colors = {
                "base": "#4fc3f7",
                "bull": "#66bb6a",
                "bear": "#ef5350",
                "tail_risk": "#ab47bc",
            }
            for s in scenarios[:4]:
                color = type_colors.get(s["type"], "#7a9bbf")
                prob_pct = f"{s['probability']*100:.0f}%" if s["probability"] else "?"
                st.markdown(f"""
                    <div class="scenario-card" style="border-color:{color}20;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                            <span style="font-family:'IBM Plex Mono'; font-size:0.7rem; color:{color}; text-transform:uppercase;">
                                {s['type']}
                            </span>
                            <span style="font-family:'IBM Plex Mono'; font-size:1.1rem; font-weight:600; color:{color};">
                                {prob_pct}
                            </span>
                        </div>
                        <div style="font-size:0.82rem; font-weight:600; color:#ccd6f6; margin-bottom:0.3rem;">
                            {s['title']}
                        </div>
                        <div style="font-size:0.75rem; color:#7a9bbf; line-height:1.4;">
                            {s['narrative'][:180]}...
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucun scénario disponible. Lance `python main.py --scenarios`")

    # ─── ALERTES (bas de page)
    if alerts:
        st.divider()
        st.markdown("#### 🚨 Alertes Récentes")
        for alert in alerts[:5]:
            cls = f"alert-{alert['level']}"
            st.markdown(f"""
                <div class="{cls}">
                    <strong style="font-size:0.85rem;">{alert['title']}</strong><br>
                    <span style="font-size:0.75rem; opacity:0.8;">{alert['message']}</span>
                </div>
            """, unsafe_allow_html=True)

    # ─── Auto-refresh
    st.markdown(f"""
        <div style="text-align:center; margin-top:2rem; font-family:'IBM Plex Mono'; font-size:0.65rem; color:#2e4a6a;">
        Auto-refresh: {DASHBOARD['refresh_interval_seconds']}s · AI Macro Intelligence System
        </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    render_dashboard()
