"""Formats de la requête et de la réponse de l'API (partie 5).

Ils suivent le contrat proposé par le front : frontend/docs/api-contract.md
(mêmes noms de champs que frontend/types/questionnaire.ts et frontend/types/music.ts).
"""
from typing import Optional

from pydantic import BaseModel, Field


#ce que le questionnaire du front envoie
class Questionnaire(BaseModel):
    moods: list[str] = []
    description: str = Field(min_length=3, max_length=1000)
    genres: list[str] = []
    listeningContext: str = ""
    contextDescription: str = ""
    energyLevel: int = Field(3, ge=1, le=5)
    favoriteArtists: str = ""
    vocalPreference: str = "No preference"
    additionalPreferences: str = ""


class Recommendation(BaseModel):
    id: str
    rank: int
    title: str
    artist: str
    coverUrl: str
    genre: str
    mood: str
    score: int          #tous les scores sont en pourcentage (0-100) comme demandé par le front
    moodScore: int
    genreScore: int
    contextScore: int
    explanation: str
    reasons: list[str]
    spotifyTrackId: Optional[str] = None


class Affinity(BaseModel):
    label: str
    score: int


#en plus du contrat : le profil par bloc, utile pour un diagramme radar
class ProfileDetails(BaseModel):
    dominantMood: str
    dominantContext: Optional[str] = None
    moodBlocks: dict[str, int]
    contextBlocks: dict[str, int]
    #partie 6 (profil utilisateur)
    emotion: Optional[str] = None           #émotion dominante détectée : colère, tristesse, stress…
    strategy: Optional[str] = None          #« réguler » (changer d'humeur) ou « accompagner »
    strategySource: Optional[str] = None    #« texte » (écrit par l'utilisateur) ou « défaut »
    intensity: Optional[int] = None         #1 à 3
    excludedGenres: list[str] = []
    instrumental: bool = False
    archetype: Optional[str] = None         #profil d'auditeur (data/archetypes.json)


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    affinities: list[Affinity]
    profileSummary: str
    scenario: str
    isDemo: bool
    profile: ProfileDetails
