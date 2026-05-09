"""
============================================================
RaAina Macro Eco — Système d'Authentification
============================================================
"""

import csv
import os
import streamlit as st
from datetime import datetime

KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "keys.csv")

def verify_key(nom: str, cle: str) -> dict:
    """
    Vérifie si un nom + clé est valide.
    Retourne : {"valid": bool, "message": str, "nom": str}
    """
    if not nom or not cle:
        return {"valid": False, "message": "Nom et clé requis."}

    if not os.path.exists(KEYS_FILE):
        return {"valid": False, "message": "Base de clés introuvable."}

    now = datetime.now().date()

    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["cle"].strip() == cle.strip():
                if row["nom"].strip().lower() != nom.strip().lower():
                    return {"valid": False, "message": "Nom incorrect pour cette clé."}
                if row["actif"].strip().lower() != "true":
                    return {"valid": False, "message": "Cette clé a été révoquée."}
                exp = datetime.strptime(row["expiration"].strip(), "%Y-%m-%d").date()
                if exp < now:
                    days_ago = (now - exp).days
                    return {"valid": False, "message": f"Clé expirée depuis {days_ago} jour(s). Contactez RaAina."}
                days_left = (exp - now).days
                return {"valid": True, "message": f"Accès autorisé — expire dans {days_left} jour(s).", "nom": row["nom"]}

    return {"valid": False, "message": "Clé invalide. Contactez RaAina pour obtenir un accès."}


def show_login_page():
    """Affiche la page de connexion."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap');
        html, body, [class*="css"] { background-color: #000000; color: #e8d5a3; font-family: 'Rajdhani', sans-serif; }
        .stApp { background-color: #000000; }

        .login-title {
            font-family: 'Orbitron', monospace;
            font-size: 2rem;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(180deg, #fff7d6 0%, #ffd700 30%, #c8960c 60%, #8b6914 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 20px rgba(255,215,0,0.6));
            letter-spacing: 0.15em;
            margin-bottom: 0.2rem;
        }
        .login-sub {
            font-family: 'Orbitron', monospace;
            font-size: 0.65rem;
            text-align: center;
            background: linear-gradient(90deg, #8b6914, #ffd700, #8b6914);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 0.3em;
            margin-bottom: 2rem;
        }
        .login-box {
            background: linear-gradient(135deg, #0a0800, #1a1400);
            border: 1px solid #c8960c;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 0 30px rgba(200,150,12,0.2);
        }
        .gold-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #ffd700, #c8960c, #ffd700, transparent);
            margin: 1.5rem 0;
        }
        div[data-testid="stTextInput"] label {
            font-family: 'Orbitron', monospace !important;
            font-size: 0.7rem !important;
            color: #8b6914 !important;
            letter-spacing: 0.1em !important;
        }
        div[data-testid="stTextInput"] input {
            background-color: #0d0a00 !important;
            border: 1px solid #3d2e00 !important;
            color: #ffd700 !important;
            font-family: 'Orbitron', monospace !important;
            font-size: 0.85rem !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #ffd700 !important;
            box-shadow: 0 0 8px rgba(255,215,0,0.3) !important;
        }
        .stButton > button {
            background: linear-gradient(135deg, #8b6914, #c8960c, #ffd700) !important;
            color: #000000 !important;
            font-family: 'Orbitron', monospace !important;
            font-weight: 700 !important;
            font-size: 0.8rem !important;
            letter-spacing: 0.15em !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.6rem 2rem !important;
            width: 100% !important;
            margin-top: 1rem !important;
        }
        .stButton > button:hover {
            box-shadow: 0 0 15px rgba(255,215,0,0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Centrer le formulaire
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">⚡ RaAina Macro Eco ⚡</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">◆ Accès Restreint ◆ Directed by RaAina ◆</div>', unsafe_allow_html=True)
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="login-box">', unsafe_allow_html=True)

        st.markdown('<p style="font-family:Orbitron;font-size:0.65rem;color:#5a4a1a;text-align:center;letter-spacing:0.1em;margin-bottom:1.5rem;">ENTREZ VOS IDENTIFIANTS POUR ACCÉDER AU DASHBOARD</p>', unsafe_allow_html=True)

        nom = st.text_input("👤 NOM D'UTILISATEUR", placeholder="Votre nom")
        cle = st.text_input("🔑 CLÉ D'ACCÈS", placeholder="RAAINA-XXXX-XXXX-XXXX", type="password")

        if st.button("⚡ ACCÉDER AU DASHBOARD"):
            if nom and cle:
                result = verify_key(nom, cle)
                if result["valid"]:
                    st.session_state["authenticated"] = True
                    st.session_state["user_nom"] = result["nom"]
                    st.session_state["auth_message"] = result["message"]
                    st.rerun()
                else:
                    st.markdown(f'<div style="background:#1a0500;border-left:3px solid #ef5350;padding:0.8rem;border-radius:4px;margin-top:1rem;font-family:Orbitron;font-size:0.7rem;color:#ef5350;">❌ {result["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:#1a0e00;border-left:3px solid #ffa726;padding:0.8rem;border-radius:4px;margin-top:1rem;font-family:Orbitron;font-size:0.7rem;color:#ffa726;">⚠️ Remplissez tous les champs.</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family:Orbitron;font-size:0.55rem;color:#3d2e00;text-align:center;margin-top:1.5rem;letter-spacing:0.15em;">Pas de clé ? Contactez RaAina pour obtenir un accès.</p>', unsafe_allow_html=True)


def require_auth():
    """
    Appeler en haut du dashboard.
    Retourne True si authentifié, sinon affiche la page de login.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        show_login_page()
        st.stop()
        return False

    return True
