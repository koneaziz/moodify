"""Configuration centrale du pipeline de construction du dataset.

Tous les chemins, seuils et paramètres sont ici : chaque choix est documenté et
modifiable sans toucher au code des phases.
"""
from __future__ import annotations

import os
from pathlib import Path

# =============================================================================
# CHEMINS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"              # fichiers bruts téléchargés (jamais modifiés, non versionnés)
INTERIM = DATA / "interim"      # sorties intermédiaires de chaque phase
PROCESSED = DATA / "processed"  # dataset final utilisé par l'application
CACHE = DATA / "cache"          # cache des appels API (Last.fm, Ticketmaster)
REPORTS = ROOT / "reports"      # figures, rapports qualité, fiche du dataset
GOLD_TRACKS = DATA / "tracks.csv"        # 84 morceaux rédigés à la main (jeu « gold »)
REFERENCE_FILES = DATA                   # blocks.json, archetypes.json, questionnaire.json...

# Noms attendus des fichiers bruts (déposez-les dans data/raw/)
SPOTIFY_RAW = RAW / "spotify_tracks.csv"   # Kaggle maharshipandya/-spotify-tracks-dataset (dataset.csv renommé)
MUSE_RAW = RAW / "muse_v3.csv"             # Kaggle / Zenodo MuSe

# =============================================================================
# CLÉS API (variables d'environnement, jamais en dur dans le code)
# =============================================================================
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# =============================================================================
# PHASE 3 — NETTOYAGE SPOTIFY
# =============================================================================
MIN_DURATION_MS = 60_000           # < 1 min : interludes, intros, sketches
MAX_DURATION_MS = 600_000          # > 10 min : mixes, albums concaténés
MIN_POPULARITY = 15                # morceaux quasi inconnus = métadonnées peu fiables
EXCLUDED_GENRES = {"kids", "children", "comedy", "disney", "show-tunes"}

# =============================================================================
# PHASE 4 — ÉCHANTILLONNAGE
# =============================================================================
TRACKS_PER_MACRO_GENRE = 150       # ~14 macro-genres → ~2 000 morceaux
SAMPLE_SEED = 42
MAX_TRACKS_PER_ARTIST = 6          # évite qu'un artiste monopolise un genre

# =============================================================================
# PHASE 6 — JOINTURE
# =============================================================================
FUZZY_THRESHOLD = 90               # score rapidfuzz (0-100) pour accepter une correspondance
FUZZY_REVIEW_SAMPLE = 50           # nb de correspondances à vérifier à la main

# =============================================================================
# PHASE 7 — LAST.FM
# =============================================================================
LASTFM_MAX_TAGS = 10
LASTFM_MIN_TAG_COUNT = 5           # poids Last.fm (0-100) minimum pour garder un tag
LASTFM_SLEEP_S = 0.25              # ≤ 4 requêtes / seconde
LASTFM_MAX_CALLS = None            # None = tout l'échantillon ; un entier pour tester

# =============================================================================
# PHASE 8 — TAGS
# =============================================================================
TAG_MIN_FREQUENCY = 2              # un tag vu sur moins de 2 morceaux est jeté (bruit)
TAG_SEMANTIC_THRESHOLD = {"sbert": 0.45, "tfidf": 0.25}  # cosinus min. pour classer un tag inconnu

# =============================================================================
# PHASE 9 — AUDIO → TEXTE (seuils sur les caractéristiques Spotify, échelle 0-1)
# =============================================================================
ENERGY_BINS = [0.30, 0.55, 0.80]           # calme | modéré | énergique | très énergique
VALENCE_SPLIT = 0.50                       # quadrant de Russell (valence × énergie)
ENERGY_SPLIT = 0.50
ACOUSTIC_HIGH, ACOUSTIC_LOW = 0.60, 0.15
INSTRUMENTAL_THRESHOLD = 0.50
SPEECHINESS_RAP = 0.33
DANCEABILITY_HIGH = 0.70
TEMPO_BINS = [90, 120]                     # lent | modéré | rapide (BPM)

# =============================================================================
# PHASE 11 — DESCRIPTIONS
# =============================================================================
USE_LLM = os.getenv("USE_LLM", "0") == "1"  # reformulation optionnelle via Ollama
DESCRIPTION_SEED = 7

# =============================================================================
# PHASE 12 — QUALITÉ
# =============================================================================
MANUAL_REVIEW_SAMPLE = 50
MAX_MEAN_DESCRIPTION_COSINE = 0.80  # au-delà, les descriptions sont trop similaires

# =============================================================================
# PHASE 17 — COMMUNAUTÉS (clustering)
# =============================================================================
CLUSTER_K_RANGE = range(8, 17)
CLUSTER_SEED = 42

# =============================================================================
# PHASE 18 — UTILISATEURS SIMULÉS
# =============================================================================
N_SIMULATED_USERS = 150
USERS_SEED = 123

# =============================================================================
# PHASE 19 — CONCERTS
# =============================================================================
N_CONCERT_ARTISTS = 60
CONCERT_YEAR = 2027
CONCERTS_SEED = 2027

# =============================================================================
# ENCODEUR (embeddings) utilisé par les phases 8, 12, 17, 18
# =============================================================================
ENCODER = os.getenv("ENCODER", "sbert")   # "sbert" | "tfidf" (repli hors ligne)

for _d in (RAW, INTERIM, PROCESSED, CACHE, REPORTS):
    _d.mkdir(parents=True, exist_ok=True)
