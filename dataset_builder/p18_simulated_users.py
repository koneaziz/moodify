"""PHASE 18 — UTILISATEURS SIMULÉS (pour la fonctionnalité « communautés de même goût »)

Une communauté, ce sont des personnes : sans vrais utilisateurs, on génère des profils fictifs
RÉALISTES et CLAIREMENT MARQUÉS comme simulés.
 18.1 Chaque utilisateur est tiré d'une communauté-cluster (persona) : ses genres, artistes,
      humeurs et contextes viennent des morceaux de ce cluster (+ un peu de bruit aléatoire)
 18.2 Ses réponses OUVERTES au quiz sont générées par modèles de phrases variés (français)
 18.3 Les réponses ont exactement le format du questionnaire -> utilisables par
      UserProfile.from_answers() comme un vrai utilisateur
 18.4 Embedding de chaque profil (SBERT) -> communauté la plus proche (cosinus) et
      5 « voisins de goût » (similarité utilisateur ↔ utilisateur)
Sorties : data/processed/users_simules.json, user_community.csv, user_neighbors.csv
"""
from __future__ import annotations

import random

import numpy as np
import pandas as pd

from . import config
from .p11_descriptions import de
from .utils import get_encoder, load_json, log, phase_timer, report, save_json

CTX_PHRASE = {
    "Étude & travail": "réviser et travailler", "Sport": "faire du sport", "Soirée & fête": "faire la fête",
    "Trajet": "mes trajets", "Sommeil & méditation": "me détendre avant de dormir",
    "Moment à deux": "les moments à deux", "Solitude & pluie": "les soirées seul quand il pleut",
    "Matin & quotidien": "bien démarrer la journée",
}
Q01 = [
    "J'aime surtout quand c'est {m1} et {m2}, plutôt {g1}. Ça m'accompagne pour {c1}.",
    "Mon truc c'est la musique {g1} quand c'est {m1}, et parfois un peu {de_g2}.",
    "J'écoute beaucoup {de_g1} : j'ai besoin que ce soit {m1} pour {c1}.",
    "La musique me sert surtout pour {c1}. Je cherche quelque chose {de_m1}, un peu {m2}.",
]
Q05 = [
    "Un morceau de {a1} m'a marqué, il est tellement {m1} que je l'écoute en boucle.",
    "Je me souviens d'avoir découvert {a1} pendant une période compliquée, c'était {m1} et ça m'a fait du bien.",
    "Tout ce que fait {a1}, surtout quand c'est {m2}.",
]
Q12 = ["Un dimanche parfait, ce serait un fond sonore {m1}, avec un peu {de_g1}.",
       "Quelque chose {de_m1} et {m2}, sans prise de tête.",
       "Un peu {de_g2}, un café, et rien d'autre."]
Q13 = ["Pour me défouler je mets un son {e} et je monte le volume.",
       "Quand j'ai besoin de motivation : quelque chose de bien {e}.",
       "Je lance une playlist {e}, ça marche à tous les coups."]
ENERGY_WORDS = ["énergique", "puissant", "rapide", "intense", "entraînant"]


