"""Profil utilisateur construit à partir des réponses au questionnaire."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .preprocessing import clean_text, parse_list, split_sentences

TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"]


@dataclass
class UserProfile:
    user_id: str = "anonyme"
    free_texts: list[str] = field(default_factory=list)   # réponses ouvertes générales
    mood_texts: list[str] = field(default_factory=list)   # réponses ouvertes sur l'humeur
    artists: list[str] = field(default_factory=list)
    genres_liked: list[str] = field(default_factory=list)
    genres_disliked: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    energy_pref: int = 3          # Likert 1-5
    lyrics_pref: int = 3          # Likert 1-5
    discovery_pref: int = 3       # Likert 1-5
    regulation_strategy: str = "réguler"   # ou "accompagner"
    personality: dict[str, float] = field(default_factory=dict)  # traits normalisés 0-1
    city: str | None = None
    travel_radius_km: int = 150

    # ------------------------------------------------------------------ helpers
    def sentences(self) -> list[str]:
        """Toutes les phrases libres de l'utilisateur, découpées pour l'encodage."""
        out: list[str] = []
        for t in self.free_texts + self.mood_texts:
            out += split_sentences(t)
        return out

    def summary_text(self) -> str:
        """Résumé textuel du profil (sert d'embedding global, ex. pour les communautés)."""
        parts = [" ".join(self.free_texts), " ".join(self.mood_texts)]
        if self.genres_liked:
            parts.append("J'aime : " + ", ".join(self.genres_liked) + ".")
        if self.contexts:
            parts.append("J'écoute surtout pour : " + ", ".join(self.contexts) + ".")
        return clean_text(" ".join(p for p in parts if p))

    def to_dict(self) -> dict:
        return asdict(self)

    # ------------------------------------------------------------- construction
    @classmethod
    def from_answers(cls, answers: dict, questionnaire: dict, user_id: str = "anonyme") -> "UserProfile":
        """Transforme les réponses brutes {question_id: valeur} en profil structuré.

        Le champ 'feeds' de chaque question (questionnaire.json) indique où va la réponse.
        """
        p = cls(user_id=user_id)
        tipi: dict[str, list[float]] = {t: [] for t in TRAITS}

        def handle(q: dict, value) -> None:
            if value in (None, "", []):
                return
            feeds = q["feeds"]
            if feeds == "free_text":
                p.free_texts.append(clean_text(value))
            elif feeds == "mood_text":
                p.mood_texts.append(clean_text(value))
            elif feeds == "artists":
                p.artists = parse_list(value) if isinstance(value, str) else list(value)
            elif feeds in ("genres_liked", "genres_disliked", "contexts"):
                setattr(p, feeds, list(value))
            elif feeds in ("energy_pref", "lyrics_pref", "discovery_pref"):
                setattr(p, feeds, int(value))
            elif feeds == "regulation_strategy":
                p.regulation_strategy = value
            elif feeds == "city":
                p.city = value
            elif feeds == "travel_radius_km":
                p.travel_radius_km = int(q["mapping_km"][str(int(value))])
            elif feeds == "personality":
                lo, hi = q["scale"]
                v = float(value)
                if q.get("reverse"):
                    v = lo + hi - v
                tipi[q["trait"]].append((v - lo) / (hi - lo))
            # 'study_music' : la question guidée n'alimente le profil que via sa relance

        for section in questionnaire["sections"]:
            for q in section["questions"]:
                handle(q, answers.get(q["id"]))
                fu = q.get("followup")
                if fu and str(answers.get(q["id"], "")).lower() == fu["if"]:
                    handle(fu, answers.get(q["id"] + "_followup"))

        p.personality = {t: round(sum(v) / len(v), 3) for t, v in tipi.items() if v}
        return p
