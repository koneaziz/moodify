"""PHASE 1 — COLLECTE
Vérifie la présence et le schéma des fichiers bruts, puis les charge sans les modifier.

Fichiers attendus dans data/raw/ :
- spotify_tracks.csv : https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
                       (fichier « dataset.csv » à renommer)
- muse_v3.csv        : https://zenodo.org/record/4281165 (muse_dataset.csv, à renommer)
                       ou la copie Kaggle « MuSe Music Sentiment Analysis »
Clé Last.fm (optionnelle mais recommandée) : variable d'environnement LASTFM_API_KEY.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .utils import log, phase_timer, report, save_interim

SPOTIFY_REQUIRED = ["track_id", "artists", "album_name", "track_name", "popularity", "duration_ms",
                    "explicit", "danceability", "energy", "key", "loudness", "mode", "speechiness",
                    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
                    "time_signature", "track_genre"]

# Les différentes copies de MuSe n'ont pas toujours les mêmes noms de colonnes
MUSE_ALIASES = {
    "track": ["track", "track_name", "title"],
    "artist": ["artist", "artists", "artist_name"],
    "seeds": ["seeds", "emotion_tags", "tags"],
    "valence_tags": ["valence_tags", "valence"],
    "arousal_tags": ["arousal_tags", "arousal"],
    "dominance_tags": ["dominance_tags", "dominance"],
    "spotify_id": ["spotify_id", "spotify_track_id"],
    "genre": ["genre"],
    "lastfm_url": ["lastfm_url"],
    "mbid": ["mbid"],
    "number_of_emotion_tags": ["number_of_emotion_tags"],
}


def _missing_file_message(path, url) -> str:
    return (f"\n✗ Fichier manquant : {path}\n  Téléchargez-le depuis {url}\n"
            f"  puis placez-le dans {config.RAW} sous le nom « {path.name} ».")


def load_spotify() -> pd.DataFrame:
    if not config.SPOTIFY_RAW.exists():
        raise FileNotFoundError(_missing_file_message(
            config.SPOTIFY_RAW, "https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset"))
    df = pd.read_csv(config.SPOTIFY_RAW)
    missing = [c for c in SPOTIFY_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes Spotify manquantes : {missing}")
    return df


def load_muse() -> pd.DataFrame | None:
    if not config.MUSE_RAW.exists():
        log.warning(_missing_file_message(config.MUSE_RAW, "Kaggle / Zenodo (MuSe)")
                    + "\n  → le pipeline continue SANS MuSe (moins de tags humains).")
        return None
    df = pd.read_csv(config.MUSE_RAW)
    rename = {}
    for target, options in MUSE_ALIASES.items():
        for o in options:
            if o in df.columns:
                rename[o] = target
                break
    df = df.rename(columns=rename)
    for col in ("track", "artist"):
        if col not in df.columns:
            raise ValueError(f"Colonne MuSe obligatoire absente : {col}")
    return df


def run() -> None:
    with phase_timer("P01 Collecte"):
        sp = load_spotify()
        log.info("  Spotify : %d lignes × %d colonnes", *sp.shape)
        save_interim(sp, "p01_spotify_raw")

        mu = load_muse()
        if mu is not None:
            log.info("  MuSe    : %d lignes × %d colonnes", *mu.shape)
            save_interim(mu, "p01_muse_raw")

        gold = pd.read_csv(config.GOLD_TRACKS)
        log.info("  Gold    : %d morceaux rédigés à la main", len(gold))
        log.info("  Last.fm : %s", "clé détectée" if config.LASTFM_API_KEY else "pas de clé (phase 7 sautée)")

        report("P01_collect", spotify_rows=len(sp), spotify_cols=sp.shape[1],
               muse_rows=None if mu is None else len(mu), gold_rows=len(gold),
               lastfm_key=bool(config.LASTFM_API_KEY))
