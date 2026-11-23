"""Prétraitement et normalisation du texte.

Choix de conception :
- Pour SBERT (embeddings contextuels), on garde des phrases quasi brutes : le modèle
  a besoin des mots-outils, de la négation et de l'ordre des mots pour capter le sens.
  On se limite donc à un nettoyage léger (espaces, casse des émojis, ponctuation répétée).
- Pour les embeddings de mots (Word2Vec / fastText) et la baseline TF-IDF, on applique
  un prétraitement plus fort : minuscules, suppression des stopwords, tokenisation.
- Pour la correspondance exacte (noms d'artistes, genres), on retire aussi les accents.
"""
from __future__ import annotations

import re
import unicodedata

# Liste courte de stopwords français (suffisante pour la baseline ; spaCy peut la remplacer).
FR_STOPWORDS = {
    "a", "à", "au", "aux", "avec", "ce", "ces", "c", "dans", "de", "des", "du", "elle", "en",
    "et", "eux", "il", "je", "j", "la", "le", "les", "leur", "lui", "ma", "mais", "me", "même",
    "mes", "moi", "mon", "ne", "nos", "notre", "nous", "on", "ou", "par", "pas", "pour", "qu",
    "que", "qui", "sa", "se", "ses", "son", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un",
    "une", "vos", "votre", "vous", "y", "l", "d", "m", "n", "s", "t", "est", "suis", "es",
    "sont", "être", "avoir", "ai", "as", "très", "trop", "plus", "bien", "fait", "faire",
    "ça", "cela", "cette", "cet", "aussi", "comme", "quand", "si", "tout", "tous",
}

_WS_RE = re.compile(r"\s+")
_REPEAT_PUNCT_RE = re.compile(r"([!?.])\1+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\n+")
_ELISION_RE = re.compile(r"^(?:l|d|j|m|n|s|t|c|qu|jusqu|lorsqu|puisqu)'(.+)$", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-zà-öø-ÿœæ0-9]+(?:[-'][a-zà-öø-ÿœæ0-9]+)*", re.IGNORECASE)


def clean_text(text: str | None) -> str:
    """Nettoyage léger, compatible SBERT (on conserve le sens et la structure)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = text.replace("’", "'").replace("`", "'")
    text = _REPEAT_PUNCT_RE.sub(r"\1", text)
    return _WS_RE.sub(" ", text).strip()


def strip_accents(text: str) -> str:
    """'Électro' -> 'electro' : utile pour la correspondance exacte de libellés."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_key(text: str) -> str:
    """Clé de comparaison robuste (minuscules, sans accents, sans ponctuation)."""
    text = strip_accents(clean_text(text).lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Découpe un texte libre en phrases : chaque phrase est encodée séparément,
    ce qui permet de capter plusieurs intentions dans une même réponse."""
    text = clean_text(text)
    if not text:
        return []
    parts = [p.strip(" ,;") for p in _SENT_SPLIT_RE.split(text)]
    return [p for p in parts if len(p) > 2]


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokenisation pour les embeddings de mots et la baseline TF-IDF."""
    tokens = [t.lower() for t in _TOKEN_RE.findall(clean_text(text))]
    # On découpe les élisions : "l'ambiance" -> "ambiance"
    tokens = [_ELISION_RE.sub(r"\1", t) for t in tokens]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in FR_STOPWORDS and len(t) > 1]
    return tokens


def parse_list(text: str | None, sep: str = r"[,;/\n]| et ") -> list[str]:
    """'Nujabes, Angèle et Daft Punk' -> ['Nujabes', 'Angèle', 'Daft Punk']."""
    if not text:
        return []
    return [p.strip() for p in re.split(sep, clean_text(text)) if p.strip()]


def split_tags(value: str | None, sep: str = "|") -> list[str]:
    """Champ multi-valué du dataset ('calme|rêveur') -> liste."""
    if not value or (isinstance(value, float)):
        return []
    return [v.strip() for v in str(value).split(sep) if v.strip()]


# =============================================================================
# Pipelines de prétraitement explicites (utilisés par semantic.py et le notebook 02)
# =============================================================================
NEGATIONS = {"pas", "ne", "n", "plus", "jamais", "sans", "aucun", "aucune", "rien", "ni"}
_NLP_SPACY = None


def lemmatize(tokens: list[str]) -> list[str]:
    """Lemmatisation française avec spaCy (fr_core_news_sm) si installé, sinon tokens inchangés.
    Ex. « énervée » -> « énerver », « chansons » -> « chanson »."""
    global _NLP_SPACY
    if _NLP_SPACY is None:
        try:
            import spacy

            _NLP_SPACY = spacy.load("fr_core_news_sm", disable=["parser", "ner"])
        except Exception:
            _NLP_SPACY = False
    if not _NLP_SPACY:
        return tokens
    return [t.lemma_.lower() for t in _NLP_SPACY(" ".join(tokens))]


def preprocess_lexical(text: str, lemma: bool = False, keep_negations: bool = True) -> list[str]:
    """Pipeline « lexical » (TF-IDF, Word2Vec, fastText) :
    nettoyage -> minuscules -> tokenisation -> élisions -> stopwords -> (lemmatisation).
    `keep_negations=True` conserve « pas », « sans »... que la liste de stopwords supprimerait."""
    tokens = [t.lower() for t in _TOKEN_RE.findall(clean_text(text))]
    tokens = [_ELISION_RE.sub(r"\1", t) for t in tokens]   # l'ambiance -> ambiance, mais aujourd'hui intact
    stop = FR_STOPWORDS - NEGATIONS if keep_negations else FR_STOPWORDS
    tokens = [t for t in tokens if t not in stop and len(t) > 1]
    return lemmatize(tokens) if lemma else tokens


def preprocess_semantic(text: str) -> list[str]:
    """Pipeline « contextuel » (SBERT) : nettoyage léger + découpage en phrases.
    Pas de minuscules forcées, pas de suppression de stopwords ni de lemmatisation :
    le transformeur a besoin de la phrase complète (ordre des mots, négation, mots-outils)."""
    return split_sentences(text) or ([clean_text(text)] if clean_text(text) else [])
