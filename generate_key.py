"""
============================================================
RaAina Macro Eco — Générateur de Clés
============================================================
Utilisez ce script pour créer une nouvelle clé d'accès.

Usage:
    python generate_key.py
"""

import csv
import random
import string
from datetime import datetime, timedelta
import os

KEYS_FILE = os.path.join(os.path.dirname(__file__), "keys.csv")

def generate_key():
    """Génère une clé unique format RAAINA-XXXX-XXXX-XXXX"""
    parts = ["RAAINA"]
    for _ in range(3):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return "-".join(parts)

def add_key(nom: str) -> str:
    """Ajoute une nouvelle clé pour un utilisateur."""
    cle = generate_key()
    date_creation = datetime.now().strftime("%Y-%m-%d")
    expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    # Créer le fichier si inexistant
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nom", "cle", "date_creation", "expiration", "actif"])

    # Vérifier si le nom existe déjà
    existing = []
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing = list(reader)

    for row in existing:
        if row["nom"].lower() == nom.lower():
            print(f"\n⚠️  Un utilisateur '{nom}' existe déjà avec la clé : {row['cle']}")
            print(f"   Expiration : {row['expiration']}")
            repl = input("\nVoulez-vous créer une nouvelle clé quand même ? (o/n) : ").strip().lower()
            if repl != "o":
                return row["cle"]

    # Ajouter la nouvelle clé
    with open(KEYS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([nom, cle, date_creation, expiration, "true"])

    return cle


def list_keys():
    """Affiche toutes les clés."""
    if not os.path.exists(KEYS_FILE):
        print("Aucune clé trouvée.")
        return
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    now = datetime.now().date()
    print(f"\n{'NOM':<20} {'CLÉ':<25} {'EXPIRATION':<15} {'STATUT'}")
    print("-" * 75)
    for row in rows:
        exp = datetime.strptime(row["expiration"], "%Y-%m-%d").date()
        statut = "✅ Actif" if exp >= now and row["actif"] == "true" else "❌ Expiré/Révoqué"
        print(f"{row['nom']:<20} {row['cle']:<25} {row['expiration']:<15} {statut}")


def revoke_key(nom: str):
    """Révoque la clé d'un utilisateur."""
    if not os.path.exists(KEYS_FILE):
        print("Fichier keys.csv introuvable.")
        return
    rows = []
    found = False
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["nom"].lower() == nom.lower():
                row["actif"] = "false"
                found = True
            rows.append(row)

    if found:
        with open(KEYS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["nom","cle","date_creation","expiration","actif"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Clé de '{nom}' révoquée.")
    else:
        print(f"❌ Utilisateur '{nom}' introuvable.")


if __name__ == "__main__":
    print("=" * 50)
    print("  RaAina Macro Eco — Gestion des Clés")
    print("=" * 50)
    print("\n1. Créer une nouvelle clé")
    print("2. Voir toutes les clés")
    print("3. Révoquer une clé")

    choix = input("\nVotre choix (1/2/3) : ").strip()

    if choix == "1":
        nom = input("Nom de l'utilisateur : ").strip()
        if nom:
            cle = add_key(nom)
            print(f"\n✅ Clé créée pour '{nom}' :")
            print(f"\n   🔑 {cle}")
            exp = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
            print(f"\n   📅 Expire le : {exp}")
            print(f"\n   Envoyez cette clé à {nom} pour qu'il accède au dashboard.")
        else:
            print("❌ Nom invalide.")

    elif choix == "2":
        list_keys()

    elif choix == "3":
        nom = input("Nom de l'utilisateur à révoquer : ").strip()
        revoke_key(nom)

    print("\n" + "=" * 50)
