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

#le front a ses propres listes (frontend/types/questionnaire.ts), on les traduit vers le dataset
GENRES_FRONT = {
    "Pop": ["Pop"], "Hip-Hop": ["Hip-hop / Rap"], "R&B": ["R&B / Soul / Funk"], "Soul": ["R&B / Soul / Funk"],
    "Rock": ["Rock"], "Jazz": ["Jazz / Blues"], "Classical": ["Classique"], "Electronic": ["Électro / House"],
    "Lo-Fi": ["Lo-fi / Chill"], "Indie": ["Indie / Folk / Country"], "Ambient": ["Ambient"],
    "Other": ["Metal", "Afro / Reggae / Latino", "Chanson française", "Musiques du monde"],
}
#les humeurs et contextes cochés deviennent des phrases, pour rester dans l'analyse sémantique
HUMEURS_FRONT = {
    "Happy": "je me sens joyeux", "Sad": "je suis triste", "Calm": "j'ai envie de calme",
    "Stressed": "je suis stressé", "Energetic": "je suis plein d'énergie",
    "Focused": "j'ai besoin de me concentrer", "Melancholic": "je me sens mélancolique",
    "Romantic": "je suis d'humeur romantique",
}
CONTEXTES_FRONT = {
    "Studying": "pour réviser et étudier", "Working": "pour travailler", "Relaxing": "pour me détendre",
    "Exercising": "pour faire du sport", "Driving": "en conduisant", "Sleeping": "pour m'endormir",
    "Partying": "pour faire la fête", "Just vibing": "juste pour le plaisir",
}
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
    """Questionnaire du front -> requête du moteur de recommandation."""
    humeur = [q.description] + [HUMEURS_FRONT[m] for m in q.moods if m in HUMEURS_FRONT]
    contexte = [CONTEXTES_FRONT.get(q.listeningContext, ""), q.contextDescription]
    textes = humeur + contexte + [q.additionalPreferences]
    if q.vocalPreference == "Instrumental":
        textes.append("musique instrumentale sans paroles")
    return {
        "textes": [t for t in textes if t.strip()],
        "humeur": humeur,
        "contexte": [t for t in contexte if t.strip()],
        "genres": [g for front in q.genres for g in GENRES_FRONT.get(front, [front])],
        "artistes": [a.strip() for a in q.favoriteArtists.replace(";", ",").split(",") if a.strip()],
        "energie": q.energyLevel,
    }


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
                    "contextBlocks": {b: pct(v) for b, v in p["blocs_contexte"].items()}},
    }


@app.get("/tracks/{track_id}")
def morceau(track_id: str):
    ligne = sm.tracks[sm.tracks["track_id"] == track_id]
    if ligne.empty:
        raise HTTPException(status_code=404, detail="Morceau introuvable")
    #to_json gère les types numpy et les valeurs manquantes
    return json.loads(ligne.iloc[0].to_json())
