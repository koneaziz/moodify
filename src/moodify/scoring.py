"""Mécanisme de scoring sémantique.

Deux niveaux de score (cf. README §5) :

1. **Analyse du profil** — affinité de l'utilisateur avec chaque *bloc* d'humeur et de
   contexte, puis **score de couverture** de chaque profil d'auditeur :
       S_bloc     = ½ · moyenne_u( max_p cos(u, p) ) + ½ · max_u( max_p cos(u, p) )
       Couverture = Σ W_i · S_i / Σ W_i     (formule du sujet)
   u = phrases de l'utilisateur, p = phrases prototypes du bloc.

2. **Score d'un morceau** pour une requête (profil ou message du chatbot) :
       Score(t) = Σ_k w_k · C_k(t) / Σ_k w_k      (k = composantes actives)
   avec C_k ∈ [0, 1] : sémantique globale, humeur, contexte, genre, artiste, énergie,
   personnalité. Les composantes sémantiques sont normalisées min-max sur le catalogue
   pour être comparables entre elles (le classement est inchangé, seules les échelles
   sont alignées).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config
from .embeddings import _l2_normalize, cosine_matrix
from .preprocessing import normalize_key
from .profile import UserProfile
from .reference import ReferenceIndex

CALIBRATION = {"sbert": (config.COS_LOW, config.COS_HIGH), "tfidf": (0.0, 0.35),
               "word2vec": (0.30, 0.90)}


def calibrate(x, encoder_name: str = "sbert"):
    """Rescale un cosinus brut en score lisible [0, 1] (affichage uniquement)."""
    lo, hi = CALIBRATION.get(encoder_name, (config.COS_LOW, config.COS_HIGH))
    return np.clip((np.asarray(x, dtype=float) - lo) / (hi - lo), 0.0, 1.0)


def minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    span = x.max() - x.min()
    return np.zeros_like(x) if span < 1e-9 else (x - x.min()) / span


def block_affinity(U: np.ndarray, P: np.ndarray) -> float:
    """Affinité entre des phrases utilisateur U et un bloc de prototypes P.
    max_p : chaque phrase est rattachée à la compétence/prototype le plus proche ;
    moyenne_u : à quel point le bloc est central dans tout ce qu'a dit l'utilisateur ;
    max_u : le bloc a-t-il été clairement évoqué au moins une fois ?"""
    if len(U) == 0:
        return 0.0
    best_per_sentence = cosine_matrix(U, P).max(axis=1)
    return float(0.5 * best_per_sentence.mean() + 0.5 * best_per_sentence.max())


# =========================================================== 1. Analyse du profil
def analyze_profile(ref: ReferenceIndex, profile: UserProfile) -> dict:
    enc = ref.encoder
    sents = profile.sentences() or [profile.summary_text() or "musique"]
    U = enc.encode(sents)

    mood_raw = {b: block_affinity(U, ref.E_mood_blocks[b]) for b in ref.mood_block_names}
    ctx_raw = {b: block_affinity(U, ref.E_ctx_blocks[b]) for b in ref.ctx_block_names}
    mood = {b: float(calibrate(v, enc.name)) for b, v in mood_raw.items()}
    ctx = {b: float(calibrate(v, enc.name)) for b, v in ctx_raw.items()}
    for b in profile.contexts:          # case cochée = signal explicite et fiable
        if b in ctx:
            ctx[b] = 1.0

    coverage = []
    for a in ref.archetypes:
        w = a["blocks"]
        score = sum(w[b] * mood[b] for b in w) / sum(w.values())
        coverage.append({"id": a["id"], "name": a["name"], "description": a["description"],
                         "coverage": round(score, 3),
                         "details": {b: round(mood[b], 3) for b in w}})
    coverage.sort(key=lambda d: d["coverage"], reverse=True)

    return {
        "mood_blocks": mood, "mood_blocks_raw": mood_raw,
        "context_blocks": ctx, "context_blocks_raw": ctx_raw,
        "archetypes": coverage, "archetype": coverage[0],
        "personality": profile.personality,
        "genre_prior": genre_personality_prior(ref, profile.personality),
        "global_coverage": round(float(np.mean(sorted(mood.values())[-3:])), 3),
    }


def genre_personality_prior(ref: ReferenceIndex, personality: dict[str, float]) -> dict[str, float]:
    """A priori faible genre ← personnalité (modèle STOMP). Renvoie un score [0,1] par genre,
    0.5 = neutre. Traits centrés : (trait - 0.5) * 2 ∈ [-1, 1]."""
    prior = {g: [] for g in ref.genres}
    if not personality:
        return {g: 0.5 for g in ref.genres}
    for dim in ref.personality_map.values():
        z = sum(w * (personality.get(t, 0.5) - 0.5) * 2 for t, w in dim["traits"].items())
        z = float(np.clip(z / max(1.0, sum(abs(w) for w in dim["traits"].values())), -1, 1))
        for g in dim["genres"]:
            if g in prior:
                prior[g].append(z)
    return {g: round((np.mean(v) + 1) / 2, 3) if v else 0.5 for g, v in prior.items()}


# ======================================================== 2. Scoring des morceaux
@dataclass
class Query:
    """Requête normalisée, construite depuis le profil et/ou un message du chatbot."""
    texts: list[str] = field(default_factory=list)          # texte libre (vue globale)
    mood_texts: list[str] = field(default_factory=list)     # description d'humeur
    target_blocks: dict[str, float] = field(default_factory=dict)  # blocs d'humeur visés
    contexts: list[str] = field(default_factory=list)       # blocs de contexte
    genres_liked: list[str] = field(default_factory=list)
    genres_disliked: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    energy_target: float | None = None
    personality: dict[str, float] = field(default_factory=dict)
    exclude_track_ids: list[str] = field(default_factory=list)


def query_from_profile(profile: UserProfile, analysis: dict | None = None, top_blocks: int = 3) -> Query:
    target = {}
    if analysis:
        best = sorted(analysis["mood_blocks"].items(), key=lambda kv: kv[1], reverse=True)[:top_blocks]
        target = {b: max(s, 0.05) for b, s in best}
    return Query(texts=profile.sentences() or [profile.summary_text()],
                 mood_texts=profile.mood_texts, target_blocks=target,
                 contexts=list(profile.contexts), genres_liked=list(profile.genres_liked),
                 genres_disliked=list(profile.genres_disliked), artists=list(profile.artists),
                 energy_target=float(profile.energy_pref), personality=profile.personality)


def score_tracks(ref: ReferenceIndex, q: Query, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Calcule toutes les composantes et le score final pour chaque morceau du catalogue."""
    weights = weights or config.WEIGHTS_PROFILE
    enc, df = ref.encoder, ref.tracks
    n = len(df)
    comp: dict[str, np.ndarray] = {}   # composantes normalisées [0,1]
    raw: dict[str, np.ndarray] = {}    # cosinus bruts (pour l'explication)

    # -- Similarité sémantique globale : texte libre vs description complète
    if q.texts:
        S = cosine_matrix(enc.encode(q.texts), ref.E_track_full)   # (n_phrases, n_tracks)
        raw["semantic"] = 0.5 * S.mean(axis=0) + 0.5 * S.max(axis=0)
        comp["semantic"] = minmax(raw["semantic"])

    # -- Humeur : vecteur d'humeur = centroïdes des blocs visés (pondérés) + texte d'humeur
    mood_vecs = []
    for b, w in q.target_blocks.items():
        mood_vecs.append(w * ref.E_mood_blocks[b].mean(axis=0))
    if q.mood_texts:
        mood_vecs.append(enc.encode(q.mood_texts).mean(axis=0))
    if mood_vecs:
        mv = _l2_normalize(np.sum(mood_vecs, axis=0, keepdims=True))
        raw["mood"] = cosine_matrix(mv, ref.E_track_mood)[0]
        comp["mood"] = minmax(raw["mood"])

    # -- Contexte d'écoute
    if q.contexts:
        C = np.vstack([ref.E_ctx_blocks[c].mean(axis=0) for c in q.contexts if c in ref.E_ctx_blocks])
        raw["context"] = cosine_matrix(_l2_normalize(C), ref.E_track_ctx).max(axis=0)
        comp["context"] = minmax(raw["context"])

    # -- Genre (préférence déclarée)
    if q.genres_liked:
        comp["genre"] = df["genre"].isin(q.genres_liked).map({True: 1.0, False: 0.4}).to_numpy()

    # -- Artistes favoris : similarité de contenu avec leurs morceaux du catalogue
    fav_keys = {normalize_key(a) for a in q.artists}
    fav_idx = np.where(df["artist"].map(normalize_key).isin(fav_keys))[0]
    if len(fav_idx):
        A = cosine_matrix(ref.E_track_full[fav_idx], ref.E_track_full)   # (n_fav, n)
        A[np.arange(len(fav_idx)), fav_idx] = -1          # on ignore l'auto-similarité
        raw["artist"] = A.max(axis=0)
        comp["artist"] = minmax(raw["artist"])
        comp["artist"][fav_idx] = 1.0                     # morceau d'un artiste suivi

    # -- Énergie (Likert 1-5)
    if q.energy_target is not None:
        comp["energy"] = 1 - np.abs(df["energy"].to_numpy() - q.energy_target) / 4

    # -- A priori personnalité (faible)
    if q.personality:
        prior = genre_personality_prior(ref, q.personality)
        comp["personality"] = df["genre"].map(prior).to_numpy(dtype=float)

    # -- Agrégation pondérée sur les composantes actives (poids renormalisés)
    active = [k for k in comp if weights.get(k, 0) > 0]
    total_w = sum(weights[k] for k in active)
    score = sum(weights[k] * comp[k] for k in active) / total_w if active else np.zeros(n)

    out = df[["track_id", "title", "artist", "genre", "mood", "context", "energy",
              "description", "keyword_list"]].copy()
    for k in active:
        out[f"c_{k}"] = comp[k]
        out[f"w_{k}"] = weights[k] / total_w
    for k, v in raw.items():
        out[f"raw_{k}"] = v
        out[f"cal_{k}"] = calibrate(v, enc.name)
    out["score"] = score

    # -- Contraintes dures : genres refusés, morceaux exclus
    mask = ~out["genre"].isin(q.genres_disliked) & ~out["track_id"].isin(q.exclude_track_ids)
    return out[mask].sort_values("score", ascending=False).reset_index(drop=True)


def top_k(scored: pd.DataFrame, k: int = 3, max_per_artist: int = config.MAX_PER_ARTIST) -> pd.DataFrame:
    """Sélection diversifiée : au plus `max_per_artist` morceaux par artiste."""
    picked, count = [], {}
    for i, row in scored.iterrows():
        if count.get(row.artist, 0) < max_per_artist:
            picked.append(i)
            count[row.artist] = count.get(row.artist, 0) + 1
        if len(picked) == k:
            break
    return scored.loc[picked].reset_index(drop=True)
