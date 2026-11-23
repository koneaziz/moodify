"""Partie 6 : profil utilisateur construit à partir de tout le questionnaire.
Les blocs d'humeur et de contexte = 50 % sémantique (partie 3) + 50 % nos règles.
L'ancien format de requête de la partie 4 est encore accepté (notebook 03)."""
import json
import re
from pathlib import Path

from .mood_analyzer import analyser_humeur, normaliser

CHEMIN_ARCHETYPES = Path(__file__).resolve().parents[2] / "data" / "archetypes.json"
ARCHETYPES = json.loads(CHEMIN_ARCHETYPES.read_text(encoding="utf-8"))["archetypes"]

POIDS_SEMANTIQUE = 0.5
POIDS_REGLES = 0.5

GENRES_FRONT = {
    "Pop": ["Pop"], "Hip-Hop": ["Hip-hop / Rap"], "R&B": ["R&B / Soul / Funk"], "Soul": ["R&B / Soul / Funk"],
    "Rock": ["Rock"], "Jazz": ["Jazz / Blues"], "Classical": ["Classique"], "Electronic": ["Électro / House"],
    "Lo-Fi": ["Lo-fi / Chill"], "Indie": ["Indie / Folk / Country"], "Ambient": ["Ambient"],
    "Other": ["Metal", "Afro / Reggae / Latino", "Chanson française", "Musiques du monde"],
}
#phrases envoyées à l'analyse sémantique pour les cases cochées
HUMEURS_FRONT = {
    "Happy": "je me sens joyeux", "Sad": "je suis triste", "Calm": "j'ai envie de calme",
    "Stressed": "je suis stressé", "Energetic": "je suis plein d'énergie",
    "Focused": "j'ai besoin de me concentrer", "Melancholic": "je me sens mélancolique",
    "Romantic": "je suis d'humeur romantique",
}
CONTEXTES_FRONT = {
    "Studying": "pour réviser et étudier", "Working": "pour travailler", "Relaxing": "pour me détendre",
    "Exercising": "pour faire du sport", "Driving": "en conduisant", "Sleeping": "pour m'endormir",
    "Partying": "pour faire la fête", "Just vibing": "juste pour le plaisir",
}
CONTEXTE_COCHE_BLOC = {
    "Studying": "Étude & travail", "Working": "Étude & travail", "Exercising": "Sport", "Driving": "Trajet",
    "Sleeping": "Sommeil & méditation", "Partying": "Soirée & fête", "Relaxing": "Sommeil & méditation",
}

MOTS_CONTEXTES = {
    "Étude & travail": [r"revis", r"etudi", r"bosser", r"travail", r"\bcours\b", r"exam", r"partiel", r"devoirs",
                        r"bibli", r"memoire\b", r"study", r"work\b", r"homework", r"coder\b"],
    "Sport": [r"sport", r"courir", r"\bcourse\b", r"footing", r"jogging", r"muscu", r"salle\b", r"seance",
              r"entrainement", r"velo", r"\brun\b", r"running", r"\bgym\b", r"workout"],
    "Soirée & fête": [r"soiree", r"\bfete\b", r"party", r"entre amis", r"avec des amis", r"apero", r"\bclub\b",
                      r"anniversaire"],
    "Trajet": [r"voiture", r"route", r"trajet", r"metro", r"\bbus\b", r"\btrain\b", r"conduis", r"conduire",
               r"commute", r"\bdriv"],
    "Sommeil & méditation": [r"dormir", r"endormir", r"sommeil", r"sieste", r"medit", r"yoga", r"respir",
                             r"sleep", r"\bnuit\b"],
    "Moment à deux": [r"a deux", r"en amoureux", r"mon copain", r"ma copine", r"mon cheri", r"ma cherie",
                      r"diner", r"\bdate\b", r"rendez-vous", r"couple"],
    "Solitude & pluie": [r"pluie", r"pleut", r"\bseule?\b", r"solitude", r"\brain", r"alone", r"grisaille"],
    "Matin & quotidien": [r"matin", r"reveil", r"petit[- ]dej", r"douche", r"menage", r"cuisine", r"ranger",
                          r"morning", r"journee"],
}
MOTS_GENRES = {
    "Hip-hop / Rap": [r"\brap\b", r"hip[- ]?hop", r"\btrap\b", r"drill"],
    "Metal": [r"metal", r"hard ?rock"],
    "Rock": [r"\brock\b"],
    "Pop": [r"\bpop\b"],
    "Électro / House": [r"electro", r"\bhouse\b", r"techno", r"\bedm\b"],
    "Classique": [r"classique", r"classical", r"opera", r"orchestr"],
    "Jazz / Blues": [r"\bjazz", r"\bblues\b"],
    "R&B / Soul / Funk": [r"r&b", r"\brnb\b", r"\bsoul\b", r"\bfunk"],
    "Lo-fi / Chill": [r"lo-?fi"],
    "Ambient": [r"ambient"],
    "Indie / Folk / Country": [r"\bfolk\b", r"country", r"\bindie\b"],
    "Afro / Reggae / Latino": [r"reggae", r"\bafro", r"latino", r"reggaeton", r"salsa"],
    "Chanson française": [r"chanson francaise", r"variete"],
}
#"pas de rap", "je déteste le metal"...
MOTS_REFUS = r"(pas de|pas du|pas d'|sans|aucun|evite[rz]?|deteste|horreur d[eu]|supporte pas|j'aime pas|" \
             r"je n'aime pas|plus de|no\b|not\b|hate|without|avoid|except)"
