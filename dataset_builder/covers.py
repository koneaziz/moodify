"""POCHETTES : colonne `cover_url` (image de l'album) à partir des identifiants Spotify.

    python -m dataset_builder.covers            # ajoute / met à jour cover_url dans data/moodify_dataset.{json,csv}
    python -m dataset_builder.covers --offline  # idem, en n'utilisant que le cache (aucun appel réseau)

Source : point d'accès public oEmbed de Spotify (aucune clé d'API) :
    https://open.spotify.com/oembed?url=https://open.spotify.com/track/<track_id>
Seuls les track_id de 22 caractères (vrais identifiants Spotify) ont une pochette ; le jeu gold (T001…) reste vide.

CACHE : data/spotify_covers_cache.json (versionné, comme lastfm_tags_cache.json) → jamais deux fois le même
appel ; une régénération du dataset retrouve les pochettes sans réseau.

`merge_datasets.py` appelle `cover_urls()` : la colonne est donc présente à chaque régénération. La commande
ci-dessus sert à l'ajouter aux fichiers existants sans relancer la fusion (les autres colonnes ne sont pas réécrites).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config
from .utils import log

SPOTIFY_ID = re.compile(r"^[A-Za-z0-9]{22}$")
OEMBED = "https://open.spotify.com/oembed?url="
COLUMN = "cover_url"


def _load_cache() -> dict[str, str | None]:
    if config.COVERS_CACHE.exists():
        return json.loads(config.COVERS_CACHE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, str | None]) -> None:
    config.COVERS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                                   encoding="utf-8")


def _fetch(track_id: str) -> str | None:
    """URL de la pochette d'un morceau Spotify, None si Spotify n'en a pas. Lève URLError si hors ligne."""
    url = OEMBED + urllib.parse.quote(f"https://open.spotify.com/track/{track_id}", safe="")
    req = urllib.request.Request(url, headers={"User-Agent": "moodify-dataset-builder"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.load(r).get("thumbnail_url") or None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 and attempt < 2:
                time.sleep(int(e.headers.get("Retry-After", "5")))
                continue
            raise
    return None


def cover_urls(track_ids, offline: bool | None = None) -> list[str]:
    """Une URL de pochette (ou "") par track_id, en complétant le cache si le réseau le permet."""
    offline = (not config.FETCH_COVERS) if offline is None else offline
    ids = [str(t) for t in track_ids]
    cache = _load_cache()
    missing = list(dict.fromkeys(t for t in ids if SPOTIFY_ID.match(t) and t not in cache))
    if missing and offline:
        log.info("Pochettes : %d morceaux absents du cache (mode hors ligne) → cover_url vide", len(missing))
    elif missing:
        log.info("Pochettes : interrogation de Spotify pour %d morceaux…", len(missing))
        try:
            for i, t in enumerate(missing, 1):
                cache[t] = _fetch(t)
                if i % 50 == 0:
                    _save_cache(cache)
                    log.info("  %d/%d", i, len(missing))
                time.sleep(config.COVERS_SLEEP_S)
        except (urllib.error.URLError, TimeoutError) as e:
            log.warning("Pochettes : Spotify injoignable (%s) → on garde le cache", e)
        finally:
            _save_cache(cache)
    urls = [cache.get(t) or "" for t in ids]
    log.info("Pochettes : %d/%d morceaux ont une cover_url", sum(map(bool, urls)), len(urls))
    return urls


# ------------------------------------------------- mise à jour des fichiers existants
def _json_str(value: str) -> str:
    # même rendu que pandas.to_json (accents conservés, « / » échappé)
    return json.dumps(value, ensure_ascii=False).replace("/", "\\/")


def _patch_json(path, covers: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    records = json.loads(text)
    ends = [m.start() for m in re.finditer(r"\n \}", text)]
    if len(ends) != len(records):
        raise SystemExit(f"{path} : mise en forme inattendue (un « \\n }} » par morceau attendu), rien n'est modifié.")
    out, prev = [], 0
    for rec, end in zip(records, ends):
        block, value = text[prev:end], _json_str(covers[rec["track_id"]])
        if f'"{COLUMN}":' in block:
            block = re.sub(rf'"{COLUMN}":"(?:[^"\\]|\\.)*"', lambda _: f'"{COLUMN}":{value}', block)
        else:
            block += f',\n  "{COLUMN}":{value}'
        out.append(block)
        prev = end
    out.append(text[prev:])
    path.write_text("".join(out), encoding="utf-8")


def _patch_csv(path, covers: dict[str, str]) -> None:
    raw = path.read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(raw, newline="")))
    header, body = rows[0], rows[1:]
    if COLUMN not in header:
        header.append(COLUMN)
        for row in body:
            row.append("")
    col, id_col = header.index(COLUMN), header.index("track_id")
    for row in body:
        row[col] = covers.get(row[id_col], "")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n" if "\r\n" in raw else "\n").writerows([header, *body])
    path.write_text(buf.getvalue(), encoding="utf-8", newline="")


def run(offline: bool | None = None) -> None:
    targets = [p for base in (config.DATA, config.PROCESSED) for p in [base / "moodify_dataset.json"] if p.exists()]
    if not targets:
        raise FileNotFoundError("Aucun moodify_dataset.json dans data/ ni data/processed/")
    ids = [r["track_id"] for r in json.loads(targets[0].read_text(encoding="utf-8"))]
    covers = dict(zip(ids, cover_urls(ids, offline)))
    for js in targets:
        _patch_json(js, covers)
        if js.with_suffix(".csv").exists():
            _patch_csv(js.with_suffix(".csv"), covers)
        log.info("cover_url ajoutée -> %s (+ .csv)", js)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ajoute la colonne cover_url au dataset Moodify")
    ap.add_argument("--offline", action="store_true", help="n'utiliser que data/spotify_covers_cache.json")
    run(offline=True if ap.parse_args().offline else None)
