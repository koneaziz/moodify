"""Génère notebooks/02_nlp_semantique.ipynb (python notebooks/build_nb02.py)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md(r"""
# Moodify — Partie NLP : prétraitement, embeddings et similarité sémantique

**Responsable : Houyem** · Projet *Analyse sémantique et systèmes intelligents de recommandation contextuelle* (ECE ING5, 2026-27) · Thème 4 – Musique

Ce notebook documente et justifie toute la chaîne NLP de Moodify : comment on passe d'une phrase libre comme
*« je suis énervée et je veux une musique calme pour réviser »* à un **score de similarité sémantique pour chaque morceau** du catalogue.

Le code réutilisable par l'équipe est dans `src/moodify/` : `preprocessing.py`, `embeddings.py` et `semantic.py`.
""")

md(r"""
## 0. Ce que le sujet exige pour cette partie, et où c'est traité

| Exigence du sujet | Où dans ce notebook |
|---|---|
| « L'analyse doit être **contextuelle et sémantique**, et non purement numérique ou exclusivement fondée sur la correspondance de mots-clés » | §5 (SBERT) et §6 (comparaison avec TF-IDF = mots-clés) |
| « Appliquer des techniques de **prétraitement de texte** » | §2 |
| « **Embeddings de mots** (Word2Vec, GloVe, fastText) » | §4 |
| « **Embeddings contextuels** (BERT, SBERT ou équivalent) » | §5 |
| « Mesures de similarité sémantique (**similarité cosinus**, **clustering sémantique**…) » | §7 (cosinus), §9 (clustering / projection) |
| « Distinguer l'analyse numérique de l'analyse sémantique et contextuelle » | §6 (tests paraphrases, négation, fautes) |
| Thème 4 : « **Extraire les représentations sémantiques** des préférences des utilisateurs » | §7.1 |
| Thème 4 : « **Comparer les descriptions des utilisateurs avec celles des morceaux** » | §7.2-7.3 |
| Thème 4 : « Calculer l'**affinité liée à l'humeur et au genre** musical » | §8 |
| Thème 4 : « **Classer** les morceaux pertinents » | §7.3 |
| « Ces choix doivent être **documentés et justifiés** » | §6 (mesures) et §10 (conclusion) |
| Livrable : « code commenté à chaque étape, documentation dans les notebooks » | Tout le notebook + docstrings des modules |
""")

md("## 1. Imports et données")
code(r"""
import sys, time, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

from moodify.preprocessing import clean_text, split_sentences, preprocess_lexical, preprocess_semantic, lemmatize
from moodify.embeddings import get_encoder, cosine_matrix, SBERT_MODELS
from moodify.semantic import SemanticMatcher, build_views

df = pd.read_csv(ROOT / "data" / "moodify_dataset.csv", dtype={"track_id": str}).fillna("")
print(df.shape)
df[["title", "artist", "genre", "mood", "context", "description"]].head()
""")

md(r"""
Le catalogue (`moodify_dataset.csv`, 684 morceaux) fusionne les données réelles Spotify + MuSe + Last.fm et notre jeu « gold » rédigé à la main.

**Ce qui sera comparé aux phrases de l'utilisateur, ce sont des textes**, et non des valeurs audio :
- la `description` en français ;
- les humeurs (`mood`) ;
- les contextes d'écoute (`context`) ;
- les `keywords`.

C'est exactement ce que demande le sujet : *« utiliser des descriptions textuelles pertinentes plutôt que de vous appuyer exclusivement sur des caractéristiques audio numériques »*.
""")
code(r"""
views = build_views(df)
for v in views: print(f"[{v}]", views[v][0][:300], "\n")
print("Longueur moyenne des descriptions :", round(df.description.str.split().map(len).mean(), 1), "mots")
""")

md(r"""
## 2. Prétraitement

On applique **deux pipelines différents**, selon le type de modèle :

| Étape | Pipeline *lexical* (TF-IDF, Word2Vec, fastText) | Pipeline *contextuel* (SBERT) |
|---|---|---|
| Normalisation Unicode, apostrophes, espaces, ponctuation répétée | ✅ | ✅ |
| Découpage en **phrases** (une phrase = une intention) | ✅ | ✅ |
| Minuscules | ✅ | ❌ (le modèle a son propre tokenizer) |
| Tokenisation + élisions (*l'ambiance → ambiance*, mais *aujourd'hui* intact) | ✅ | ❌ |
| Suppression des stopwords | ✅ **sauf les négations** (*pas, sans, jamais…*) | ❌ |
| Lemmatisation (spaCy `fr_core_news_sm`, optionnelle) | ✅ | ❌ |

