"""PHASE 19 — ARTISTES SIMILAIRES, VILLES ET CONCERTS

 19.1 Vecteur sémantique par artiste = centroïde des embeddings des descriptions de ses morceaux
      -> 5 artistes les plus proches (cosinus) : sert à proposer des concerts d'artistes
         « proches de ceux que tu écoutes »
 19.2 Table des villes (coordonnées GPS) + salles réelles par ville
 19.3 Concerts :
      - si TICKETMASTER_API_KEY est défini : vrais événements (API Discovery, mis en cache)
      - sinon / en complément : concerts SIMULÉS (dates, salles réelles, marqués « simulé »)
 19.4 Mise à jour de la question « ville » du questionnaire
Sorties : data/processed/artist_similarity.csv, cities.csv, concerts.csv
"""
from __future__ import annotations

import hashlib
import json
import random
import urllib.parse
import urllib.request
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config
from .utils import get_encoder, load_json, log, phase_timer, report, save_json

CITIES = {  # ville: (lat, lon, [salles])
    "Paris": (48.8566, 2.3522, ["Accor Arena", "Zénith Paris", "Olympia", "La Cigale", "Le Trianon"]),
    "Lyon": (45.7640, 4.8357, ["LDLC Arena", "Halle Tony Garnier", "Le Transbordeur", "Le Ninkasi Kao"]),
    "Marseille": (43.2965, 5.3698, ["Le Dôme", "Le Silo", "Espace Julien"]),
    "Toulouse": (43.6047, 1.4442, ["Zénith Toulouse Métropole", "Le Bikini"]),
    "Bordeaux": (44.8378, -0.5792, ["Arkéa Arena", "Le Rocher de Palmer"]),
    "Lille": (50.6292, 3.0573, ["Zénith de Lille", "L'Aéronef"]),
    "Nantes": (47.2184, -1.5536, ["Zénith Nantes Métropole", "Stereolux"]),
    "Strasbourg": (48.5734, 7.7521, ["La Laiterie", "Zénith de Strasbourg"]),
    "Montpellier": (43.6108, 3.8767, ["Sud de France Arena", "Le Rockstore"]),
    "Nice": (43.7102, 7.2620, ["Palais Nikaïa"]),
    "Rennes": (48.1173, -1.6778, ["Le Liberté", "L'Ubu"]),
    "Bruxelles": (50.8503, 4.3517, ["Forest National", "Ancienne Belgique", "Palais 12"]),
    "Genève": (46.2044, 6.1432, ["Arena de Genève", "L'Usine"]),
}
TM_CACHE = config.CACHE / "ticketmaster"


def fetch_ticketmaster(artist: str) -> list[dict]:
    """Événements réels via l'API Ticketmaster Discovery (clé gratuite). Mis en cache."""
    if not config.TICKETMASTER_API_KEY:
        return []
    TM_CACHE.mkdir(parents=True, exist_ok=True)
    path = TM_CACHE / (hashlib.md5(artist.encode()).hexdigest() + ".json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        q = urllib.parse.urlencode({"apikey": config.TICKETMASTER_API_KEY, "keyword": artist,
                                    "classificationName": "music", "size": 20})
        try:
            with urllib.request.urlopen(f"https://app.ticketmaster.com/discovery/v2/events.json?{q}", timeout=15) as r:
                data = json.loads(r.read())
            path.write_text(json.dumps(data), encoding="utf-8")
        except Exception as exc:
            log.debug("    Ticketmaster erreur %s", exc)
            return []
    out = []
    for ev in data.get("_embedded", {}).get("events", []):
        try:
            v = ev["_embedded"]["venues"][0]
            out.append({"artist": artist, "city": v["city"]["name"], "venue": v["name"],
                        "date": ev["dates"]["start"]["localDate"],
                        "lat": float(v["location"]["latitude"]), "lon": float(v["location"]["longitude"]),
                        "source": "ticketmaster", "url": ev.get("url", "")})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def run() -> None:
    with phase_timer("P19 Artistes, villes, concerts"):
        rng = random.Random(config.CONCERTS_SEED)
        t = pd.read_csv(config.PROCESSED / "tracks.csv").fillna("")
        artists = pd.read_csv(config.PROCESSED / "artists.csv").fillna("")

        # 19.1 similarité entre artistes
        enc = get_encoder(t["description"].tolist())
        E = enc.encode(t["description"].tolist())
        names = artists["artist"].tolist()
        V = np.vstack([E[t.index[t["artist"] == a]].mean(axis=0) for a in names])
        V /= np.linalg.norm(V, axis=1, keepdims=True)
        S = V @ V.T
        np.fill_diagonal(S, -1)
        sim_rows = []
        for i, a in enumerate(names):
            top = np.argsort(-S[i])[:5]
            sim_rows.append({"artist": a, "similar_artists": "|".join(names[j] for j in top),
                             "similarities": "|".join(f"{S[i, j]:.3f}" for j in top)})
        pd.DataFrame(sim_rows).to_csv(config.PROCESSED / "artist_similarity.csv", index=False)

        # 19.2 villes
        pd.DataFrame([{"city": c, "lat": la, "lon": lo, "venues": "|".join(v)}
                      for c, (la, lo, v) in CITIES.items()]).to_csv(config.PROCESSED / "cities.csv", index=False)

        # 19.3 concerts
        top_artists = artists.sort_values("popularity_mean", ascending=False).head(config.N_CONCERT_ARTISTS)
        concerts = []
        for a in top_artists["artist"]:
            real = fetch_ticketmaster(a)
            if real:
                concerts += real
                continue
            for _ in range(rng.randint(1, 3)):
                city = rng.choice(list(CITIES))
                la, lo, venues = CITIES[city]
                d = date(config.CONCERT_YEAR, 1, 15) + timedelta(days=rng.randint(0, 300))
                concerts.append({"artist": a, "city": city, "venue": rng.choice(venues),
                                 "date": d.isoformat(), "lat": la, "lon": lo, "source": "simulé", "url": ""})
        cdf = pd.DataFrame(concerts).sort_values(["date", "artist"]).reset_index(drop=True)
        cdf.insert(0, "concert_id", [f"K{i + 1:04d}" for i in range(len(cdf))])
        cdf.to_csv(config.PROCESSED / "concerts.csv", index=False)

        # 19.4 questionnaire : options de ville
        quiz_path = config.PROCESSED / "questionnaire.json"
        quiz = load_json(quiz_path)
        for s in quiz["sections"]:
            for q in s["questions"]:
                if q["id"] == "Q14":
                    q["options"] = list(CITIES)
        save_json(quiz, quiz_path)

        src = cdf["source"].value_counts().to_dict()
        log.info("  %d concerts (%s) pour %d artistes", len(cdf), src, cdf["artist"].nunique())
        report("P19_artists_concerts", concerts=len(cdf), by_source=src, cities=len(CITIES))
