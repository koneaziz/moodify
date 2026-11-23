"""Lexiques et tables de correspondance utilisés par le pipeline.

Tout est explicite et modifiable ici (c'est aussi ce qu'on montre pour justifier les choix) :
1. GENRE_TO_MACRO     : 114-125 genres Spotify  -> 14 macro-genres du projet
2. MOOD_GENRES        : « genres » Spotify qui sont en réalité des humeurs / contextes
3. TAG_LEXICON        : tags Last.fm / MuSe (anglais) -> (catégorie, libellé français)
4. MOOD_TO_BLOCK      : libellé d'humeur français -> bloc d'humeur (blocks.json)
5. CONTEXT_TO_BLOCK   : libellé de contexte français -> bloc de contexte
6. NOISE_TAGS         : tags sans valeur sémantique à supprimer
"""
from __future__ import annotations

# =============================================================================
# 1. GENRES SPOTIFY -> MACRO-GENRES
# =============================================================================
MACRO_GENRES = [
    "Lo-fi / Chill", "Jazz / Blues", "Classique", "Ambient", "Électro / House", "Pop",
    "Rock", "Metal", "Hip-hop / Rap", "R&B / Soul / Funk", "Chanson française",
    "Indie / Folk / Country", "Afro / Reggae / Latino", "Musiques du monde",
]

GENRE_TO_MACRO = {
    # Lo-fi / Chill
    "chill": "Lo-fi / Chill", "study": "Lo-fi / Chill", "trip-hop": "Lo-fi / Chill",
    # Jazz / Blues
    "jazz": "Jazz / Blues", "blues": "Jazz / Blues",
    # Classique
    "classical": "Classique", "opera": "Classique", "piano": "Classique",
    # Ambient
    "ambient": "Ambient", "new-age": "Ambient", "sleep": "Ambient",
    # Électro
    "edm": "Électro / House", "electro": "Électro / House", "electronic": "Électro / House",
    "house": "Électro / House", "deep-house": "Électro / House", "chicago-house": "Électro / House",
    "progressive-house": "Électro / House", "techno": "Électro / House",
    "minimal-techno": "Électro / House", "detroit-techno": "Électro / House",
    "trance": "Électro / House", "dubstep": "Électro / House", "drum-and-bass": "Électro / House",
    "breakbeat": "Électro / House", "club": "Électro / House", "dance": "Électro / House",
    "hardstyle": "Électro / House", "garage": "Électro / House", "idm": "Électro / House",
    "j-dance": "Électro / House",
    # Pop
    "pop": "Pop", "power-pop": "Pop", "synth-pop": "Pop", "indie-pop": "Pop", "pop-film": "Pop",
    "cantopop": "Pop", "mandopop": "Pop", "k-pop": "Pop", "j-pop": "Pop", "j-idol": "Pop",
    "anime": "Pop", "british": "Pop", "german": "Pop", "swedish": "Pop",
    "happy": "Pop", "sad": "Pop", "party": "Pop", "romance": "Pop",
    # Rock
    "rock": "Rock", "alt-rock": "Rock", "alternative": "Rock", "hard-rock": "Rock",
    "psych-rock": "Rock", "punk": "Rock", "punk-rock": "Rock", "grunge": "Rock",
    "rock-n-roll": "Rock", "rockabilly": "Rock", "j-rock": "Rock", "emo": "Rock", "goth": "Rock",
    "ska": "Rock", "guitar": "Rock",
    # Metal
    "metal": "Metal", "heavy-metal": "Metal", "black-metal": "Metal", "death-metal": "Metal",
    "metalcore": "Metal", "grindcore": "Metal", "hardcore": "Metal", "industrial": "Metal",
    # Hip-hop
    "hip-hop": "Hip-hop / Rap",
    # R&B / Soul / Funk
    "r-n-b": "R&B / Soul / Funk", "soul": "R&B / Soul / Funk", "funk": "R&B / Soul / Funk",
    "gospel": "R&B / Soul / Funk", "disco": "R&B / Soul / Funk", "groove": "R&B / Soul / Funk",
    # Chanson française
    "french": "Chanson française",
    # Indie / Folk / Country
    "indie": "Indie / Folk / Country", "folk": "Indie / Folk / Country",
    "singer-songwriter": "Indie / Folk / Country", "songwriter": "Indie / Folk / Country",
    "acoustic": "Indie / Folk / Country", "bluegrass": "Indie / Folk / Country",
    "country": "Indie / Folk / Country", "honky-tonk": "Indie / Folk / Country",
    # Afro / Reggae / Latino
    "afrobeat": "Afro / Reggae / Latino", "reggae": "Afro / Reggae / Latino",
    "dancehall": "Afro / Reggae / Latino", "dub": "Afro / Reggae / Latino",
    "reggaeton": "Afro / Reggae / Latino", "latin": "Afro / Reggae / Latino",
    "latino": "Afro / Reggae / Latino", "salsa": "Afro / Reggae / Latino",
    "samba": "Afro / Reggae / Latino", "brazil": "Afro / Reggae / Latino",
    "forro": "Afro / Reggae / Latino", "mpb": "Afro / Reggae / Latino",
    "pagode": "Afro / Reggae / Latino", "sertanejo": "Afro / Reggae / Latino",
    "tango": "Afro / Reggae / Latino", "spanish": "Afro / Reggae / Latino",
    # Musiques du monde
    "world-music": "Musiques du monde", "indian": "Musiques du monde",
    "iranian": "Musiques du monde", "turkish": "Musiques du monde", "malay": "Musiques du monde",
}

