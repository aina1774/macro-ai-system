"""
============================================================
RaAina Macro Eco — Dashboard Premium
============================================================
Directed by RaAina
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import DASHBOARD
from database.models.models import get_session, News, MacroScore, Alert, Scenario, FredData
from app.auth import require_auth

st.set_page_config(
    page_title="RaAina Macro Eco",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
        background-color: #000000;
        color: #e8d5a3;
    }
    .stApp { background-color: #000000; }

    .main-title {
        font-family: 'Orbitron', monospace;
        font-size: 2.2rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #fff7d6 0%, #ffd700 30%, #c8960c 60%, #8b6914 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 20px rgba(255,215,0,0.6));
        letter-spacing: 0.15em;
        margin-bottom: 0.2rem;
        padding-top: 1rem;
    }

    .sub-title {
        font-family: 'Orbitron', monospace;
        font-size: 0.75rem;
        text-align: center;
        background: linear-gradient(90deg, #8b6914, #ffd700, #8b6914);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.3em;
        margin-bottom: 2rem;
    }

    .gold-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #ffd700, #c8960c, #ffd700, transparent);
        margin: 1.5rem 0;
        box-shadow: 0 0 8px rgba(255,215,0,0.4);
    }

    .section-header {
        font-family: 'Orbitron', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        color: #ffd700;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        border-left: 3px solid #ffd700;
        padding-left: 0.8rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(255,215,0,0.5);
    }

    .forex-card {
        background: linear-gradient(135deg, #0a0800, #150f00);
        border: 1px solid #3d2e00;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .forex-symbol { font-family: 'Orbitron', monospace; font-size: 0.65rem; color: #8b6914; letter-spacing: 0.1em; }
    .forex-price  { font-family: 'Orbitron', monospace; font-size: 1.05rem; font-weight: 700; color: #ffd700; }
    .chg-pos { color: #00e676; font-size: 0.75rem; font-family: 'Orbitron', monospace; }
    .chg-neg { color: #ff5252; font-size: 0.75rem; font-family: 'Orbitron', monospace; }

    .news-item {
        background: linear-gradient(135deg, #080600, #120e00);
        border-left: 3px solid #3d2e00;
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .news-title { font-size: 0.85rem; font-weight: 600; color: #e8d5a3; margin-bottom: 0.2rem; }
    .news-meta  { font-family: 'Orbitron', monospace; font-size: 0.6rem; color: #5a4a1a; }

    .tone-hawkish  { border-left-color: #ef5350 !important; }
    .tone-dovish   { border-left-color: #26c6da !important; }
    .tone-riskoff  { border-left-color: #ffa726 !important; }
    .tone-riskon   { border-left-color: #66bb6a !important; }

    .regime-badge {
        background: linear-gradient(135deg, #1a1200, #2a1e00);
        border: 1px solid #c8960c;
        border-radius: 20px;
        padding: 0.4rem 1.5rem;
        font-family: 'Orbitron', monospace;
        font-size: 0.7rem;
        color: #ffd700;
        display: inline-block;
        box-shadow: 0 0 12px rgba(200,150,12,0.3);
    }

    .alert-critical { border-left: 4px solid #ef5350; background: #1a0500; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }
    .alert-warning  { border-left: 4px solid #ffa726; background: #1a0e00; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }
    .alert-info     { border-left: 4px solid #ffd700; background: #0d0a00; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #c8960c; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


def score_color(score):
    if score >= 70: return "#ef5350"
    elif score >= 55: return "#ffa726"
    elif score <= 30: return "#26c6da"
    elif score <= 45: return "#66bb6a"
    return "#ffd700"

def tone_color(tone):
    return {"hawkish": "#ef5350", "slightly-hawkish": "#ff7043",
            "dovish": "#26c6da", "slightly-dovish": "#4dd0e1",
            "risk-off": "#ffa726", "risk-on": "#66bb6a"}.get(tone, "#8b6914")

def gauge_chart(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        domain={"x": [0,1], "y": [0,1]},
        title={"text": title, "font": {"size": 11, "color": "#8b6914", "family": "Orbitron"}},
        number={"font": {"size": 28, "color": color, "family": "Orbitron"}},
        gauge={
            "axis": {"range": [0,100], "tickcolor": "#3d2e00", "tickfont": {"size": 8}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#080600", "bordercolor": "#3d2e00",
            "steps": [{"range":[0,33],"color":"#050300"},{"range":[33,66],"color":"#080600"},{"range":[66,100],"color":"#0d0a00"}],
            "threshold": {"line": {"color": "#ffd700","width": 2}, "thickness": 0.8, "value": 50},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20,r=20,t=40,b=10),
                      paper_bgcolor="#000000", plot_bgcolor="#000000",
                      font={"color": "#e8d5a3"})
    return fig


@st.cache_data(ttl=60)
def load_forex():
    symbols = {"DXY": "DX-Y.NYB", "EUR/USD": "EURUSD=X", "NASDAQ": "^IXIC", "XAU/USD": "GC=F", "BTC/USD": "BTC-USD"}
    results = {}
    try:
        import yfinance as yf
        for label, ticker in symbols.items():
            try:
                data = yf.Ticker(ticker).history(period="2d", interval="1d")
                if len(data) >= 2:
                    price = data["Close"].iloc[-1]
                    chg = ((price - data["Close"].iloc[-2]) / data["Close"].iloc[-2]) * 100
                    results[label] = {"price": price, "change": chg}
                else:
                    results[label] = {"price": 0, "change": 0}
            except Exception:
                results[label] = {"price": 0, "change": 0}
    except ImportError:
        for label in symbols:
            results[label] = {"price": 0, "change": 0}
    return results


@st.cache_data(ttl=60)
def candle_data(symbol_label):
    ticker_map = {"DXY":"DX-Y.NYB","EUR/USD":"EURUSD=X","NASDAQ":"^IXIC","XAU/USD":"GC=F","BTC/USD":"BTC-USD"}
    try:
        import yfinance as yf
        data = yf.Ticker(ticker_map.get(symbol_label,"EURUSD=X")).history(period="30d", interval="1d")
        return data if not data.empty else None
    except Exception:
        return None


@st.cache_data(ttl=DASHBOARD["refresh_interval_seconds"])
def load_scores():
    db = get_session()
    try:
        row = db.query(MacroScore).order_by(MacroScore.timestamp.desc()).first()
        if not row: return None
        return {"timestamp": row.timestamp,
                "usd_strength": row.usd_strength or 50, "usd_label": row.usd_label or "N/A",
                "inflation_pressure": row.inflation_pressure or 50, "inflation_label": row.inflation_label or "N/A",
                "recession_risk": row.recession_risk or 50, "recession_label": row.recession_label or "N/A",
                "fear_index": row.fear_index or 50, "fear_label": row.fear_label or "N/A",
                "regime": row.regime or "Unknown", "hawkish_pct": row.hawkish_pct or 0,
                "dovish_pct": row.dovish_pct or 0, "news_count": row.news_count or 0}
    finally:
        db.close()

@st.cache_data(ttl=120)
def load_news(limit=20):
    db = get_session()
    try:
        rows = db.query(News).filter(News.published_at >= datetime.utcnow()-timedelta(days=3)).order_by(News.published_at.desc()).limit(limit).all()
        return [{"title":r.title,"source":r.source,"published_at":r.published_at,
                 "macro_tone":r.macro_tone or "neutral","sentiment_label":r.sentiment_label or "neutral",
                 "impact_level":r.impact_level or "low","category":r.category or "General"} for r in rows]
    finally:
        db.close()

@st.cache_data(ttl=300)
def load_history(days=30):
    db = get_session()
    try:
        cutoff = datetime.utcnow()-timedelta(days=days)
        rows = db.query(MacroScore).filter(MacroScore.timestamp>=cutoff).order_by(MacroScore.timestamp.asc()).all()
        return pd.DataFrame([{"timestamp":r.timestamp,"USD Strength":r.usd_strength,
                               "Inflation Pressure":r.inflation_pressure,"Recession Risk":r.recession_risk,
                               "Fear Index":r.fear_index} for r in rows])
    finally:
        db.close()

@st.cache_data(ttl=120)
def load_alerts(limit=10):
    db = get_session()
    try:
        rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
        return [{"level":r.level,"title":r.title,"message":r.message} for r in rows]
    finally:
        db.close()


def render_dashboard():
    # ── AUTH ──
    require_auth()
    nom = st.session_state.get("user_nom", "Utilisateur")

    # ── HEADER ──
    st.markdown('<div class="main-title">⚡ RaAina Macro Eco ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">◆ Directed by RaAina ◆ Institutional AI Analysis ◆</div>', unsafe_allow_html=True)
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:right;font-family:Orbitron;font-size:0.6rem;color:#5a4a1a;margin-top:-1rem;margin-bottom:1rem;">🕐 {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC &nbsp;|&nbsp; 👤 {nom} &nbsp;|&nbsp; {st.session_state.get("auth_message","")}</div>', unsafe_allow_html=True)

    scores  = load_scores()
    alerts  = load_alerts()
    news    = load_news()
    history = load_history()
    forex   = load_forex()

    # ── ALERTES ──
    for a in [x for x in alerts if x["level"]=="critical"][:2]:
        st.markdown(f'<div class="alert-critical"><strong>{a["title"]}</strong><br><span style="font-size:0.8rem;color:#ffcdd2;">{a["message"]}</span></div>', unsafe_allow_html=True)

    # ── REGIME ──
    if scores:
        st.markdown(f'<div style="text-align:center;margin-bottom:1.5rem;"><span class="regime-badge">👑 RÉGIME : {scores["regime"].upper()}</span><span style="font-family:Orbitron;font-size:0.6rem;color:#5a4a1a;margin-left:1rem;">{scores["news_count"]} articles analysés</span></div>', unsafe_allow_html=True)

    # ── SCORES MACRO ──
    st.markdown('<div class="section-header">◆ Scores Macro Temps Réel</div>', unsafe_allow_html=True)
    if scores:
        g1,g2,g3,g4 = st.columns(4)
        gauges = [(g1,"usd_strength","💵 USD STRENGTH","usd_label"),(g2,"inflation_pressure","🔥 INFLATION","inflation_label"),(g3,"recession_risk","📉 RECESSION RISK","recession_label"),(g4,"fear_index","😱 FEAR INDEX","fear_label")]
        for col,key,title,lbl in gauges:
            with col:
                c = score_color(scores[key])
                st.plotly_chart(gauge_chart(scores[key],title,c), use_container_width=True, key=f"g_{key}")
                st.markdown(f"<div style='text-align:center;font-size:0.75rem;color:{c};font-family:Orbitron;'>{scores[lbl]}</div>", unsafe_allow_html=True)
    else:
        st.info("Aucun score. Lancez `python main.py --run`")

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ── FOREX LIVE ──
    st.markdown('<div class="section-header">◆ Marchés Live</div>', unsafe_allow_html=True)
    fc = st.columns(5)
    for i,(label,data) in enumerate(forex.items()):
        with fc[i]:
            p = data["price"]
            ch = data["change"]
            cls = "chg-pos" if ch >= 0 else "chg-neg"
            arr = "▲" if ch >= 0 else "▼"
            st.markdown(f'<div class="forex-card"><div class="forex-symbol">{label}</div><div class="forex-price">{f"{p:,.2f}" if p else "N/A"}</div><div class="{cls}">{arr} {abs(ch):.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ── BOUGIES JAPONAISES ──
    st.markdown('<div class="section-header">◆ Graphiques en Bougies Japonaises</div>', unsafe_allow_html=True)
    pairs = list(forex.keys())
    row1 = st.columns(3)
    row2 = st.columns(2)
    all_cols = row1 + row2
    for i,pair in enumerate(pairs):
        with all_cols[i]:
            data = candle_data(pair)
            if data is not None:
                fig = go.Figure(go.Candlestick(
                    x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
                    increasing_line_color="#ffd700", decreasing_line_color="#ef5350",
                    increasing_fillcolor="#c8960c", decreasing_fillcolor="#8b0000", name=pair,
                ))
                fig.update_layout(height=280, paper_bgcolor="#000000", plot_bgcolor="#080600",
                    font={"color":"#e8d5a3","family":"Orbitron","size":9},
                    margin=dict(l=10,r=10,t=30,b=10),
                    title=dict(text=pair,font=dict(color="#ffd700",size=11,family="Orbitron")),
                    xaxis=dict(gridcolor="#1a1200",rangeslider=dict(visible=False),color="#5a4a1a"),
                    yaxis=dict(gridcolor="#1a1200",color="#5a4a1a"), showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"candle_{pair}")
            else:
                st.markdown(f'<div class="forex-card"><div class="forex-symbol">{pair}</div><div style="color:#5a4a1a;font-size:0.7rem;margin-top:0.5rem;">Installez yfinance<br>pip install yfinance</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ── HISTORIQUE + SENTIMENT ──
    col_hist, col_tone = st.columns([2,1])
    with col_hist:
        st.markdown('<div class="section-header">◆ Historique des Scores (30j)</div>', unsafe_allow_html=True)
        if not history.empty:
            fig_h = go.Figure()
            for col_name,color in [("USD Strength","#ffd700"),("Inflation Pressure","#ef5350"),("Recession Risk","#ffa726"),("Fear Index","#ab47bc")]:
                if col_name in history.columns:
                    fig_h.add_trace(go.Scatter(x=history["timestamp"],y=history[col_name],name=col_name,line=dict(color=color,width=2),mode="lines+markers",marker=dict(size=4)))
            fig_h.update_layout(height=280,paper_bgcolor="#000000",plot_bgcolor="#080600",
                font={"color":"#e8d5a3","family":"Orbitron","size":9},margin=dict(l=10,r=10,t=10,b=10),
                legend=dict(orientation="h",y=-0.25,font={"size":8},bgcolor="rgba(0,0,0,0)"),
                yaxis=dict(range=[0,100],gridcolor="#1a1200",color="#5a4a1a"),
                xaxis=dict(gridcolor="#1a1200",color="#5a4a1a"))
            st.plotly_chart(fig_h, use_container_width=True, key="hist")
        else:
            st.info("Disponible après plusieurs cycles.")

    with col_tone:
        st.markdown('<div class="section-header">◆ Sentiment</div>', unsafe_allow_html=True)
        if scores:
            h = scores.get("hawkish_pct",0)
            d = scores.get("dovish_pct",0)
            n = max(0,100-h-d)
            fig_t = go.Figure(go.Bar(x=["Hawkish","Dovish","Neutral"],y=[h,d,n],
                marker_color=["#ef5350","#26c6da","#ffd700"],
                text=[f"{v:.0f}%" for v in [h,d,n]],textposition="auto",
                textfont=dict(family="Orbitron",size=9)))
            fig_t.update_layout(height=280,paper_bgcolor="#000000",plot_bgcolor="#080600",
                font={"color":"#e8d5a3","family":"Orbitron","size":9},
                margin=dict(l=10,r=10,t=10,b=10),showlegend=False,
                yaxis=dict(gridcolor="#1a1200",color="#5a4a1a"),
                xaxis=dict(gridcolor="#1a1200",color="#5a4a1a"))
            st.plotly_chart(fig_t, use_container_width=True, key="tone")

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ── CORRELATIONS ──
    st.markdown('<div class="section-header">◆ Corrélations des Scores</div>', unsafe_allow_html=True)
    if not history.empty and len(history) > 2:
        cols = [c for c in ["USD Strength","Inflation Pressure","Recession Risk","Fear Index"] if c in history.columns]
        corr = history[cols].corr()
        fig_c = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale=[[0,"#000000"],[0.5,"#8b6914"],[1,"#ffd700"]],
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate="%{text}", textfont=dict(family="Orbitron",size=10,color="#000000"),showscale=True))
        fig_c.update_layout(height=280,paper_bgcolor="#000000",plot_bgcolor="#000000",
            font={"color":"#e8d5a3","family":"Orbitron","size":9},margin=dict(l=10,r=10,t=10,b=10),
            xaxis=dict(color="#5a4a1a"),yaxis=dict(color="#5a4a1a"))
        st.plotly_chart(fig_c, use_container_width=True, key="corr")
    else:
        st.info("Disponible après plusieurs cycles de collecte.")

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ── NEWS ──
    st.markdown('<div class="section-header">◆ News Macro Live — Sentiment IA</div>', unsafe_allow_html=True)
    if news:
        for article in news[:15]:
            tone = article["macro_tone"]
            tone_cls = f"tone-{tone.replace('-','')}"
            impact_emoji = {"critical":"🔴","high":"🟠","medium":"🟡","low":"⚪"}.get(article["impact_level"],"⚪")
            pub = article["published_at"]
            time_str = pub.strftime("%d/%m %H:%M") if pub else "?"
            sc = tone_color(tone)
            st.markdown(f'<div class="news-item {tone_cls}"><div class="news-title">{impact_emoji} {article["title"][:110]}</div><div class="news-meta">{article["source"]} · {time_str} · <span style="color:{sc};font-weight:700;">{tone.upper()}</span> · {article["sentiment_label"]}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Aucune news. Lancez `python main.py --collect`")

    # ── FOOTER ──
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:1rem 0;font-family:Orbitron;font-size:0.6rem;color:#3d2e00;letter-spacing:0.2em;">◆ RaAina Macro Eco ◆ Directed by RaAina ◆ AI-Powered Institutional Analysis ◆</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    render_dashboard()
