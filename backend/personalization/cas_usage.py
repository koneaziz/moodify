"""Cas d'usage pour vérifier la pertinence du profil et des recommandations (partie 6).

Chaque cas = un utilisateur type qui remplit le questionnaire du front, et ce qu'on attend :
  - pour le PROFIL : émotion détectée, stratégie, bloc d'humeur et contexte dominants, exclusions… ;
  - pour les RECOMMANDATIONS : à quoi ressemble un morceau pertinent (blocs d'humeur, énergie…),
    ce qui permet de calculer la Precision@3 (part des 3 morceaux recommandés qui sont pertinents).

Les cas couvrent les situations du sujet et les « cas pièges » du README (§19) : paraphrase sans
mot-clé, négation, stratégie « changer d'humeur » vs « rester dedans », exclusion de genre,
demande d'instrumental, texte en anglais, fautes de frappe.

Utilisés par tests/test_profile.py et par `python -m backend.personalization.evaluation`.
"""


def questionnaire(description, moods=(), genres=(), contexte="", contexte_texte="", energie=3,
                  artistes="", voix="No preference", extra=""):
    """Même format que ce qu'envoie le front (frontend/types/questionnaire.ts)."""
    return {"moods": list(moods), "description": description, "genres": list(genres),
            "listeningContext": contexte, "contextDescription": contexte_texte, "energyLevel": energie,
            "favoriteArtists": artistes, "vocalPreference": voix, "additionalPreferences": extra}