**Pourquoi un prétraitement minimal pour SBERT ?** Un transformeur encode la phrase *dans son contexte* : les mots-outils, l'ordre des mots et la négation portent du sens.
*« Je ne veux **pas** de musique triste »* perd tout son sens si on enlève « ne » et « pas ». Lemmatiser ou retirer des mots dégraderait donc l'embedding.
""")
code(r"""
exemples = [
    "Aujourd'hui je ne suis pas dans le mood !!! Je suis énervée et je veux une musique calme, sans rap.",
    "J'écoute du lofi pour réviser, ça m'aide à me concentrer.",
    "jsuis trop enervé laisse moi tranquil",
]
for t in exemples:
    print("BRUT        :", t)
    print("Sémantique  :", preprocess_semantic(t))
    print("Lexical     :", preprocess_lexical(t))
    print("Lexical+lem :", preprocess_lexical(t, lemma=True), "(identique si spaCy n'est pas installé)")
    print("Sans garder les négations :", preprocess_lexical(t, keep_negations=False), "\n")
""")
md(r"""
Ce qu'on observe :
- **Découpage en phrases** : la première entrée contient deux intentions, un état (« pas dans le mood ») et un souhait (« musique calme »). Les encoder séparément évite de les mélanger.
- **Négations** : si on ne les protège pas, la liste de stopwords supprime « pas » et « sans ». C'est une limite structurelle des approches par mots-clés (voir §6.3).
- **Langage familier** (*jsuis*, *enervé*, *tranquil*) : le pipeline lexical ne le corrige pas. On verra que fastText (n-grammes de caractères) et SBERT (sous-mots) y sont plus robustes.
""")

md("## 3. Tokenisation")
md(r"""
- **Modèles lexicaux** : tokenisation **en mots**. Un mot absent du vocabulaire est perdu (Word2Vec) ou approché par ses n-grammes de caractères (fastText).
- **SBERT** : tokenisation **en sous-mots**, ce qui permet de représenter n'importe quel mot, même mal orthographié, par des morceaux connus.
""")
code(r"""
AVAILABLE = {}          # encodeurs effectivement disponibles sur cette machine
def try_encoder(name):
    try:
        enc = get_encoder(name)
        if enc.name == "tfidf" and name != "tfidf":   # SBERT indisponible -> repli silencieux
            raise RuntimeError("sentence-transformers indisponible")
        return enc
    except Exception as e:
        print(f"⚠ {name} indisponible : {e}")
        return None

sbert = try_encoder("sbert-minilm")
for t in ["énervée", "jsuis enervee", "musique apaisante pour réviser"]:
    print(f"{t!r:35} mots : {preprocess_lexical(t)}")
    if sbert: print(f"{'':35} SBERT : {sbert.tokenize(t)}")
""")

md(r"""
## 4. Embeddings de mots : Word2Vec et fastText

Un embedding de mots associe un vecteur dense à chaque mot. On en déduit l'embedding d'une phrase comme la **moyenne des vecteurs de ses mots**.

- **Word2Vec** (Mikolov et al., 2013) : un vecteur par mot du vocabulaire. Il ne connaît pas les mots absents du vocabulaire.
- **fastText** (Bojanowski et al., 2017) : un mot est la somme de ses **n-grammes de caractères**. Un mot inconnu ou mal orthographié reçoit donc quand même un vecteur.
- **Entraînement** : les deux modèles sont entraînés sur notre corpus, c'est-à-dire les vues textuelles des 684 morceaux et les phrases prototypes des blocs. Un modèle pré-entraîné serait meilleur (par exemple fastText français `cc.fr.300.bin`, environ 7 Go, chargeable avec `get_encoder("fasttext", vectors_path=...)`), mais trop lourd pour le projet.

**Limite de fond** : la moyenne des mots ignore l'ordre et le contexte. Les phrases *« pas calme du tout »* et *« très calme »* obtiennent des vecteurs proches.
""")
code(r"""
corpus = views["full"] + [p for g in ("mood_blocks", "context_blocks")
                          for ps in json.load(open(ROOT/"data/blocks.json", encoding="utf-8"))[g].values() for p in ps]
