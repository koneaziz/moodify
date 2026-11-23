"""Paramètres du scoring (centralisés pour être documentés, justifiés et ajustés).

Justification des poids (voir README §5) :
- La similarité sémantique globale et l'humeur pèsent le plus : c'est le cœur du
  sujet (analyse contextuelle du texte libre) et la promesse du produit (musique ↔ humeur).
- Contexte, genre et artistes affinent le classement sans l'écraser.
- Énergie (Likert) et personnalité sont des signaux numériques / faibles :
  petits poids, pour que l'analyse reste avant tout sémantique.
"""

# Poids des composantes du score d'un morceau, mode « profil » (après le quiz)
WEIGHTS_PROFILE = {
    "semantic": 0.30,   # cos(texte libre utilisateur, description complète du morceau)
    "mood": 0.25,       # cos(humeur exprimée / blocs d'humeur ciblés, vue humeur du morceau)
    "context": 0.10,    # cos(contextes d'écoute, vue contexte du morceau)
    "genre": 0.10,      # genre coché (1), neutre (0.5)
    "artist": 0.15,     # similarité avec les morceaux des artistes favoris
    "energy": 0.05,     # 1 - |énergie morceau - énergie souhaitée| / 4
    "personality": 0.05,  # a priori STOMP (faible)
}

# Mode « chatbot » : la demande instantanée prime sur le profil long terme
WEIGHTS_CHAT = {
    "semantic": 0.30,
    "mood": 0.35,
    "context": 0.10,
    "genre": 0.05,
    "artist": 0.05,
    "energy": 0.10,
    "personality": 0.05,
}

# Calibration des similarités cosinus pour l'affichage (0-100 %).
# Avec SBERT, deux textes sans rapport ont typiquement un cosinus ~0.1-0.2 et deux
# paraphrases ~0.7-0.9. On rescale linéairement [COS_LOW, COS_HIGH] -> [0, 1].
# À recalibrer dans le notebook 03 à partir de la distribution observée.
COS_LOW = 0.10
COS_HIGH = 0.70

# Seuils
EMOTION_MIN_SIM = 0.35        # en dessous, le chatbot considère l'émotion « incertaine »
SIMILAR_ARTIST_MIN_SIM = 0.55  # pour proposer les concerts d'artistes « similaires »
MAX_PER_ARTIST = 1            # diversité : 1 morceau max par artiste dans le top-k

# Concerts : score = a * affinité + (1 - a) * proximité
CONCERT_AFFINITY_WEIGHT = 0.6

# Communautés : score = somme pondérée
COMMUNITY_WEIGHTS = {"semantic": 0.6, "genre": 0.2, "mood": 0.2}