CAS = [
    {
        "id": "C01", "persona": "Étudiante stressée qui veut se calmer pour réviser",
        "piege": "stratégie « réguler » + exclusion + instrumental",
        "questionnaire": questionnaire(
            "Je suis à bout avec les partiels, trop de pression, il faut que je me calme",
            moods=["Stressed"], genres=["Lo-Fi", "Jazz"], contexte="Studying", energie=2,
            voix="Instrumental", extra="pas de rap"),
        "profil": {"emotion": "stress", "strategie": "réguler", "humeur_top2": ["Calme & détente", "Concentration"],
                   "contexte": "Étude & travail", "genres_exclus": ["Hip-hop / Rap"], "instrumental": True},
        "pertinent": {"blocs": ["Calme & détente", "Concentration", "Rêverie & évasion"], "energie": (1, 3),
                      "instrumental": True},
    },
    {
        "id": "C02", "persona": "Énervé qui veut se défouler à la salle",
        "piege": "même émotion que C03, stratégie inverse (« accompagner »)",
        "questionnaire": questionnaire(
            "Je suis vraiment énervé contre tout le monde, j'ai besoin de me défouler !",
            moods=["Energetic"], genres=["Rock"], contexte="Exercising", energie=5),
        "profil": {"emotion": "colère", "strategie": "accompagner",
                   "humeur_top2": ["Colère & défoulement", "Énergie & motivation"], "contexte": "Sport"},
        "pertinent": {"blocs": ["Colère & défoulement", "Énergie & motivation"], "energie": (4, 5)},
    },
    {
        "id": "C03", "persona": "Énervée qui veut retrouver son calme",
        "piege": "même émotion que C02, stratégie « réguler »",
        "questionnaire": questionnaire("Je suis énervée, je veux juste me calmer et souffler un peu",
                                       contexte="Relaxing", energie=1),
        "profil": {"emotion": "colère", "strategie": "réguler", "humeur_top2": ["Calme & détente"]},
        "pertinent": {"blocs": ["Calme & détente"], "energie": (1, 3)},
    },
    {
        "id": "C04", "persona": "Chagrin d'amour, veut des chansons tristes",
        "piege": "émotion négative sans stratégie explicite (par défaut : accompagner)",
        "questionnaire": questionnaire("J'ai le cœur brisé depuis ma rupture, je suis triste ce soir",
                                       moods=["Sad"], genres=["Pop", "Indie"], energie=2),
        "profil": {"emotion": "tristesse", "strategie": "accompagner",
                   "humeur_top2": ["Mélancolie & introspection"]},
        "pertinent": {"blocs": ["Mélancolie & introspection"], "energie": (1, 3)},
    },
    {
        "id": "C05", "persona": "Triste mais veut qu'on lui remonte le moral",
        "piege": "même émotion que C04, stratégie « réguler »",
        "questionnaire": questionnaire("Je suis triste aujourd'hui, j'ai besoin d'un truc pour me remonter le moral",
                                       moods=["Sad"], energie=3),
        "profil": {"emotion": "tristesse", "strategie": "réguler", "humeur_top2": ["Joie & bonne humeur"]},
        "pertinent": {"blocs": ["Joie & bonne humeur", "Fête & danse"], "energie": (2, 5)},
    },
    {
        "id": "C06", "persona": "Fatigué mais PAS triste, veut se réveiller",
        "piege": "négation (« pas triste ») : la tristesse ne doit pas être retenue",
        "questionnaire": questionnaire("Je ne suis pas triste, juste crevé, il me faut un truc pour me réveiller le matin",
                                       contexte_texte="avant d'aller en cours", energie=4),
        "profil": {"emotion": "fatigue", "strategie": "réguler", "emotions_niees": ["tristesse"],
                   "humeur_top2": ["Énergie & motivation"]},
        "pertinent": {"blocs": ["Énergie & motivation", "Joie & bonne humeur"], "energie": (3, 5)},
    },
    {
        "id": "C07", "persona": "Soirée entre amis",
        "piege": "joie + contexte écrit dans le texte",
        "questionnaire": questionnaire("Trop contente, on fait une soirée chez moi avec des amis ce soir, on veut danser",
                                       moods=["Happy"], genres=["Electronic", "Pop"], contexte="Partying", energie=5),
        "profil": {"emotion": "joie", "humeur_top2": ["Fête & danse"], "contexte": "Soirée & fête"},
        "pertinent": {"blocs": ["Fête & danse", "Joie & bonne humeur", "Énergie & motivation"], "energie": (3, 5)},
    },
    {
        "id": "C08", "persona": "Dîner romantique",
        "piege": "émotion positive : jamais « régulée »",
        "questionnaire": questionnaire("Je prépare un dîner aux chandelles pour mon copain, ambiance romantique",
                                       moods=["Romantic"], genres=["R&B", "Soul"], energie=2),
        "profil": {"emotion": "amour", "humeur_top2": ["Romance & sensualité"], "contexte": "Moment à deux"},
        "pertinent": {"blocs": ["Romance & sensualité"], "energie": (1, 4)},
    },
    {
        "id": "C09", "persona": "Concentration au travail, sans paroles",
        "piege": "aucune émotion, seulement une ambiance + instrumental écrit dans le texte",
        "questionnaire": questionnaire("Je dois coder toute l'après-midi, il me faut quelque chose sans paroles pour rester concentré",
                                       moods=["Focused"], contexte="Working", energie=2),
        "profil": {"emotion": None, "humeur_top2": ["Concentration", "Calme & détente"],
                   "contexte": "Étude & travail", "instrumental": True},
        "pertinent": {"blocs": ["Concentration", "Calme & détente", "Rêverie & évasion"], "energie": (1, 3),
                      "instrumental": True},
    },
    {
        "id": "C10", "persona": "Nostalgique un jour de pluie",
        "piege": "deux émotions proches (nostalgie, tristesse) + contexte « pluie »",
        "questionnaire": questionnaire("Il pleut, je regarde de vieilles photos, je suis nostalgique de mon enfance",
                                       moods=["Melancholic"], energie=2),
        "profil": {"emotion": "nostalgie", "humeur_top2": ["Mélancolie & introspection", "Rêverie & évasion"],
                   "contexte": "Solitude & pluie"},
        "pertinent": {"blocs": ["Mélancolie & introspection", "Rêverie & évasion"], "energie": (1, 3)},
    },
    {
        "id": "C11", "persona": "Endormissement, pas de metal",
        "piege": "exclusion formulée autrement (« je déteste le metal »)",
        "questionnaire": questionnaire("J'ai du mal à dormir, je veux une musique très douce pour m'endormir",
                                       contexte="Sleeping", energie=1, extra="je déteste le metal"),
        "profil": {"humeur_top2": ["Calme & détente"], "contexte": "Sommeil & méditation",
                   "genres_exclus": ["Metal"]},
        "pertinent": {"blocs": ["Calme & détente", "Rêverie & évasion"], "energie": (1, 2)},
    },
    {
        "id": "C12", "persona": "Road trip ensoleillé",
        "piege": "contexte uniquement dans le texte (rien de coché)",
        "questionnaire": questionnaire("On part en road trip en voiture cet été, je veux des sons ensoleillés et optimistes",
                                       energie=4),
        "profil": {"humeur_top2": ["Joie & bonne humeur"], "contexte": "Trajet"},
        "pertinent": {"blocs": ["Joie & bonne humeur", "Fête & danse", "Énergie & motivation"], "energie": (3, 5)},
    },
    {
        "id": "C13", "persona": "Utilisateur qui écrit en anglais",
        "piege": "texte en anglais (l'interface est en anglais)",
        "questionnaire": questionnaire("I'm so stressed about my exams, I need something to calm down",
                                       moods=["Stressed"], contexte="Studying", energie=2),
        "profil": {"emotion": "stress", "strategie": "réguler", "humeur_top2": ["Calme & détente", "Concentration"],
                   "contexte": "Étude & travail"},
        "pertinent": {"blocs": ["Calme & détente", "Concentration"], "energie": (1, 3)},
    },
    {
        "id": "C14", "persona": "Paraphrase sans mot d'émotion connu",
        "piege": "les règles ne trouvent rien : seul le sémantique (partie 3) peut aider",
        "questionnaire": questionnaire("La journée a été longue et lourde, j'ai la tête qui tourne, besoin de me poser",
                                       energie=1),
        "profil": {"strategie": "réguler", "humeur_top2": ["Calme & détente"]},
        "pertinent": {"blocs": ["Calme & détente", "Rêverie & évasion"], "energie": (1, 3)},
    },
    {
        "id": "C15", "persona": "Fautes de frappe",
        "piege": "orthographe approximative (« enervé », « defoulé », sans accents)",
        "questionnaire": questionnaire("chui trop enervé jveux me defouler a fond", genres=["Rock"], energie=5),
        "profil": {"emotion": "colère", "strategie": "accompagner", "humeur_top2": ["Colère & défoulement"]},
        "pertinent": {"blocs": ["Colère & défoulement", "Énergie & motivation"], "energie": (4, 5)},
    },
]


def morceau_pertinent(morceau, attendu: dict) -> bool:
    """Un morceau (ligne du dataset) est pertinent s'il partage un bloc d'humeur attendu, a une énergie
    dans la plage attendue et respecte la demande d'instrumental. (Approximation automatique : à
    compléter par une relecture humaine, comme indiqué au §19 du README.)"""
    blocs = {b.strip() for b in str(morceau.get("mood_blocks", "")).split("|") if b.strip()}
    if not blocs & set(attendu["blocs"]):
        return False
    emin, emax = attendu.get("energie", (1, 5))
    if not emin <= int(morceau.get("energy", 3)) <= emax:
        return False
    if attendu.get("instrumental"):
        instru = str(morceau.get("language", "")) == "instrumental" or float(morceau.get("instrumentalness") or 0) >= 0.5
        if not instru:
            return False
    return True