def run() -> None:
    with phase_timer("P18 Utilisateurs simulés"):
        rng = random.Random(config.USERS_SEED)
        t = pd.read_csv(config.PROCESSED / "tracks.csv").fillna("")
        cl = pd.read_csv(config.PROCESSED / "track_cluster.csv")
        t = t.merge(cl, on="track_id")
        comms = pd.read_csv(config.PROCESSED / "communities.csv").fillna("")
        clusters = comms[comms["source"] == "cluster"].reset_index(drop=True)
        quiz = load_json(config.PROCESSED / "questionnaire.json")
        genres_all = next(q["options"] for s in quiz["sections"] for q in s["questions"] if q["id"] == "Q02")
        cities = next(q["options"] for s in quiz["sections"] for q in s["questions"] if q["id"] == "Q14")
        weights = clusters["n_tracks"].tolist()

        users = []
        for u in range(config.N_SIMULATED_USERS):
            ci = rng.choices(range(len(clusters)), weights=weights)[0]
            c = clusters.iloc[ci]
            g = t[t["cluster"] == int(c["community_id"][1:]) - 1]
            moods = [m for l in g["mood"].str.split("|") for m in l if m]
            mtop = pd.Series(moods).value_counts().index[:6].tolist() or ["calme", "doux"]
            m1, m2 = rng.sample(mtop, 2) if len(mtop) >= 2 else (mtop[0], mtop[0])
            gen = [x for x in c["genres"].split("|") if x]
            liked = list(dict.fromkeys(gen[:2] + ([rng.choice(genres_all)] if rng.random() < .4 else [])))
            disliked = [x for x in rng.sample(genres_all, 2) if x not in liked][:1]
            artists = g.sort_values("popularity", ascending=False)["artist"].drop_duplicates().head(8).tolist()
            fav = rng.sample(artists, min(3, len(artists))) if artists else []
            ctx_blocks = [x for x in c["contexts"].split("|") if x] or ["Trajet"]
            c1 = CTX_PHRASE.get(ctx_blocks[0], "écouter de la musique")
            g1 = (liked[0] if liked else "pop").lower()
            g2 = (liked[-1] if liked else "pop").lower()
            fmt = dict(m1=m1, m2=m2, g1=g1, g2=g2, c1=c1, de_m1=de(m1), de_g1=de(g1), de_g2=de(g2), a1=fav[0] if fav else "un artiste inconnu",
                       e=rng.choice(ENERGY_WORDS))
            study = "oui" if "Étude & travail" in ctx_blocks or rng.random() < .3 else "non"
            answers = {
                "Q01": rng.choice(Q01).format(**fmt), "Q02": liked, "Q03": disliked,
                "Q04": ", ".join(fav), "Q05": rng.choice(Q05).format(**fmt),
                "Q06": ctx_blocks, "Q07": study,
                "Q08": int(np.clip(round(g["energy"].mean() + rng.uniform(-.7, .7)), 1, 5)) if len(g) else 3,
                "Q09": rng.randint(1, 5), "Q10": rng.randint(1, 5),
                "Q11": rng.choice(["réguler", "accompagner"]),
                "Q12": rng.choice(Q12).format(**fmt), "Q13": rng.choice(Q13).format(**fmt),
                "Q14": rng.choice(cities), "Q15": rng.randint(1, 5),
                **{f"P{i:02d}": rng.randint(1, 7) for i in range(1, 11)},
            }
            if study == "oui":
                answers["Q07_followup"] = f"Plutôt des sons {m1} et sans trop de paroles."
            users.append({"user_id": f"U{u + 1:04d}", "pseudo": f"auditeur_{u + 1:04d}",
                          "source": "simulé", "persona_community": c["community_id"], "answers": answers})

        # 18.4 embeddings des profils -> communauté la plus proche + voisins
        texts = [" ".join([x["answers"]["Q01"], x["answers"]["Q05"], x["answers"]["Q12"]]) for x in users]
        enc = get_encoder(texts + comms["description"].tolist())
        U = enc.encode(texts)
        C = enc.encode((comms["name"] + ". " + comms["description"]).tolist())
        S = U @ C.T
        best = S.argmax(axis=1)
        uc = pd.DataFrame({"user_id": [x["user_id"] for x in users],
                           "persona_community": [x["persona_community"] for x in users],
                           "assigned_community": comms["community_id"].iloc[best].values,
                           "similarity": S[np.arange(len(users)), best].round(3)})
        uc.to_csv(config.PROCESSED / "user_community.csv", index=False)
        UU = U @ U.T
        np.fill_diagonal(UU, -1)
        nb = [{"user_id": users[i]["user_id"],
               "neighbors": "|".join(users[j]["user_id"] for j in np.argsort(-UU[i])[:5]),
               "similarities": "|".join(f"{UU[i, j]:.3f}" for j in np.argsort(-UU[i])[:5])}
              for i in range(len(users))]
        pd.DataFrame(nb).to_csv(config.PROCESSED / "user_neighbors.csv", index=False)
        save_json({"_doc": "Utilisateurs SIMULÉS (démonstration) — format identique au questionnaire.",
                   "users": users}, config.PROCESSED / "users_simules.json")

        agree = float((uc["persona_community"] == uc["assigned_community"]).mean())
        log.info("  %d utilisateurs ; communauté retrouvée par le cosinus : %.0f %%", len(users), 100 * agree)
        report("P18_simulated_users", n_users=len(users), persona_recovered_rate=round(agree, 3))
