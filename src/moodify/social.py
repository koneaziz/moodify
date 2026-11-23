"""Fonctionnalités « sociales » : communautés et concerts.

Communautés — score sémantique + préférences structurées :
    Score(c) = 0.6 · cos(profil, description_c) + 0.2 · Jaccard(genres) + 0.2 · overlap(humeurs)

Concerts — on cherche les concerts :
    (a) des artistes suivis (affinité = 1),
    (b) d'artistes sémantiquement proches de ceux suivis / écoutés
        (cos entre « profils d'artistes » = centroïde des embeddings de leurs morceaux),
    puis on filtre par distance (haversine) et on classe :
    Score(k) = 0.6 · affinité + 0.4 · (1 − distance / rayon)
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config
from .embeddings import _l2_normalize, cosine_matrix
from .preprocessing import normalize_key
from .profile import UserProfile
from .reference import ReferenceIndex
from .scoring import minmax


# ------------------------------------------------------------------ communautés
def recommend_communities(ref: ReferenceIndex, profile: UserProfile, analysis: dict, k: int = 3) -> list[dict]:
    w = config.COMMUNITY_WEIGHTS
    u = ref.encoder.encode_mean(profile.sentences() or [profile.summary_text()])
    sem_raw = cosine_matrix(u, ref.E_comm)[0]
    sem = minmax(sem_raw)
    top_moods = {b for b, _ in sorted(analysis["mood_blocks"].items(), key=lambda kv: -kv[1])[:3]}
    liked = set(profile.genres_liked)
    out = []
    for i, c in ref.communities.iterrows():
        g = set(c.genres_list)
        jacc = len(liked & g) / len(liked | g) if liked else 0.0
        mood_ov = len(top_moods & set(c.moods_list)) / max(1, len(c.moods_list))
        score = w["semantic"] * sem[i] + w["genre"] * jacc + w["mood"] * mood_ov
        reasons = []
        if sem_raw[i] == sem_raw.max():
            reasons.append("sa description est la plus proche de ce que tu as écrit")
        if liked & g:
            reasons.append("genres en commun : " + ", ".join(sorted(liked & g)))
        if top_moods & set(c.moods_list):
            reasons.append("même ambiance : " + ", ".join(sorted(top_moods & set(c.moods_list))))
        out.append({"community_id": c.community_id, "name": c["name"], "description": c.description,
                    "score": round(float(score), 3), "semantic_raw": round(float(sem_raw[i]), 3),
                    "reasons": reasons or ["proximité sémantique avec ton profil"]})
    return sorted(out, key=lambda d: d["score"], reverse=True)[:k]


# --------------------------------------------------------------------- concerts
def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def artist_vectors(ref: ReferenceIndex) -> tuple[list[str], np.ndarray]:
    """Un vecteur par artiste = centroïde des embeddings de ses morceaux."""
    names, vecs = [], []
    for artist, idx in ref.tracks.groupby("artist").groups.items():
        names.append(artist)
        vecs.append(ref.E_track_full[list(idx)].mean(axis=0))
    return names, _l2_normalize(np.vstack(vecs))


def recommend_concerts(ref: ReferenceIndex, profile: UserProfile, listened_artists: list[str] | None = None,
                       k: int = 5) -> list[dict]:
    origin = ref.coords(profile.city) if profile.city else None
    if origin is None:
        return []
    names, V = artist_vectors(ref)
    key_to_i = {normalize_key(n): i for i, n in enumerate(names)}
    followed = {normalize_key(a) for a in profile.artists}
    listened = {normalize_key(a) for a in (listened_artists or [])}
    seeds = [key_to_i[a] for a in followed | listened if a in key_to_i]

    # Affinité de chaque artiste du catalogue
    affinity: dict[str, tuple[float, str]] = {}
    if seeds:
        S = cosine_matrix(V[seeds], V)          # (n_seeds, n_artists)
        for j, name in enumerate(names):
            i_best = int(np.argmax(S[:, j]))
            affinity[normalize_key(name)] = (float(S[i_best, j]), names[seeds[i_best]])
    for a in followed:
        affinity[a] = (1.0, "tu suis cet artiste")
    for a in listened - followed:
        affinity[a] = (max(affinity.get(a, (0, ""))[0], 0.85), "tu l'écoutes souvent")

    out = []
    for _, c in ref.concerts.iterrows():
        key = normalize_key(c.artist)
        aff, why = affinity.get(key, (0.0, ""))
        if key not in followed and key not in listened and aff < config.SIMILAR_ARTIST_MIN_SIM:
            continue
        dest = ref.coords(c.city)
        if dest is None:
            continue
        d = haversine_km(origin, dest)
        if d > profile.travel_radius_km:
            continue
        prox = 1 - d / max(profile.travel_radius_km, 1)
        a = config.CONCERT_AFFINITY_WEIGHT
        if why in ("tu suis cet artiste", "tu l'écoutes souvent"):
            reason = why
        else:
            reason = f"style proche de {why} (similarité {aff:.2f})"
        out.append({"concert_id": c.concert_id, "artist": c.artist, "city": c.city, "venue": c.venue,
                    "date": c.date, "distance_km": round(d), "affinity": round(aff, 3),
                    "score": round(a * aff + (1 - a) * prox, 3), "reason": reason,
                    "source": c.source})
    return sorted(out, key=lambda d: (-d["score"], d["date"]))[:k]
