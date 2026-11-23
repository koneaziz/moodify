"""PHASE 4 — ÉCHANTILLONNAGE STRATIFIÉ

Pourquoi : 100k+ morceaux, c'est trop pour les appels Last.fm et pour une démo fluide.
Méthode :
 - par macro-genre, on garde les N morceaux les plus populaires,
 - au plus MAX_TRACKS_PER_ARTIST morceaux par artiste (diversité),
 - les morceaux du jeu gold présents dans Spotify sont toujours inclus (pour l'évaluation).
"""
from __future__ import annotations

import pandas as pd

from . import config
from .utils import load_interim, log, phase_timer, report, save_interim, track_key


def run() -> None:
    with phase_timer("P04 Échantillonnage"):
        df = load_interim("p03_spotify_clean")
        gold = pd.read_csv(config.GOLD_TRACKS)
        gold_keys = {track_key(a, t) for a, t in zip(gold["artist"], gold["title"])}
        df["in_gold"] = df["track_key"].isin(gold_keys)

        parts = []
        for macro, g in df.groupby("macro_genre"):
            g = g.sort_values("popularity", ascending=False)
            g = g.groupby("artist", group_keys=False).head(config.MAX_TRACKS_PER_ARTIST)
            parts.append(g.head(config.TRACKS_PER_MACRO_GENRE))
        sample = pd.concat(parts + [df[df["in_gold"]]]).drop_duplicates("track_id")
        sample = sample.sample(frac=1, random_state=config.SAMPLE_SEED).reset_index(drop=True)

        save_interim(sample, "p04_sample")
        counts = sample["macro_genre"].value_counts()
        log.info("  échantillon : %d morceaux, %d artistes, %d morceaux gold retrouvés",
                 len(sample), sample["artist"].nunique(), int(sample["in_gold"].sum()))
        small = counts[counts < config.TRACKS_PER_MACRO_GENRE * 0.5]
        if len(small):
            log.warning("  macro-genres sous-représentés : %s", small.to_dict())
        report("P04_sample", rows=len(sample), artists=int(sample["artist"].nunique()),
               gold_found=int(sample["in_gold"].sum()), per_macro_genre=counts.to_dict())
