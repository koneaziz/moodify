"""PHASE 8 — NETTOYAGE ET CLASSIFICATION DES TAGS (partie NLP du prétraitement)

Sources de tags par morceau :
 - Last.fm (poids 0-100 donné par l'API)
 - MuSe « seeds » (tags d'émotion validés, poids fixe 60)
 - « genres-humeurs » Spotify (chill, sad, study... poids fixe 70)

 8.1 Normalisation : minuscules, espaces, synonymes (hip hop -> hip-hop, chill-out -> chillout)
 8.2 Suppression du bruit : tags génériques (« seen live », « favorites »), années, nom de l'artiste
 8.3 Filtre de fréquence : un tag inconnu vu sur < TAG_MIN_FREQUENCY morceaux est supprimé
 8.4 Classification de chaque tag en mood / context / attribute / era / genre :
     a) lexique explicite (lexicon.py)
     b) sinon, CLASSIFICATION SÉMANTIQUE : cosinus entre l'embedding du tag et les
        embeddings des entrées du lexique -> on hérite de la catégorie de la plus proche
        si cos >= TAG_SEMANTIC_THRESHOLD (ex. « melancolic » -> « melancholic »)
 8.5 Traduction vers le vocabulaire français du projet
Sorties : p08_tags (colonnes de tags par catégorie), reports/tag_vocabulary.csv,
          data/interim/track_tags.parquet (table longue morceau × tag)
"""
from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd

from . import config
from .lexicon import GENRE_TO_MACRO, NOISE_TAGS, TAG_LEXICON, TAG_SYNONYMS
from .utils import get_encoder, load_interim, log, norm_key, phase_timer, report, save_interim

MUSE_WEIGHT = 60
GENRE_TAG_WEIGHT = 70
GENRE_WORDS = set(GENRE_TO_MACRO) | {g.replace("-", " ") for g in GENRE_TO_MACRO} | {
    "rap", "hip-hop", "electronic", "indie rock", "soundtrack", "lo-fi hip hop", "chanson",
    "chanson francaise", "french rap", "rap francais", "variete francaise", "classic rock",
    "pop rock", "dream pop", "shoegaze", "post-rock", "neo-soul", "nu metal", "thrash metal"}


# 8.1
def normalize_tag(tag: str) -> str:
    t = re.sub(r"\s+", " ", str(tag).lower().strip().replace("_", " "))
    return TAG_SYNONYMS.get(t, t)


# 8.2
def is_noise(tag: str, artist: str) -> bool:
    if len(tag) < 2 or tag in NOISE_TAGS:
        return True
    if re.fullmatch(r"\d{4}", tag):          # une année seule n'apporte rien sémantiquement
        return True
    return norm_key(tag) == norm_key(artist)  # le nom de l'artiste comme tag


