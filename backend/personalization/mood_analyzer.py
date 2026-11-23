"""Partie 6 : analyse de l'humeur (émotion, négation, intensité, envie de changer d'humeur ou non)."""
import json
import re
import unicodedata
from pathlib import Path

CHEMIN_BLOCS = Path(__file__).resolve().parents[2] / "data" / "blocks.json"
BLOCS = json.loads(CHEMIN_BLOCS.read_text(encoding="utf-8"))
REGULATION = {"réguler": BLOCS["regulation"]["réguler"], "accompagner": BLOCS["regulation"]["accompagner"]}


def normaliser(texte):
    #minuscules et sans accents, pour ne pas écrire chaque mot en double
    texte = texte.lower().replace("’", "'")
    texte = unicodedata.normalize("NFKD", texte)
    sans_accents = ""
    for lettre in texte:
        if not unicodedata.combining(lettre):
            sans_accents += lettre
    return sans_accents


#\b = limite de mot (pour ne pas trouver "rage" dans "orage")
MOTS_EMOTIONS = {
    "colère": [r"enerve", r"en colere", r"agace", r"irrite", r"furieu", r"\brage\b", r"a bout\b", r"saoule",
               r"vener", r"j'en peux plus", r"marre", r"angry", r"mad\b", r"pissed", r"frustre"],
    "tristesse": [r"trist", r"deprim", r"coeur brise", r"chagrin", r"pleur", r"rupture", r"largue", r"seul\b",
                  r"seule\b", r"le moral (a zero|dans les chaussettes)", r"pas le moral", r"cafard", r"\bsad\b",
                  r"\bdown\b", r"heartbroken", r"lonely", r"blues\b(?! rock)"],
    "stress": [r"stress", r"angoiss", r"anxi", r"pression", r"\bpartiels?\b", r"examens?\b", r"deadline",
               r"debord", r"tendu", r"overwhelm", r"nervous", r"panique"],
    "fatigue": [r"fatigu", r"epuise", r"creve", r"\bko\b", r"tired", r"exhausted", r"sleepy",
                r"sans energie", r"plus d'energie", r"flemme", r"mou\b"],
    "joie": [r"joyeu", r"heureu", r"\bcontent", r"bonne humeur", r"la peche", r"trop bien",
             r"genial", r"happy", r"excited", r"euphori", r"en forme", r"au top"],
    "ennui": [r"m'ennui", r"\bennui", r"rien a faire", r"bored", r"routine", r"monoton"],
    "amour": [r"amoureu", r"en couple", r"romanti", r"crush", r"\bdate\b", r"rendez-vous", r"in love",
              r"mon copain", r"ma copine", r"mon cheri", r"ma cherie", r"diner a deux", r"saint-valentin"],
    "nostalgie": [r"nostalg", r"souvenir", r"enfance", r"l'ancien temps", r"le bon vieux", r"autrefois",
                  r"me manque", r"nostalgic", r"memories"],
}

MOTS_AMBIANCES = {
    "Calme & détente": [r"calme", r"doux\b", r"douce", r"apais", r"detend", r"relax", r"zen\b", r"tranquill",
                        r"chill", r"pose\b", r"soft\b", r"calm\b"],
    "Concentration": [r"concentr", r"focus", r"reviser", r"etudier", r"bosser", r"travailler", r"study"],
    "Énergie & motivation": [r"motiv", r"booster", r"la peche", r"energique", r"pump", r"puissant", r"energy",
                             r"me reveiller", r"me donner de l'energie"],
    "Fête & danse": [r"danser", r"dansant", r"\bfete\b", r"soiree", r"party", r"\bdance"],
    "Rêverie & évasion": [r"evad", r"planant", r"rever", r"\breve\b", r"voyage", r"ailleurs", r"dream"],
    "Romance & sensualité": [r"sensuel", r"romanti", r"romance"],
    "Mélancolie & introspection": [r"melancoli", r"introspect", r"reflechir", r"pensif"],
    "Colère & défoulement": [r"defouler", r"defoule", r"lacher", r"crier", r"bruyant", r"sature"],
    "Joie & bonne humeur": [r"joyeu", r"ensoleill", r"optimis", r"feel good", r"bonne humeur", r"sourire"],
}

#envie de changer d'humeur / de rester dedans
MOTS_REGULER = [r"me calm", r"\bcalmer", r"me deten", r"me remonter", r"remonter le moral", r"me changer les idees",
                r"oublier", r"aller mieux", r"me motiver", r"me booster", r"me reveiller", r"me redonner",
                r"me faire sourire", r"me rendre (heureu|joyeu)", r"decompresser", r"me poser", r"m'apaiser",
                r"faire baisser", r"cheer me up", r"calm (me )?down", r"feel better", r"pick me up", r"relax"]
MOTS_ACCOMPAGNER = [r"me defouler", r"defouler", r"lacher", r"pleurer", r"m'accompagne", r"accompagner",
                    r"qui me ressemble", r"comme moi", r"rester dans", r"vibrer avec", r"ressasser", r"vider",
                    r"exprimer", r"let it out", r"vent\b", r"wallow", r"feel it", r"sad songs?"]