w2v = get_encoder("word2vec").fit(corpus)
ft = get_encoder("fasttext").fit(corpus)
for mot in ["calme", "énergique", "triste"]:
    print(f"Voisins de « {mot} » — Word2Vec :", [w for w, _ in w2v.kv.most_similar(mot, topn=5)])
    print(f"{'':20}— fastText :", [w for w, _ in ft.kv.most_similar(mot, topn=5)])
print("Mot hors vocabulaire « enervee » dans Word2Vec ?", "enervee" in w2v.kv.key_to_index,
      "| fastText le représente quand même :", ft.kv["enervee"].shape)
""")

md(r"""
## 5. Embeddings contextuels : SBERT

**Sentence-BERT** (Reimers & Gurevych, 2019) est un transformeur BERT affiné pour que **deux phrases de même sens aient des vecteurs proches au sens du cosinus**. C'est exactement l'opération dont nous avons besoin.

Candidats comparés (tous **multilingues**, car nos utilisateurs écrivent en français et parfois en anglais) :

| Modèle | Taille | Dimension | Remarque |
|---|---|---|---|
| `paraphrase-multilingual-MiniLM-L12-v2` | 118 M param. | 384 | rapide sur CPU, entraîné sur des paraphrases |
| `paraphrase-multilingual-mpnet-base-v2` | 278 M param. | 768 | plus précis, 2 à 3 fois plus lent |
| `intfloat/multilingual-e5-small` | 118 M param. | 384 | modèle récent orienté recherche d'information (préfixe `query:`) |

Au premier lancement, chaque modèle est téléchargé depuis Hugging Face (470 Mo à 1,1 Go), puis mis en cache.
""")
code(r"""
CANDIDATES = ["tfidf", "word2vec", "fasttext", "sbert-minilm", "sbert-mpnet", "e5-small"]
matchers, timing = {}, {}
for name in CANDIDATES:
    t0 = time.time()
    if name in ("tfidf", "word2vec", "fasttext"):
        matchers[name] = SemanticMatcher(name)              # baseline entraînée sur le corpus
    else:
        e = try_encoder(name)
        if e is None: continue
        matchers[name] = SemanticMatcher(e)
    timing[name] = round(time.time() - t0, 1)
    print(f"{name:14} prêt en {timing[name]:5.1f} s | dimension {matchers[name].E['full'].shape[1]}")
""")

md(r"""
## 6. Choisir le modèle : comparaison chiffrée

On mesure ce qui compte pour Moodify :
1. **Paraphrases** : deux phrases de même sens **sans mot commun** doivent être plus proches qu'une phrase sans rapport. C'est le cœur de l'analyse sémantique.
2. **Recherche** : pour une requête en langage naturel, les premiers morceaux renvoyés ont-ils la bonne humeur ou le bon contexte ? Mesures : Precision@5, Precision@10, MRR.
3. **Robustesse** : fautes de frappe, langage familier, anglais, négation.
4. **Coût** : temps d'encodage et taille du modèle.
""")
md("### 6.1 Paraphrases sans mot commun")
code(r"""
TRIPLETS = [  # (phrase, paraphrase sans mot commun, phrase sans rapport)
    ("je suis énervée", "j'ai les nerfs, tout m'agace", "je suis de très bonne humeur"),
    ("je suis à bout, j'ai besoin de souffler", "il me faut quelque chose d'apaisant", "mets-moi un son pour faire la fête"),
    ("musique pour réviser", "fond sonore pour bosser mes partiels", "musique pour danser en boîte"),
    ("j'ai le cœur brisé", "ma copine m'a quitté hier", "je viens d'avoir mon diplôme"),
    ("un truc qui donne la pêche", "j'ai besoin d'énergie pour courir", "je veux m'endormir doucement"),
    ("ambiance romantique", "dîner aux chandelles avec mon chéri", "séance de musculation intense"),
    ("I want chill music to study", "musique calme pour travailler", "heavy metal pour se défouler"),
    ("musique triste et mélancolique", "des chansons qui font pleurer", "des chansons joyeuses et ensoleillées"),
]
rows = []
for name, sm in matchers.items():
    enc = sm.encoder
    ok, margins = 0, []
    for a, p, u in TRIPLETS:
        A, P, U = enc.encode([a]), enc.encode([p]), enc.encode([u])
        sp, su = (A @ P.T).item(), (A @ U.T).item()
        ok += sp > su; margins.append(sp - su)
    rows.append({"modèle": name, "paraphrase > sans rapport": f"{ok}/{len(TRIPLETS)}",
                 "marge moyenne": round(float(np.mean(margins)), 3)})
