"""Fonctions communes à toutes les phases : entrées/sorties, rapport, normalisation."""
from __future__ import annotations

import ast
import json
import logging
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("dataset")

# Accès au moteur NLP du projet (src/moodify) pour réutiliser les mêmes encodeurs
sys.path.insert(0, str(config.ROOT / "src"))


# =============================================================================
# Entrées / sorties des phases
# =============================================================================
def save_interim(df: pd.DataFrame, name: str) -> Path:
    """Sauvegarde une sortie intermédiaire en parquet (conserve les listes)."""
    path = config.INTERIM / f"{name}.parquet"
    df.to_parquet(path, index=False)
    log.info("  → %s (%d lignes)", path.relative_to(config.ROOT), len(df))
    return path


def load_interim(name: str) -> pd.DataFrame:
    path = config.INTERIM / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} introuvable : lancez d'abord la phase qui le produit.")
    df = pd.read_parquet(path)
    # parquet renvoie des numpy arrays pour les listes : on les remet en listes Python
    for col in df.columns:
        if len(df) and hasattr(df[col].iloc[0], "tolist") and not isinstance(df[col].iloc[0], (str, bytes)):
            if df[col].dtype == object:
                df[col] = df[col].map(lambda v: v.tolist() if hasattr(v, "tolist") else v)
    return df


def save_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Rapport du pipeline (entonnoir du nombre de lignes, décisions, durées)
# =============================================================================
REPORT_PATH = config.REPORTS / "pipeline_report.json"


def report(phase: str, **info) -> None:
    """Ajoute/écrase l'entrée d'une phase dans le rapport global."""
    data = load_json(REPORT_PATH) if REPORT_PATH.exists() else {}
    data[phase] = {"date": datetime.now().isoformat(timespec="seconds"), **info}
    save_json(data, REPORT_PATH)


class phase_timer:
    """with phase_timer('P03'): ... → log de début/fin et durée."""

    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.t0 = time.time()
        log.info("━━━━ %s ━━━━", self.name)
        return self

    def __exit__(self, *exc):
        log.info("     %s terminée en %.1f s", self.name, time.time() - self.t0)


# =============================================================================
# Normalisation de texte pour les jointures
# =============================================================================
_VERSION_RE = re.compile(
    r"\s*[\(\[\-–]\s*(?:\d{4}\s*)?(?:remaster(?:ed)?|remix|live|radio edit|edit|version|mono|stereo|"
    r"acoustic|demo|deluxe|bonus|single|original mix|extended|feat\.?|ft\.?|with)\b.*$",
    re.IGNORECASE)
_FEAT_RE = re.compile(r"\s*[\(\[]?\s*(?:feat\.?|ft\.?|featuring)\s+[^\)\]]*[\)\]]?", re.IGNORECASE)


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def clean_title(title: str) -> str:
    """'Song (feat. X) - Remastered 2011' -> 'Song' (pour détecter les versions d'un même titre)."""
    if not isinstance(title, str):
        return ""
    t = _FEAT_RE.sub("", title)
    t = _VERSION_RE.sub("", t)
    return t.strip()


def norm_key(text: str) -> str:
    """Clé de jointure : minuscules, sans accents, sans ponctuation, espaces uniques."""
    if not isinstance(text, str):
        return ""
    t = strip_accents(text.lower())
    t = re.sub(r"&", " and ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def track_key(artist: str, title: str) -> str:
    return f"{norm_key(artist)}||{norm_key(clean_title(title))}"


def parse_list_cell(value) -> list:
    """"['a', 'b']" ou 'a;b' ou liste -> liste Python."""
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if s.startswith("["):
        try:
            return [str(x).strip() for x in ast.literal_eval(s)]
        except (ValueError, SyntaxError):
            s = s.strip("[]")
    return [x.strip(" '\"") for x in re.split(r"[;,]", s) if x.strip(" '\"")]


def get_encoder(corpus: list[str] | None = None):
    """Encodeur du moteur NLP (SBERT, repli TF-IDF si indisponible).
    `corpus` sert uniquement à entraîner la baseline TF-IDF si SBERT est absent."""
    from moodify.embeddings import get_encoder as _get

    enc = _get(config.ENCODER)
    if enc.name == "tfidf":
        enc.fit(corpus or ["musique"])
        log.warning("  ⚠ encodeur TF-IDF (repli) : installez sentence-transformers pour SBERT")
    log.info("  encodeur : %s", enc.name)
    return enc
