"""Chargement du jeu de données de référence et pré-calcul des embeddings.

Pour chaque morceau, on construit plusieurs « vues » textuelles, chacune comparée
à la partie correspondante du profil utilisateur :

- ``text_full``    : vue globale (titre, artiste, genre, ambiance, contexte, description, mots-clés)
- ``text_mood``    : vue humeur (tags d'humeur + description)
- ``text_context`` : vue contexte d'écoute
Séparer les vues permet un scoring par critère (humeur, contexte...) et donc des
explications claires : on sait *quel* critère a fait remonter un morceau.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .embeddings import Encoder, TfidfEncoder, Word2VecEncoder
from .preprocessing import split_tags

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_tracks(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "tracks.csv", dtype=str).fillna("")
    df["energy"] = df["energy"].astype(int)
    df["mood_tags"] = df["mood"].map(split_tags)
    df["context_tags"] = df["context"].map(split_tags)
    df["keyword_list"] = df["keywords"].map(split_tags)
    df["text_full"] = df.apply(
        lambda r: (f"{r.title} de {r.artist}. Genre : {r.genre}. "
                   f"Ambiance : {', '.join(r.mood_tags)}. "
                   f"À écouter pour : {', '.join(r.context_tags)}. "
                   f"{r.description} Mots-clés : {', '.join(r.keyword_list)}."), axis=1)
    df["text_mood"] = df.apply(
        lambda r: f"Ambiance {', '.join(r.mood_tags)}. {r.description}", axis=1)
    df["text_context"] = df.apply(
        lambda r: f"Idéal pour : {', '.join(r.context_tags)}.", axis=1)
    return df


def load_communities(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "communities.csv", dtype=str).fillna("")
    for col in ("genres", "moods", "contexts"):
        df[col + "_list"] = df[col].map(split_tags)
    df["text_full"] = df["name"] + ". " + df["description"]
    return df


@dataclass
class ReferenceIndex:
    """Toutes les données de référence + leurs embeddings pré-calculés."""

    encoder: Encoder
    data_dir: Path = DATA_DIR
    tracks: pd.DataFrame = field(init=False)
    communities: pd.DataFrame = field(init=False)
    concerts: pd.DataFrame = field(init=False)
    cities: pd.DataFrame = field(init=False)
    blocks: dict = field(init=False)
    archetypes: list = field(init=False)
    personality_map: dict = field(init=False)
    questionnaire: dict = field(init=False)

    def __post_init__(self) -> None:
        d = Path(self.data_dir)
        self.tracks = load_tracks(d)
        self.communities = load_communities(d)
        self.concerts = pd.read_csv(d / "concerts_simules.csv", dtype=str)
        self.cities = pd.read_csv(d / "cities.csv").set_index("city")
        self.blocks = _read_json(d / "blocks.json")
        self.archetypes = _read_json(d / "archetypes.json")["archetypes"]
        self.personality_map = _read_json(d / "personality_music.json")["dimensions"]
        self.questionnaire = _read_json(d / "questionnaire.json")

        # Les baselines (TF-IDF, Word2Vec entraîné) doivent apprendre leur vocabulaire
        # sur le corpus de référence avant tout encodage.
        if isinstance(self.encoder, TfidfEncoder) or (
                isinstance(self.encoder, Word2VecEncoder) and self.encoder.kv is None):
            self.encoder.fit(self.corpus())

        enc = self.encoder.encode
        self.E_track_full = enc(self.tracks["text_full"].tolist())
        self.E_track_mood = enc(self.tracks["text_mood"].tolist())
        self.E_track_ctx = enc(self.tracks["text_context"].tolist())
        self.E_comm = enc(self.communities["text_full"].tolist())
        # Un vecteur prototype (centroïde) par bloc d'humeur / de contexte / émotion
        self.mood_block_names = list(self.blocks["mood_blocks"])
        self.ctx_block_names = list(self.blocks["context_blocks"])
        self.emotion_names = [k for k in self.blocks["emotions"] if not k.startswith("_")]
        self.E_mood_blocks = {b: enc(p) for b, p in self.blocks["mood_blocks"].items()}
        self.E_ctx_blocks = {b: enc(p) for b, p in self.blocks["context_blocks"].items()}
        self.E_emotions = {e: enc(self.blocks["emotions"][e]) for e in self.emotion_names}
        self.genres = sorted(self.tracks["genre"].unique())

    def corpus(self) -> list[str]:
        """Tous les textes de référence (pour entraîner les baselines)."""
        texts = (self.tracks["text_full"].tolist() + self.communities["text_full"].tolist())
        for group in ("mood_blocks", "context_blocks"):
            for phrases in self.blocks[group].values():
                texts += phrases
        for k, phrases in self.blocks["emotions"].items():
            if not k.startswith("_"):
                texts += phrases
        return texts

    def artist_tracks(self, artist: str) -> pd.DataFrame:
        from .preprocessing import normalize_key

        key = normalize_key(artist)
        return self.tracks[self.tracks["artist"].map(normalize_key) == key]

    def coords(self, city: str) -> tuple[float, float] | None:
        if city in self.cities.index:
            row = self.cities.loc[city]
            return float(row.lat), float(row.lon)
        return None
