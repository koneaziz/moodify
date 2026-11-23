"""Encodeurs de texte interchangeables.

Tous les encodeurs exposent la même interface : ``encode(list[str]) -> np.ndarray``
avec des vecteurs **normalisés L2**, ce qui permet de calculer la similarité cosinus
par un simple produit scalaire.

- ``SBERTEncoder``  : embeddings contextuels de phrases (moteur principal).
  Modèle par défaut : ``paraphrase-multilingual-MiniLM-L12-v2`` (multilingue, donc
  l'utilisateur peut écrire en français ou en anglais ; 384 dimensions ; rapide sur CPU).
- ``Word2VecEncoder`` : moyenne d'embeddings de mots (Word2Vec / fastText) — baseline
  "embeddings de mots" demandée par le sujet, pour comparaison.
- ``TfidfEncoder`` : baseline lexicale (sac de mots + n-grammes de caractères).
  Sert à montrer la différence entre correspondance de mots-clés et analyse sémantique,
  et de solution de repli si aucun modèle n'est disponible hors-ligne.
"""
from __future__ import annotations

import logging
from typing import Iterable

import numpy as np

from .preprocessing import clean_text, tokenize

log = logging.getLogger(__name__)

# Modèle retenu après la comparaison du notebook 02 (meilleur sur paraphrases, jeu gold et négation)
DEFAULT_SBERT_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Modèles contextuels comparés dans le notebook 02 (tous multilingues, donc compatibles français)
SBERT_MODELS = {
    "sbert-minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",   # 118M param., 384 dim.
    "sbert-mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",    # 278M param., 768 dim.
    "e5-small": "intfloat/multilingual-e5-small",                                    # 118M param., 384 dim.
}
# Les modèles E5 attendent un préfixe devant chaque texte
SBERT_PREFIX = {"intfloat/multilingual-e5-small": "query: "}


def _l2_normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Similarité cosinus entre deux matrices de vecteurs déjà normalisés."""
    if a.ndim == 1:
        a = a[None, :]
    if b.ndim == 1:
        b = b[None, :]
    return a @ b.T


class Encoder:
    """Interface commune + cache (un même texte n'est encodé qu'une fois)."""

    name = "base"

    def __init__(self) -> None:
        self._cache: dict[str, np.ndarray] = {}

    def fit(self, corpus: Iterable[str]) -> "Encoder":  # pour les baselines
        return self

    def _encode(self, texts: list[str]) -> np.ndarray:  # à implémenter
        raise NotImplementedError

    def encode(self, texts: list[str] | str) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        texts = [clean_text(t) for t in texts]
        missing = [t for t in dict.fromkeys(texts) if t not in self._cache]
        if missing:
            vecs = _l2_normalize(np.asarray(self._encode(missing), dtype=np.float32))
            self._cache.update(zip(missing, vecs))
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._cache[t] for t in texts])

    def encode_mean(self, texts: list[str]) -> np.ndarray:
        """Embedding moyen d'un ensemble de phrases (centroïde normalisé)."""
        m = self.encode(texts)
        return _l2_normalize(m.mean(axis=0, keepdims=True))[0]

    @property
    def dim(self) -> int:
        return 0


class SBERTEncoder(Encoder):
    name = "sbert"

    def __init__(self, model_name: str = DEFAULT_SBERT_MODEL, device: str | None = None):
        super().__init__()
        from sentence_transformers import SentenceTransformer  # import paresseux

        self.model_name = model_name
        self.prefix = SBERT_PREFIX.get(model_name, "")
        self.model = SentenceTransformer(model_name, device=device)

    def _encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode([self.prefix + t for t in texts], batch_size=32,
                                 show_progress_bar=False, normalize_embeddings=True)

    def tokenize(self, text: str) -> list[str]:
        """Tokens sous-mots (WordPiece / SentencePiece) réellement vus par le modèle."""
        return self.model.tokenizer.tokenize(self.prefix + text)

    @property
    def dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()


