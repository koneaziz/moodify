"""PHASE 10 — CONSTRUCTION DES COLONNES mood / context / keywords

Règle de priorité (documentée pour la soutenance) :
  1. tags HUMAINS (Last.fm, MuSe, genres-humeurs Spotify) — ce que les auditeurs ressentent
  2. complétés par les humeurs AUDIO (quadrant de Russell) si moins de 2 humeurs humaines
  3. contextes : tags humains + règles explicites sur les caractéristiques audio

Règles de contexte (10.2) :
  instrumental & énergie ≤ modérée          -> étude, concentration
  énergie ≥ 0.8 & tempo ≥ 120               -> sport
  dansant & énergie ≥ 0.6                   -> soirée
  acoustique & énergie < 0.3                -> sommeil / détente
  valence basse & énergie basse              -> pluie / solitude
  valence haute & acoustique / mixte         -> matin
"""
from __future__ import annotations

from .lexicon import CONTEXT_TO_BLOCK, MOOD_TO_BLOCK
from .utils import load_interim, log, phase_timer, report, save_interim


def _uniq(seq):
    return list(dict.fromkeys(x for x in seq if x))


def contexts_from_audio(r) -> list[str]:
    ctx = []
    if r.is_instrumental and r.energy < 0.55:
        ctx += ["étude", "concentration"]
    if r.energy >= 0.8 and r.tempo >= 120:
        ctx.append("sport")
    if r.is_danceable and r.energy >= 0.6:
        ctx.append("soirée")
    if r.acousticness >= 0.6 and r.energy < 0.3:
        ctx += ["détente", "sommeil"]
    if r.valence_final < 0.35 and r.energy < 0.45:
        ctx += ["pluie", "solitude"]
    if r.valence_final >= 0.6 and r.acousticness >= 0.3:
        ctx.append("matin")
    if not ctx:
        ctx.append("trajet")   # contexte neutre par défaut
    return ctx


def run() -> None:
    with phase_timer("P10 Colonnes mood / context / keywords"):
        df = load_interim("p09_audio_text")

        moods, ctxs, srcs, kws = [], [], [], []
        for r in df.itertuples():
            human = _uniq(r.tags_mood)
            m = human[:4]
            src = "humain"
            if len(m) < 2:
                m = _uniq(m + list(r.audio_moods))[:4]
                src = "humain+audio" if human else "audio"
            if r.is_danceable and "dansant" not in m and len(m) < 4:
                m.append("dansant")
            moods.append(m)
            srcs.append(src)

            c = _uniq(list(r.tags_context) + contexts_from_audio(r))[:4]
            ctxs.append(c)

            kw = _uniq(list(r.tags_attribute) + list(r.tags_genre)[:2] + list(r.tags_era)[:1]
                       + [r.lbl_vocals, r.lbl_acoustic if r.lbl_acoustic != "mixte" else None,
                          f"tempo {r.lbl_tempo}"] + human[:2])[:7]
            kws.append(kw)

        df["mood_list"], df["context_list"], df["mood_source"], df["keyword_list"] = moods, ctxs, srcs, kws
        df["mood_blocks"] = df["mood_list"].map(lambda l: _uniq(MOOD_TO_BLOCK.get(m) for m in l))
        df["context_blocks"] = df["context_list"].map(lambda l: _uniq(CONTEXT_TO_BLOCK.get(c) for c in l))

        save_interim(df, "p10_columns")
        dist = df["mood_source"].value_counts().to_dict()
        no_block = int((df["mood_blocks"].map(len) == 0).sum())
        log.info("  source des humeurs : %s ; morceaux sans bloc d'humeur : %d", dist, no_block)
        report("P10_build_columns", mood_source=dist, tracks_without_mood_block=no_block)
