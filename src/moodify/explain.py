"""Explications transparentes, générées par règles + modèles de phrases (sans LLM).

Pour chaque recommandation on expose :
- les critères qui contribuent le plus au score (w_k · C_k),
- les mots-clés du morceau les plus proches sémantiquement de la demande,
- une phrase d'explication construite à partir de ces éléments.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .embeddings import cosine_matrix
from .reference import ReferenceIndex
from .scoring import Query

CRITERIA_LABELS = {
    "semantic": "description proche de ce que tu as écrit",
    "mood": "ambiance en phase avec l'humeur recherchée",
    "context": "adapté à ton contexte d'écoute",
    "genre": "genre que tu as indiqué aimer",
    "artist": "proche des artistes que tu suis",
    "energy": "niveau d'énergie qui te correspond",
    "personality": "cohérent avec ton profil de personnalité",
}


def contributions(row: pd.Series) -> list[tuple[str, float]]:
    out = []
    for col in row.index:
        if col.startswith("c_"):
            k = col[2:]
            out.append((k, float(row[f"w_{k}"] * row[col])))
    return sorted(out, key=lambda kv: kv[1], reverse=True)


def matched_keywords(ref: ReferenceIndex, row: pd.Series, q: Query, n: int = 2) -> list[tuple[str, float]]:
    """Mots-clés du morceau les plus proches (cosinus) de la demande utilisateur."""
    query_texts = q.texts + q.mood_texts + list(q.target_blocks)
    kws = list(row["keyword_list"])
    if not query_texts or not kws:
        return []
    qv = ref.encoder.encode(query_texts)
    sims = cosine_matrix(ref.encoder.encode(kws), qv).max(axis=1)
    order = np.argsort(-sims)[:n]
    return [(kws[i], float(sims[i])) for i in order]


def explain(ref: ReferenceIndex, row: pd.Series, q: Query) -> dict:
    contrib = contributions(row)
    top = [k for k, v in contrib[:3] if v > 0]
    kws = matched_keywords(ref, row, q)
    parts = [CRITERIA_LABELS[k] for k in top[:2]]
    sentence = f"« {row.title} » de {row.artist} est recommandé car : " + " ; ".join(parts)
    if kws:
        sentence += f". Mots-clés les plus proches de ta demande : {', '.join(k for k, _ in kws)}"
    if "cal_semantic" in row:
        sentence += f" (similarité sémantique : {row.cal_semantic:.0%})"
    return {
        "track_id": row.track_id, "title": row.title, "artist": row.artist, "genre": row.genre,
        "score": round(float(row.score), 3),
        "semantic_similarity_raw": round(float(row.get("raw_semantic", np.nan)), 3),
        "criteria": [{"criterion": k, "label": CRITERIA_LABELS[k], "contribution": round(v, 3)}
                     for k, v in contrib],
        "matched_keywords": [{"keyword": k, "similarity": round(s, 3)} for k, s in kws],
        "explanation": sentence + ".",
    }
