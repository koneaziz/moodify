"""FUSION : dataset de l'équipe (Spotify + MuSe + Last.fm, 609 morceaux) + jeu gold (84 morceaux)

    python -m dataset_builder.merge_datasets
Entrées  : data/raw/dataset_final.csv (collègue), data/tracks.csv (jeu gold)
Sorties  : data/processed/moodify_dataset.csv et .json

Étapes (mêmes principes que les phases 8 à 13 du pipeline) :
 M1 Nettoyage des tags Last.fm : années, nom de l'artiste, bruit (« my top songs »...),
    liste blanche : on ne garde que les tags d'humeur / contexte / attribut / époque / genre
 M2 Traduction des tags et des « seeds » MuSe en français (lexicon.py)
 M3 Macro-genre (14 valeurs) à partir des genres Spotify nettoyés
 M4 Humeurs : tags humains d'abord, quadrant de Russell (Spotify + MuSe) en complément
 M5 Contextes : tags humains + règles sur les caractéristiques audio
 M6 Descriptions françaises à variantes (+ genres fins, ressenti des auditeurs)
 M7 Fusion avec le jeu gold (doublons fusionnés : on garde la description écrite à la main)
"""
from __future__ import annotations

import ast
import random
import re
import zlib
from types import SimpleNamespace

import numpy as np
import pandas as pd

from . import config
from .lexicon import (CONTEXT_TO_BLOCK, GENRE_HINTS, MOOD_TO_BLOCK, NOISE_TAGS, OLD_TO_NEW_GENRE,
                      TAG_LEXICON, TAG_SYNONYMS)
from .p03_clean_spotify import pick_macro
from .p09_audio_to_text import energy_label, russell, tempo_label
from .p10_build_columns import contexts_from_audio
from .p11_descriptions import template_description
from .utils import clean_title, log, norm_key, track_key

COLLEAGUE = config.RAW / "dataset_final.csv"
OUT = config.PROCESSED / "moodify_dataset"
J = "|".join
EXTRA_NOISE = re.compile(r"(best of|my |fave|favorit|love at first|stars|loved|eargasm|amazing|legend|"
                         r"\bbop\b|masterpiece|\bfm\b|radio|\bsex|milf|swag|ratchet|cover)", re.I)
# Contexte typique associé à un bloc d'humeur (complète les règles audio)
MOOD_CONTEXT = {"Calme & détente": "détente", "Concentration": "étude", "Énergie & motivation": "sport",
                "Fête & danse": "soirée", "Mélancolie & introspection": "solitude",
                "Colère & défoulement": "sport", "Romance & sensualité": "moment à deux",
                "Joie & bonne humeur": "matin", "Rêverie & évasion": "trajet"}
GENRE_LABELS = {"Lo-fi / Chill", "Jazz / Blues", "Classique", "Ambient", "Électro / House", "Pop", "Rock",
                "Metal", "Hip-hop / Rap", "R&B / Soul / Funk", "Chanson française",
                "Indie / Folk / Country", "Afro / Reggae / Latino", "Musiques du monde"}


def _list(v) -> list:
    if isinstance(v, list):
        return v
    try:
        return list(ast.literal_eval(v)) if isinstance(v, str) and v.startswith("[") else []
    except (ValueError, SyntaxError):
        return []


def _uniq(seq):
    return list(dict.fromkeys(x for x in seq if x))


# --------------------------------------------------------------------- M3
# Genres Spotify ambigus (playlists d'humeur ou de pays) : faible poids
AMBIGUOUS = {"piano", "french", "emo", "sad", "happy", "party", "romance", "chill", "study", "sleep",
             "acoustic", "guitar", "british", "german", "swedish", "spanish", "indie", "alternative"}