MOTS_INSTRUMENTAL = r"(sans paroles?|pas de paroles?|instrumental|no lyrics|without lyrics|pas de voix|sans voix)"

NOMS_EMOTIONS = {"colère": "énervé(e)", "tristesse": "triste", "stress": "stressé(e)", "fatigue": "fatigué(e)",
                 "joie": "joyeux(se)", "ennui": "désœuvré(e)", "amour": "amoureux(se)", "nostalgie": "nostalgique"}
NOMS_INTENSITE = {1: "", 2: "assez ", 3: "très "}


def normaliser_blocs(scores):
    #min-max comme dans la partie 4
    if not scores:
        return {}
    mini = min(scores.values())
    maxi = max(scores.values())
    resultat = {}
    for bloc, score in scores.items():
        resultat[bloc] = (score - mini) / (maxi - mini + 1e-9)
    return resultat


def combiner(semantique, regles):
    if not regles:
        return semantique
    if not semantique:
        return regles
    blocs = list(semantique) + [b for b in regles if b not in semantique]
    melange = {}
    for bloc in blocs:
        melange[bloc] = POIDS_SEMANTIQUE * semantique.get(bloc, 0) + POIDS_REGLES * regles.get(bloc, 0)
    return dict(sorted(melange.items(), key=lambda paire: -paire[1]))


def detecter_contextes(texte, contexte_coche=""):
    #case cochée = 1, mot trouvé dans le texte = 0.8
    texte = normaliser(texte)
    scores = {}
    if contexte_coche in CONTEXTE_COCHE_BLOC:
        scores[CONTEXTE_COCHE_BLOC[contexte_coche]] = 1.0
    for bloc, motifs in MOTS_CONTEXTES.items():
        for motif in motifs:
            if re.search(motif, texte):
                scores[bloc] = max(scores.get(bloc, 0), 0.8)
                break
    return dict(sorted(scores.items(), key=lambda paire: -paire[1]))


def detecter_exclusions(texte):
    texte = normaliser(texte)
    exclus = []
    for genre, motifs in MOTS_GENRES.items():
        for motif in motifs:
            if re.search(MOTS_REFUS + r"\s+(?:\w+\s+){0,2}?" + motif, texte):
                exclus.append(genre)
                break
    return exclus


def trouver_archetype(blocs_humeur):
    #couverture = somme(poids * score du bloc) / somme(poids), comme dans le sujet
    meilleur = None
    for archetype in ARCHETYPES:
        somme = 0
        for bloc, poids in archetype["blocks"].items():
            somme += poids * blocs_humeur.get(bloc, 0)
        couverture = somme / sum(archetype["blocks"].values())
        if meilleur is None or couverture > meilleur["couverture"]:
            meilleur = {"id": archetype["id"], "nom": archetype["name"],
                        "description": archetype["description"], "couverture": round(couverture, 3)}
    return meilleur


def ecrire_synthese(profil):
    if profil["emotion"]:
        debut = "Vous vous sentez " + NOMS_INTENSITE[profil["intensite"]] + profil["emotion_label"]
        if profil["strategie_source"] == "texte":
            if profil["strategie"] == "réguler":
                debut += " et voulez changer d'humeur"
            else:
                debut += " et voulez rester dans cette émotion"
        debut += " : vous cherchez"
    else:
        debut = "Vous cherchez"

    blocs = list(profil["blocs_humeur"].items())
    meilleur_score = max(profil["blocs_humeur"].values())
    ambiances = [bloc for bloc, score in blocs[:2] if score >= 0.75 * meilleur_score]
    phrase = debut + " une ambiance « " + ambiances[0] + " »"
    if len(ambiances) > 1:
        phrase += " / « " + ambiances[1] + " »"

    details = []
    if profil["contexte_dominant"]:
        details.append("pour un contexte « " + profil["contexte_dominant"] + " »")
    if profil["energie"]:
        details.append("énergie " + str(profil["energie"]) + "/5")
    if profil["genres"]:
        details.append("genres : " + ", ".join(profil["genres"]))
    if profil["genres_exclus"]:
        details.append("sans " + ", ".join(profil["genres_exclus"]))
    if profil["instrumental"]:
        details.append("plutôt instrumental")
    if details:
        phrase += ", " + ", ".join(details)
    return phrase + "."


