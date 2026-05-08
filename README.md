# ⚡ AI Macro Intelligence System

Système d'analyse macroéconomique institutionnel alimenté par l'IA.
Collecte les news économiques, analyse le sentiment, calcule des scores macro et génère des scénarios probabilistes.

---

## 🚀 Démarrage Rapide (15 minutes)

### 1. Installation

```bash
git clone <ton-repo>
cd macro_ai_system
pip install -r requirements.txt
```

### 2. Configuration des clés API

```bash
cp .env.example .env
# Édite .env avec tes vraies clés API
```

**APIs nécessaires (toutes gratuites) :**
| API | Lien | Limite gratuite |
|-----|------|-----------------|
| FRED | https://fred.stlouisfed.org/docs/api/fred/ | Illimitée |
| NewsAPI | https://newsapi.org | 500 req/jour |
| Finnhub | https://finnhub.io | 60 req/min |
| Anthropic | https://console.anthropic.com | Pay-as-you-go |

### 3. Initialisation

```bash
python main.py --init
```

### 4. Premier Pipeline Complet

```bash
python main.py --run
```

### 5. Dashboard

```bash
streamlit run app/dashboard/dashboard.py
```

Ouvre http://localhost:8501 dans ton navigateur.

---

## 📁 Structure du Projet

```
macro_ai_system/
│
├── main.py                          # Orchestrateur principal
├── requirements.txt
├── .env.example                     # Template variables d'env
│
├── config/
│   └── settings.py                  # ⚙️ Configuration centrale
│
├── database/
│   └── models/
│       └── models.py                # Schéma SQLite/PostgreSQL
│
├── api_clients/
│   ├── fred/
│   │   └── fred_client.py           # Client FRED (données éco)
│   ├── newsapi/
│   │   └── newsapi_client.py        # Client NewsAPI (headlines)
│   ├── finnhub/                     # Client Finnhub (marchés)
│   └── alphavantage/                # Client Alpha Vantage
│
├── ai/
│   ├── sentiment/
│   │   └── sentiment_analyzer.py    # FinBERT + règles hawkish/dovish
│   ├── macro_reasoning/
│   │   └── macro_engine.py          # Claude API — raisonnement macro
│   ├── embeddings/                  # Phase 4 — RAG
│   ├── memory/                      # Phase 4 — mémoire vectorielle
│   └── scenarios/                   # Générateur de scénarios
│
├── engines/
│   ├── sentiment_engine/
│   │   └── macro_score_engine.py    # Calcul scores USD/Inflation/etc.
│   ├── correlation_engine/          # Phase 3 — corrélations marchés
│   ├── probability_engine/          # Phase 3 — probabilités
│   └── anomaly_engine/              # Phase 4 — détection anomalies
│
├── app/
│   └── dashboard/
│       └── dashboard.py             # Dashboard Streamlit
│
├── data/
│   ├── raw/                         # Données brutes
│   ├── processed/                   # Données nettoyées
│   └── historical/                  # Archives historiques
│
└── logs/
    └── macro_ai.log                 # Logs du système
```

---

## 🔧 Commandes Disponibles

```bash
# Initialiser la base de données
python main.py --init

# Collecter les données (FRED + NewsAPI)
python main.py --collect

# Analyser le sentiment NLP (FinBERT)
python main.py --analyze

# Calculer les scores macro
python main.py --scores

# Générer les scénarios IA (Claude)
python main.py --scenarios

# Pipeline complet (toutes les étapes)
python main.py --run

# Boucle automatique production (toutes les 60 min)
python main.py --scheduler

# Lancer le dashboard
python main.py --dashboard
# ou directement :
streamlit run app/dashboard/dashboard.py
```

---

## 📊 Scores Macro Calculés

| Score | Formule | Interprétation |
|-------|---------|----------------|
| **USD Strength** | Sentiment hawkish + Yield spread + CPI | >70 = Bullish USD |
| **Inflation Pressure** | CPI + Oil + News hawkish | >70 = High inflation |
| **Recession Risk** | Yield curve + Unemployment + Tone dovish | >65 = Risk élevé |
| **Fear Index** | VIX + News négatif + Risk-off | >70 = Fear |

---

## 🤖 Architecture IA

```
News Articles
     │
     ▼
FinBERT (NLP)
├── Sentiment: positive / negative / neutral
├── Tone: hawkish / dovish / risk-on / risk-off
└── Impact: low / medium / high / critical
     │
     ▼
Macro Score Engine
├── USD Strength Score
├── Inflation Pressure Score
├── Recession Risk Score
└── Fear Index Score
     │
     ▼
Claude API (Raisonnement)
├── Analyse narrative institutionnelle
├── Scénarios probabilistes (base/bull/bear)
└── Détection changements de régime
     │
     ▼
Dashboard Streamlit
```

---

## 🗺️ Roadmap

- [x] **Phase 1** — Data Pipeline (FRED + NewsAPI + SQLite)
- [x] **Phase 2** — NLP Sentiment (FinBERT + Hawkish/Dovish)
- [x] **Phase 3** — Scores Macro + Scénarios IA (Claude)
- [ ] **Phase 4** — Corrélations marchés avancées
- [ ] **Phase 5** — RAG + Mémoire vectorielle (ChromaDB)
- [ ] **Phase 6** — Multi-agent + Analyse discours banques centrales

---

## ⚠️ Limitations

- Le système est un **outil d'analyse uniquement** — pas de trading automatique
- La qualité des scores dépend du volume de news collectées
- FinBERT nécessite ~2GB RAM et 30s de chargement initial
- NewsAPI gratuit : 500 req/jour max

---

## 📝 Coûts Estimés (Claude API)

- Analyse macro narrative : ~$0.003 par génération
- Scénarios probabilistes : ~$0.005 par génération
- Budget estimé : **$5-15/mois** pour usage quotidien normal