para = pd.DataFrame(rows).set_index("modèle"); para
""")
md(r"""
**Comment lire le tableau** : la *marge* est la différence entre le cosinus de la paraphrase et celui de la phrase sans rapport. Une marge positive et élevée signifie que le modèle **comprend le sens**, et pas seulement les mots.

TF-IDF ne peut pas réussir les cas sans mot commun : c'est la démonstration concrète que *la correspondance de mots-clés ne suffit pas*.
""")

md(r"""
### 6.2 Recherche dans le catalogue

Pour chaque requête, on connaît l'**humeur** attendue (bloc d'humeur) et parfois le **contexte**. Un morceau renvoyé est considéré pertinent s'il appartient à ces blocs.

Deux évaluations :
- **Tout le catalogue** : les étiquettes viennent des colonnes construites lors de la préparation des données. C'est une étiquette « silver », dont le biais est expliqué plus bas.
- **Jeu gold uniquement** (84 morceaux) : les humeurs et contextes ont été écrits à la main. C'est l'évaluation la plus fiable.
""")
code(r"""
QUERIES = [
    ("Une musique calme et instrumentale pour réviser tard le soir", "Calme & détente", None),
    ("J'ai besoin de me concentrer, quelque chose de doux sans paroles", "Calme & détente", None),
    ("Je suis énervée, je veux me calmer", "Calme & détente", None),
    ("Je suis énervé et j'ai besoin de me défouler", "Colère & défoulement", None),
    ("Des sons rageurs avec des guitares saturées", "Colère & défoulement", None),
    ("Musique motivante pour ma séance de sport", "Énergie & motivation", None),
    ("Un truc qui donne la pêche pour courir", "Énergie & motivation", None),
    ("Des morceaux pour danser en soirée avec des amis", "Fête & danse", None),
    ("Je suis triste, j'ai le cœur brisé", "Mélancolie & introspection", None),
    ("Des chansons mélancoliques pour un jour de pluie", "Mélancolie & introspection", None),
    ("Une ambiance romantique pour un dîner à deux", "Romance & sensualité", None),
    ("Quelque chose de joyeux pour bien commencer la journée", "Joie & bonne humeur", None),
    ("Des sons ensoleillés et optimistes", "Joie & bonne humeur", None),
    ("Une musique planante pour m'évader", "Rêverie & évasion", None),
    ("Des nappes douces pour m'endormir", "Calme & détente", "Sommeil & méditation"),
    ("Musique pour méditer et faire baisser le stress", "Calme & détente", "Sommeil & méditation"),
    ("Un fond sonore pour travailler sans être distrait", None, "Étude & travail"),
    ("I want chill music to study, nothing too loud", "Calme & détente", None),
    ("jsuis trop enervé faut que je me pose", "Calme & détente", None),
    ("Je viens de me faire larguer, je veux pleurer un bon coup", "Mélancolie & introspection", None),
]

def relevant(sub, mood, ctx):
    m = np.ones(len(sub), bool)
    if mood: m &= sub["mood_blocks"].str.contains(mood, regex=False).values
    if ctx:  m &= sub["context_blocks"].str.contains(ctx, regex=False).values
    return m

def evaluate(sm, subset_mask=None):
    p5, p10, rr = [], [], []
    sub = sm.tracks if subset_mask is None else sm.tracks[subset_mask]
    idx = np.arange(len(sm.tracks)) if subset_mask is None else np.where(subset_mask)[0]
    for q, mood, ctx in QUERIES:
        s = sm.semantic_score(q)[idx]
        order = np.argsort(-s)
        rel = relevant(sub, mood, ctx)[order]
        p5.append(rel[:5].mean()); p10.append(rel[:10].mean())
        rr.append(1 / (np.argmax(rel) + 1) if rel.any() else 0)
    return round(np.mean(p5), 3), round(np.mean(p10), 3), round(np.mean(rr), 3)

