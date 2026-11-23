"""PHASE 7 — ENRICHISSEMENT VIA L'API LAST.FM

Pour chaque morceau de l'échantillon :
 - track.getTopTags  (tags écrits par les auditeurs, avec un poids 0-100)
 - repli artist.getTopTags si le morceau n'a aucun tag
Pour chaque artiste :
 - artist.getInfo    (courte biographie, nettoyée du HTML)

Bonnes pratiques :
 - clé API dans la variable d'environnement LASTFM_API_KEY (https://www.last.fm/api/account/create)
 - CACHE disque : chaque réponse est stockée dans data/cache/lastfm/ -> jamais deux fois le même appel,
   le pipeline peut être relancé / interrompu sans perte
 - limitation du débit (LASTFM_SLEEP_S) et nouvelles tentatives en cas d'erreur réseau
Sans clé, la phase est sautée proprement (les tags MuSe et les genres-humeurs restent disponibles).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request

import pandas as pd

from . import config
from .utils import load_interim, log, phase_timer, report, save_interim

API = "https://ws.audioscrobbler.com/2.0/"
CACHE_DIR = config.CACHE / "lastfm"


def _cached_call(params: dict, retries: int = 3) -> dict | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if not config.LASTFM_API_KEY:
        return None
    q = {**params, "api_key": config.LASTFM_API_KEY, "format": "json", "autocorrect": 1}
    url = API + "?" + urllib.parse.urlencode(q)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            time.sleep(config.LASTFM_SLEEP_S)
            return data
        except Exception as exc:  # réseau, quota...
            log.debug("    Last.fm erreur (%s), tentative %d", exc, attempt + 1)
            time.sleep(2 ** attempt)
    return None


def _tags(data: dict | None) -> list[tuple[str, int]]:
    if not data or "toptags" not in data:
        return []
    tags = data["toptags"].get("tag", [])
    tags = tags if isinstance(tags, list) else [tags]
    out = [(t["name"].lower().strip(), int(t.get("count", 0))) for t in tags]
    return [(n, c) for n, c in out if c >= config.LASTFM_MIN_TAG_COUNT][: config.LASTFM_MAX_TAGS]


def _bio(data: dict | None) -> str:
    try:
        txt = data["artist"]["bio"]["summary"]
    except (TypeError, KeyError):
        return ""
    txt = re.sub(r"<a [^>]*>.*?</a>", "", txt)           # lien « Read more on Last.fm »
    txt = re.sub(r"<[^>]+>", "", txt).strip()
    return txt[:600]


def run() -> None:
    with phase_timer("P07 Enrichissement Last.fm"):
        df = load_interim("p06_joined")
        has_cache = CACHE_DIR.exists() and any(CACHE_DIR.glob("*.json"))
        if not config.LASTFM_API_KEY and not has_cache:
            log.warning("  pas de LASTFM_API_KEY ni de cache → phase sautée")
            df["lastfm_tags"] = [[] for _ in range(len(df))]
            df["lastfm_tag_weights"] = [[] for _ in range(len(df))]
            df["lastfm_tag_source"] = "aucun"
            df["artist_bio"] = ""
            save_interim(df, "p07_lastfm")
            report("P07_lastfm", skipped=True)
            return

        rows = df if config.LASTFM_MAX_CALLS is None else df.head(config.LASTFM_MAX_CALLS)
        tags, weights, source = [], [], []
        for i, r in enumerate(rows.itertuples()):
            t = _tags(_cached_call({"method": "track.getTopTags", "artist": r.artist, "track": r.title}))
            src = "morceau"
            if not t:
                t = _tags(_cached_call({"method": "artist.getTopTags", "artist": r.artist}))
                src = "artiste" if t else "aucun"
            tags.append([n for n, _ in t]); weights.append([c for _, c in t]); source.append(src)
            if (i + 1) % 100 == 0:
                log.info("    %d / %d morceaux", i + 1, len(rows))
        pad = len(df) - len(rows)
        df["lastfm_tags"] = tags + [[]] * pad
        df["lastfm_tag_weights"] = weights + [[]] * pad
        df["lastfm_tag_source"] = source + ["aucun"] * pad

        bios = {a: _bio(_cached_call({"method": "artist.getInfo", "artist": a}))
                for a in df["artist"].unique()}
        df["artist_bio"] = df["artist"].map(bios)

        save_interim(df, "p07_lastfm")
        stats = df["lastfm_tag_source"].value_counts().to_dict()
        log.info("  source des tags : %s", stats)
        report("P07_lastfm", tag_source=stats,
               artists_with_bio=int(sum(1 for b in bios.values() if b)))
