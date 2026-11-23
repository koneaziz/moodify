"""PHASE 9 — CONVERSION DES CARACTÉRISTIQUES AUDIO EN TEXTE

Les nombres Spotify ne sont pas comparables sémantiquement à une phrase utilisateur :
on les traduit en LIBELLÉS français, qui alimenteront les descriptions (phase 11).

 9.1 Discrétisation par seuils (config.py) : énergie, tempo, acoustique, instrumental, rap, dansant
 9.2 Quadrant de Russell valence × énergie -> humeur « audio »
     (si MuSe fournit valence / arousal humains, on les moyenne avec Spotify : plus fiable)
 9.3 Niveau d'énergie 1-5 (attribut structuré pour la question Likert du quiz)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .utils import load_interim, log, phase_timer, report, save_interim


def energy_label(e: float) -> str:
    b = config.ENERGY_BINS
    return "calme" if e < b[0] else "modéré" if e < b[1] else "énergique" if e < b[2] else "très énergique"


def tempo_label(t: float) -> str:
    return "lent" if t < config.TEMPO_BINS[0] else "modéré" if t < config.TEMPO_BINS[1] else "rapide"


def russell(valence: float, arousal: float) -> tuple[str, list[str]]:
    """Quadrant + humeurs associées (modèle circomplexe de Russell, 1980)."""
    hi_v, hi_a = valence >= config.VALENCE_SPLIT, arousal >= config.ENERGY_SPLIT
    if hi_v and hi_a:
        return "joyeux-énergique", ["joyeux", "entraînant"]
    if not hi_v and hi_a:
        return "tendu-intense", ["intense", "tendu"]
    if not hi_v and not hi_a:
        return "triste-calme", ["mélancolique", "introspectif"]
    return "serein-calme", ["calme", "serein"]


def run() -> None:
    with phase_timer("P09 Audio → texte"):
        df = load_interim("p08_tags")

        # 9.1
        df["lbl_energy"] = df["energy"].map(energy_label)
        df["lbl_tempo"] = df["tempo"].map(tempo_label)
        df["lbl_acoustic"] = np.select(
            [df["acousticness"] >= config.ACOUSTIC_HIGH, df["acousticness"] <= config.ACOUSTIC_LOW],
            ["acoustique", "électronique / produit"], default="mixte")
        df["is_instrumental"] = df["instrumentalness"] >= config.INSTRUMENTAL_THRESHOLD
        df["lbl_vocals"] = np.where(df["is_instrumental"], "instrumental",
                                    np.where(df["speechiness"] >= config.SPEECHINESS_RAP,
                                             "très parlé / rappé", "chanté"))
        df["is_danceable"] = df["danceability"] >= config.DANCEABILITY_HIGH

        # 9.2 Valence / arousal combinés (Spotify + MuSe si disponible)
        mv = pd.to_numeric(df.get("muse_valence"), errors="coerce")
        ma = pd.to_numeric(df.get("muse_arousal"), errors="coerce")
        df["valence_final"] = np.where(mv.notna(), (df["valence"] + mv) / 2, df["valence"])
        df["arousal_final"] = np.where(ma.notna(), (df["energy"] + ma) / 2, df["energy"])
        q = [russell(v, a) for v, a in zip(df["valence_final"], df["arousal_final"])]
        df["russell_quadrant"] = [x[0] for x in q]
        df["audio_moods"] = [x[1] for x in q]

        # 9.3
        df["energy_level"] = np.clip(np.ceil(df["energy"] * 5), 1, 5).astype(int)

        save_interim(df, "p09_audio_text")
        dist = df["russell_quadrant"].value_counts().to_dict()
        log.info("  quadrants : %s", dist)
        report("P09_audio_to_text", russell_quadrants=dist,
               instrumental_share=round(float(df["is_instrumental"].mean()), 3),
               muse_va_used=int(mv.notna().sum()))
