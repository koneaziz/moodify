"""Formule de score de la partie 4 (recommandation).

On utilise le module NLP de la partie 3 (src/moodify/semantic.py) pour toutes les similarités,
puis on combine 6 critères avec la formule de l'exemple du sujet :
    score = somme(Wi * Si) / somme(Wi)
Tout est expliqué dans notebooks/03_recommandation_api.ipynb.
"""
import numpy as np
import pandas as pd

from backend.personalization import construire_profil_utilisateur

#poids des critères : 70 % sémantique (description + humeur + contexte), 30 % préférences cochées
POIDS = {
    "description": 0.30,
    "humeur": 0.25,
    "contexte": 0.15,
    "genre": 0.15,
    "energie": 0.10,
    "artiste": 0.05,
}

#calibration donnée par la partie 3 (notebook 02, section 7.3) : 5e et 99,5e centile du score sémantique
COS_LOW = 0.29
COS_HIGH = 0.53

#partie 6 : multiplicateur du score d'un morceau chanté quand l'utilisateur demande de l'instrumental
PENALITE_CHANTE = 0.6

#seuils d'interprétation du score final (étape 5 de l'exemple du sujet)
SEUILS = [(0.65, "Très forte correspondance"), (0.45, "Bonne correspondance"), (0.0, "Correspondance partielle")]


def separer(texte):
    #"calme|doux|serein" -> ["calme", "doux", "serein"]
    return [x.strip() for x in str(texte).split("|") if x.strip()]


def niveau(score):
    for seuil, libelle in SEUILS:
        if score >= seuil:
            return libelle
    return SEUILS[-1][1]


def normaliser(scores):
    #min-max : le bloc le plus proche vaut 1 et le plus loin 0 (les cosinus bruts sont très serrés)
    if not scores:
        return {}
    mini, maxi = min(scores.values()), max(scores.values())
    return {b: (s - mini) / (maxi - mini + 1e-9) for b, s in scores.items()}


def construire_profil(sm, requete):
    """Profil utilisateur de la partie 6 (backend/personalization).
    requete = le questionnaire du front, ou l'ancien format {"textes", "humeur", "contexte",
    "genres", "artistes", "energie"} (toujours accepté, par exemple dans le notebook 03)."""
    return construire_profil_utilisateur(sm, requete)


def moyenne_blocs(blocs_morceau, profil_blocs):
    #moyenne du profil sur les blocs du morceau (comme un poste qui "demande" certains blocs)
    valeurs = [profil_blocs[b] for b in separer(blocs_morceau) if b in profil_blocs]
    return float(np.mean(valeurs)) if valeurs else 0.0


def calculer_scores(sm, profil):
    """Calcule les critères Si de tous les morceaux et le score final."""
    df = sm.tracks
    S = pd.DataFrame(index=df.index)

    #score sémantique de la partie 3 (3 vues du morceau), recalé entre 0 et 1
    brut = sm.semantic_score(profil["textes"])
    S["description"] = np.clip((brut - COS_LOW) / (COS_HIGH - COS_LOW), 0, 1)
    S["humeur"] = df["mood_blocks"].fillna("").apply(lambda b: moyenne_blocs(b, profil["blocs_humeur"]))

    #un critère que l'utilisateur n'a pas rempli n'est pas calculé (son poids ne compte pas)
    if profil["blocs_contexte"]:
        S["contexte"] = df["context_blocks"].fillna("").apply(lambda b: moyenne_blocs(b, profil["blocs_contexte"]))
    if profil["genres"]:
        S["genre"] = df["genre"].isin(profil["genres"]).astype(float)
    if profil["energie"]:
        S["energie"] = 1 - abs(df["energy"].astype(int) - profil["energie"]) / 4
    if profil["artistes"]:
        noms = (df["artist"].fillna("") + " " + df["featured_artists"].fillna("")).str.lower()
        S["artiste"] = noms.apply(lambda n: any(a in n for a in profil["artistes"])).astype(float)

    #formule du sujet : score = somme(Wi * Si) / somme(Wi)
    poids = {c: POIDS[c] for c in S.columns}
    score = sum(S[c] * poids[c] for c in S.columns) / sum(poids.values())

    #contraintes du profil (partie 6) : genres refusés exclus, morceaux chantés pénalisés si
    #l'utilisateur veut de l'instrumental
    if profil.get("genres_exclus"):
        score = score.where(~df["genre"].isin(profil["genres_exclus"]), 0.0)
    if profil.get("instrumental"):
        instru = (df["language"].fillna("") == "instrumental") | (df["instrumentalness"].fillna(0) >= 0.5)
        score = score.where(instru, score * PENALITE_CHANTE)
    return S, poids, score, brut
