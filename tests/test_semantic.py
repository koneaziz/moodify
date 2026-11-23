"""Tests rapides du module NLP (encodeur TF-IDF : pas de téléchargement nécessaire).
    python -m pytest -q tests/test_semantic.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moodify.preprocessing import preprocess_lexical, preprocess_semantic  # noqa: E402
from moodify.semantic import SemanticMatcher  # noqa: E402

SM = SemanticMatcher("tfidf")


def test_preprocessing_keeps_negation_and_splits_sentences():
    assert len(preprocess_semantic("Je suis énervée. Je veux du calme.")) == 2
    toks = preprocess_lexical("Je ne veux pas de rap, aujourd'hui")
    assert "pas" in toks and "aujourd'hui" in toks


def test_one_score_per_track():
    s = SM.semantic_score("musique calme pour réviser")
    assert s.shape == (len(SM.tracks),)


def test_rank_returns_sorted_topk():
    top = SM.rank(["musique calme pour réviser", "piano doux"], k=5)
    assert len(top) == 5 and top["semantic_score"].is_monotonic_decreasing


def test_affinities_cover_all_blocks_and_genres():
    assert len(SM.mood_affinity("je suis triste")) == len(SM.blocks["mood_blocks"])
    assert set(SM.genre_affinity("du jazz")) == set(SM.tracks["genre"])
