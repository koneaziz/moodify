"""PHASE 3 — NETTOYAGE DU DATASET SPOTIFY

Étapes (chacune est comptée dans l'entonnoir du rapport) :
 3.1 Colonnes inutiles et valeurs manquantes
 3.2 Genres hors sujet (kids, comedy...)
 3.3 Doublons de track_id (même morceau listé sous plusieurs genres) -> 1 ligne + liste de genres
 3.4 Artiste principal / artistes invités
 3.5 Doublons de versions (Remastered, Live, feat...) -> on garde la plus populaire
 3.6 Filtres durée et popularité
 3.7 Macro-genre + extraction des « genres-humeurs » (chill, sad, study...) en tags
"""
from __future__ import annotations

import pandas as pd

from . import config
from .lexicon import GENRE_TO_MACRO, MACRO_PRIORITY, MOOD_GENRES
from .utils import clean_title, load_interim, log, phase_timer, report, save_interim, track_key


def pick_macro(genres: list[str]) -> str | None:
    macros = {GENRE_TO_MACRO[g] for g in genres if g in GENRE_TO_MACRO}
    for m in MACRO_PRIORITY:
        if m in macros:
            return m
    return None


def run() -> None:
    with phase_timer("P03 Nettoyage Spotify"):
        df = load_interim("p01_spotify_raw")
        funnel = {"0_brut": len(df)}

        # 3.1 Colonnes inutiles / valeurs manquantes
        df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])
        df = df.dropna(subset=["track_id", "track_name", "artists"])
        df["track_name"] = df["track_name"].astype(str).str.strip()
        df["artists"] = df["artists"].astype(str).str.strip()
        df = df[(df["track_name"] != "") & (df["artists"] != "")]
        funnel["1_sans_manquants"] = len(df)

        # 3.2 Genres hors sujet
        df = df[~df["track_genre"].isin(config.EXCLUDED_GENRES)]
        funnel["2_genres_exclus"] = len(df)

        # 3.3 Doublons de track_id -> agrégation des genres
        genres = df.groupby("track_id")["track_genre"].agg(lambda s: sorted(set(s)))
        df = df.drop_duplicates("track_id").drop(columns="track_genre").set_index("track_id")
        df["spotify_genres"] = genres
        df = df.reset_index()
        funnel["3_track_id_uniques"] = len(df)

        # 3.4 Artiste principal / invités (séparateur ';' dans le dataset Spotify)
        split = df["artists"].str.split(";")
        df["artist"] = split.str[0].str.strip()
        df["featured_artists"] = split.str[1:].map(lambda l: [a.strip() for a in l])
        df["title"] = df["track_name"].map(clean_title)
        df.loc[df["title"] == "", "title"] = df["track_name"]

        # 3.5 Doublons de versions : même artiste + même titre nettoyé
        df["track_key"] = [track_key(a, t) for a, t in zip(df["artist"], df["title"])]
        merged_genres = df.groupby("track_key")["spotify_genres"].agg(
            lambda s: sorted({g for lst in s for g in lst}))
        df = df.sort_values("popularity", ascending=False).drop_duplicates("track_key")
        df["spotify_genres"] = df["track_key"].map(merged_genres)
        funnel["4_versions_dedoublonnees"] = len(df)

        # 3.6 Filtres durée / popularité
        df = df[df["duration_ms"].between(config.MIN_DURATION_MS, config.MAX_DURATION_MS)]
        funnel["5_duree_ok"] = len(df)
        df = df[df["popularity"] >= config.MIN_POPULARITY]
        funnel["6_popularite_ok"] = len(df)

        # 3.7 Macro-genre + tags issus des genres-humeurs
        df["macro_genre"] = df["spotify_genres"].map(pick_macro)
        unmapped = df["macro_genre"].isna().sum()
        df = df.dropna(subset=["macro_genre"])
        funnel["7_macro_genre_ok"] = len(df)
        df["genre_mood_tags"] = df["spotify_genres"].map(
            lambda gs: sorted({m for g in gs for m in MOOD_GENRES.get(g, {}).get("mood", [])}))
        df["genre_context_tags"] = df["spotify_genres"].map(
            lambda gs: sorted({c for g in gs for c in MOOD_GENRES.get(g, {}).get("context", [])}))

        df["explicit"] = df["explicit"].astype(bool)
        df = df.rename(columns={"album_name": "album"}).drop(columns=["track_name", "artists"])
        save_interim(df.reset_index(drop=True), "p03_spotify_clean")

        log.info("  entonnoir : %s", funnel)
        log.info("  répartition macro-genres :\n%s", df["macro_genre"].value_counts().to_string())
        report("P03_clean_spotify", funnel=funnel, unmapped_genre_rows=int(unmapped),
               macro_genre_counts=df["macro_genre"].value_counts().to_dict())
