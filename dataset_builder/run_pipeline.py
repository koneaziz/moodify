"""Point d'entrée : exécute tout ou partie des 20 phases du pipeline.

Exemples :
    python -m dataset_builder.run_pipeline              # tout (P01 -> P20)
    python -m dataset_builder.run_pipeline --from 8     # reprendre à la phase 8
    python -m dataset_builder.run_pipeline --only 11    # une seule phase
    python -m dataset_builder.run_pipeline --list       # liste des phases

Chaque phase lit la sortie de la précédente dans data/interim/ : on peut donc relancer
une phase isolément après avoir modifié son code ou config.py.
"""
from __future__ import annotations

import argparse
import importlib

PHASES = [
    (1, "p01_collect", "Collecte et vérification des fichiers bruts"),
    (2, "p02_eda", "Exploration initiale (statistiques, figures)"),
    (3, "p03_clean_spotify", "Nettoyage Spotify (doublons, versions, filtres, macro-genres)"),
    (4, "p04_sample", "Échantillonnage stratifié"),
    (5, "p05_prepare_muse", "Préparation MuSe"),
    (6, "p06_join", "Jointure Spotify ↔ MuSe (id, clé, fuzzy)"),
    (7, "p07_lastfm", "Enrichissement Last.fm (tags, biographies)"),
    (8, "p08_clean_tags", "Nettoyage et classification sémantique des tags"),
    (9, "p09_audio_to_text", "Caractéristiques audio → libellés texte"),
    (10, "p10_build_columns", "Colonnes mood / context / keywords"),
    (11, "p11_descriptions", "Génération des descriptions"),
    (12, "p12_quality", "Contrôle qualité"),
    (13, "p13_structure", "Tables finales + dictionnaire des données"),
    (14, "p14_datacard", "Fiche du dataset"),
    (15, "p15_eval_queries", "Requêtes d'évaluation"),
    (16, "p16_align_reference", "Alignement blocs / archétypes / questionnaire"),
    (17, "p17_communities", "Communautés par clustering sémantique"),
    (18, "p18_simulated_users", "Utilisateurs simulés + voisins de goût"),
    (19, "p19_artists_concerts", "Artistes similaires, villes, concerts"),
    (20, "p20_app_data", "Base SQLite + tests du chatbot"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Pipeline de construction du dataset Moodify")
    ap.add_argument("--from", dest="start", type=int, default=1)
    ap.add_argument("--to", dest="end", type=int, default=20)
    ap.add_argument("--only", type=int)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for n, mod, desc in PHASES:
            print(f"P{n:02d}  {mod:<24} {desc}")
        return
    start, end = (args.only, args.only) if args.only else (args.start, args.end)
    for n, mod, _ in PHASES:
        if start <= n <= end:
            importlib.import_module(f"dataset_builder.{mod}").run()


if __name__ == "__main__":
    main()
