"""PHASE 6 — JOINTURE SPOTIFY ↔ MuSe (en cascade)

 6.1 Jointure exacte sur spotify_id
 6.2 Jointure exacte sur la clé normalisée « artiste||titre »
 6.3 Correspondance approximative (rapidfuzz) : on compare les titres des morceaux du
     MÊME artiste (artiste normalisé identique ou très proche) -> rapide et peu d'erreurs
 6.4 Export d'un échantillon de correspondances approximatives à vérifier à la main
Sortie : p06_joined (échantillon + colonnes muse_*), reports/join_review.csv
"""
from __future__ import annotations

import pandas as pd
from rapidfuzz import fuzz, process

from . import config
from .utils import load_interim, log, norm_key, phase_timer, report, save_interim

MUSE_COLS = ["muse_seeds", "muse_valence", "muse_arousal", "muse_dominance", "muse_genre"]


def run() -> None:
    with phase_timer("P06 Jointure Spotify ↔ MuSe"):
        sp = load_interim("p04_sample")
        if not (config.INTERIM / "p05_muse_clean.parquet").exists():
            for c in MUSE_COLS:
                sp[c] = None
            sp["muse_seeds"] = [[] for _ in range(len(sp))]
            sp["match_method"] = "aucun"
            save_interim(sp, "p06_joined")
            report("P06_join", skipped=True)
            return
        mu = load_interim("p05_muse_clean")
        sp["match_method"] = "aucun"
        sp["match_score"] = None
        sp["muse_index"] = None

        # 6.1 spotify_id
        by_id = {sid: i for i, sid in mu["spotify_id"].dropna().items()}
        m = sp["track_id"].map(by_id)
        sp.loc[m.notna(), ["muse_index", "match_method", "match_score"]] = \
            list(zip(m[m.notna()], ["spotify_id"] * m.notna().sum(), [100] * m.notna().sum()))

        # 6.2 clé normalisée
        by_key = {k: i for i, k in mu["track_key"].items()}
        todo = sp["muse_index"].isna()
        m = sp.loc[todo, "track_key"].map(by_key)
        idx = m[m.notna()].index
        sp.loc[idx, "muse_index"] = m[m.notna()]
        sp.loc[idx, "match_method"] = "cle_normalisee"
        sp.loc[idx, "match_score"] = 100

        # 6.3 fuzzy : bloc par artiste
        mu["artist_key"] = mu["artist"].map(norm_key)
        mu["title_key"] = mu["track_key"].str.split(r"\|\|").str[1]
        groups = {a: g for a, g in mu.groupby("artist_key")}
        artist_keys = list(groups)
        todo = sp.index[sp["muse_index"].isna()]
        for i in todo:
            a_key = norm_key(sp.at[i, "artist"])
            cand = groups.get(a_key)
            if cand is None:
                best_a = process.extractOne(a_key, artist_keys, scorer=fuzz.ratio,
                                            score_cutoff=config.FUZZY_THRESHOLD)
                if not best_a:
                    continue
                cand = groups[best_a[0]]
            t_key = sp.at[i, "track_key"].split("||")[1]
            best = process.extractOne(t_key, cand["title_key"].tolist(), scorer=fuzz.token_sort_ratio,
                                      score_cutoff=config.FUZZY_THRESHOLD)
            if best:
                sp.at[i, "muse_index"] = cand.index[best[2]]
                sp.at[i, "match_method"] = "fuzzy"
                sp.at[i, "match_score"] = round(best[1], 1)

        # Rattachement des colonnes MuSe
        for c in MUSE_COLS:
            sp[c] = sp["muse_index"].map(lambda j: mu.at[int(j), c] if pd.notna(j) else None)
        sp["muse_seeds"] = sp["muse_seeds"].map(lambda v: list(v) if isinstance(v, (list, tuple)) or hasattr(v, "tolist") else [])
        sp["muse_title"] = sp["muse_index"].map(lambda j: mu.at[int(j), "track"] if pd.notna(j) else None)
        sp["muse_artist"] = sp["muse_index"].map(lambda j: mu.at[int(j), "artist"] if pd.notna(j) else None)

        # 6.4 Échantillon à vérifier manuellement
        fz = sp[sp["match_method"] == "fuzzy"]
        review = fz.sample(min(len(fz), config.FUZZY_REVIEW_SAMPLE), random_state=0)[
            ["track_id", "artist", "title", "muse_artist", "muse_title", "match_score"]]
        review["correct (o/n)"] = ""
        review.to_csv(config.REPORTS / "join_review.csv", index=False)

        counts = sp["match_method"].value_counts().to_dict()
        rate = 1 - counts.get("aucun", 0) / len(sp)
        sp = sp.drop(columns=["muse_index"])
        save_interim(sp, "p06_joined")
        log.info("  correspondances : %s → taux %.1f %%", counts, 100 * rate)
        report("P06_join", by_method=counts, match_rate=round(rate, 3),
               review_file="reports/join_review.csv")