gold_mask = df["source"].str.contains("gold").values
res = []
for name, sm in matchers.items():
    a = evaluate(sm); g = evaluate(sm, gold_mask)
    res.append({"modèle": name, "P@5 catalogue": a[0], "P@10 catalogue": a[1], "MRR catalogue": a[2],
                "P@5 gold": g[0], "P@10 gold": g[1], "MRR gold": g[2], "temps chargement (s)": timing[name]})
results = pd.DataFrame(res).set_index("modèle"); results
""")
code(r"""
ax = results[["P@5 catalogue", "P@5 gold", "MRR gold"]].plot.bar(figsize=(9, 4), rot=0)
ax.set_title("Qualité de la recherche sémantique par modèle"); ax.set_ylim(0, 1); plt.tight_layout(); plt.show()
""")
md(r"""
⚠ **Biais de l'évaluation « catalogue »** : pour les 600 morceaux issus de Spotify / MuSe / Last.fm, les colonnes humeur et contexte et les descriptions viennent des **mêmes** tags. Le score est donc un peu optimiste, surtout pour TF-IDF, qui retrouve les mêmes mots.

L'évaluation **gold**, faite sur les descriptions écrites à la main, est plus juste : c'est elle qui sert de critère principal.
""")

md("### 6.3 Robustesse : fautes, langage familier, anglais, négation")
code(r"""
PAIRS = [  # (A, B, attendu) : True = même sens
    ("je suis énervée", "jsuis enervee", True),
    ("je veux me détendre", "jveux me poser tranquille", True),
    ("musique calme pour étudier", "calm music to study", True),
    ("je veux une musique calme", "je ne veux surtout pas de musique calme", False),
    ("je suis triste", "je ne suis pas triste", False),
]
rows = []
for name, sm in matchers.items():
    r = {"modèle": name}
    for a, b, same in PAIRS:
        r[f"{a[:18]}… ↔ {b[:22]}…"] = round((sm.encoder.encode([a]) @ sm.encoder.encode([b]).T).item(), 2)
    rows.append(r)
pd.DataFrame(rows).set_index("modèle").T
""")
md(r"""
**À retenir pour la soutenance :**
- **Fautes, familier, anglais** : SBERT multilingue garde un cosinus élevé. Word2Vec s'effondre sur les mots inconnus, fastText résiste mieux grâce aux n-grammes.
- **Négation** : **tous** les modèles, y compris SBERT, donnent un cosinus élevé à « je veux du calme » et « je ne veux surtout pas de calme ». Les embeddings mesurent surtout le **sujet** de la phrase, pas sa polarité.

  👉 C'est pourquoi le chatbot de Moodify traite la négation **par règles** en amont (« pas de rap » → exclusion du genre). C'est une difficulté rencontrée et sa solution, à présenter.
""")

md(r"""
## 7. Similarité sémantique entre l'utilisateur et chaque morceau

Le modèle retenu est utilisé via `SemanticMatcher`, qui prend le meilleur modèle disponible sur la machine. On reprend l'exemple de texte libre donné dans le sujet pour le Thème 4.
""")
code(r"""
BEST = next((m for m in ["sbert-minilm", "sbert-mpnet", "e5-small", "fasttext"] if m in matchers), "tfidf")
sm = matchers[BEST]; print("Modèle utilisé :", BEST)

user_answers = {   # réponses ouvertes du questionnaire
    "Q01": "Je recherche une musique instrumentale relaxante qui m'aide à me concentrer pendant mes études, "
           "avec une atmosphère calme et apaisante.",                       # exemple du sujet (Thème 4)
    "Q12": "Le dimanche j'aime les ambiances douces, un peu jazzy.",
    "Q13": "Quand je suis énervée j'ai besoin de souffler.",
}
""")
md("### 7.1 Représentation sémantique des préférences")
code(r"""
sents, U = sm.encode_user(user_answers)
print(len(sents), "phrases →", U.shape, "(une ligne = un vecteur normalisé)")
for s in sents: print(" •", s)
""")
md(r"""
### 7.2 Similarité cosinus avec **chaque** morceau

$\cos(u, t) = \dfrac{u \cdot t}{\lVert u\rVert\,\lVert t\rVert}$. Les vecteurs sont normalisés, donc un simple produit matriciel donne le score des 684 morceaux en une seule opération.

