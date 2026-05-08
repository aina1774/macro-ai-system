@echo off
set FRED_API_KEY=ab0c0640542228f570891b3496b05685
set NEWSAPI_KEY=03f421cb28f94eecb66a8b5e369dca81
set FINNHUB_KEY=d7v2r9hr01qp7l70qncgd7v2r9hr01qp7l70qnd0
set ALPHAVANTAGE_KEY=5DXCH7PZS9XJ2BZY
set PYTHONUTF8=1
echo Collecte des donnees...
py main.py --collect
echo Analyse du sentiment...
py main.py --analyze
echo Calcul des scores...
py main.py --scores
echo Lancement du dashboard...
py -m streamlit run app/dashboard/dashboard.py