# Ordre de priorité quand un morceau a plusieurs genres Spotify : on préfère le genre
# le plus « spécifique » (un morceau tagué 'pop' ET 'french' est d'abord de la chanson FR).
MACRO_PRIORITY = [
    "Chanson française", "Metal", "Hip-hop / Rap", "Jazz / Blues", "Classique", "Ambient",
    "Lo-fi / Chill", "Afro / Reggae / Latino", "R&B / Soul / Funk", "Électro / House",
    "Indie / Folk / Country", "Musiques du monde", "Rock", "Pop",
]

# =============================================================================
# 2. « GENRES » SPOTIFY QUI SONT DES HUMEURS / CONTEXTES
# =============================================================================
MOOD_GENRES = {
    "chill": {"mood": ["calme"], "context": ["détente"]},
    "study": {"mood": ["studieux"], "context": ["étude"]},
    "sleep": {"mood": ["apaisant"], "context": ["sommeil"]},
    "sad": {"mood": ["triste"], "context": []},
    "happy": {"mood": ["joyeux"], "context": []},
    "party": {"mood": ["festif"], "context": ["soirée"]},
    "romance": {"mood": ["romantique"], "context": ["moment à deux"]},
    "piano": {"mood": [], "context": []},
}

# =============================================================================
# 3. LEXIQUE DES TAGS (Last.fm + MuSe) -> (catégorie, libellé français)
#    catégories : mood | context | attribute | era | genre (géré à part) | noise
# =============================================================================
_MOOD = {
    "chill": "calme", "chillout": "calme", "chill out": "calme", "calm": "calme",
    "relaxing": "relaxant", "relax": "relaxant", "relaxed": "relaxant", "laid back": "relaxant",
    "peaceful": "serein", "serene": "serein", "spiritual": "serein",
    "mellow": "doux", "soft": "doux", "smooth": "doux", "gentle": "doux", "warm": "doux",
    "delicate": "doux", "soothing": "apaisant",
    "sad": "triste", "depressing": "triste", "depressive": "triste", "sad songs": "triste",
    "melancholic": "mélancolique", "melancholy": "mélancolique", "lonely": "mélancolique",
    "gloomy": "sombre", "dark": "sombre", "brooding": "sombre", "menacing": "sombre", "ominous": "sombre",
    "nostalgic": "nostalgique", "nostalgia": "nostalgique", "bittersweet": "nostalgique",
    "wistful": "nostalgique", "emotional": "émouvant", "poignant": "émouvant", "beautiful": "émouvant",
    "introspective": "introspectif", "reflective": "introspectif", "thoughtful": "introspectif",
    "happy": "joyeux", "cheerful": "joyeux", "feel good": "joyeux", "feelgood": "joyeux",
    "bright": "joyeux", "carefree": "joyeux", "uplifting": "optimiste", "hopeful": "optimiste",
    "sunny": "ensoleillé", "fun": "ludique", "playful": "ludique", "quirky": "ludique",
    "whimsical": "ludique", "silly": "ludique",
    "upbeat": "entraînant", "lively": "entraînant", "catchy": "entraînant",
    "energetic": "énergique", "energy": "énergique", "exciting": "énergique",
    "powerful": "puissant", "heavy": "puissant", "intense": "intense", "hard": "intense",
    "epic": "épique", "dramatic": "épique", "triumphant": "épique",
    "motivational": "motivant", "motivation": "motivant", "inspiring": "motivant",
    "rousing": "motivant", "confident": "motivant",
    "aggressive": "agressif", "fierce": "agressif", "harsh": "agressif", "hostile": "agressif",
    "angry": "rageur", "rage": "rageur", "rebellious": "rageur",
    "anxious": "tendu", "tense": "tendu",
    "romantic": "romantique", "love": "romantique", "love songs": "romantique",
    "sentimental": "tendre", "tender": "tendre", "sweet": "tendre",
    "sexy": "sensuel", "sensual": "sensuel", "seductive": "sensuel", "passionate": "sensuel",
    "sexual": "sensuel",
    "dreamy": "rêveur", "atmospheric": "atmosphérique", "ethereal": "éthéré",
    "psychedelic": "psychédélique", "trippy": "planant", "spacey": "planant", "hypnotic": "planant",
    "euphoric": "euphorique", "groovy": "dansant", "danceable": "dansant",
}
_CONTEXT = {
    "study": "étude", "studying": "étude", "focus": "concentration", "concentration": "concentration",
    "work": "travail", "working": "travail", "background": "travail", "coding": "travail",
    "workout": "sport", "gym": "sport", "running": "course", "training": "entraînement",
    "sport": "sport", "fitness": "sport",
    "driving": "conduite", "road trip": "route", "travel": "voyage", "commute": "trajet",
    "party": "soirée", "club": "club", "dancing": "danse",
    "sleep": "sommeil", "sleeping": "sommeil", "meditation": "méditation", "yoga": "méditation",
    "relaxation": "détente", "lounge": "détente",
    "rainy day": "pluie", "rain": "pluie", "night": "nuit", "late night": "nuit",
    "morning": "matin", "sunday": "matin", "coffee": "matin", "summer": "été", "cooking": "cuisine",
    "date": "moment à deux", "love making": "moment à deux",
}
_ATTRIBUTE = {
    "instrumental": "instrumental", "acoustic": "acoustique", "piano": "piano",
    "female vocalists": "voix féminine", "female vocals": "voix féminine",
    "male vocalists": "voix masculine", "male vocals": "voix masculine",
    "guitar": "guitare", "strings": "cordes", "orchestral": "orchestral",
    "lo-fi": "lo-fi", "lofi": "lo-fi", "beats": "beats", "vocal": "chanté",
}
_ERA = {
    "50s": "années 50", "60s": "années 60", "70s": "années 70", "80s": "années 80",
    "90s": "années 90", "00s": "années 2000", "2000s": "années 2000", "2010s": "années 2010",
    "oldies": "classique d'antan", "classic": "classique d'antan",
}
NOISE_TAGS = {
    "seen live", "favorites", "favourite", "favorite", "favourites", "love it", "awesome", "best",
    "albums i own", "amazing", "cool", "good", "great", "my favorite", "spotify", "loved",
    "under 2000 listeners", "check out", "fav", "favs", "songs", "music", "all", "001", "best songs",
    "my music", "to listen", "beautiful songs", "american", "british", "usa", "uk", "english",
}

