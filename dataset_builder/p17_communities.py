"""PHASE 17 — COMMUNAUTÉS PAR CLUSTERING SÉMANTIQUE

 17.1 Embeddings des descriptions (SBERT)
 17.2 KMeans pour k ∈ CLUSTER_K_RANGE, choix de k par le score de silhouette (cosinus)
 17.3 Nommage automatique de chaque cluster à partir de ses humeurs / contextes / genres dominants
      + description générée (modèle de phrase) + morceaux représentatifs (proches du centroïde)
 17.4 Ajout des communautés « éditoriales » écrites à la main (data/communities.csv)
Sorties : data/processed/communities.csv, data/processed/track_cluster.csv,
          reports/communities_silhouette.png
"""
from __future__ import annotations

from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.metrics import silhouette_score  # noqa: E402

from . import config  # noqa: E402
from .lexicon import OLD_TO_NEW_GENRE  # noqa: E402
from .utils import get_encoder, log, phase_timer, report  # noqa: E402

CONTEXT_NAME = {
    "Étude & travail": "Study", "Sport": "Workout", "Soirée & fête": "Party", "Trajet": "On the Road",
    "Sommeil & méditation": "Sleep & Zen", "Moment à deux": "Duo", "Solitude & pluie": "Rainy Days",
    "Matin & quotidien": "Morning",
}
MOOD_NAME = {
    "Calme & détente": "Chill", "Concentration": "Focus", "Énergie & motivation": "Power",
    "Fête & danse": "Dance", "Mélancolie & introspection": "Blue", "Colère & défoulement": "Rage",
    "Romance & sensualité": "Love", "Joie & bonne humeur": "Good Vibes", "Rêverie & évasion": "Dream",
}


def _top(series_of_lists, n):
    return [x for x, _ in Counter(x for l in series_of_lists for x in l if x).most_common(n)]


def run() -> None:
    with phase_timer("P17 Communautés (clustering)"):
        t = pd.read_csv(config.PROCESSED / "tracks.csv").fillna("")
        enc = get_encoder(t["description"].tolist())
        E = enc.encode(t["description"].tolist())
        if E.shape[1] > 512:   # baseline TF-IDF : réduction de dimension (LSA) avant KMeans
            from sklearn.decomposition import TruncatedSVD
            E = TruncatedSVD(n_components=128, random_state=config.CLUSTER_SEED).fit_transform(E)
            E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9

        # 17.2 choix de k
        scores = {}
        for k in config.CLUSTER_K_RANGE:
            if k >= len(t):
                break
            km = KMeans(n_clusters=k, n_init=10, random_state=config.CLUSTER_SEED).fit(E)
            scores[k] = float(silhouette_score(E, km.labels_, metric="cosine"))
        best_k = max(scores, key=scores.get)
        km = KMeans(n_clusters=best_k, n_init=10, random_state=config.CLUSTER_SEED).fit(E)
        t["cluster"] = km.labels_

        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(list(scores), list(scores.values()), marker="o")
        ax.axvline(best_k, color="red", ls="--"); ax.set_xlabel("k"); ax.set_ylabel("silhouette (cosinus)")
        ax.set_title("Choix du nombre de communautés"); fig.tight_layout()
        fig.savefig(config.REPORTS / "communities_silhouette.png", dpi=110); plt.close(fig)

        # 17.3 nommage + description
        rows, used = [], Counter()
        for c in range(best_k):
            g = t[t["cluster"] == c]
            mb = _top(g["mood_blocks"].str.split("|"), 2)
            cb = _top(g["context_blocks"].str.split("|"), 2)
            gen = g["genre"].value_counts().index[:3].tolist()
            moods = _top(g["mood"].str.split("|"), 4)
            mood_n = MOOD_NAME.get(mb[0], "Mix") if mb else "Mix"
            genre_n = gen[0].split(" /")[0] if gen else "Music"
            ctx_n = CONTEXT_NAME.get(cb[0], "Club") if cb else "Club"
            # nom lisible : humeur + genre dominant, puis + contexte si déjà pris
            for name in (f"{mood_n} {genre_n}", f"{mood_n} {genre_n} {ctx_n}"):
                if not used[name]:
                    break
            used[name] += 1
            if used[name] > 1:
                name += f" #{used[name]}"
            # morceaux représentatifs = les plus proches du centroïde
            idx = g.index.to_numpy()
            cen = km.cluster_centers_[c] / np.linalg.norm(km.cluster_centers_[c])
            rep_idx = idx[np.argsort(-(E[idx] @ cen))[:5]]
            desc = (f"Communauté d'auditeurs qui aiment une musique {', '.join(moods[:3])}, "
                    f"surtout {', '.join(gen[:2])}. On s'y retrouve pour {', '.join(x.lower() for x in cb) or 'écouter ensemble'} "
                    f"et partager des découvertes.")
            rows.append({"community_id": f"K{c + 1:02d}", "name": name, "description": desc,
                         "genres": "|".join(gen), "moods": "|".join(mb), "contexts": "|".join(cb),
                         "n_tracks": len(g), "representative_tracks": "|".join(t.loc[rep_idx, "track_id"]),
                         "source": "cluster"})

        # 17.4 communautés éditoriales
        edito = pd.read_csv(config.DATA / "communities.csv")
        edito["source"] = "éditoriale"
        edito["genres"] = edito["genres"].map(
            lambda s: "|".join(dict.fromkeys(OLD_TO_NEW_GENRE.get(g, g) for g in s.split("|"))))
        out = pd.concat([pd.DataFrame(rows), edito], ignore_index=True)
        out.to_csv(config.PROCESSED / "communities.csv", index=False)
        t[["track_id", "cluster"]].to_csv(config.PROCESSED / "track_cluster.csv", index=False)

        log.info("  k=%d (silhouette %.3f) ; communautés : %s", best_k, scores[best_k],
                 [r["name"] for r in rows])
        report("P17_communities", k=best_k, silhouette=round(scores[best_k], 3), silhouettes=scores,
               clusters=[{k: r[k] for k in ("community_id", "name", "n_tracks", "genres")} for r in rows],
               editorial=len(edito))
