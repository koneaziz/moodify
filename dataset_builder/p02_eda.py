"""PHASE 2 — EXPLORATION INITIALE (EDA)
Statistiques et figures sur les données brutes, avant tout nettoyage.
Sorties : reports/eda/*.png + reports/eda/eda_summary.json
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402
from .lexicon import GENRE_TO_MACRO, MOOD_GENRES  # noqa: E402
from .utils import load_interim, log, phase_timer, report, save_json  # noqa: E402

AUDIO = ["danceability", "energy", "valence", "acousticness", "instrumentalness",
         "speechiness", "liveness", "tempo", "loudness"]
OUT = config.REPORTS / "eda"


def run() -> None:
    with phase_timer("P02 EDA"):
        OUT.mkdir(parents=True, exist_ok=True)
        df = load_interim("p01_spotify_raw")

        summary = {
            "rows": len(df),
            "columns": list(df.columns),
            "missing_values": {k: int(v) for k, v in df.isna().sum().items() if v},
            "duplicate_track_id_rows": int(df.duplicated("track_id").sum()),
            "unique_track_ids": int(df["track_id"].nunique()),
            "duplicate_artist_title_rows": int(df.duplicated(["artists", "track_name"]).sum()),
            "n_genres": int(df["track_genre"].nunique()),
            "genres": sorted(df["track_genre"].dropna().unique().tolist()),
            "genres_not_in_mapping": sorted(set(df["track_genre"].dropna()) - set(GENRE_TO_MACRO)
                                           - config.EXCLUDED_GENRES),
            "mood_like_genres_found": sorted(set(df["track_genre"]) & set(MOOD_GENRES)),
            "popularity": df["popularity"].describe().round(2).to_dict(),
            "duration_min": (df["duration_ms"] / 60000).describe().round(2).to_dict(),
            "audio_features": df[AUDIO].describe().round(3).to_dict(),
        }
        save_json(summary, OUT / "eda_summary.json")

        # --- Figures
        fig, ax = plt.subplots(figsize=(10, 22))
        df["track_genre"].value_counts().sort_values().plot.barh(ax=ax, color="#5B8DEF")
        ax.set_title("Nombre de morceaux par genre Spotify (brut)")
        fig.tight_layout(); fig.savefig(OUT / "genres_bruts.png", dpi=110); plt.close(fig)

        fig, axes = plt.subplots(3, 3, figsize=(13, 10))
        for ax, col in zip(axes.flat, AUDIO):
            ax.hist(df[col].dropna(), bins=40, color="#7C5CFF", alpha=.85)
            ax.set_title(col)
        fig.suptitle("Distribution des caractéristiques audio"); fig.tight_layout()
        fig.savefig(OUT / "audio_features.png", dpi=110); plt.close(fig)

        fig, ax = plt.subplots(figsize=(9, 7))
        corr = df[AUDIO + ["popularity"]].corr()
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr)), corr.columns, rotation=60, ha="right")
        ax.set_yticks(range(len(corr)), corr.columns)
        fig.colorbar(im); ax.set_title("Corrélations"); fig.tight_layout()
        fig.savefig(OUT / "correlations.png", dpi=110); plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 7))
        s = df.sample(min(len(df), 8000), random_state=0)
        ax.scatter(s["valence"], s["energy"], s=3, alpha=.3, color="#E4572E")
        ax.axhline(.5, color="grey", lw=.8); ax.axvline(.5, color="grey", lw=.8)
        for (x, y, t) in [(.75, .95, "joyeux / euphorique"), (.05, .95, "rageur / tendu"),
                          (.05, .02, "triste / mélancolique"), (.75, .02, "calme / serein")]:
            ax.text(x, y, t, fontsize=9, weight="bold")
        ax.set_xlabel("valence"); ax.set_ylabel("energy")
        ax.set_title("Quadrant de Russell (valence × énergie)")
        fig.tight_layout(); fig.savefig(OUT / "quadrant_russell.png", dpi=110); plt.close(fig)

        if summary["genres_not_in_mapping"]:
            log.warning("  genres absents de GENRE_TO_MACRO (seront ignorés) : %s",
                        summary["genres_not_in_mapping"])
        log.info("  %d lignes, %d track_id uniques, %d genres",
                 summary["rows"], summary["unique_track_ids"], summary["n_genres"])
        report("P02_eda", **{k: summary[k] for k in ("rows", "unique_track_ids", "n_genres",
                                                     "duplicate_track_id_rows", "missing_values",
                                                     "genres_not_in_mapping")})
