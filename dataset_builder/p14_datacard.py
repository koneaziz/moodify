"""PHASE 14 — FICHE DU DATASET (data card) — reports/DATASET_CARD.md

Rassemble automatiquement : sources et licences, entonnoir du nombre de lignes,
choix de conception, statistiques finales, qualité, limites.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .utils import REPORT_PATH, load_json, log, phase_timer, report


def _table(d: dict, k="Élément", v="Valeur") -> str:
    lines = [f"| {k} | {v} |", "|---|---|"]
    lines += [f"| {a} | {b} |" for a, b in d.items()]
    return "\n".join(lines)


def run() -> None:
    with phase_timer("P14 Fiche du dataset"):
        rep = load_json(REPORT_PATH)
        tracks = pd.read_csv(config.PROCESSED / "tracks.csv")
        qual = load_json(config.REPORTS / "quality_report.json")
        funnel = dict(rep.get("P03_clean_spotify", {}).get("funnel", {}))
        funnel["8_echantillon (P04)"] = rep.get("P04_sample", {}).get("rows")
        funnel["9_final (P13)"] = len(tracks)

        md = f"""# Fiche du dataset Moodify

*Générée automatiquement par `dataset_builder` (phase 14).*

## 1. Sources

| Source | Contenu utilisé | Licence / conditions |
|---|---|---|
| Spotify Tracks Dataset (Kaggle, maharshipandya) | métadonnées, genres, caractéristiques audio | BSD (voir la page du dataset) |
| MuSe – Musical Sentiment Dataset (Akiki & Burghardt, 2021) | tags d'émotion, valence / arousal / dominance | CC BY 4.0 |
| API Last.fm | tags des auditeurs, biographies d'artistes | conditions d'utilisation de l'API Last.fm |
| Jeu gold (équipe) | 84 morceaux décrits à la main | création de l'équipe |

## 2. Entonnoir de nettoyage (nombre de morceaux)

{_table(funnel, "Étape", "Morceaux")}

## 3. Jointure Spotify ↔ MuSe

{_table(rep.get("P06_join", {}).get("by_method", {"(MuSe absent)": "-"}), "Méthode", "Morceaux")}

Taux de correspondance : **{rep.get("P06_join", {}).get("match_rate", "n/a")}**.
Échantillon à vérifier à la main : `reports/join_review.csv`.

## 4. Tags

- Source des tags Last.fm : {rep.get("P07_lastfm", {}).get("tag_source", "phase sautée")}
- Taille du vocabulaire après nettoyage : {rep.get("P08_clean_tags", {}).get("vocabulary_size", 0)}
- Tags classés par similarité sémantique (SBERT) : {rep.get("P08_clean_tags", {}).get("semantic_classified", 0)}
- Vocabulaire complet : `reports/tag_vocabulary.csv`

## 5. Dataset final

- **{len(tracks)} morceaux**, **{tracks['artist'].nunique()} artistes**, **{tracks['genre'].nunique()} macro-genres**
- Longueur moyenne des descriptions : {rep.get("P11_descriptions", {}).get("mean_words")} mots
- Source des humeurs : {rep.get("P10_build_columns", {}).get("mood_source")}
- Source des descriptions : {rep.get("P11_descriptions", {}).get("sources")}

{_table(tracks['genre'].value_counts().to_dict(), "Macro-genre", "Morceaux")}

## 6. Qualité

{_table(qual.get("completude", {}), "Complétude", "Part")}

- Diversité des descriptions (cosinus moyen) : {qual.get("diversite", {}).get("cosinus_moyen_descriptions")}
- Conflits tags humains ↔ audio : {qual.get("coherence")}
- Comparaison avec le jeu gold : {qual.get("gold")}

## 7. Choix de conception

- Les **humeurs humaines** (Last.fm, MuSe) sont prioritaires sur les humeurs déduites de l'audio.
- Les caractéristiques audio sont **traduites en texte** (seuils dans `config.py`) pour être
  comparables sémantiquement aux phrases des utilisateurs.
- Les descriptions sont **générées par modèles de phrases à variantes** (pas de copie de texte
  protégé, aucune parole de chanson).

## 8. Limites

- Les descriptions générées à partir de l'audio seul (`description_source = template_audio`) sont
  moins riches que celles issues de tags humains.
- Les seuils audio sont des heuristiques, à valider avec `reports/manual_review.csv`.
- Le catalogue reste biaisé vers les morceaux populaires (échantillonnage par popularité).
"""
        (config.REPORTS / "DATASET_CARD.md").write_text(md, encoding="utf-8")
        log.info("  → reports/DATASET_CARD.md")
        report("P14_datacard", file="reports/DATASET_CARD.md")
