"""Tests du profil utilisateur (partie 6). Encodeur TF-IDF : aucun téléchargement nécessaire.
    python -m pytest -q tests/test_profile.py
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from backend.personalization import analyser_humeur, construire_profil_utilisateur  # noqa: E402
from backend.personalization.cas_usage import CAS  # noqa: E402
from backend.personalization.evaluation import top_k, verifier_profil  # noqa: E402
from backend.personalization.preference_profiler import detecter_exclusions  # noqa: E402
from moodify.semantic import SemanticMatcher  # noqa: E402

SM = SemanticMatcher("tfidf")


# --------------------------------------------------------------------- analyse de l'humeur
def test_negation_ignore_l_emotion():
    a = analyser_humeur("Je ne suis pas triste, juste fatigué")
    assert "tristesse" not in a["emotions"] and "tristesse" in a["emotions_niees"]
    assert a["emotion_dominante"] == "fatigue"


def test_strategie_reguler_ou_accompagner():
    assert analyser_humeur("Je suis énervée, je veux me calmer")["blocs_cibles"].get("Calme & détente") == 1
    assert analyser_humeur("Je suis énervé, je veux me défouler")["blocs_cibles"].get("Colère & défoulement") == 1
    a = analyser_humeur("Je suis triste")
    assert a["strategie"] == "accompagner" and a["strategie_source"] == "défaut"


def test_intensite():
    assert analyser_humeur("je suis stressé")["intensite"] == 1
    assert analyser_humeur("je suis vraiment très stressé !")["intensite"] == 3


def test_emotion_positive_jamais_regulee():
    # « me calmer » ne doit pas transformer la joie en calme : seules les émotions négatives sont régulées
    a = analyser_humeur("je suis heureux et je veux me calmer un peu")
    assert a["strategie"] == "réguler" and a["emotion_dominante"] == "joie"
    assert "Fête & danse" in a["blocs_cibles"]          # joie -> règle « accompagner », même si « me calmer »


def test_exclusions_de_genres():
    assert detecter_exclusions("pas de rap s'il te plaît") == ["Hip-hop / Rap"]
    assert detecter_exclusions("je déteste le metal") == ["Metal"]
    assert detecter_exclusions("j'adore le rap") == []


# --------------------------------------------------------------------------- cas d'usage
@pytest.mark.parametrize("cas", CAS, ids=[c["id"] for c in CAS])
def test_profil_des_cas_d_usage(cas):
    profil = construire_profil_utilisateur(SM, cas["questionnaire"])
    echecs = [(c, o, a) for c, ok, o, a in verifier_profil(profil, cas["profil"]) if not ok]
    assert not echecs, f"{cas['id']} {cas['persona']} : {echecs}"


@pytest.mark.parametrize("cas", [c for c in CAS if c["profil"].get("genres_exclus")], ids=lambda c: c["id"])
def test_genres_exclus_absents_du_top(cas):
    profil = construire_profil_utilisateur(SM, cas["questionnaire"])
    assert not {m["genre"] for m in top_k(SM, profil, 10)} & set(profil["genres_exclus"])


def test_instrumental_respecte():
    cas = next(c for c in CAS if c["id"] == "C01")
    top = top_k(SM, construire_profil_utilisateur(SM, cas["questionnaire"]), 3)
    assert all(m["language"] == "instrumental" or (m["instrumentalness"] or 0) >= 0.5 for m in top)


# -------------------------------------------------------------------- compatibilité partie 4
def test_ancien_format_de_requete_accepte():
    p = construire_profil_utilisateur(SM, {"textes": ["je suis triste"], "humeur": ["je suis triste"],
                                           "contexte": [], "genres": ["Pop"], "artistes": [], "energie": 2})
    for cle in ("textes", "genres", "artistes", "energie", "blocs_humeur", "blocs_contexte",
                "humeur_dominante", "contexte_dominant"):
        assert cle in p
    assert p["genres"] == ["Pop"] and p["emotion"] == "tristesse"


def test_api_renvoie_le_profil(monkeypatch):
    monkeypatch.setenv("MOODIFY_ENCODER", "tfidf")
    from fastapi.testclient import TestClient
    import backend.main as api
    r = TestClient(api.app).post("/recommendations", json=CAS[0]["questionnaire"])
    assert r.status_code == 200
    profil = r.json()["profile"]
    assert profil["strategy"] == "réguler" and profil["excludedGenres"] == ["Hip-hop / Rap"]
    assert len(r.json()["recommendations"]) == 3
