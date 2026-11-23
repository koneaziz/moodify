"""PHASE 15 — JEU DE REQUÊTES D'ÉVALUATION

30 requêtes en langage naturel, chacune avec des CRITÈRES structurés. On en déduit une
liste de morceaux pertinents « silver » (pré-annotation automatique) à partir des colonnes
structurées du catalogue. L'équipe doit ensuite RELIRE et corriger (champ `reviewed`).

⚠ Biais à mentionner : les labels silver viennent des mêmes tags que les descriptions.
La vérité terrain finale doit être validée à la main (et sur le jeu gold).
Sortie : data/processed/eval_queries.json
"""
from __future__ import annotations

import pandas as pd

from . import config
from .utils import log, phase_timer, report, save_json

# (requête, bloc d'humeur, bloc de contexte ou None, macro-genre ou None, énergie min, énergie max)
QUERIES = [
    ("Une musique calme et instrumentale pour réviser tard le soir", "Calme & détente", "Étude & travail", None, 1, 3),
    ("J'ai besoin de me concentrer, quelque chose de doux sans paroles", "Concentration", "Étude & travail", None, 1, 3),
    ("Du lofi tranquille pour bosser", "Calme & détente", "Étude & travail", "Lo-fi / Chill", 1, 3),
    ("Je suis énervée, je veux me calmer", "Calme & détente", None, None, 1, 2),
    ("Je suis énervé et j'ai besoin de me défouler", "Colère & défoulement", None, None, 4, 5),
    ("Des sons rageurs avec des guitares saturées", "Colère & défoulement", None, "Metal", 4, 5),
    ("Musique motivante pour ma séance de sport", "Énergie & motivation", "Sport", None, 4, 5),
    ("Un truc qui donne la pêche pour courir", "Énergie & motivation", "Sport", None, 4, 5),
    ("Des morceaux pour danser en soirée avec des amis", "Fête & danse", "Soirée & fête", None, 3, 5),
    ("De l'électro festive pour une house party", "Fête & danse", "Soirée & fête", "Électro / House", 4, 5),
    ("Je suis triste, j'ai le cœur brisé", "Mélancolie & introspection", None, None, 1, 3),
    ("Des chansons mélancoliques pour un jour de pluie", "Mélancolie & introspection", "Solitude & pluie", None, 1, 3),
    ("Je me sens nostalgique ce soir", "Mélancolie & introspection", None, None, 1, 3),
    ("Une ambiance romantique pour un dîner à deux", "Romance & sensualité", "Moment à deux", None, 1, 3),
    ("Du R&B sensuel pour la fin de soirée", "Romance & sensualité", None, "R&B / Soul / Funk", 1, 4),
    ("Quelque chose de joyeux pour bien commencer la journée", "Joie & bonne humeur", "Matin & quotidien", None, 2, 5),
    ("Des sons ensoleillés et optimistes", "Joie & bonne humeur", None, None, 2, 5),
    ("Du reggae ou de l'afro pour l'été", "Joie & bonne humeur", None, "Afro / Reggae / Latino", 2, 5),
    ("Une musique planante pour m'évader", "Rêverie & évasion", None, None, 1, 3),
    ("Des nappes ambient pour m'endormir", "Calme & détente", "Sommeil & méditation", "Ambient", 1, 2),
    ("Musique pour méditer et faire baisser le stress", "Calme & détente", "Sommeil & méditation", None, 1, 2),
    ("Du piano classique apaisant", "Calme & détente", None, "Classique", 1, 2),
    ("Du jazz feutré pour un dimanche matin", "Calme & détente", None, "Jazz / Blues", 1, 3),
    ("Un rap motivant pour me donner confiance", "Énergie & motivation", None, "Hip-hop / Rap", 3, 5),
    ("Des chansons françaises douces et tendres", "Romance & sensualité", None, "Chanson française", 1, 3),
    ("Du folk acoustique pour un trajet en train", "Calme & détente", "Trajet", "Indie / Folk / Country", 1, 3),
    ("Je suis fatiguée mais je dois rester éveillée pour travailler", "Énergie & motivation", "Étude & travail", None, 3, 4),
    ("Un son sombre et intense pour conduire la nuit", "Rêverie & évasion", "Trajet", None, 2, 4),
    ("Je m'ennuie, surprends-moi avec un truc entraînant", "Fête & danse", None, None, 3, 5),
    ("I want chill music to study, nothing too loud", "Calme & détente", "Étude & travail", None, 1, 3),
]


def run() -> None:
    with phase_timer("P15 Requêtes d'évaluation"):
        t = pd.read_csv(config.PROCESSED / "tracks.csv").fillna("")
        items = []
        for i, (q, mb, cb, g, emin, emax) in enumerate(QUERIES, 1):
            m = t["mood_blocks"].str.contains(mb, regex=False) & t["energy"].between(emin, emax)
            if cb:
                m &= t["context_blocks"].str.contains(cb, regex=False)
            if g:
                m &= t["genre"] == g
            rel = t[m].sort_values("popularity", ascending=False)["track_id"].tolist()
            items.append({"query_id": f"Q{i:02d}", "query": q,
                          "criteria": {"mood_block": mb, "context_block": cb, "genre": g,
                                       "energy": [emin, emax]},
                          "relevant_track_ids_silver": rel[:50], "n_relevant_silver": len(rel),
                          "relevant_track_ids_reviewed": [], "reviewed": False})
        save_json({"_doc": __doc__, "queries": items}, config.PROCESSED / "eval_queries.json")
        empty = [x["query_id"] for x in items if x["n_relevant_silver"] == 0]
        log.info("  %d requêtes ; sans morceau pertinent : %s", len(items), empty or "aucune")
        report("P15_eval_queries", n_queries=len(items), queries_without_relevant=empty)
