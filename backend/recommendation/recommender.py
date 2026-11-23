"""Classement des morceaux et explications (partie 4).

Pour chaque recommandation : le morceau, son score, les principaux critères et une
explication construite avec des phrases toutes faites (pas d'IA générative).
"""
from .scoring import calculer_scores, construire_profil, niveau, separer

NOMS = {"description": "Proche de votre description", "humeur": "Humeur", "contexte": "Contexte d'écoute",
        "genre": "Genre préféré", "energie": "Énergie", "artiste": "Artiste préféré"}


def meilleur_bloc(blocs_morceau, profil_blocs):
    blocs = [b for b in separer(blocs_morceau) if b in profil_blocs]
    return max(blocs, key=profil_blocs.get) if blocs else ""


def phrase(critere, m, valeur, profil):
    #une phrase par critère, remplie avec les scores
    if critere == "description":
        return f"sa description est proche de ce que vous avez écrit ({valeur:.0%})"
    if critere == "humeur":
        return f"son ambiance « {meilleur_bloc(m['mood_blocks'], profil['blocs_humeur'])} » correspond à votre humeur ({valeur:.0%})"
    if critere == "contexte":
        return f"il colle au contexte « {meilleur_bloc(m['context_blocks'], profil['blocs_contexte'])} » ({valeur:.0%})"
    if critere == "genre":
        return f"c'est du {m['genre']}, un genre que vous aimez"
    if critere == "energie":
        return f"son énergie ({m['energy']}/5) est proche de celle demandée ({profil['energie']}/5)"
    return f"c'est un morceau de {m['artist']}, un de vos artistes préférés"


def recommander(sm, requete, top_k=3):
    profil = construire_profil(sm, requete)
    S, poids, score, brut = calculer_scores(sm, profil)
    df = sm.tracks
    total = sum(poids.values())

    resultats, artistes_vus = [], set()
    for i in score.sort_values(ascending=False).index:
        m = df.loc[i].fillna("")
        #un seul morceau par artiste pour avoir un top varié
        if m["artist"] in artistes_vus:
            continue
        artistes_vus.add(m["artist"])

        s = float(score[i])
        #contribution de chaque critère = Wi * Si / somme(Wi)
        contrib = {c: float(S.loc[i, c] * poids[c] / total) for c in poids}
        principaux = [c for c in sorted(contrib, key=contrib.get, reverse=True) if S.loc[i, c] > 0][:3]
        resultats.append({
            "rang": len(resultats) + 1,
            "track_id": str(m["track_id"]),
            "titre": m["title"],
            "artiste": m["artist"],
            "genre": m["genre"],
            "humeurs": separer(m["mood"]),
            "blocs_humeur": separer(m["mood_blocks"]),
            "contextes": separer(m["context"]),
            "energie": int(m["energy"]),
            "score": round(s, 3),
            "niveau": niveau(s),
            "cosinus_brut": round(float(brut[i]), 3),
            "criteres": {c: round(float(S.loc[i, c]), 3) for c in S.columns},
            "contributions": {c: round(v, 3) for c, v in contrib.items()},
            "principaux_criteres": [NOMS[c] for c in principaux],
            "explication": f"« {m['title']} » de {m['artist']} est recommandé car "
                           + ", ".join(phrase(c, m, S.loc[i, c], profil) for c in principaux)
                           + f". {niveau(s)} (score {s:.0%}).",
        })
        if len(resultats) == top_k:
            break

    top2 = sorted(profil["blocs_humeur"], key=profil["blocs_humeur"].get, reverse=True)[:2]
    synthese = f"Vous cherchez une ambiance « {top2[0]} » / « {top2[1]} »"
    if profil["contexte_dominant"]:
        synthese += f", pour un contexte « {profil['contexte_dominant']} »"
    if profil["energie"]:
        synthese += f", énergie {profil['energie']}/5"
    if profil["genres"]:
        synthese += ", genres : " + ", ".join(profil["genres"])

    return {"profil": {**profil, "synthese": profil.get("synthese") or synthese + "."}, "recommandations": resultats, "poids": poids,
            "scores": score, "criteres": S}