Comme l'utilisateur écrit **plusieurs phrases**, on agrège :

$$S(t) = \tfrac12\,\text{moyenne}_u \cos(u,t) + \tfrac12\,\max_u \cos(u,t)$$

- la **moyenne** mesure l'accord avec *tout* ce que l'utilisateur a dit ;
- le **max** évite qu'un morceau parfait pour *une* phrase soit noyé par les autres phrases.

On calcule ce score sur **trois vues** de chaque morceau (globale, humeur, contexte), puis on les combine avec les poids 0,5 / 0,3 / 0,2. La vue globale porte le sens général ; l'humeur est la promesse du produit ; le contexte sert à affiner.
""")
code(r"""
sents, S = sm.similarity_matrix(user_answers, view="full")
print("Matrice phrases × morceaux :", S.shape)
top = sm.rank(user_answers, k=10)
top[["title", "artist", "genre", "cos_full", "cos_mood", "cos_context", "semantic_score", "best_user_sentence"]]
""")
code(r"""
idx = [df.index[df.track_id == t][0] for t in top.track_id]
fig, ax = plt.subplots(figsize=(11, 3.2))
im = ax.imshow(S[:, idx], cmap="viridis", aspect="auto")
ax.set_xticks(range(len(idx)), [f"{df.title[i][:18]}" for i in idx], rotation=45, ha="right")
ax.set_yticks(range(len(sents)), [s[:45] + "…" for s in sents])
for i in range(S.shape[0]):
    for j, k in enumerate(idx): ax.text(j, i, f"{S[i, k]:.2f}", ha="center", va="center", color="w", fontsize=8)
fig.colorbar(im); ax.set_title(f"Cosinus phrases utilisateur × top 10 ({BEST})"); plt.tight_layout(); plt.show()
""")
md(r"""
### 7.3 Distribution des scores et calibration

Les cosinus bruts n'ont pas la même échelle selon les modèles. Avec SBERT, deux textes sans rapport ont typiquement un cosinus entre 0,1 et 0,3 ; un très bon match se situe entre 0,6 et 0,8. La distribution ci-dessous sert à fixer les bornes de calibration utilisées pour l'affichage en pourcentage (`COS_LOW` / `COS_HIGH` dans `config.py`) : on prend environ le 5e et le 99,5e centile.
""")
code(r"""
s_all = sm.semantic_score(user_answers)
lo, hi = np.percentile(s_all, [5, 99.5])
plt.figure(figsize=(8, 3)); plt.hist(s_all, bins=40, color="#7C5CFF")
for x in (lo, hi): plt.axvline(x, color="red", ls="--")
plt.title(f"Score sémantique sur tout le catalogue ({BEST}) — bornes proposées {lo:.2f} / {hi:.2f}")
plt.tight_layout(); plt.show()
print(f"Calibration proposée : COS_LOW={lo:.2f}, COS_HIGH={hi:.2f} -> score affiché = (s - LOW) / (HIGH - LOW)")
""")

md(r"""
## 8. Affinité liée à l'humeur et au genre

- **Humeur** : on compare les phrases de l'utilisateur aux phrases prototypes de chaque bloc d'humeur (`data/blocks.json`), comme dans l'exemple « blocs de compétences » du sujet.

  $S_{bloc} = \tfrac12\,\text{moyenne}_u \max_p \cos(u,p) + \tfrac12 \max_u \max_p \cos(u,p)$

  Ces affinités alimentent le **score de couverture** $\sum W_i S_i / \sum W_i$ (partie Recommandation).
- **Genre** : cosinus entre l'utilisateur et le **centroïde sémantique** des morceaux de chaque genre. L'utilisateur peut ainsi découvrir un genre qu'il n'a pas coché, mais que ses mots décrivent.
""")
code(r"""
mood_aff, genre_aff = sm.mood_affinity(user_answers), sm.genre_affinity(user_answers)
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
pd.Series(mood_aff).sort_values().plot.barh(ax=axes[0], color="#2E86AB", title="Affinité par bloc d'humeur")
pd.Series(genre_aff).sort_values().plot.barh(ax=axes[1], color="#E4572E", title="Affinité par genre (centroïdes)")
plt.tight_layout(); plt.show()
print("Mots-clés expliquant le n°1 :", sm.matched_keywords(top.track_id[0], user_answers))
""")

md(r"""
## 9. Clustering sémantique du catalogue

