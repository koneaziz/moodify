"""Chatbot « mood » : comprend une demande libre et la transforme en requête de scoring.

Fonctionne SANS LLM (exigence : le moteur doit rester autonome). Pipeline NLU :
1. Séparer l'**état actuel** (« je suis énervée ») du **souhait** (« je veux du calme »)
   grâce à des marqueurs de désir (règles).
2. Détecter l'**émotion actuelle** : classification zero-shot par similarité cosinus
   avec des phrases prototypes d'émotions (blocks.json > emotions).
3. Déterminer le **bloc d'humeur cible** :
   - si un souhait est exprimé → bloc le plus proche sémantiquement du souhait ;
   - sinon → stratégie de l'utilisateur (quiz Q11) : « réguler » (changer d'humeur)
     ou « accompagner » (rester dans l'émotion, principe d'iso-musique).
4. Détecter le **contexte** (étudier, sport...) et les **exclusions** (« pas de rap »).
5. Appeler le moteur de scoring et formuler une réponse expliquée.
Si l'intention est trop incertaine, le bot pose une question de clarification.

Un LLM (Ollama / Gemini) pourra ensuite être branché en option pour reformuler la
demande ou rédiger la réponse (bonus), sans remplacer ce pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from . import config
from .embeddings import cosine_matrix
from .preprocessing import clean_text, normalize_key, split_sentences
from .profile import UserProfile
from .reference import ReferenceIndex
from .semantic import SemanticMatcher
from .scoring import Query, block_affinity

DESIRE_RE = re.compile(
    r"\b(?:je veux|je voudrais|j'aimerais|j'ai envie d(?:e |')|envie d(?:e |')|"
    r"j'ai besoin d(?:e |')|besoin d(?:e |')|je cherche|mets[- ]moi|propose[- ]moi|"
    r"donne[- ]moi|un truc|quelque chose d(?:e |'))\s*(.+)", re.IGNORECASE)
NEGATION_RE = re.compile(
    r"\b(?:pas de|pas d'|pas du|sans|aucune?|[ée]vite[rz]?|plus de|surtout pas)\s*([^,.;!?]+)",
    re.IGNORECASE)

# Alias de genres (forme normalisée -> genre du dataset)
GENRE_ALIASES = {
    "lofi": "Lo-fi / Chillhop", "lo fi": "Lo-fi / Chillhop", "chillhop": "Lo-fi / Chillhop",
    "jazz": "Jazz", "classique": "Classique", "piano": "Classique", "ambient": "Ambient",
    "electro": "Électro / House", "house": "Électro / House", "techno": "Électro / House",
    "pop": "Pop", "rock": "Rock", "metal": "Metal", "rap francais": "Rap FR",
    "rap fr": "Rap FR", "rap us": "Hip-hop US", "hip hop": "Hip-hop US", "rap": "Rap FR",
    "rnb": "R&B / Soul", "r b": "R&B / Soul", "soul": "R&B / Soul",
    "chanson": "Chanson française", "variete": "Chanson française",
    "folk": "Indie / Folk", "indie": "Indie / Folk", "reggae": "Afro / Reggae / Latino",
    "afro": "Afro / Reggae / Latino", "reggaeton": "Afro / Reggae / Latino",
    "latino": "Afro / Reggae / Latino",
}

# Énergie typique associée à chaque bloc d'humeur cible (échelle 1-5)
BLOCK_ENERGY = {
    "Calme & détente": 1.5, "Concentration": 2.0, "Mélancolie & introspection": 1.5,
    "Romance & sensualité": 2.0, "Rêverie & évasion": 2.5, "Joie & bonne humeur": 3.5,
    "Fête & danse": 4.5, "Énergie & motivation": 4.5, "Colère & défoulement": 5.0,
}

EMOTION_THRESHOLDS = {"sbert": config.EMOTION_MIN_SIM, "tfidf": 0.12, "word2vec": 0.5}
CONTEXT_THRESHOLDS = {"sbert": 0.45, "tfidf": 0.12, "word2vec": 0.6}


@dataclass
class Intent:
    message: str
    state_text: str = ""
    desire_text: str = ""
    emotion: str | None = None
    emotion_score: float = 0.0
    emotion_scores: dict[str, float] = field(default_factory=dict)
    target_block: str | None = None
    target_scores: dict[str, float] = field(default_factory=dict)
    target_source: str = ""        # "souhait", "stratégie:réguler", "profil"...
    contexts: list[str] = field(default_factory=list)
    excluded_genres: list[str] = field(default_factory=list)
    needs_clarification: bool = False


class ChatIntentIndex:
    """Prototypes d'intention calculés avec l'encodeur déjà chargé par l'API."""

    def __init__(self, matcher: SemanticMatcher):
        self.encoder = matcher.encoder
        self.blocks = matcher.blocks
        self.E_mood_blocks = matcher.mood_blocks
        self.E_ctx_blocks = matcher.ctx_blocks
        self.mood_block_names = list(self.E_mood_blocks)
        self.ctx_block_names = list(self.E_ctx_blocks)
        self.emotion_names = [name for name in self.blocks["emotions"] if not name.startswith("_")]
        self.E_emotions = {name: self.encoder.encode(self.blocks["emotions"][name])
                           for name in self.emotion_names}