NEGATIONS = r"(\bpas\b|\bplus\b|\bjamais\b|\bnon\b|\bni\b|\bsans\b|\bnot\b|n't\b|\bno\b|\bnever\b)"
INTENSIFS = r"(\btres\b|\btrop\b|\bvraiment\b|\btellement\b|\bhyper\b|\bsuper\b|\bgrave\b|\bcompletement\b|" \
            r"\btotalement\b|\bextremement\b|\breally\b|\bso\b|\bvery\b|\bextremely\b)"

HUMEURS_COCHEES_EMOTION = {"Happy": "joie", "Sad": "tristesse", "Stressed": "stress",
                           "Melancholic": "nostalgie", "Romantic": "amour"}
HUMEURS_COCHEES_AMBIANCE = {"Calm": "Calme & détente", "Energetic": "Énergie & motivation",
                            "Focused": "Concentration"}

EMOTIONS_NEGATIVES = ["colère", "tristesse", "stress", "fatigue", "ennui", "nostalgie"]


def trouver(motifs, texte):
    trouves = []
    for motif in motifs:
        for resultat in re.finditer(motif, texte):
            trouves.append((resultat.start(), resultat.group(0)))
    return trouves


def est_nie(texte, position):
    #négation dans les 3 mots d'avant : "je ne suis pas triste"
    debut_de_phrase = re.split(r"[.!?;,]", texte[:position])[-1]
    trois_mots_avant = " ".join(debut_de_phrase.split()[-3:])
    return re.search(NEGATIONS, trois_mots_avant) is not None


def ajouter(dico, cle, valeur):
    dico[cle] = dico.get(cle, 0) + valeur


def trier_et_ramener_a_1(dico, diviseur):
    trie = sorted(dico.items(), key=lambda paire: -paire[1])
    return {cle: round(valeur / diviseur, 3) for cle, valeur in trie}


def analyser_humeur(texte="", humeurs_cochees=None):
    texte = normaliser(texte or "")
    humeurs_cochees = humeurs_cochees or []

    emotions = {}          #émotion -> score
    emotions_niees = []    #émotions trouvées mais niées ("pas triste")
    ambiances = {}         #bloc d'humeur demandé directement -> score
    indices = []           #mots trouvés dans le texte (pour expliquer le profil)

    for emotion, motifs in MOTS_EMOTIONS.items():
        for position, mot in trouver(motifs, texte):
            if est_nie(texte, position):
                if emotion not in emotions_niees:
                    emotions_niees.append(emotion)
            else:
                ajouter(emotions, emotion, 1.0)
                indices.append(mot)

    for bloc, motifs in MOTS_AMBIANCES.items():
        for position, mot in trouver(motifs, texte):
            if not est_nie(texte, position):
                ajouter(ambiances, bloc, 1.0)
                indices.append(mot)

    #les cases cochées comptent un peu moins que le texte
    for humeur in humeurs_cochees:
        if humeur in HUMEURS_COCHEES_EMOTION:
            emotion = HUMEURS_COCHEES_EMOTION[humeur]
            if emotion not in emotions_niees:
                ajouter(emotions, emotion, 0.8)
        elif humeur in HUMEURS_COCHEES_AMBIANCE:
            ajouter(ambiances, HUMEURS_COCHEES_AMBIANCE[humeur], 0.8)

    nb_intensifs = len(re.findall(INTENSIFS, texte)) + min(texte.count("!"), 2)
    if nb_intensifs >= 2:
        intensite = 3
    elif nb_intensifs == 1:
        intensite = 2
    else:
        intensite = 1

    #par défaut on accompagne l'émotion
    strategie = "accompagner"
    strategie_source = "défaut"
    trouves_reguler = trouver(MOTS_REGULER, texte)
    trouves_accompagner = trouver(MOTS_ACCOMPAGNER, texte)
    if trouves_reguler or trouves_accompagner:
        strategie_source = "texte"
        if len(trouves_reguler) > len(trouves_accompagner):
            strategie = "réguler"
            indices += [mot for _, mot in trouves_reguler]
        else:
            indices += [mot for _, mot in trouves_accompagner]

    blocs_cibles = {}
    for emotion, score in emotions.items():
        #on ne cherche pas à "réguler" une émotion positive
        regle = strategie if emotion in EMOTIONS_NEGATIVES else "accompagner"
        bloc = REGULATION[regle].get(emotion)
        if bloc:
            ajouter(blocs_cibles, bloc, score)
    for bloc, score in ambiances.items():
        ajouter(blocs_cibles, bloc, score * 1.2)

    emotion_dominante = None
    if emotions:
        emotions = trier_et_ramener_a_1(emotions, sum(emotions.values()))
        emotion_dominante = list(emotions)[0]
    if blocs_cibles:
        blocs_cibles = trier_et_ramener_a_1(blocs_cibles, max(blocs_cibles.values()))

    indices_uniques = []
    for mot in indices:
        if mot not in indices_uniques:
            indices_uniques.append(mot)

    return {
        "emotions": emotions,
        "emotion_dominante": emotion_dominante,
        "emotions_niees": emotions_niees,
        "intensite": intensite,
        "strategie": strategie,
        "strategie_source": strategie_source,
        "ambiances": ambiances,
        "blocs_cibles": blocs_cibles,
        "indices": indices_uniques,
    }
