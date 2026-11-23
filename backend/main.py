"""API FastAPI de Moodify (partie 5).

Lancer depuis la racine du dépôt :
    uvicorn backend.main:app --reload --port 8000
Doc interactive pour tester : http://localhost:8000/docs
Côté front : mettre NEXT_PUBLIC_USE_MOCKS=false dans frontend/.env.local
"""
import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

#le module NLP de la partie 3 est dans src/moodify
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from moodify.semantic import SemanticMatcher  # noqa: E402

from backend.recommendation.recommender import recommander  # noqa: E402
from backend.schemas import Questionnaire, RecommendationResponse  # noqa: E402

#chargé une seule fois au démarrage : dataset + modèle SBERT + embeddings du catalogue
#(MOODIFY_ENCODER=tfidf permet de tester sans télécharger le modèle)
sm = SemanticMatcher(os.getenv("MOODIFY_ENCODER", "sbert"))

app = FastAPI(title="Moodify API")

#sinon le navigateur bloque les appels du front (localhost:3000) vers l'API (localhost:8000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

#pochette de secours : le front a 4 images, on choisit selon le bloc d'humeur principal du morceau
POCHETTES = {
    "Calme & détente": "calm", "Rêverie & évasion": "calm", "Mélancolie & introspection": "melancholic",
    "Romance & sensualité": "melancholic", "Concentration": "focused",
}


#vraies pochettes (colonne cover_url du dataset, remplie par dataset_builder/covers.py)
COVER_URLS = dict(zip(sm.tracks["track_id"], sm.tracks["cover_url"])) if "cover_url" in sm.tracks else {}


def pochette(track_id, bloc):
    """Pochette Spotify du morceau si elle existe, sinon une des 4 images du front."""
    url = COVER_URLS.get(track_id)
    return url if isinstance(url, str) and url.startswith("https://") else f"/covers/{POCHETTES.get(bloc, 'energetic')}.svg"


def vers_requete(q: Questionnaire):
    """Questionnaire du front -> requête du moteur : le profil complet (humeur, contexte, préférences)
    est construit par la partie 6 (backend/personalization), on lui passe toutes les réponses."""
    return q.model_dump()


def pct(x):
    return int(round(100 * float(x)))


@app.get("/")
def accueil():
    return {"status": "ok", "nb_morceaux": len(sm.tracks), "encodeur": sm.encoder.name}


@app.post("/recommendations", response_model=RecommendationResponse, response_model_exclude_none=True)
def recommendations(q: Questionnaire):
    res = recommander(sm, vers_requete(q), top_k=3)
    recos = []
    for r in res["recommandations"]:
        c = r["criteres"]
        bloc = r["blocs_humeur"][0] if r["blocs_humeur"] else ""
        recos.append({
            "id": r["track_id"], "rank": r["rang"], "title": r["titre"], "artist": r["artiste"],
            "coverUrl": pochette(r["track_id"], bloc),
            "genre": r["genre"], "mood": (r["humeurs"] or [""])[0].capitalize(),
            "score": pct(r["score"]), "moodScore": pct(c.get("humeur", 0)),
            "genreScore": pct(c.get("genre", 0)), "contextScore": pct(c.get("contexte", 0)),
            "explanation": r["explication"], "reasons": r["principaux_criteres"],
            #les identifiants de 22 caractères sont de vrais identifiants Spotify
            "spotifyTrackId": r["track_id"] if len(r["track_id"]) == 22 else None,
        })

    def moyenne(cle):
        return int(round(sum(x[cle] for x in recos) / max(len(recos), 1)))

    p = res["profil"]
    return {
        "recommendations": recos,
        "affinities": [{"label": "Mood", "score": moyenne("moodScore")},
                       {"label": "Genre", "score": moyenne("genreScore")},
                       {"label": "Context", "score": moyenne("contextScore")},
                       {"label": "Overall", "score": moyenne("score")}],
        "profileSummary": p["synthese"],
        "scenario": "semantic",
        "isDemo": False,
        "profile": {"dominantMood": p["humeur_dominante"], "dominantContext": p["contexte_dominant"],
                    "moodBlocks": {b: pct(v) for b, v in p["blocs_humeur"].items()},
                    "contextBlocks": {b: pct(v) for b, v in p["blocs_contexte"].items()},
                    #partie 6
                    "emotion": p.get("emotion"), "strategy": p.get("strategie"),
                    "strategySource": p.get("strategie_source"),
                    "intensity": p.get("intensite"), "excludedGenres": p.get("genres_exclus", []),
                    "instrumental": p.get("instrumental", False),
                    "archetype": (p.get("archetype") or {}).get("nom")},
    }


@app.get("/tracks/{track_id}")
def morceau(track_id: str):
    ligne = sm.tracks[sm.tracks["track_id"] == track_id]
    if ligne.empty:
        raise HTTPException(status_code=404, detail="Morceau introuvable")
    #to_json gère les types numpy et les valeurs manquantes
    return json.loads(ligne.iloc[0].to_json())
