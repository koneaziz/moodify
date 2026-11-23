"""PHASE 12 — CONTRÔLE QUALITÉ

 12.1 Complétude : % de morceaux avec tags humains, humeur, contexte, description
 12.2 Équilibre : nb de morceaux par bloc d'humeur / de contexte / macro-genre
 12.3 Diversité des descriptions : cosinus moyen entre descriptions (embeddings)
      -> trop élevé = descriptions répétitives = mauvais pouvoir discriminant
 12.4 Cohérence : conflits entre tags humains et audio (ex. « triste » mais valence > 0.75)
 12.5 Échantillon de relecture humaine (reports/manual_review.csv)
 12.6 Comparaison avec le jeu gold (humeurs générées vs humeurs rédigées à la main)
Sortie : reports/quality_report.json + figures reports/quality/*.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402
from .utils import (get_encoder, load_interim, log, phase_timer, report, save_interim, save_json,  # noqa: E402
                    track_key)  # noqa: E402

OUT = config.REPORTS / "quality"


def run() -> None:
    with phase_timer("P12 Contrôle qualité"):
        OUT.mkdir(parents=True, exist_ok=True)
        df = load_interim("p11_descriptions")
        q: dict = {}

        # 12.1
        q["completude"] = {
            "tags_humains": round(float(df["has_human_tags"].mean()), 3),
            "humeur": round(float((df["mood_list"].map(len) > 0).mean()), 3),
            "contexte": round(float((df["context_list"].map(len) > 0).mean()), 3),
            "description": round(float((df["description_words"] >= 15).mean()), 3),
            "bio_artiste": round(float((df.get("artist_bio", pd.Series([""] * len(df))).fillna("") != "").mean()), 3),
        }

        # 12.2
        mb = df.explode("mood_blocks")["mood_blocks"].value_counts()
        cb = df.explode("context_blocks")["context_blocks"].value_counts()
        q["equilibre"] = {"blocs_humeur": mb.to_dict(), "blocs_contexte": cb.to_dict(),
                          "macro_genres": df["macro_genre"].value_counts().to_dict()}
        for name, s in (("blocs_humeur", mb), ("blocs_contexte", cb)):
            fig, ax = plt.subplots(figsize=(8, 4))
            s.sort_values().plot.barh(ax=ax, color="#2E86AB")
            ax.set_title(f"Morceaux par {name.replace('_', ' ')}")
            fig.tight_layout(); fig.savefig(OUT / f"{name}.png", dpi=110); plt.close(fig)

        # 12.3 diversité (sur un échantillon pour rester rapide)
        sample = df["description"].sample(min(len(df), 500), random_state=0).tolist()
        enc = get_encoder(df["description"].tolist())
        E = enc.encode(sample)
        S = E @ E.T
        mean_cos = float(S[np.triu_indices(len(S), 1)].mean())
        q["diversite"] = {"cosinus_moyen_descriptions": round(mean_cos, 3), "encodeur": enc.name,
                          "seuil_alerte": config.MAX_MEAN_DESCRIPTION_COSINE,
                          "alerte": mean_cos > config.MAX_MEAN_DESCRIPTION_COSINE}
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(S[np.triu_indices(len(S), 1)], bins=50, color="#A23B72")
        ax.set_title(f"Similarité cosinus entre descriptions ({enc.name})")
        fig.tight_layout(); fig.savefig(OUT / "diversite_descriptions.png", dpi=110); plt.close(fig)

        # 12.4 cohérence
        sad = df["tags_mood"].map(lambda l: any(t in ("triste", "mélancolique") for t in l))
        happy = df["tags_mood"].map(lambda l: any(t in ("joyeux", "euphorique") for t in l))
        calm = df["tags_mood"].map(lambda l: any(t in ("calme", "relaxant", "apaisant") for t in l))
        conflicts = pd.DataFrame({
            "triste_mais_valence_haute": sad & (df["valence"] > 0.75),
            "joyeux_mais_valence_basse": happy & (df["valence"] < 0.25),
            "calme_mais_energie_haute": calm & (df["energy"] > 0.85),
        })
        q["coherence"] = {k: int(v.sum()) for k, v in conflicts.items()}
        df["conflict"] = conflicts.any(axis=1)

        # 12.5 relecture humaine
        cols = ["track_id", "artist", "title", "macro_genre", "mood_list", "context_list", "description"]
        rev = df.sample(min(len(df), config.MANUAL_REVIEW_SAMPLE), random_state=1)[cols].copy()
        rev["humeur_ok (o/n)"] = ""; rev["contexte_ok (o/n)"] = ""; rev["commentaire"] = ""
        rev.to_csv(config.REPORTS / "manual_review.csv", index=False)

        # 12.6 comparaison avec le jeu gold
        gold = pd.read_csv(config.GOLD_TRACKS)
        gold["track_key"] = [track_key(a, t) for a, t in zip(gold["artist"], gold["title"])]
        g = gold.merge(df[["track_key", "mood_list", "description"]], on="track_key",
                       suffixes=("_gold", "_gen"))
        if len(g):
            gm = g["mood"].str.split("|").map(set)
            jacc = [len(a & set(b)) / max(1, len(a | set(b))) for a, b in zip(gm, g["mood_list"])]
            Eg = enc.encode(g["description_gold"].tolist())
            Ed = enc.encode(g["description_gen"].tolist())
            q["gold"] = {"morceaux_communs": len(g), "jaccard_humeurs_moyen": round(float(np.mean(jacc)), 3),
                         "cosinus_descriptions_moyen": round(float((Eg * Ed).sum(axis=1).mean()), 3)}
        else:
            q["gold"] = {"morceaux_communs": 0}

        save_interim(df, "p12_quality")
        save_json(q, config.REPORTS / "quality_report.json")
        log.info("  complétude %s", q["completude"])
        log.info("  diversité : cos moyen %.3f ; conflits %s ; gold %s", mean_cos, q["coherence"], q["gold"])
        report("P12_quality", **q)