TAG_LEXICON: dict[str, tuple[str, str]] = {}
for _d, _cat in ((_MOOD, "mood"), (_CONTEXT, "context"), (_ATTRIBUTE, "attribute"), (_ERA, "era")):
    for _k, _v in _d.items():
        TAG_LEXICON.setdefault(_k, (_cat, _v))

# Synonymes de tags à fusionner avant classification
TAG_SYNONYMS = {
    "hiphop": "hip-hop", "hip hop": "hip-hop", "rnb": "r-n-b", "r&b": "r-n-b", "rn b": "r-n-b",
    "chill-out": "chillout", "electronica": "electronic", "lo fi": "lo-fi", "drum n bass": "drum-and-bass",
    "dnb": "drum-and-bass", "alternative rock": "alt-rock", "indie rock": "indie",
    "female vocalist": "female vocalists", "male vocalist": "male vocalists",
}

# =============================================================================
# 4-5. LIBELLÉS FRANÇAIS -> BLOCS (blocks.json)
# =============================================================================
MOOD_TO_BLOCK = {
    "calme": "Calme & détente", "relaxant": "Calme & détente", "serein": "Calme & détente",
    "doux": "Calme & détente", "apaisant": "Calme & détente",
    "studieux": "Concentration", "concentré": "Concentration",
    "énergique": "Énergie & motivation", "puissant": "Énergie & motivation",
    "intense": "Énergie & motivation", "épique": "Énergie & motivation", "motivant": "Énergie & motivation",
    "festif": "Fête & danse", "dansant": "Fête & danse", "entraînant": "Fête & danse",
    "euphorique": "Fête & danse",
    "triste": "Mélancolie & introspection", "mélancolique": "Mélancolie & introspection",
    "sombre": "Mélancolie & introspection", "nostalgique": "Mélancolie & introspection",
    "émouvant": "Mélancolie & introspection", "introspectif": "Mélancolie & introspection",
    "agressif": "Colère & défoulement", "rageur": "Colère & défoulement", "tendu": "Colère & défoulement",
    "romantique": "Romance & sensualité", "tendre": "Romance & sensualité", "sensuel": "Romance & sensualité",
    "joyeux": "Joie & bonne humeur", "optimiste": "Joie & bonne humeur",
    "ensoleillé": "Joie & bonne humeur", "ludique": "Joie & bonne humeur",
    "rêveur": "Rêverie & évasion", "atmosphérique": "Rêverie & évasion", "éthéré": "Rêverie & évasion",
    "psychédélique": "Rêverie & évasion", "planant": "Rêverie & évasion",
}
CONTEXT_TO_BLOCK = {
    "étude": "Étude & travail", "concentration": "Étude & travail", "travail": "Étude & travail",
    "sport": "Sport", "course": "Sport", "entraînement": "Sport",
    "soirée": "Soirée & fête", "club": "Soirée & fête", "danse": "Soirée & fête",
    "conduite": "Trajet", "route": "Trajet", "voyage": "Trajet", "trajet": "Trajet",
    "sommeil": "Sommeil & méditation", "méditation": "Sommeil & méditation", "détente": "Sommeil & méditation",
    "moment à deux": "Moment à deux",
    "pluie": "Solitude & pluie", "nuit": "Solitude & pluie", "solitude": "Solitude & pluie",
    "matin": "Matin & quotidien", "été": "Matin & quotidien", "cuisine": "Matin & quotidien",
}