# Tag Last.fm (genre) -> macro-genre, testé dans l'ordre (le premier motif trouvé gagne)
TAG_GENRE_RULES = [
    (("metal", "metalcore", "rapcore"), "Metal"),
    (("electropop", "synthpop", "dance-pop", "alt-pop", "dream pop", "indie pop", "power pop", "art pop",
      "baroque pop", "chamber pop", "sunshine pop", "jangle pop"), "Pop"),
    (("hip hop", "hip-hop", "hiphop", "rap", "trap", "boom bap", "gangsta"), "Hip-hop / Rap"),
    (("rnb", "r&b", "soul", "funk", "disco", "motown", "gospel", "new jack", "doo"), "R&B / Soul / Funk"),
    (("jazz", "blues", "swing", "bossa"), "Jazz / Blues"),
    (("modern classical", "classical", "impressionism", "minimalism", "orchestral"), "Classique"),
    (("ambient", "new age"), "Ambient"),
    (("trip", "chillout", "downtempo", "lo-fi", "jazz hop"), "Lo-fi / Chill"),
    (("house", "edm", "electro", "techno", "trance", "dubstep", "future bass", "synthwave", "electronic",
      "dance"), "Électro / House"),
    (("folk", "country", "singer-songwriter", "americana"), "Indie / Folk / Country"),
    (("reggae", "reggaeton", "latin", "dancehall", "salsa", "cuban", "ska"), "Afro / Reggae / Latino"),
    (("rock", "punk", "grunge", "emo", "new wave", "post-punk", "shoegaze", "britpop", "madchester",
      "merseybeat", "rockabilly", "aor"), "Rock"),
    (("pop", "boy band", "boyband"), "Pop"),
]


def macro_from_tag(tag: str) -> str | None:
    for keys, macro in TAG_GENRE_RULES:
        if any(k in tag for k in keys):
            return macro
    return None


def choose_macro(spotify_genres: list[str], lastfm_genre_tags: list[str]) -> str:
    """Vote pondéré : tags Last.fm (humains) > genres Spotify précis > genres Spotify ambigus."""
    from .lexicon import GENRE_TO_MACRO, MACRO_PRIORITY
    score: dict[str, float] = {}
    for i, t in enumerate(lastfm_genre_tags[:6]):
        m = macro_from_tag(t)
        if m:
            score[m] = score.get(m, 0) + 2.0 * (1 - 0.1 * i)
    for g in spotify_genres:
        m = GENRE_TO_MACRO.get(g)
        if m:
            score[m] = score.get(m, 0) + (0.3 if g in AMBIGUOUS else 1.5)
    if not score:
        return pick_macro(spotify_genres) or "Pop"
    best = max(score.values())
    return next(m for m in MACRO_PRIORITY if score.get(m) == best)


# ----------------------------------------------------------------- M1 + M2
def classify_tag(tag: str, artists: list[str]) -> tuple[str, str] | None:
    t = TAG_SYNONYMS.get(tag.lower().strip(), tag.lower().strip())
    if not t or t in NOISE_TAGS or re.fullmatch(r"\d{4}( single)?", t):
        return None
    if any(norm_key(a) and norm_key(a) in norm_key(t) for a in artists):   # nom d'artiste
        return None
    if t in TAG_LEXICON:
        return TAG_LEXICON[t]
    if re.fullmatch(r"(19)?\d0s|\d{4}s", t):
        return ("era", "années " + t.replace("19", "")[:3])
    if EXTRA_NOISE.search(t):
        return None
    if any(h in t for h in GENRE_HINTS):
        return ("genre", t)
    return None                                                               # liste blanche


