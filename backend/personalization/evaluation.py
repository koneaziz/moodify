"""Partie 6 : évaluation des cas d'usage (profil + Precision@3), comparée au profil d'avant.
    python -m backend.personalization.evaluation [--encoder tfidf]
Le rapport est écrit dans docs/cas_usage_profil.md."""
import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src"))

from backend.personalization.cas_usage import CAS, morceau_pertinent  # noqa: E402
from backend.personalization.preference_profiler import (CONTEXTES_FRONT, GENRES_FRONT,  # noqa: E402
                                                         HUMEURS_FRONT, construire_profil_utilisateur,
                                                         normaliser_blocs)

RAPPORT = RACINE / "docs" / "cas_usage_profil.md"


def verifier_profil(profil, attendu):
    #liste de (critère, réussi, obtenu, attendu)
    verifications = []
    if "emotion" in attendu:
        verifications.append(("emotion", profil["emotion"] == attendu["emotion"],
                              profil["emotion"], attendu["emotion"]))
    if "strategie" in attendu:
        verifications.append(("strategie", profil["strategie"] == attendu["strategie"],
                              profil["strategie"], attendu["strategie"]))
    if "contexte" in attendu:
        verifications.append(("contexte", profil["contexte_dominant"] == attendu["contexte"],
                              profil["contexte_dominant"], attendu["contexte"]))
    if "instrumental" in attendu:
        verifications.append(("instrumental", profil["instrumental"] == attendu["instrumental"],
                              profil["instrumental"], attendu["instrumental"]))
    if "genres_exclus" in attendu:
        ok = sorted(profil["genres_exclus"]) == sorted(attendu["genres_exclus"])
        verifications.append(("genres_exclus", ok, profil["genres_exclus"], attendu["genres_exclus"]))
    if "emotions_niees" in attendu:
        ok = all(e in profil["emotions_niees"] for e in attendu["emotions_niees"])
        verifications.append(("emotions_niees", ok, profil["emotions_niees"], attendu["emotions_niees"]))
    if "humeur_top2" in attendu:
        top2 = list(profil["blocs_humeur"])[:2]
        bloc_attendu = attendu["humeur_top2"][0]
        verifications.append(("humeur", bloc_attendu in top2, top2, bloc_attendu))
    return verifications


def profil_avant_partie6(sm, q):
    #profil d'avant la partie 6 : affinités sémantiques seules (pour comparer)
    textes_humeur = [q["description"]]
    for humeur in q["moods"]:
        if humeur in HUMEURS_FRONT:
            textes_humeur.append(HUMEURS_FRONT[humeur])
    textes_humeur = [t for t in textes_humeur if t]
    textes_contexte = [t for t in [CONTEXTES_FRONT.get(q["listeningContext"], ""), q["contextDescription"]] if t]

    textes = textes_humeur + textes_contexte
    if q["additionalPreferences"]:
        textes.append(q["additionalPreferences"])
    if q["vocalPreference"] == "Instrumental":
        textes.append("musique instrumentale sans paroles")

    genres = []
    for genre_front in q["genres"]:
        genres += GENRES_FRONT.get(genre_front, [genre_front])
    artistes = [a.strip().lower() for a in q["favoriteArtists"].split(",") if a.strip()]

    blocs_contexte = {}
    if textes_contexte:
        blocs_contexte = normaliser_blocs(sm.context_affinity(textes_contexte))
    return {"textes": textes, "genres": genres, "artistes": artistes, "energie": q["energyLevel"],
            "blocs_humeur": normaliser_blocs(sm.mood_affinity(textes_humeur)), "blocs_contexte": blocs_contexte}


def top_k(sm, profil, k=3):
    #un seul morceau par artiste, comme recommender.py
    from backend.recommendation.scoring import calculer_scores
    _, _, score, _ = calculer_scores(sm, profil)
    top = []
    artistes_vus = []
    for i in score.sort_values(ascending=False).index:
        morceau = sm.tracks.loc[i].to_dict()
        if morceau["artist"] not in artistes_vus:
            artistes_vus.append(morceau["artist"])
            top.append(morceau)
        if len(top) == k:
            break
    return top


def tester_un_profil(sm, profil, cas, k=3):
    top = top_k(sm, profil, k)
    pertinents = [morceau_pertinent(m, cas["pertinent"]) for m in top]
    genres_refuses = cas["profil"].get("genres_exclus", [])
    exclus_ok = True
    for morceau in top:
        if morceau["genre"] in genres_refuses:
            exclus_ok = False
    return {"top": top, "pertinents": pertinents, "precision": sum(pertinents) / k, "exclus_ok": exclus_ok}


def evaluer(sm):
    resultats = []
    for cas in CAS:
        profil = construire_profil_utilisateur(sm, cas["questionnaire"])
        resultat = tester_un_profil(sm, profil, cas)
        resultat["cas"] = cas
        resultat["profil"] = profil
        resultat["checks"] = verifier_profil(profil, cas["profil"])
        resultat["avant"] = tester_un_profil(sm, profil_avant_partie6(sm, cas["questionnaire"]), cas)
        resultats.append(resultat)
    return resultats


def moyenne(valeurs):
    return sum(valeurs) / len(valeurs)