class TfidfEncoder(Encoder):
    """Baseline lexicale. Doit être 'fit' sur le corpus de référence."""

    name = "tfidf"

    def __init__(self) -> None:
        super().__init__()
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import FeatureUnion

        self.vectorizer = FeatureUnion([
            ("words", TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None,
                                      ngram_range=(1, 2), sublinear_tf=True)),
            # Les n-grammes de caractères rendent la baseline robuste aux flexions
            # (énervé / énervée) mais restent purement lexicaux.
            ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])
        self._fitted = False

    def fit(self, corpus: Iterable[str]) -> "TfidfEncoder":
        self.vectorizer.fit([clean_text(t) for t in corpus])
        self._fitted = True
        self._cache.clear()
        return self

    def _encode(self, texts: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("TfidfEncoder doit être entraîné avec .fit(corpus) avant usage.")
        return self.vectorizer.transform(texts).toarray()

    @property
    def dim(self) -> int:
        return sum(len(t.vocabulary_) for _, t in self.vectorizer.transformer_list) if self._fitted else 0


class Word2VecEncoder(Encoder):
    """Moyenne des vecteurs de mots (Word2Vec, GloVe ou fastText via gensim).

    - ``vectors_path`` : fichier de vecteurs pré-entraînés (ex. fastText français
      ``cc.fr.300.vec`` réduit, ou un modèle gensim). Recommandé.
    - sinon, ``fit(corpus)`` entraîne un petit Word2Vec sur le corpus de référence
      (utile pour la démonstration, mais peu fiable vu la taille du corpus).
    """

    name = "word2vec"

    def __init__(self, vectors_path: str | None = None, binary: bool = False):
        super().__init__()
        self.kv = None
        if vectors_path:
            from gensim.models import KeyedVectors

            if vectors_path.endswith((".kv", ".model")):
                self.kv = KeyedVectors.load(vectors_path)
            else:
                self.kv = KeyedVectors.load_word2vec_format(vectors_path, binary=binary)

    def fit(self, corpus: Iterable[str]) -> "Word2VecEncoder":
        if self.kv is None:
            from gensim.models import Word2Vec

            sentences = [tokenize(t) for t in corpus]
            model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, sg=1,
                             epochs=200, seed=42, workers=1)
            self.kv = model.wv
        self._cache.clear()
        return self

    def _encode(self, texts: list[str]) -> np.ndarray:
        if self.kv is None:
            raise RuntimeError("Word2VecEncoder : fournir vectors_path ou appeler .fit(corpus).")
        out = np.zeros((len(texts), self.kv.vector_size), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = [w for w in tokenize(t) if w in self.kv.key_to_index]
            if toks:
                out[i] = np.mean([self.kv[w] for w in toks], axis=0)
        return out

    @property
    def dim(self) -> int:
        return self.kv.vector_size if self.kv is not None else 0


class FastTextEncoder(Word2VecEncoder):
    """Embeddings de mots fastText : chaque mot = somme de ses n-grammes de caractères.
    Avantage sur Word2Vec : un mot jamais vu (faute de frappe, « énervéeee ») reçoit quand même
    un vecteur. Entraîné sur notre corpus, ou chargé depuis un modèle pré-entraîné
    (ex. cc.fr.300.bin de fasttext.cc, via `vectors_path`)."""

    name = "fasttext"

    def __init__(self, vectors_path: str | None = None):
        Encoder.__init__(self)
        self.kv = None
        if vectors_path:
            from gensim.models.fasttext import load_facebook_vectors

            self.kv = load_facebook_vectors(vectors_path)

    def fit(self, corpus: Iterable[str]) -> "FastTextEncoder":
        if self.kv is None:
            from gensim.models import FastText

            sentences = [tokenize(t) for t in corpus]
            model = FastText(sentences, vector_size=100, window=5, min_count=1, sg=1, min_n=3,
                             max_n=5, epochs=100, seed=42, workers=1)
            self.kv = model.wv
        self._cache.clear()
        return self

    def _encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.kv.vector_size), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = tokenize(t)          # fastText gère les mots hors vocabulaire
            if toks:
                out[i] = np.mean([self.kv[w] for w in toks], axis=0)
        return out


def get_encoder(name: str = "sbert", **kwargs) -> Encoder:
    """Fabrique d'encodeurs. Si SBERT est indisponible (pas installé / hors-ligne),
    on bascule sur la baseline TF-IDF en le signalant clairement."""
    name = name.lower()
    if name in SBERT_MODELS:
        name, kwargs = "sbert", {**kwargs, "model_name": SBERT_MODELS[name]}
    if name == "sbert":
        try:
            return SBERTEncoder(**kwargs)
        except Exception as exc:  # pragma: no cover - dépend de l'environnement
            log.warning("SBERT indisponible (%s) -> repli sur la baseline TF-IDF.", exc)
            return TfidfEncoder()
    if name == "tfidf":
        return TfidfEncoder()
    if name == "fasttext":
        return FastTextEncoder(**kwargs)
    if name in {"word2vec", "glove"}:
        return Word2VecEncoder(**kwargs)
    raise ValueError(f"Encodeur inconnu : {name}")
