"""PHASE 13 — STRUCTURATION FINALE (data/processed/)

Tables produites :
 - tracks.csv          : catalogue final (compatible avec le moteur src/moodify)
 - artists.csv         : 1 ligne par artiste (genres, popularité, tags, biographie)
 - genre_mapping.csv   : genre Spotify -> macro-genre
 - track_tags.csv      : table longue morceau × tag (source, catégorie, poids)
 - data_dictionary.csv : description de chaque colonne
Champs multi-valués séparés par « | ».
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from . import config
from .lexicon import GENRE_TO_MACRO
from .utils import load_interim, log, phase_timer, report

J = "|".join

DICTIONARY = [
    ("track_id", "str", "Spotify", "Identifiant Spotify du morceau"),
    ("title", "str", "Spotify (nettoyé)", "Titre sans mentions de version (Remastered, feat...)"),
    ("artist", "str", "Spotify", "Artiste principal"),
    ("featured_artists", "liste", "Spotify", "Artistes invités"),
    ("album", "str", "Spotify", "Album"),
    ("genre", "str", "Construit (P03)", "Macro-genre du projet (14 valeurs)"),
    ("spotify_genres", "liste", "Spotify", "Genres Spotify d'origine (après fusion des doublons)"),
    ("mood", "liste", "Construit (P10)", "Humeurs en français : tags humains puis quadrant audio"),
    ("context", "liste", "Construit (P10)", "Contextes d'écoute : tags humains puis règles audio"),
    ("mood_blocks", "liste", "Construit (P10)", "Blocs d'humeur de blocks.json couverts"),
    ("context_blocks", "liste", "Construit (P10)", "Blocs de contexte couverts"),
    ("energy", "int 1-5", "Construit (P09)", "Niveau d'énergie (Spotify energy × 5, arrondi sup.)"),
    ("language", "str", "Construit", "Langue présumée (instrumental / français / inconnu)"),
    ("description", "texte", "Généré (P11)", "Description en français, texte comparé par SBERT"),
    ("keywords", "liste", "Construit (P10)", "Mots-clés (attributs, genres, tempo, humeurs)"),
    ("popularity", "int 0-100", "Spotify", "Popularité"),
    ("explicit", "bool", "Spotify", "Paroles explicites"),
    ("danceability|energy_raw|valence|acousticness|instrumentalness|speechiness|tempo", "float",
     "Spotify", "Caractéristiques audio brutes"),
    ("valence_final|arousal_final", "float 0-1", "Construit (P09)", "Moyenne Spotify + MuSe si disponible"),
    ("russell_quadrant", "str", "Construit (P09)", "Quadrant valence × énergie"),
    ("tags_mood_human", "liste", "Last.fm / MuSe / Spotify", "Tags d'humeur humains (français)"),
    ("mood_source", "str", "Construit", "humain | humain+audio | audio"),
    ("description_source", "str", "Construit", "template_tags | template_audio | llm"),
    ("match_method", "str", "P06", "Méthode de jointure avec MuSe"),
    ("in_gold", "bool", "P04", "Morceau présent dans le jeu gold rédigé à la main"),
    ("conflict", "bool", "P12", "Incohérence détectée entre tags humains et audio"),
]


def run() -> None:
    with phase_timer("P13 Structuration finale"):
        df = load_interim("p12_quality")
        out = config.PROCESSED

        language = ["instrumental" if i else "français" if g == "Chanson française" else "inconnu"
                    for i, g in zip(df["is_instrumental"], df["macro_genre"])]
        tracks = pd.DataFrame({
            "track_id": df["track_id"], "title": df["title"], "artist": df["artist"],
            "genre": df["macro_genre"], "mood": df["mood_list"].map(J),
            "context": df["context_list"].map(J), "energy": df["energy_level"],
            "language": language, "description": df["description"],
            "keywords": df["keyword_list"].map(J),
            # --- colonnes complémentaires
            "featured_artists": df["featured_artists"].map(J), "album": df["album"],
            "spotify_genres": df["spotify_genres"].map(J),
            "mood_blocks": df["mood_blocks"].map(J), "context_blocks": df["context_blocks"].map(J),
            "popularity": df["popularity"], "explicit": df["explicit"],
            "danceability": df["danceability"], "energy_raw": df["energy"], "valence": df["valence"],
            "acousticness": df["acousticness"], "instrumentalness": df["instrumentalness"],
            "speechiness": df["speechiness"], "tempo": df["tempo"].round(1),
            "valence_final": df["valence_final"].round(3), "arousal_final": df["arousal_final"].round(3),
            "russell_quadrant": df["russell_quadrant"], "tags_mood_human": df["tags_mood"].map(J),
            "mood_source": df["mood_source"], "description_source": df["description_source"],
            "match_method": df["match_method"], "in_gold": df["in_gold"], "conflict": df["conflict"],
        })
        tracks.to_csv(out / "tracks.csv", index=False)

        # artists
        tags = load_interim("track_tags")
        tag_by_track = tags[tags["category"].isin(["mood", "context", "genre", "attribute"])] \
            .groupby("track_id")["tag_fr"].agg(list)
        rows = []
        for i, (name, g) in enumerate(df.groupby("artist")):
            tcount = Counter(t for tid in g["track_id"] for t in tag_by_track.get(tid, []))
            rows.append({
                "artist_id": f"A{i + 1:05d}", "artist": name,
                "genres": J(g["macro_genre"].value_counts().index), "n_tracks": len(g),
                "popularity_mean": round(g["popularity"].mean(), 1),
                "top_tags": J(t for t, _ in tcount.most_common(8)),
                "moods": J(pd.Series([m for l in g["mood_list"] for m in l]).value_counts().index[:6]),
                "bio": (g["artist_bio"].dropna().iloc[0] if "artist_bio" in g and g["artist_bio"].notna().any() else ""),
            })
        artists = pd.DataFrame(rows)
        artists.to_csv(out / "artists.csv", index=False)

        pd.DataFrame(sorted(GENRE_TO_MACRO.items()), columns=["spotify_genre", "macro_genre"]) \
            .to_csv(out / "genre_mapping.csv", index=False)
        tags[tags["track_id"].isin(df["track_id"])].to_csv(out / "track_tags.csv", index=False)
        pd.DataFrame(DICTIONARY, columns=["colonne", "type", "source", "description"]) \
            .to_csv(out / "data_dictionary.csv", index=False)

        log.info("  tracks.csv %d | artists.csv %d | track_tags.csv %d", len(tracks), len(artists), len(tags))
        report("P13_structure", tracks=len(tracks), artists=len(artists), track_tags=len(tags))