def ecrire_rapport(resultats, encodeur):
    nb_criteres = sum(len(r["checks"]) for r in resultats)
    nb_reussis = sum(1 for r in resultats for c in r["checks"] if c[1])
    p3 = moyenne([r["precision"] for r in resultats])
    p3_avant = moyenne([r["avant"]["precision"] for r in resultats])
    nb_exclus_ok = sum(1 for r in resultats if r["exclus_ok"])
    nb_refus_avant = sum(1 for r in resultats if not r["avant"]["exclus_ok"])
    nb_refus_apres = len(resultats) - nb_exclus_ok

    lignes = [
        "# Cas d'usage du profil utilisateur (partie 6)", "",
        f"Généré par `python -m backend.personalization.evaluation --encoder {encodeur}` "
        f"(encodeur sémantique : **{encodeur}**).", "",
        f"- **Profil** : {nb_reussis}/{nb_criteres} critères conformes à l'attendu ({nb_reussis / nb_criteres:.0%}).",
        f"- **Recommandations** : Precision@3 moyenne = **{p3:.2f}** sur {len(resultats)} cas "
        "(objectif du README : ≥ 0,7).",
        f"- **Exclusions respectées** : {nb_exclus_ok}/{len(resultats)} cas.", "",
        "**Apport de la partie 6** — mêmes cas, même moteur, avec le profil provisoire utilisé avant "
        "(affinités sémantiques seules) :", "",
        "| | Avant (profil provisoire) | Avec le profil de la partie 6 |",
        "|---|---|---|",
        f"| Precision@3 moyenne | {p3_avant:.2f} | {p3:.2f} |",
        f"| Cas avec un genre refusé dans le top 3 | {nb_refus_avant} | {nb_refus_apres} |", "",
        "Un morceau est jugé pertinent s'il partage un bloc d'humeur attendu, a une énergie dans la plage "
        "attendue et respecte la demande d'instrumental (`cas_usage.morceau_pertinent`). C'est une "
        "pré-annotation automatique : à confirmer par une relecture humaine (README §19).", "",
        "| Cas | Situation | Piège testé | Profil | P@3 avant | P@3 partie 6 |",
        "|---|---|---|---|---|---|",
    ]
    for r in resultats:
        cas = r["cas"]
        reussis = sum(1 for c in r["checks"] if c[1])
        lignes.append(f"| {cas['id']} | {cas['persona']} | {cas['piege']} | {reussis}/{len(r['checks'])} "
                      f"| {r['avant']['precision']:.2f} | {r['precision']:.2f} |")

    lignes += ["", "## Détail par cas", ""]
    for r in resultats:
        cas, profil, q = r["cas"], r["profil"], r["cas"]["questionnaire"]
        texte = f"- **Texte** : « {q['description']} »"
        if q["listeningContext"]:
            texte += f" · contexte coché : {q['listeningContext']}"
        if q["moods"]:
            texte += f" · humeurs cochées : {', '.join(q['moods'])}"
        if q["additionalPreferences"]:
            texte += f" · préférences : « {q['additionalPreferences']} »"
        lignes += [f"### {cas['id']} — {cas['persona']}", "", texte,
                   f"- **Profil** : {profil['synthese']}",
                   f"- **Archétype** : {profil['archetype']['nom']} · **indices** : {', '.join(profil['indices']) or '—'}"]
        for critere, ok, obtenu, attendu in r["checks"]:
            lignes.append(f"  - {'✅' if ok else '❌'} {critere} : obtenu `{obtenu}`, attendu `{attendu}`")
        lignes.append(f"- **Top 3** (P@3 = {r['precision']:.2f}) :")
        for morceau, pertinent in zip(r["top"], r["pertinents"]):
            lignes.append(f"  - {'✅' if pertinent else '❌'} {morceau['title']} — {morceau['artist']} "
                          f"({morceau['genre']}, énergie {morceau['energy']}, {morceau['mood_blocks']})")
        lignes.append("")
    return "\n".join(lignes)


def main():
    parser = argparse.ArgumentParser(description="Évalue les cas d'usage du profil utilisateur")
    parser.add_argument("--encoder", default="sbert", help="sbert (par défaut) ou tfidf (rapide, hors ligne)")
    args = parser.parse_args()

    from moodify.semantic import SemanticMatcher
    sm = SemanticMatcher(args.encoder)
    resultats = evaluer(sm)
    RAPPORT.write_text(ecrire_rapport(resultats, sm.encoder.name) + "\n", encoding="utf-8")

    for r in resultats:
        reussis = sum(1 for c in r["checks"] if c[1])
        print(f"{r['cas']['id']}  profil {reussis}/{len(r['checks'])}  P@3 avant {r['avant']['precision']:.2f}"
              f" -> partie 6 {r['precision']:.2f}  {r['cas']['persona']}")
    p3_avant = moyenne([r["avant"]["precision"] for r in resultats])
    p3 = moyenne([r["precision"] for r in resultats])
    print(f"\nPrecision@3 moyenne : avant {p3_avant:.2f} -> partie 6 {p3:.2f}  ({RAPPORT})")


if __name__ == "__main__":
    main()
