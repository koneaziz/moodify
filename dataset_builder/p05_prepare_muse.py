"""PHASE 5 — PRÉPARATION DE MuSe

 5.1 Les tags d'émotion (« seeds ») sont stockés en texte "['sad', 'mellow']" -> vraie liste
 5.2 Nettoyage des spotify_id (valeurs vides, espaces, préfixes 'spotify:track:')
 5.3 Normalisation des scores valence / arousal / dominance de [1, 9] (échelle ANEW) vers [0, 1]
 5.4 Clé de jointure normalisée artiste + titre
"""
from __future__ import annotations

import pandas as pd

from .utils import load_interim, log, parse_list_cell, phase_timer, report, save_interim, track_key
from . import config


def _scale_1_9(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return ((s - 1) / 8).clip(0, 1)


def run() -> None:
    with phase_timer("P05 Préparation MuSe"):
        path = config.INTERIM / "p01_muse_raw.parquet"
        if not path.exists():
            log.warning("  MuSe absent → phase sautée")
            report("P05_prepare_muse", skipped=True)
            return
        mu = load_interim("p01_muse_raw")
        n0 = len(mu)

        mu = mu.dropna(subset=["track", "artist"])
        mu["muse_seeds"] = mu.get("seeds", pd.Series([[]] * len(mu))).map(parse_list_cell)
        mu["muse_seeds"] = mu["muse_seeds"].map(lambda l: [t.lower().strip() for t in l if t])

        if "spotify_id" in mu.columns:
            mu["spotify_id"] = (mu["spotify_id"].astype(str).str.strip()
                                .str.replace("spotify:track:", "", regex=False)
                                .replace({"nan": None, "": None, "None": None}))
        else:
            mu["spotify_id"] = None

        for col in ("valence_tags", "arousal_tags", "dominance_tags"):
            mu[f"muse_{col.split('_')[0]}"] = _scale_1_9(mu[col]) if col in mu.columns else None
        mu["muse_genre"] = mu.get("genre")
        mu["track_key"] = [track_key(a, t) for a, t in zip(mu["artist"], mu["track"])]
        mu = mu.drop_duplicates("track_key")

        keep = ["track", "artist", "spotify_id", "track_key", "muse_seeds", "muse_valence",
                "muse_arousal", "muse_dominance", "muse_genre"]
        mu = mu[[c for c in keep if c in mu.columns]].reset_index(drop=True)
        save_interim(mu, "p05_muse_clean")
        n_ids = int(mu["spotify_id"].notna().sum())
        log.info("  MuSe : %d → %d lignes, %d avec spotify_id (%.0f %%)", n0, len(mu), n_ids,
                 100 * n_ids / max(1, len(mu)))
        report("P05_prepare_muse", rows_in=n0, rows_out=len(mu), with_spotify_id=n_ids)
