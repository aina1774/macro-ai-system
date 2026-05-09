"""
============================================================
API CLIENT — FRED (Federal Reserve Economic Data)
============================================================
Récupère les séries économiques officielles de la Fed.
API gratuite : https://fred.stlouisfed.org/docs/api/fred/
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import API_KEYS, FRED_SERIES
from database.models.models import get_session, FredData

BASE_URL = "https://api.stlouisfed.org/fred"


class FREDClient:

    def __init__(self):
        self.api_key = API_KEYS["fred"]
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict) -> dict:
        params["api_key"] = self.api_key
        params["file_type"] = "json"
        r = self.session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def fetch_series(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Récupère les observations d'une série FRED.

        Args:
            series_id: Ex: "CPIAUCSL", "FEDFUNDS", "GDP"
            observation_start: "YYYY-MM-DD" (défaut: 2 ans)
            observation_end: "YYYY-MM-DD" (défaut: aujourd'hui)
            limit: Nombre max d'observations

        Returns:
            DataFrame avec colonnes [date, value, series_id]
        """
        if not observation_start:
            observation_start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        if not observation_end:
            observation_end = datetime.now().strftime("%Y-%m-%d")

        data = self._get("series/observations", {
            "series_id": series_id,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "limit": limit,
            "sort_order": "desc",
        })

        observations = data.get("observations", [])
        if not observations:
            return pd.DataFrame()

        df = pd.DataFrame(observations)
        df = df[df["value"] != "."]   # FRED utilise "." pour les valeurs manquantes
        df["value"] = pd.to_numeric(df["value"])
        df["date"] = pd.to_datetime(df["date"])
        df["series_id"] = series_id
        df["series_name"] = FRED_SERIES.get(series_id, series_id)

        return df[["date", "value", "series_id", "series_name"]].reset_index(drop=True)

    def fetch_series_info(self, series_id: str) -> dict:
        """Métadonnées d'une série (units, frequency, title)."""
        data = self._get("series", {"series_id": series_id})
        series = data.get("seriess", [{}])[0]
        return {
            "id": series.get("id"),
            "title": series.get("title"),
            "units": series.get("units_short"),
            "frequency": series.get("frequency_short"),
            "last_updated": series.get("last_updated"),
        }

    def fetch_all_series(self, lookback_days: int = 365) -> dict[str, pd.DataFrame]:
        """
        Récupère toutes les séries définies dans settings.FRED_SERIES.
        Retourne un dict {series_id: DataFrame}.
        """
        start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        results = {}

        for series_id, name in FRED_SERIES.items():
            try:
                df = self.fetch_series(series_id, observation_start=start)
                if not df.empty:
                    results[series_id] = df
                    print(f"  ✅ {series_id} ({name}): {len(df)} observations")
                else:
                    print(f"  ⚠️  {series_id}: aucune donnée")
            except Exception as e:
                print(f"  ❌ {series_id}: erreur — {e}")

        return results

    def save_to_db(self, series_id: str, df: pd.DataFrame):
        """Sauvegarde les observations en base de données."""
        if df.empty:
            return 0

        db = get_session()
        saved = 0

        try:
            for _, row in df.iterrows():
                # Vérification doublon
                existing = db.query(FredData).filter_by(
                    series_id=series_id,
                    date=row["date"]
                ).first()

                if not existing:
                    entry = FredData(
                        series_id=series_id,
                        series_name=row.get("series_name", ""),
                        date=row["date"],
                        value=row["value"],
                    )
                    db.add(entry)
                    saved += 1

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur DB: {e}")
        finally:
            db.close()

        return saved

    def get_latest_values(self) -> dict:
        """
        Retourne la dernière valeur de chaque série FRED depuis la DB.
        Utile pour le calcul des scores macro.
        """
        db = get_session()
        result = {}

        try:
            for series_id in FRED_SERIES.keys():
                latest = (
                    db.query(FredData)
                    .filter_by(series_id=series_id)
                    .order_by(FredData.date.desc())
                    .first()
                )
                if latest:
                    result[series_id] = {
                        "value": latest.value,
                        "date": latest.date,
                        "name": FRED_SERIES.get(series_id, series_id),
                    }
        finally:
            db.close()

        return result


# ──────────────────────────────────────────────────────────────
# Test rapide
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = FREDClient()

    print("📡 Récupération CPI...")
    df = client.fetch_series("CPIAUCSL", limit=12)
    print(df.head())

    print("\n📊 Dernières observations:")
    info = client.fetch_series_info("CPIAUCSL")
    print(info)
