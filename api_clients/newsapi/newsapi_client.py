"""
============================================================
API CLIENT — NewsAPI
============================================================
Récupère les headlines économiques en temps réel.
API gratuite (100 req/jour) : https://newsapi.org
"""

import requests
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import API_KEYS, NEWS_QUERIES, COLLECTION
from database.models.models import get_session, News

BASE_URL = "https://newsapi.org/v2"

ECONOMIC_SOURCES = [
    "reuters", "bloomberg", "financial-times", "the-wall-street-journal",
    "cnbc", "the-economist", "business-insider", "fortune",
    "associated-press", "bbc-news"
]


class NewsAPIClient:

    def __init__(self):
        self.api_key = API_KEYS["newsapi"]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })

    def _get(self, endpoint: str, params: dict) -> dict:
        r = self.session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def fetch_everything(
        self,
        query: str,
        from_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
    ) -> list[dict]:
        """
        Recherche d'articles par mot-clé.

        Args:
            query: Ex: "Federal Reserve interest rates"
            from_date: "YYYY-MM-DD" (défaut: 7 jours)
            language: "en" ou "fr"
            sort_by: publishedAt / relevancy / popularity
            page_size: 1-100

        Returns:
            Liste d'articles bruts
        """
        if not from_date:
            from_date = (datetime.now() - timedelta(days=COLLECTION["lookback_days"])).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
        }

        data = self._get("everything", params)
        return data.get("articles", [])

    def fetch_top_headlines(self, category: str = "business") -> list[dict]:
        """Top headlines business/finance."""
        data = self._get("top-headlines", {
            "category": category,
            "language": "en",
            "pageSize": 20,
        })
        return data.get("articles", [])

    def fetch_all_macro_news(self) -> list[dict]:
        """
        Récupère les news pour toutes les requêtes macro définies.
        Évite les doublons via URL.
        """
        seen_urls = set()
        all_articles = []

        for query in NEWS_QUERIES:
            try:
                articles = self.fetch_everything(query, page_size=15)
                for article in articles:
                    url = article.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        article["_query"] = query
                        all_articles.append(article)

                print(f"  ✅ '{query}': {len(articles)} articles")

            except Exception as e:
                print(f"  ❌ '{query}': {e}")

        print(f"\n📰 Total unique: {len(all_articles)} articles")
        return all_articles

    def clean_article(self, article: dict) -> dict:
        """Nettoie et normalise un article brut."""
        title = (article.get("title") or "").strip()
        content = (article.get("content") or article.get("description") or "").strip()
        content = content.replace("[+", "").replace("chars]", "").strip()

        # Supprime contenu trop court
        if len(title) < 10:
            return None

        # Hash pour déduplication
        content_hash = hashlib.sha256(f"{title}{content}".encode()).hexdigest()

        source = article.get("source", {})
        source_name = source.get("name", "Unknown") if isinstance(source, dict) else str(source)

        published_str = article.get("publishedAt", "")
        try:
            published_at = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            published_at = datetime.utcnow()

        return {
            "title": title,
            "content": content,
            "summary": article.get("description", "")[:500],
            "source": source_name,
            "url": article.get("url", ""),
            "author": article.get("author", ""),
            "published_at": published_at,
            "content_hash": content_hash,
            "category": self._categorize(title + " " + content),
            "is_processed": False,
        }

    def _categorize(self, text: str) -> str:
        """Catégorisation simple par mots-clés."""
        text_lower = text.lower()
        categories = {
            "FOMC/FED":       ["federal reserve", "fomc", "fed rate", "powell", "fed funds"],
            "CPI/Inflation":  ["cpi", "inflation", "consumer price", "price index"],
            "GDP":            ["gdp", "gross domestic", "economic growth", "recession"],
            "NFP/Jobs":       ["nonfarm payrolls", "jobs report", "unemployment", "labor market"],
            "ECB":            ["ecb", "european central bank", "lagarde", "euro zone"],
            "BOJ":            ["boj", "bank of japan", "ueda", "yen"],
            "BOE":            ["boe", "bank of england", "bailey", "sterling"],
            "Treasury/Bonds": ["treasury", "yield", "bonds", "10-year", "2-year"],
            "Oil/Energy":     ["oil", "opec", "crude", "energy", "wti", "brent"],
            "Markets":        ["nasdaq", "s&p", "dow jones", "equity", "stocks"],
            "USD/DXY":        ["dollar", "dxy", "usd", "currency", "forex"],
            "PMI":            ["pmi", "manufacturing", "services index", "purchasing managers"],
        }

        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return cat

        return "General/Macro"

    def save_to_db(self, articles: list[dict]) -> int:
        """Sauvegarde les articles nettoyés en base de données."""
        db = get_session()
        saved = 0

        try:
            for raw in articles:
                cleaned = self.clean_article(raw)
                if not cleaned:
                    continue

                # Vérification doublon
                existing = db.query(News).filter_by(
                    content_hash=cleaned["content_hash"]
                ).first()

                if not existing:
                    news = News(**cleaned)
                    db.add(news)
                    saved += 1

            db.commit()
            print(f"✅ {saved} articles sauvegardés en base.")

        except Exception as e:
            db.rollback()
            print(f"❌ Erreur DB: {e}")
        finally:
            db.close()

        return saved


# ──────────────────────────────────────────────────────────────
# Test rapide
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = NewsAPIClient()
    print("📡 Récupération des news macro...")
    articles = client.fetch_all_macro_news()
    print(f"\nPremier article:")
    if articles:
        cleaned = client.clean_article(articles[0])
        for k, v in cleaned.items():
            print(f"  {k}: {v}")
