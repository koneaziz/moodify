"""Génère de FAUX fichiers bruts au schéma exact de Spotify Tracks et MuSe, pour tester le
pipeline sans les vrais téléchargements. NE PAS utiliser ces données pour le projet.

    python tests/fixtures/make_mock_raw.py   # écrit data/raw/spotify_tracks.csv et muse_v3.csv
"""
from __future__ import annotations

import random
import string
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
rng = np.random.default_rng(0)
R = random.Random(0)

GENRES = ["acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", "black-metal", "blues",
          "brazil", "chill", "classical", "club", "comedy", "country", "dance", "dancehall", "death-metal",
          "deep-house", "disco", "drum-and-bass", "dub", "edm", "electro", "electronic", "emo", "folk",
          "french", "funk", "gospel", "grunge", "happy", "hard-rock", "heavy-metal", "hip-hop", "house",
          "idm", "indie", "indie-pop", "jazz", "k-pop", "kids", "latin", "metal", "new-age", "opera",
          "party", "piano", "pop", "punk", "r-n-b", "reggae", "reggaeton", "rock", "romance", "sad",
          "salsa", "singer-songwriter", "sleep", "soul", "study", "synth-pop", "techno", "trance",
          "trip-hop", "world-music"]
# profils audio moyens par famille (energy, valence, acousticness, instrumentalness, danceability)
PROFILE = {"calm": (.2, .35, .8, .7, .4), "dance": (.85, .7, .05, .2, .8), "heavy": (.92, .3, .02, .1, .45),
           "pop": (.65, .6, .2, .02, .68), "rap": (.7, .5, .15, .01, .78), "sad": (.3, .2, .6, .05, .45)}
FAMILY = {g: "calm" for g in ["ambient", "chill", "classical", "new-age", "piano", "sleep", "study", "jazz", "acoustic", "folk"]}
FAMILY.update({g: "dance" for g in ["club", "dance", "deep-house", "edm", "electro", "house", "techno", "trance", "party", "reggaeton", "salsa", "afrobeat", "disco", "funk"]})
FAMILY.update({g: "heavy" for g in ["black-metal", "death-metal", "heavy-metal", "metal", "hard-rock", "punk", "grunge"]})
FAMILY.update({g: "rap" for g in ["hip-hop", "dancehall"]})
FAMILY.update({g: "sad" for g in ["sad", "emo", "blues", "soul"]})

GOLD = pd.read_csv(ROOT / "data" / "tracks.csv")
SEEDS = ["sad", "happy", "mellow", "aggressive", "calm", "energetic", "romantic", "dreamy", "dark",
         "nostalgic", "melancholy", "cheerful", "angry", "sentimental", "playful", "intense", "relaxed"]


def word():
    return "".join(R.choices(string.ascii_lowercase, k=R.randint(4, 8))).capitalize()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    artists = [f"{word()} {word()}" for _ in range(900)]
    tid = 0
    for g in GENRES:
        e, v, a, ins, d = PROFILE[FAMILY.get(g, "pop")]
        for _ in range(110):
            tid += 1
            rows.append({
                "track_id": f"sp{tid:07d}", "artists": R.choice(artists) + (f";{R.choice(artists)}" if R.random() < .15 else ""),
                "album_name": f"{word()} {word()}", "track_name": f"{word()} {word()}",
                "popularity": int(rng.integers(0, 90)), "duration_ms": int(rng.normal(210000, 60000)),
                "explicit": bool(R.random() < .15),
                "danceability": float(np.clip(rng.normal(d, .12), 0, 1)), "energy": float(np.clip(rng.normal(e, .12), 0, 1)),
                "key": int(rng.integers(0, 12)), "loudness": float(rng.normal(-8, 3)), "mode": int(rng.integers(0, 2)),
                "speechiness": float(np.clip(rng.normal(.25 if g == "hip-hop" else .05, .08), 0, 1)),
                "acousticness": float(np.clip(rng.normal(a, .15), 0, 1)),
                "instrumentalness": float(np.clip(rng.normal(ins, .2), 0, 1)),
                "liveness": float(np.clip(rng.normal(.18, .1), 0, 1)), "valence": float(np.clip(rng.normal(v, .15), 0, 1)),
                "tempo": float(np.clip(rng.normal(120 if FAMILY.get(g) != "calm" else 85, 20), 50, 200)),
                "time_signature": 4, "track_genre": g})
    # morceaux du jeu gold (pour tester leur récupération)
    for r in GOLD.itertuples():
        tid += 1
        rows.append({**rows[R.randrange(len(rows))], "track_id": f"sp{tid:07d}", "artists": r.artist,
                     "track_name": r.title, "popularity": 70, "track_genre": "pop"})
    df = pd.DataFrame(rows)
    # doublons : même track_id sous un autre genre, versions remasterisées, valeurs manquantes
    dup = df.sample(600, random_state=1).assign(track_genre=lambda x: x["track_genre"].map(lambda _: R.choice(GENRES)))
    ver = df.sample(300, random_state=2).copy()
    ver["track_id"] = [f"v{i:07d}" for i in range(len(ver))]
    ver["track_name"] = ver["track_name"] + " - Remastered 2011"
    ver["popularity"] = (ver["popularity"] * .5).astype(int)
    df = pd.concat([df, dup, ver], ignore_index=True)
    df.loc[df.sample(5, random_state=3).index, "track_name"] = None
    df.insert(0, "Unnamed: 0", range(len(df)))
    df.to_csv(RAW / "spotify_tracks.csv", index=False)

    # MuSe : recouvre ~45 % des morceaux (ids exacts, titres exacts sans id, titres modifiés -> fuzzy)
    base = df.dropna(subset=["track_name"]).drop_duplicates("track_id").sample(3500, random_state=4)
    mu = []
    for i, r in enumerate(base.itertuples()):
        mode = i % 3
        title = r.track_name if mode < 2 else r.track_name[:-1] + "s"   # faute de frappe -> fuzzy
        mu.append({"lastfm_url": "", "track": title, "artist": r.artists.split(";")[0],
                   "seeds": str(R.sample(SEEDS, R.randint(1, 3))), "number_of_emotion_tags": R.randint(1, 20),
                   "valence_tags": round(R.uniform(2, 8), 2), "arousal_tags": round(R.uniform(2, 7), 2),
                   "dominance_tags": round(R.uniform(3, 7), 2), "mbid": "",
                   "spotify_id": r.track_id if mode == 0 else None, "genre": "pop"})
    for _ in range(1500):  # morceaux absents de Spotify
        mu.append({"lastfm_url": "", "track": word(), "artist": word(), "seeds": str(R.sample(SEEDS, 2)),
                   "number_of_emotion_tags": 3, "valence_tags": 5, "arousal_tags": 5, "dominance_tags": 5,
                   "mbid": "", "spotify_id": None, "genre": "rock"})
    pd.DataFrame(mu).to_csv(RAW / "muse_v3.csv", index=False)
    print(f"mock : spotify {len(df)} lignes, muse {len(mu)} lignes -> {RAW}")


if __name__ == "__main__":
    main()
