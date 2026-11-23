"""Module NLP de Moodify : similarité sémantique entre les réponses de l'utilisateur et les
descriptions des morceaux.

Correspondance avec le sujet (« Analyse NLP attendue », Thème 4) :
  • « Extraire les représentations sémantiques des préférences des utilisateurs »
        -> encode_user() : prétraitement + embeddings de chaque phrase de l'utilisateur
  • « Comparer les descriptions des utilisateurs avec celles des morceaux »
        -> similarity() / rank() : similarité cosinus avec CHAQUE morceau, sur plusieurs vues
  • « Calculer l'affinité liée à l'humeur et au genre musical »
        -> mood_affinity() (blocs d'humeur) et genre_affinity() (centroïdes de genre)
  • « Classer les morceaux pertinents »  -> rank()

Utilisation :
    from moodify.semantic import SemanticMatcher
    sm = SemanticMatcher()                                 # SBERT multilingue par défaut
    top = sm.rank("je suis énervée, je veux une musique calme", k=10)
    sm.mood_affinity(["J'écoute du lofi pour réviser"])
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .embeddings import Encoder, TfidfEncoder, Word2VecEncoder, cosine_matrix, get_encoder
from .preprocessing import preprocess_semantic, split_tags

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "moodify_dataset.csv"
BLOCKS = ROOT / "data" / "blocks.json"
CACHE = ROOT / "data" / "cache" / "embeddings"

# Poids des vues dans le score sémantique combiné (justifiés dans le notebook 02) :
# la vue globale porte le sens général ; la vue humeur cible la promesse du produit ;
# la vue contexte affine (étude, sport...).
VIEW_WEIGHTS = {"full": 0.5, "mood": 0.3, "context": 0.2}


def _join(v) -> str:
    return ", ".join(split_tags(v)) if isinstance(v, str) else ""


def build_views(df: pd.DataFrame) -> dict[str, list[str]]:
    """Construit 3 textes par morceau, chacun comparé aux phrases de l'utilisateur.
    - full    : tout ce qui décrit le morceau (sens global)
    - mood    : humeurs + description (ce que l'on ressent)
    - context : contextes d'écoute (quand l'écouter)"""
    full, mood, ctx = [], [], []
    for r in df.itertuples():
        full.append(f"{r.title} de {r.artist}. Genre : {r.genre} ({_join(r.sub_genres)}). "
                    f"Ambiance : {_join(r.mood)}. À écouter pour : {_join(r.context)}. "
                    f"{r.description} Mots-clés : {_join(r.keywords)}.")
        mood.append(f"Ambiance {_join(r.mood)}. {r.description}")
        ctx.append(f"Idéal pour : {_join(r.context)}.")
    return {"full": full, "mood": mood, "context": ctx}


class SemanticMatcher:
    def __init__(self, encoder: str | Encoder = "sbert", dataset: Path | str = DATASET,
                 blocks: Path | str = BLOCKS, use_cache: bool = True):
        self.tracks = pd.read_csv(dataset, dtype={"track_id": str}).fillna({
            "sub_genres": "", "mood": "", "context": "", "keywords": "", "description": ""})
        self.blocks = json.loads(Path(blocks).read_text(encoding="utf-8"))
        self.views = build_views(self.tracks)
        self.encoder = get_encoder(encoder) if isinstance(encoder, str) else encoder
        # Les baselines (TF-IDF, Word2Vec, fastText entraînés) apprennent leur vocabulaire ici
        if isinstance(self.encoder, TfidfEncoder) or (
                isinstance(self.encoder, Word2VecEncoder) and self.encoder.kv is None):
            self.encoder.fit(self.views["full"] + self._block_phrases())
        self.use_cache = use_cache and self.encoder.name == "sbert"
        self.E = {v: self._encode_cached(v, texts) for v, texts in self.views.items()}
        self.mood_blocks = {b: self.encoder.encode(p) for b, p in self.blocks["mood_blocks"].items()}
        self.ctx_blocks = {b: self.encoder.encode(p) for b, p in self.blocks["context_blocks"].items()}

    # ------------------------------------------------------------------ interne
    def _block_phrases(self) -> list[str]:
        return [p for g in ("mood_blocks", "context_blocks") for ps in self.blocks[g].values() for p in ps]

    def _encode_cached(self, view: str, texts: list[str]) -> np.ndarray:
        """Les embeddings du catalogue sont calculés une fois puis stockés sur disque (.npy)."""
        if not self.use_cache:
            return self.encoder.encode(texts)
        key = hashlib.md5(("\n".join(texts) + getattr(self.encoder, "model_name", "")).encode()).hexdigest()[:12]
        path = CACHE / f"{view}_{key}.npy"
        if path.exists():
            return np.load(path)
        E = self.encoder.encode(texts)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(path, E)
        return E

    # ------------------------------------------------------- 1. représentation
    def encode_user(self, answers) -> tuple[list[str], np.ndarray]:
        """Réponses libres (texte, liste ou dict {question: réponse}) -> phrases + embeddings.
        Chaque réponse est découpée en phrases : une phrase = une intention."""
        if isinstance(answers, str):
            answers = [answers]
        elif isinstance(answers, dict):
            answers = [a for a in answers.values() if isinstance(a, str) and a.strip()]
        sentences = [s for a in answers for s in preprocess_semantic(a)]
        return sentences, self.encoder.encode(sentences)

    # ------------------------------------------------------ 2. similarité
    def similarity_matrix(self, answers, view: str = "full") -> tuple[list[str], np.ndarray]:
        """Matrice cosinus (phrases utilisateur × morceaux) pour une vue."""
        sents, U = self.encode_user(answers)
        return sents, cosine_matrix(U, self.E[view])

    def similarity(self, answers, view: str = "full") -> np.ndarray:
        """Score par morceau : ½ moyenne + ½ max sur les phrases de l'utilisateur.
        - la moyenne mesure l'accord avec TOUT ce qu'a dit l'utilisateur,
        - le max évite qu'un morceau parfait pour UNE phrase soit noyé par les autres."""
        _, S = self.similarity_matrix(answers, view)
        return 0.5 * S.mean(axis=0) + 0.5 * S.max(axis=0)

    def semantic_score(self, answers, weights: dict[str, float] = VIEW_WEIGHTS) -> np.ndarray:
        """Score sémantique combiné sur les vues (pondération VIEW_WEIGHTS)."""
        tot = sum(weights.values())
        return sum(w * self.similarity(answers, v) for v, w in weights.items()) / tot

    # ---------------------------------------------------------- 3. classement
    def rank(self, answers, k: int = 10, weights: dict[str, float] = VIEW_WEIGHTS) -> pd.DataFrame:
        sents, U = self.encode_user(answers)
        out = self.tracks[["track_id", "title", "artist", "genre", "mood", "context"]].copy()
        total = 0
        for v, w in weights.items():
            S = cosine_matrix(U, self.E[v])
            out[f"cos_{v}"] = 0.5 * S.mean(axis=0) + 0.5 * S.max(axis=0)
            total = total + w * out[f"cos_{v}"]
            if v == "full":   # phrase de l'utilisateur la plus proche (pour l'explication)
                out["best_user_sentence"] = [sents[i] for i in S.argmax(axis=0)]
        out["semantic_score"] = total / sum(weights.values())
        return out.sort_values("semantic_score", ascending=False).head(k).reset_index(drop=True)

    # --------------------------------------------- 4. affinités humeur / genre
    def mood_affinity(self, answers) -> dict[str, float]:
        """Affinité avec chaque bloc d'humeur (formule du sujet : moyenne des max par phrase,
        combinée au max global)."""
        _, U = self.encode_user(answers)
        out = {}
        for b, P in self.mood_blocks.items():
            best = cosine_matrix(U, P).max(axis=1)
            out[b] = float(0.5 * best.mean() + 0.5 * best.max())
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def context_affinity(self, answers) -> dict[str, float]:
        _, U = self.encode_user(answers)
        out = {b: float(cosine_matrix(U, P).max()) for b, P in self.ctx_blocks.items()}
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def genre_affinity(self, answers) -> dict[str, float]:
        """Cosinus entre l'utilisateur et le centroïde des morceaux de chaque genre."""
        _, U = self.encode_user(answers)
        u = U.mean(axis=0)
        u /= np.linalg.norm(u) + 1e-9
        out = {}
        for g, idx in self.tracks.groupby("genre").groups.items():
            c = self.E["full"][list(idx)].mean(axis=0)
            out[g] = float(u @ (c / (np.linalg.norm(c) + 1e-9)))
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def matched_keywords(self, track_id: str, answers, n: int = 3) -> list[tuple[str, float]]:
        """Mots-clés / humeurs du morceau les plus proches de la demande (pour expliquer)."""
        r = self.tracks[self.tracks["track_id"] == track_id].iloc[0]
        words = list(dict.fromkeys(split_tags(r["mood"]) + split_tags(r["keywords"])))
        if not words:
            return []
        _, U = self.encode_user(answers)
        sims = cosine_matrix(self.encoder.encode(words), U).max(axis=1)
        order = np.argsort(-sims)[:n]
        return [(words[i], round(float(sims[i]), 3)) for i in order]