def depuis_ancien_format(requete):
    #ancien format de la partie 4 -> questionnaire (genres déjà au format du dataset)
    textes = [t for t in requete.get("textes", []) if t]
    humeur = [t for t in requete.get("humeur", []) if t]
    contexte = [t for t in requete.get("contexte", []) if t]
    return {
        "moods": [],
        "description": " ".join(humeur or textes),
        "genres": [],
        "genres_dataset": requete.get("genres") or [],
        "listeningContext": "",
        "contextDescription": " ".join(contexte),
        "energyLevel": requete.get("energie"),
        "favoriteArtists": ", ".join(requete.get("artistes") or []),
        "vocalPreference": "No preference",
        "additionalPreferences": "",
        "textes_supplementaires": textes,
    }


def garder_textes_non_vides(textes):
    resultat = []
    for texte in textes:
        if texte and texte.strip() and texte not in resultat:
            resultat.append(texte)
    return resultat


def construire_profil_utilisateur(sm, donnees):
    if "textes" in donnees or "humeur" in donnees:
        q = depuis_ancien_format(donnees)
    else:
        q = dict(donnees)

    description = q.get("description") or ""
    contexte_texte = q.get("contextDescription") or ""
    preferences_texte = q.get("additionalPreferences") or ""
    contexte_coche = q.get("listeningContext") or ""
    humeurs_cochees = q.get("moods") or []
    tout_le_texte = description + " " + contexte_texte + " " + preferences_texte

    analyse = analyser_humeur(description + " " + contexte_texte, humeurs_cochees)

    textes_humeur = [description]
    for humeur in humeurs_cochees:
        if humeur in HUMEURS_FRONT:
            textes_humeur.append(HUMEURS_FRONT[humeur])
    textes_contexte = [CONTEXTES_FRONT.get(contexte_coche, ""), contexte_texte]
    textes = textes_humeur + textes_contexte + [preferences_texte] + q.get("textes_supplementaires", [])

    instrumental = q.get("vocalPreference") == "Instrumental"
    if re.search(MOTS_INSTRUMENTAL, normaliser(tout_le_texte)):
        instrumental = True
    if instrumental:
        textes.append("musique instrumentale sans paroles")

    textes = garder_textes_non_vides(textes)
    textes_humeur = [t for t in textes_humeur if t and t.strip()] or textes
    textes_contexte = [t for t in textes_contexte if t and t.strip()]

    humeur_brut = {}
    if sm is not None and textes_humeur:
        humeur_brut = sm.mood_affinity(textes_humeur)
    blocs_humeur = combiner(normaliser_blocs(humeur_brut), analyse["blocs_cibles"])
    if not blocs_humeur:
        blocs_humeur = {"Calme & détente": 0.0}

    contextes_regles = detecter_contextes(tout_le_texte, contexte_coche)
    contexte_brut = {}
    if sm is not None and textes_contexte:
        contexte_brut = sm.context_affinity(textes_contexte)
    blocs_contexte = {}
    if textes_contexte or contextes_regles:
        blocs_contexte = combiner(normaliser_blocs(contexte_brut), contextes_regles)

    exclus = detecter_exclusions(tout_le_texte)
    genres = list(q.get("genres_dataset") or [])
    for genre_front in q.get("genres") or []:
        genres += GENRES_FRONT.get(genre_front, [genre_front])
    genres_gardes = []
    for genre in genres:
        if genre not in exclus and genre not in genres_gardes:
            genres_gardes.append(genre)

    artistes = []
    for nom in re.split(r"[,;]| et | and ", q.get("favoriteArtists") or ""):
        if nom.strip():
            artistes.append(nom.strip().lower())

    profil = {
        #utilisé par la partie 4
        "textes": textes,
        "genres": genres_gardes,
        "artistes": artistes,
        "energie": q.get("energyLevel"),
        "humeur_brut": humeur_brut,
        "contexte_brut": contexte_brut,
        "blocs_humeur": blocs_humeur,
        "blocs_contexte": blocs_contexte,
        "humeur_dominante": max(blocs_humeur, key=blocs_humeur.get),
        "contexte_dominant": max(blocs_contexte, key=blocs_contexte.get) if blocs_contexte else None,
        #ajouts de la partie 6
        "emotion": analyse["emotion_dominante"],
        "emotion_label": NOMS_EMOTIONS.get(analyse["emotion_dominante"] or "", ""),
        "emotions": analyse["emotions"],
        "emotions_niees": analyse["emotions_niees"],
        "intensite": analyse["intensite"],
        "strategie": analyse["strategie"],
        "strategie_source": analyse["strategie_source"],
        "blocs_cibles_regles": analyse["blocs_cibles"],
        "contextes_regles": contextes_regles,
        "genres_exclus": exclus,
        "instrumental": instrumental,
        "indices": analyse["indices"],
    }
    profil["archetype"] = trouver_archetype(blocs_humeur)
    profil["synthese"] = ecrire_synthese(profil)
    return profil
