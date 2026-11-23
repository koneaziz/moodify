"""PHASE 11 — GÉNÉRATION DES DESCRIPTIONS EN LANGAGE NATUREL (français)

La description est le texte que SBERT comparera aux phrases de l'utilisateur.
 11.1 Modèles de phrases à PLUSIEURS VARIANTES par segment (présentation, humeur, son,
      contexte, ressenti des auditeurs) choisies de façon reproductible (graine = track_id).
      Sans variantes, toutes les descriptions se ressemblent et le cosinus ne discrimine plus.
 11.2 (optionnel, USE_LLM=1) reformulation par un LLM local (Ollama) qui reçoit UNIQUEMENT
      les champs du morceau et a l'interdiction d'inventer — repli sur le modèle si échec.
 11.3 Traçabilité : colonne description_source (template_tags | template_audio | llm)
"""
from __future__ import annotations

import json
import random
import urllib.request
import zlib

from . import config
from .lexicon import MACRO_PHRASE
from .utils import load_interim, log, phase_timer, report, save_interim

INTRO = [
    "« {title} » de {artist} est un morceau {genre}{vocals}.",
    "Signé {artist}, « {title} » est un titre {genre}{vocals}.",
    "Avec « {title} », {artist} propose un morceau {genre}{vocals}.",
    "« {title} » ({artist}) : un titre {genre}{vocals}.",
]
MOOD = [
    "Le climat est {m1} et {m2}.",
    "Son univers se veut {m1}, presque {m2}.",
    "On y ressent quelque chose {de_m1} et {de_m2}.",
    "L'ensemble est {m1}, avec un côté {m2}.",
]
MOOD_ONE = ["Le climat est {m1}.", "On y ressent quelque chose {de_m1}.", "L'ensemble est {m1}."]
SOUND = [
    "Le tempo est {tempo}, avec {energy}{acoustic}.",
    "Côté son : un tempo {tempo}, {energy}{acoustic}.",
    "Il avance sur un tempo {tempo}, avec {energy}{acoustic}.",
]
CONTEXT = [
    "Idéal pour {c1}{c2}.", "Parfait pour {c1}{c2}.", "À écouter pour {c1}{c2}.",
    "Une bonne bande-son pour {c1}{c2}.",
]
LISTENERS = [
    "Les auditeurs le décrivent comme {t}.", "Souvent associé à : {t}.",
    "Les fans y entendent quelque chose {de_t}.",
]

VOCALS = {"instrumental": ", entièrement instrumental", "chanté": " porté par la voix",
          "très parlé / rappé": " au flow très présent"}
ENERGY = {"calme": "une énergie douce", "modéré": "une énergie modérée",
          "énergique": "une énergie soutenue", "très énergique": "une énergie explosive"}
ACOUSTIC = {"acoustique": " et des sonorités acoustiques",
            "électronique / produit": " et une production électronique", "mixte": ""}
CONTEXT_PHRASE = {
    "étude": "réviser", "concentration": "se concentrer", "travail": "travailler",
    "sport": "le sport", "course": "courir", "entraînement": "s'entraîner",
    "soirée": "les soirées", "club": "le club", "danse": "danser", "conduite": "conduire",
    "route": "les longues routes", "voyage": "voyager", "trajet": "les trajets",
    "sommeil": "s'endormir", "méditation": "méditer", "détente": "se détendre",
    "moment à deux": "un moment à deux", "pluie": "les jours de pluie",
    "nuit": "les nuits tardives", "solitude": "les moments de solitude",
    "matin": "bien commencer la journée", "été": "les journées d'été", "cuisine": "cuisiner",
}


def de(word: str) -> str:
    """Élision française : de + apaisant -> d'apaisant."""
    return f"d'{word}" if word[:1].lower() in "aâeéèêiîoôuûyh" else f"de {word}"


def template_description(r, rng: random.Random) -> str:
    parts = [rng.choice(INTRO).format(title=r.title, artist=r.artist,
                                      genre=MACRO_PHRASE.get(r.macro_genre, "musical"),
                                      vocals=VOCALS.get(r.lbl_vocals, ""))]
    m = list(r.mood_list)
    if len(m) >= 2:
        parts.append(rng.choice(MOOD).format(m1=m[0], m2=m[1], de_m1=de(m[0]), de_m2=de(m[1])))
    elif m:
        parts.append(rng.choice(MOOD_ONE).format(m1=m[0], de_m1=de(m[0])))
    parts.append(rng.choice(SOUND).format(tempo=r.lbl_tempo, energy=ENERGY[r.lbl_energy],
                                          acoustic=ACOUSTIC[r.lbl_acoustic]))
    c = [CONTEXT_PHRASE.get(x, x) for x in r.context_list][:2]
    if c:
        parts.append(rng.choice(CONTEXT).format(c1=c[0], c2=f" ou {c[1]}" if len(c) > 1 else ""))
    human = [t for t in r.tags_mood if t not in m[:2]][:3]
    if human:
        parts.append(rng.choice(LISTENERS).format(t=", ".join(human), de_t=de(", ".join(human))))
    if len(r.tags_era):
        parts.append(f"Un son qui évoque les {r.tags_era[0]}." if r.tags_era[0].startswith("années")
                     else "Un classique d'antan.")
    return " ".join(parts)


def llm_rewrite(text: str, r) -> str | None:
    """Reformulation par un LLM local (Ollama). Le prompt interdit toute invention."""
    prompt = (
        "Réécris en français cette description musicale en 2 ou 3 phrases fluides (40 à 60 mots). "
        "N'ajoute AUCUNE information absente (pas de date, pas d'anecdote, pas de paroles). "
        f"Données : titre={r.title}; artiste={r.artist}; genre={r.macro_genre}; "
        f"humeurs={', '.join(r.mood_list)}; contextes={', '.join(r.context_list)}.\n"
        f"Description : {text}\nRéécriture :")
    body = json.dumps({"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.4}}).encode()
    try:
        req = urllib.request.Request(config.OLLAMA_URL + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read())["response"].strip()
        return out if 20 <= len(out.split()) <= 90 else None
    except Exception:
        return None


def run() -> None:
    with phase_timer("P11 Descriptions"):
        df = load_interim("p10_columns")
        descs, sources = [], []
        n_llm = 0
        for r in df.itertuples():
            rng = random.Random(config.DESCRIPTION_SEED + zlib.crc32(r.track_id.encode()))
            d = template_description(r, rng)
            src = "template_tags" if r.has_human_tags else "template_audio"
            if config.USE_LLM:
                new = llm_rewrite(d, r)
                if new:
                    d, src = new, "llm"
                    n_llm += 1
            descs.append(d)
            sources.append(src)
        df["description"] = descs
        df["description_source"] = sources
        df["description_words"] = df["description"].str.split().map(len)

        save_interim(df, "p11_descriptions")
        log.info("  exemple :\n    %s", df["description"].iloc[0])
        log.info("  longueur moyenne : %.0f mots ; sources : %s", df["description_words"].mean(),
                 df["description_source"].value_counts().to_dict())
        report("P11_descriptions", sources=df["description_source"].value_counts().to_dict(),
               mean_words=round(float(df["description_words"].mean()), 1), llm_rewrites=n_llm)
