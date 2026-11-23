"""PHASE 16 — ALIGNEMENT DES FICHIERS DE RÉFÉRENCE SUR LE NOUVEAU CATALOGUE

 16.1 Couverture des blocs d'humeur / contexte (nb de morceaux par bloc, alerte si < 30)
 16.2 Enrichissement des phrases prototypes des blocs avec le vocabulaire RÉEL des tags
      (une phrase supplémentaire par bloc, construite à partir des tags les plus fréquents)
 16.3 Profils d'auditeur (archetypes) : vérification que chaque bloc requis est couvert
 16.4 Questionnaire : options de genres = macro-genres réellement présents
 16.5 Personnalité → genres (STOMP) réécrit avec les nouveaux macro-genres
Sorties dans data/processed/ : blocks.json, archetypes.json, questionnaire.json,
personality_music.json, block_coverage.csv
"""
from __future__ import annotations

import copy
from collections import Counter

import pandas as pd

from . import config
from .lexicon import CONTEXT_TO_BLOCK, MACRO_GENRES, MOOD_TO_BLOCK
from .utils import load_json, log, phase_timer, report, save_json

MIN_TRACKS_PER_BLOCK = 30

STOMP = {
    "_doc": "Lien personnalité → genres (Rentfrow & Gosling, 2003). Corrélations faibles : a priori léger uniquement.",
    "dimensions": {
        "Réflexif & complexe": {"genres": ["Jazz / Blues", "Classique", "Indie / Folk / Country", "Ambient",
                                           "Lo-fi / Chill", "Chanson française", "Musiques du monde"],
                                "traits": {"openness": 1.0}},
        "Intense & rebelle": {"genres": ["Rock", "Metal"], "traits": {"openness": 0.6}},
        "Optimiste & conventionnel": {"genres": ["Pop", "Chanson française", "Indie / Folk / Country"],
                                      "traits": {"extraversion": 0.6, "agreeableness": 0.6,
                                                 "conscientiousness": 0.4, "openness": -0.4}},
        "Énergique & rythmé": {"genres": ["Hip-hop / Rap", "Électro / House", "R&B / Soul / Funk",
                                          "Afro / Reggae / Latino"],
                               "traits": {"extraversion": 1.0, "agreeableness": 0.3}},
    },
}


def run() -> None:
    with phase_timer("P16 Alignement des fichiers de référence"):
        t = pd.read_csv(config.PROCESSED / "tracks.csv").fillna("")
        blocks = load_json(config.REFERENCE_FILES / "blocks.json")
        new_blocks = copy.deepcopy(blocks)

        # 16.1 couverture
        rows = []
        for kind, col, names in (("humeur", "mood_blocks", blocks["mood_blocks"]),
                                 ("contexte", "context_blocks", blocks["context_blocks"])):
            for b in names:
                n = int(t[col].str.contains(b, regex=False).sum())
                rows.append({"type": kind, "bloc": b, "morceaux": n, "alerte": n < MIN_TRACKS_PER_BLOCK})
        cov = pd.DataFrame(rows)
        cov.to_csv(config.PROCESSED / "block_coverage.csv", index=False)
        weak = cov[cov["alerte"]]["bloc"].tolist()

        # 16.2 phrases prototypes enrichies avec les tags réels
        mood_counts = Counter(m for l in t["mood"].str.split("|") for m in l if m)
        ctx_counts = Counter(c for l in t["context"].str.split("|") for c in l if c)
        for b in new_blocks["mood_blocks"]:
            top = [m for m, _ in mood_counts.most_common() if MOOD_TO_BLOCK.get(m) == b][:3]
            if top:
                new_blocks["mood_blocks"][b].append("musique " + ", ".join(top))
        for b in new_blocks["context_blocks"]:
            top = [c for c, _ in ctx_counts.most_common() if CONTEXT_TO_BLOCK.get(c) == b][:3]
            if top:
                new_blocks["context_blocks"][b].append("pour " + ", ".join(top))
        save_json(new_blocks, config.PROCESSED / "blocks.json")

        # 16.3 archétypes
        arche = load_json(config.REFERENCE_FILES / "archetypes.json")
        cov_map = dict(zip(cov["bloc"], cov["morceaux"]))
        arche_issues = {a["name"]: [b for b in a["blocks"] if cov_map.get(b, 0) < MIN_TRACKS_PER_BLOCK]
                        for a in arche["archetypes"]}
        arche_issues = {k: v for k, v in arche_issues.items() if v}
        save_json(arche, config.PROCESSED / "archetypes.json")

        # 16.4 questionnaire
        quiz = load_json(config.REFERENCE_FILES / "questionnaire.json")
        present = [g for g in MACRO_GENRES if g in set(t["genre"])]
        for s in quiz["sections"]:
            for q in s["questions"]:
                if q["id"] in ("Q02", "Q03"):
                    q["options"] = present
        save_json(quiz, config.PROCESSED / "questionnaire.json")

        # 16.5 personnalité
        save_json(STOMP, config.PROCESSED / "personality_music.json")

        log.info("  blocs sous-couverts (< %d morceaux) : %s", MIN_TRACKS_PER_BLOCK, weak or "aucun")
        if arche_issues:
            log.warning("  archétypes avec blocs faibles : %s", arche_issues)
        report("P16_align_reference", weak_blocks=weak, archetype_issues=arche_issues,
               genres_in_quiz=present)