# Phrases françaises par macro-genre (utilisées dans les descriptions générées)
MACRO_PHRASE = {
    "Lo-fi / Chill": "lo-fi / chill aux beats feutrés", "Jazz / Blues": "jazz / blues",
    "Classique": "classique", "Ambient": "ambient aux nappes enveloppantes",
    "Électro / House": "électro", "Pop": "pop", "Rock": "rock", "Metal": "metal",
    "Hip-hop / Rap": "hip-hop / rap", "R&B / Soul / Funk": "R&B / soul",
    "Chanson française": "de chanson française", "Indie / Folk / Country": "indie / folk",
    "Afro / Reggae / Latino": "aux rythmes afro / latino", "Musiques du monde": "aux sonorités du monde",
}

# Anciens noms de genres (jeu gold, communautés éditoriales) -> nouveaux macro-genres
OLD_TO_NEW_GENRE = {
    "Lo-fi / Chillhop": "Lo-fi / Chill", "Jazz": "Jazz / Blues", "Rap FR": "Hip-hop / Rap",
    "Hip-hop US": "Hip-hop / Rap", "R&B / Soul": "R&B / Soul / Funk",
    "Indie / Folk": "Indie / Folk / Country",
}

# Tags d'émotion MuSe supplémentaires rencontrés dans dataset_final.csv (collègue)
_EXTRA_MOOD = {
    "optimistic": "optimiste", "positive": "optimiste", "quiet": "calme", "light": "doux",
    "lazy": "relaxant", "graceful": "doux", "elegant": "doux", "autumnal": "nostalgique",
    "yearning": "nostalgique", "wintry": "mélancolique", "tragic": "triste", "heartbreak": "triste",
    "almosttears": "triste", "negative": "sombre", "cold": "sombre", "somber": "sombre",
    "bleak": "sombre", "spooky": "sombre", "austere": "sombre", "urgent": "intense",
    "raucous": "intense", "reckless": "intense", "cathartic": "intense", "thrilling": "énergique",
    "strong": "puissant", "martial": "puissant", "savage": "agressif", "brash": "agressif",
    "defiant": "rageur", "provocative": "rageur", "humorous": "ludique", "eccentric": "ludique",
    "sarcastic": "ludique", "ironic": "ludique", "wry": "ludique", "erotic": "sensuel",
    "spicy": "sensuel", "hot": "sensuel", "precious": "tendre", "sparkling": "joyeux",
    "joyous": "joyeux", "exotic": "ensoleillé", "lyrical": "émouvant",
    "heartbreakingly beautiful": "émouvant", "bombastic": "épique", "theatrical": "épique",
    "monumental": "épique", "hedonistic": "festif", "celebratory": "festif", "rowdy": "festif",
    "rambunctious": "festif", "flashy": "festif", "swaggering": "motivant", "ecstatic": "euphorique",
    "exuberant": "euphorique", "philosophical": "introspectif", "complex": "introspectif",
    "narrative": "introspectif", "serious": "introspectif", "deep": "introspectif",
    "growing up": "nostalgique", "lush": "rêveur", "mystical": "éthéré", "enigmatic": "éthéré",
}
_EXTRA_CONTEXT = {"nocturnal": "nuit", "drive": "conduite", "slow jams": "moment à deux"}
_EXTRA_ATTRIBUTE = {"ballad": "ballade", "ballads": "ballade", "power ballad": "ballade",
                    "rock ballad": "ballade", "soundtrack": "bande originale", "rustic": "acoustique",
                    "female vocalist": "voix féminine", "male vocalist": "voix masculine"}
for _d, _cat in ((_EXTRA_MOOD, "mood"), (_EXTRA_CONTEXT, "context"), (_EXTRA_ATTRIBUTE, "attribute")):
    for _k, _v in _d.items():
        TAG_LEXICON.setdefault(_k, (_cat, _v))

# Mots qui signalent un tag de GENRE (liste blanche : tout le reste est considéré comme bruit)
GENRE_HINTS = ("rock", "pop", "metal", "jazz", "folk", "rap", "hip", "soul", "rnb", "r&b", "house",
               "electro", "punk", "indie", "wave", "ambient", "classical", "country", "blues", "disco",
               "funk", "trap", "emo", "grunge", "dance", "techno", "reggae", "latin", "ska", "swing",
               "gospel", "synth", "trip", "downtempo", "chillout", "edm", "dubstep", "garage", "shoegaze",
               "britpop", "bossa", "doo", "motown", "neo-soul", "singer-songwriter", "hardcore", "industrial",
               "bass", "progressive", "psychedelic", "baroque", "chamber", "madchester", "merseybeat",
               "rockabilly", "rock and roll", "new jack", "boom bap", "gangsta", "minimalism", "impressionism",
               "modern classical", "easy listening", "adult contemporary", "aor", "boy band", "boyband")