def run() -> None:
    with phase_timer("P08 Nettoyage et classification des tags"):
        df = load_interim("p07_lastfm")

        # --- Collecte des tags bruts (morceau, tag, poids, source)
        long_rows = []
        for r in df.itertuples():
            for t, w in zip(r.lastfm_tags, r.lastfm_tag_weights):
                long_rows.append((r.track_id, r.artist, normalize_tag(t), float(w), "lastfm"))
            for t in r.muse_seeds:
                long_rows.append((r.track_id, r.artist, normalize_tag(t), MUSE_WEIGHT, "muse"))
        raw = pd.DataFrame(long_rows, columns=["track_id", "artist", "tag", "weight", "source"])
        n_raw = len(raw)

        # 8.2 bruit
        if len(raw):
            raw = raw[~raw.apply(lambda x: is_noise(x.tag, x.artist), axis=1)]
        n_after_noise = len(raw)

        # 8.3 fréquence (on garde toujours les tags du lexique)
        freq = Counter(raw["tag"]) if len(raw) else Counter()
        keep = {t for t, c in freq.items() if c >= config.TAG_MIN_FREQUENCY or t in TAG_LEXICON}
        raw = raw[raw["tag"].isin(keep)] if len(raw) else raw

        # 8.4 classification
        vocab = sorted(set(raw["tag"])) if len(raw) else []
        classes: dict[str, tuple[str, str, str, float]] = {}   # tag -> (cat, fr, méthode, score)
        unknown = []
        for t in vocab:
            if t in TAG_LEXICON:
                cat, fr = TAG_LEXICON[t]
                classes[t] = (cat, fr, "lexique", 1.0)
            elif t in GENRE_WORDS or t.replace(" ", "-") in GENRE_TO_MACRO:
                classes[t] = ("genre", t, "lexique_genre", 1.0)
            else:
                unknown.append(t)
        if unknown:
            lex_keys = list(TAG_LEXICON)
            enc = get_encoder(lex_keys + unknown)
            sims = enc.encode(unknown) @ enc.encode(lex_keys).T
            best = sims.argmax(axis=1)
            for t, j, s in zip(unknown, best, sims[np.arange(len(unknown)), best]):
                if s >= config.TAG_SEMANTIC_THRESHOLD.get(enc.name, 0.45):
                    cat, fr = TAG_LEXICON[lex_keys[j]]
                    classes[t] = (cat, fr, f"semantique (~{lex_keys[j]})", float(s))
                else:
                    classes[t] = ("other", t, "non_classe", float(s))

        vocab_df = pd.DataFrame(
            [(t, freq[t], *classes[t]) for t in vocab],
            columns=["tag", "frequence", "categorie", "libelle_fr", "methode", "score"]
        ).sort_values("frequence", ascending=False)
        vocab_df.to_csv(config.REPORTS / "tag_vocabulary.csv", index=False)

        if len(raw):
            raw["category"] = raw["tag"].map(lambda t: classes[t][0])
            raw["tag_fr"] = raw["tag"].map(lambda t: classes[t][1])
        else:
            raw = raw.assign(category=[], tag_fr=[])

        # Ajout des genres-humeurs Spotify (déjà en français)
        extra = []
        for r in df.itertuples():
            extra += [(r.track_id, r.artist, m, GENRE_TAG_WEIGHT, "spotify_genre", "mood", m) for m in r.genre_mood_tags]
            extra += [(r.track_id, r.artist, c, GENRE_TAG_WEIGHT, "spotify_genre", "context", c) for c in r.genre_context_tags]
        track_tags = pd.concat([raw, pd.DataFrame(extra, columns=list(raw.columns))], ignore_index=True)
        track_tags = (track_tags.sort_values("weight", ascending=False)
                      .drop_duplicates(["track_id", "category", "tag_fr"]))
        save_interim(track_tags.drop(columns="artist"), "track_tags")

        # 8.5 Colonnes agrégées par morceau (libellés français triés par poids)
        def agg(cat):
            s = track_tags[track_tags["category"] == cat].groupby("track_id")["tag_fr"].agg(list)
            return df["track_id"].map(s).map(lambda v: v if isinstance(v, list) else [])

        for cat in ("mood", "context", "attribute", "era", "genre", "other"):
            df[f"tags_{cat}"] = agg(cat)
        df["has_human_tags"] = (df["tags_mood"].map(len) + df["tags_context"].map(len)) > 0

        save_interim(df, "p08_tags")
        cat_counts = vocab_df["categorie"].value_counts().to_dict() if len(vocab_df) else {}
        log.info("  tags bruts %d → après bruit %d ; vocabulaire %d (%s)", n_raw, n_after_noise,
                 len(vocab_df), cat_counts)
        log.info("  morceaux avec tags d'humeur/contexte : %.0f %%", 100 * df["has_human_tags"].mean())
        report("P08_clean_tags", raw_tag_occurrences=n_raw, after_noise=n_after_noise,
               vocabulary_size=len(vocab_df), by_category=cat_counts,
               semantic_classified=int((vocab_df["methode"].str.startswith("semantique")).sum()) if len(vocab_df) else 0,
               share_tracks_with_tags=round(float(df["has_human_tags"].mean()), 3))