Le sujet cite le *clustering sémantique* comme mesure possible. On projette les embeddings des morceaux en 2D (t-SNE) et on les regroupe avec KMeans.

Si des groupes cohérents apparaissent (par humeur et par genre), les embeddings capturent bien l'**ambiance**. Ces groupes servent aussi aux **communautés** de l'application.
""")
code(r"""
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
E = sm.E["full"]
X2 = TSNE(n_components=2, metric="cosine", random_state=0, perplexity=30).fit_transform(E)
km = KMeans(n_clusters=8, n_init=10, random_state=0).fit(E)
print("Silhouette (cosinus) :", round(silhouette_score(E, km.labels_, metric="cosine"), 3))
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for g in df.genre.unique():
    m = (df.genre == g).values; axes[0].scatter(X2[m, 0], X2[m, 1], s=8, label=g)
axes[0].legend(fontsize=7, markerscale=2); axes[0].set_title("Catalogue coloré par genre")
axes[1].scatter(X2[:, 0], X2[:, 1], c=km.labels_, s=8, cmap="tab10"); axes[1].set_title("Clusters KMeans (k=8)")
u2 = X2[np.argsort(-sm.semantic_score(user_answers))[:10]]
axes[1].scatter(u2[:, 0], u2[:, 1], marker="*", s=200, c="red", label="top 10 utilisateur"); axes[1].legend()
plt.tight_layout(); plt.show()
for c in range(8):
    sub = df[km.labels_ == c]
    print(f"Cluster {c} ({len(sub)}) : humeurs {sub['mood'].str.split('|').explode().value_counts().index[:3].tolist()} | genres {sub.genre.value_counts().index[:2].tolist()}")
""")

md(r"""
## 10. Conclusion : choix et justification

**Modèle retenu : SBERT multilingue `paraphrase-multilingual-MiniLM-L12-v2`.** Le choix final se confirme avec les tableaux du §6, une fois exécutés sur votre machine.

Justification :
1. **Analyse réellement sémantique** : il rapproche des phrases de même sens sans mot commun (§6.1), ce que TF-IDF ne peut pas faire et que les embeddings de mots moyennés font mal.
2. **Qualité de recherche** sur le jeu gold (§6.2). ⚠ À vérifier dans *vos* résultats. TF-IDF est avantagé sur l'évaluation « catalogue », car les descriptions et les étiquettes réutilisent les mêmes mots. Si SBERT n'y est pas premier, c'est ce biais qu'il faut expliquer. Le test des paraphrases (§6.1), lui, n'a pas ce biais.
3. **Robuste** aux fautes, au langage familier et à l'anglais, grâce à la tokenisation en sous-mots et à l'entraînement multilingue (§6.3).
4. **Léger** (118 M paramètres, 384 dimensions) : il tourne sur CPU et répond en moins d'une seconde, avec les embeddings du catalogue pré-calculés et mis en cache. `mpnet` peut être légèrement meilleur, mais il est 2 à 3 fois plus lent : à garder si les gains du §6.2 sont nets.

**Rôle des autres modèles** : TF-IDF, Word2Vec et fastText sont conservés comme **bases de comparaison**, comme le demande le sujet (« embeddings de mots »). TF-IDF sert aussi de repli automatique si SBERT ne peut pas être chargé.

**Limite connue et solution** : les embeddings captent mal la négation (§6.3). Celle-ci est donc gérée par des règles dans le chatbot (« pas de rap », « sans électro »).

**Interface pour l'équipe :**
```python
from moodify.semantic import SemanticMatcher
sm = SemanticMatcher()                          # chargé une fois au démarrage de l'API
sm.rank(reponses_libres, k=10)                  # morceaux classés + cosinus par vue
sm.semantic_score(reponses_libres)              # 1 score par morceau (pour la formule de Messade)
sm.mood_affinity(reponses_libres)               # blocs d'humeur (score de couverture, profil de Maureen)
sm.genre_affinity(reponses_libres)              # affinité par genre
sm.matched_keywords(track_id, reponses_libres)  # mots-clés pour l'explication
```
""")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, "notebooks/02_nlp_semantique.ipynb")
print("ok")