def prepare_colleague() -> pd.DataFrame:
    d = pd.read_csv(COLLEAGUE)
    rows = []
    for r in d.itertuples():
        artists = [a.strip() for a in str(r.artists).split(";")]
        tags = {"mood": [], "context": [], "attribute": [], "era": [], "genre": []}
        for t in _list(r.seeds_list) + _list(r.lastfm_tags):             # seeds MuSe en premier
            c = classify_tag(t, artists)
            if c and c[1] not in tags[c[0]]:
                tags[c[0]].append(c[1])

        # M3 macro-genre
        macro = choose_macro(_list(r.clean_genres), tags["genre"])

        # M4 humeurs (Russell sur valence/arousal Spotify + MuSe ramenés à [0,1])
        mv = np.clip((r.valence_tags - 1) / 8, 0, 1) if pd.notna(r.valence_tags) else np.nan
        ma = np.clip((r.arousal_tags - 1) / 8, 0, 1) if pd.notna(r.arousal_tags) else np.nan
        v = (r.valence + mv) / 2 if pd.notna(mv) else r.valence
        a = (r.energy + ma) / 2 if pd.notna(ma) else r.energy
        quadrant, audio_moods = russell(v, a)
        human = tags["mood"]
        moods = human[:4] if len(human) >= 2 else _uniq(human + audio_moods)[:4]
        mood_source = "humain" if len(human) >= 2 else ("humain+audio" if human else "audio")

        # M5 contextes
        is_instr = r.instrumentalness >= config.INSTRUMENTAL_THRESHOLD
        is_dance = r.danceability >= config.DANCEABILITY_HIGH
        if is_dance and "dansant" not in moods and len(moods) < 4:
            moods.append("dansant")
        ns = SimpleNamespace(is_instrumental=is_instr, energy=r.energy, tempo=r.tempo,
                             is_danceable=is_dance, acousticness=r.acousticness, valence_final=v)
        audio_ctx = [c for c in contexts_from_audio(ns) if c != "trajet"]   # "trajet" = défaut neutre
        mood_ctx = [MOOD_CONTEXT[b] for b in _uniq(MOOD_TO_BLOCK.get(m) for m in moods) if b in MOOD_CONTEXT]
        contexts = _uniq(tags["context"] + audio_ctx + mood_ctx)[:4] or ["trajet"]

        lbl_acoustic = ("acoustique" if r.acousticness >= config.ACOUSTIC_HIGH else
                        "électronique / produit" if r.acousticness <= config.ACOUSTIC_LOW else "mixte")
        vocals = "instrumental" if is_instr else ("très parlé / rappé" if macro == "Hip-hop / Rap" else "chanté")
        rows.append({
            "track_id": r.track_id, "title": clean_title(r.track_name) or r.track_name,
            "artist": artists[0], "featured_artists": J(artists[1:]), "album": r.album_name,
            "genre": macro, "sub_genres": J(tags["genre"][:4] or _list(r.clean_genres)[:4]),
            "mood_list": moods, "context_list": contexts, "tags_mood": human, "tags_era": tags["era"],
            "attributes": tags["attribute"], "mood_source": mood_source,
            "energy": int(np.clip(np.ceil(r.energy * 5), 1, 5)),
            "language": "instrumental" if is_instr else "inconnu",
            "lbl_energy": energy_label(r.energy), "lbl_tempo": tempo_label(r.tempo),
            "lbl_acoustic": lbl_acoustic, "lbl_vocals": vocals, "has_human_tags": bool(human),
            "russell_quadrant": quadrant, "popularity": r.popularity, "danceability": r.danceability,
            "energy_raw": r.energy, "valence": r.valence, "acousticness": r.acousticness,
            "instrumentalness": r.instrumentalness, "tempo": round(r.tempo, 1),
            "muse_valence": round(float(mv), 3) if pd.notna(mv) else None,
            "muse_arousal": round(float(ma), 3) if pd.notna(ma) else None,
            "source": "spotify+muse+lastfm",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------- M6
def describe(df: pd.DataFrame) -> pd.DataFrame:
    descs = []
    for r in df.itertuples():
        rng = random.Random(config.DESCRIPTION_SEED + zlib.crc32(r.track_id.encode()))
        d = template_description(SimpleNamespace(
            title=r.title, artist=r.artist, macro_genre=r.genre, lbl_vocals=r.lbl_vocals,
            mood_list=r.mood_list, lbl_tempo=r.lbl_tempo, lbl_energy=r.lbl_energy,
            lbl_acoustic=r.lbl_acoustic, context_list=r.context_list, tags_mood=r.tags_mood,
            tags_era=r.tags_era), rng)
        subs = [s for s in r.sub_genres.split("|") if s]
        subs = [s for s in subs if not any(s != o and s in o for o in subs)][:3]   # « songwriter » ⊂ « singer-songwriter »
        if subs:
            d += " " + rng.choice(["Dans la veine {}.", "Style : {}.", "Influences : {}."]).format(", ".join(subs))
        descs.append(d)
    df["description"] = descs
    df["description_source"] = np.where(df["has_human_tags"], "template_tags", "template_audio")
    return df


# ----------------------------------------------------------------------- M7
def prepare_gold() -> pd.DataFrame:
    g = pd.read_csv(config.GOLD_TRACKS, dtype=str).fillna("")
    return pd.DataFrame({
        "track_id": g["track_id"], "title": g["title"], "artist": g["artist"], "featured_artists": "",
        "album": "", "genre": g["genre"].map(lambda x: OLD_TO_NEW_GENRE.get(x, x)), "sub_genres": g["genre"],
        "mood_list": g["mood"].str.split("|"), "context_list": g["context"].str.split("|"),
        "attributes": g["keywords"].str.split("|"), "mood_source": "manuel",
        "energy": g["energy"].astype(int), "language": g["language"], "description": g["description"],
        "description_source": "manuel", "source": "gold (équipe)",
    })


def run() -> None:
    if not COLLEAGUE.exists():
        raise FileNotFoundError(f"Placez le fichier du collègue ici : {COLLEAGUE}")
    col = describe(prepare_colleague())
    gold = prepare_gold()

    # Doublons internes (même titre nettoyé, ex. version single / album) : on garde la plus populaire,
    # en privilégiant celle qui a des tags humains
    col["key"] = [track_key(a, t) for a, t in zip(col["artist"], col["title"])]
    n0 = len(col)
    col = (col.sort_values(["has_human_tags", "popularity"], ascending=False)
              .drop_duplicates("key").sort_index().reset_index(drop=True))
    log.info("Doublons internes supprimés : %d", n0 - len(col))

    # Doublons gold ↔ collègue : description manuelle + données Spotify du collègue
    gold["key"] = [track_key(a, t) for a, t in zip(gold["artist"], gold["title"])]
    common = set(col["key"]) & set(gold["key"])
    for k in common:
        gi = gold.index[gold["key"] == k][0]
        ci = col.index[col["key"] == k][0]
        for c in ("description", "mood_list", "context_list", "language"):
            col.at[ci, c] = gold.at[gi, c]
        col.at[ci, "description_source"] = col.at[ci, "mood_source"] = "manuel"
        col.at[ci, "source"] = "spotify+muse+lastfm + gold"
    df = pd.concat([col, gold[~gold["key"].isin(common)]], ignore_index=True)

    df["mood_blocks"] = df["mood_list"].map(lambda l: J(_uniq(MOOD_TO_BLOCK.get(m) for m in l)))
    df["context_blocks"] = df["context_list"].map(lambda l: J(_uniq(CONTEXT_TO_BLOCK.get(c) for c in l)))
    df["keywords"] = [J(_uniq(list(a if isinstance(a, list) else []) + [s for s in str(sg).split("|") if s][:3]
                              + (list(m)[:2] if isinstance(m, list) else []))[:7])
                      for a, sg, m in zip(df["attributes"], df["sub_genres"], df["tags_mood"])]
    df["mood"] = df["mood_list"].map(J)
    df["context"] = df["context_list"].map(J)
    df["tags_mood_human"] = df["tags_mood"].map(lambda l: J(l) if isinstance(l, list) else "")
    assert set(df["genre"]) <= GENRE_LABELS, set(df["genre"]) - GENRE_LABELS

    cols = ["track_id", "title", "artist", "featured_artists", "album", "genre", "sub_genres", "mood",
            "context", "energy", "language", "description", "keywords", "mood_blocks", "context_blocks",
            "tags_mood_human", "mood_source", "description_source", "source", "popularity",
            "danceability", "energy_raw", "valence", "acousticness", "instrumentalness", "tempo",
            "muse_valence", "muse_arousal", "russell_quadrant"]
    df = df[cols]
    df.to_csv(OUT.with_suffix(".csv"), index=False)
    df.to_json(OUT.with_suffix(".json"), orient="records", force_ascii=False, indent=1)
    log.info("Fusion : %d morceaux (%d collègue après dédoublonnage, %d gold, %d en commun) -> %s",
             len(df), len(col), len(gold), len(common), OUT.with_suffix(".csv"))


if __name__ == "__main__":
    run()