def detect_exclusions(text: str) -> list[str]:
    found = []
    for m in NEGATION_RE.finditer(text):
        span = " " + normalize_key(m.group(1)) + " "
        for alias, genre in sorted(GENRE_ALIASES.items(), key=lambda kv: -len(kv[0])):
            if f" {alias} " in span and genre not in found:
                found.append(genre)
                span = span.replace(f" {alias} ", " ")
    return found


def parse_message(ref: ReferenceIndex | ChatIntentIndex, message: str, profile: UserProfile | None = None) -> Intent:
    enc = ref.encoder
    msg = clean_text(message)
    it = Intent(message=msg)

    # 1. Exclusions d'abord, puis on les retire du texte pour ne pas fausser la sémantique
    it.excluded_genres = detect_exclusions(msg)
    msg_sem = NEGATION_RE.sub(" ", msg)

    # 2. État vs souhait
    m = DESIRE_RE.search(msg_sem)
    if m:
        it.desire_text = m.group(1).strip(" .,!")
        it.state_text = msg_sem[: m.start()].strip(" .,!")
    else:
        it.state_text = msg_sem

    # 3. Émotion actuelle (zero-shot par similarité aux prototypes)
    state_sents = split_sentences(it.state_text) or ([it.state_text] if it.state_text else [])
    # on découpe aussi sur les virgules / "et" pour isoler "je suis énervée"
    clauses = [c.strip() for s in state_sents for c in re.split(r",| et | mais ", s) if len(c.strip()) > 2]
    if clauses:
        U = enc.encode(clauses)
        it.emotion_scores = {e: float(cosine_matrix(U, ref.E_emotions[e]).max())
                             for e in ref.emotion_names}
        best = max(it.emotion_scores, key=it.emotion_scores.get)
        it.emotion_score = it.emotion_scores[best]
        if it.emotion_score >= EMOTION_THRESHOLDS.get(enc.name, config.EMOTION_MIN_SIM):
            it.emotion = best

    # 4. Bloc d'humeur cible
    if it.desire_text:
        D = enc.encode([it.desire_text])
        it.target_scores = {b: block_affinity(D, ref.E_mood_blocks[b]) for b in ref.mood_block_names}
        it.target_block = max(it.target_scores, key=it.target_scores.get)
        it.target_source = "souhait exprimé"
    elif it.emotion:
        strategy = profile.regulation_strategy if profile else "réguler"
        it.target_block = ref.blocks["regulation"][strategy][it.emotion]
        it.target_source = f"stratégie « {strategy} » de ton profil"
    else:
        # Ni souhait ni émotion claire : on tente quand même une correspondance directe
        U = enc.encode([msg_sem])
        it.target_scores = {b: block_affinity(U, ref.E_mood_blocks[b]) for b in ref.mood_block_names}
        it.target_block = max(it.target_scores, key=it.target_scores.get)
        it.target_source = "correspondance directe"
        it.needs_clarification = it.target_scores[it.target_block] < EMOTION_THRESHOLDS.get(enc.name, 0.35)

    # 5. Contexte d'écoute
    U = enc.encode([msg_sem])
    thr = CONTEXT_THRESHOLDS.get(enc.name, 0.45)
    for b in ref.ctx_block_names:
        if float(cosine_matrix(U, ref.E_ctx_blocks[b]).max()) >= thr:
            it.contexts.append(b)
    return it


def intent_to_query(intent: Intent, profile: UserProfile | None) -> Query:
    p = profile or UserProfile()
    texts = [t for t in (intent.desire_text, intent.message) if t]
    return Query(
        texts=texts,
        mood_texts=[intent.desire_text] if intent.desire_text else [],
        target_blocks={intent.target_block: 1.0} if intent.target_block else {},
        contexts=intent.contexts,
        genres_liked=p.genres_liked,
        genres_disliked=list(set(p.genres_disliked) | set(intent.excluded_genres)),
        artists=p.artists,
        energy_target=BLOCK_ENERGY.get(intent.target_block, float(p.energy_pref)),
        personality=p.personality,
    )


def compose_reply(intent: Intent, recos: list[dict]) -> str:
    """Réponse du bot générée à partir de modèles de phrases (transparent, sans LLM)."""
    if intent.needs_clarification:
        return ("Je ne suis pas sûr d'avoir bien saisi ton humeur 🤔 Tu préfères quelque chose "
                "de calme, d'énergique, de festif ou de mélancolique ?")
    lines = []
    if intent.emotion:
        lines.append(f"J'ai l'impression que tu te sens plutôt **{intent.emotion}** "
                     f"(confiance {intent.emotion_score:.2f}).")
    if intent.target_block:
        lines.append(f"Je vise une ambiance **{intent.target_block}** ({intent.target_source}).")
    if intent.contexts:
        lines.append("Contexte détecté : " + ", ".join(intent.contexts) + ".")
    if intent.excluded_genres:
        lines.append("J'ai exclu : " + ", ".join(intent.excluded_genres) + ".")
    lines.append("Voici ma sélection :")
    for i, r in enumerate(recos, 1):
        lines.append(f"{i}. **{r['title']}** – {r['artist']} ({r['genre']}, score {r['score']:.2f})")
    return "\n".join(lines)
