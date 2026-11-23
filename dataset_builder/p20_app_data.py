"""PHASE 20 — DONNÉES DE L'APPLICATION : STOCKAGE + TESTS DU CHATBOT

 20.1 Base SQLite (storage/moodify.db) :
      - tables de RÉFÉRENCE chargées depuis data/processed (tracks, artists, communities, concerts...)
      - tables APPLICATIVES vides, prêtes à recevoir les vraies réponses :
        users, quiz_responses, profiles, chat_messages, recommendations
      - les utilisateurs simulés y sont insérés (source = 'simulé')
 20.2 Jeu de messages de test du chatbot (émotion, souhait, exclusions, contexte attendus)
Sorties : storage/moodify.db, storage/schema.sql, data/processed/chatbot_test_messages.json
"""
from __future__ import annotations

import json
import sqlite3

import pandas as pd

from . import config
from .utils import load_json, log, phase_timer, report, save_json

STORAGE = config.ROOT / "storage"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY, pseudo TEXT, source TEXT DEFAULT 'réel',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS quiz_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT REFERENCES users(user_id),
    answers_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id), profile_json TEXT, analysis_json TEXT,
    archetype TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT REFERENCES users(user_id),
    role TEXT CHECK(role IN ('user','bot')), content TEXT, intent_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS recommendations (
    reco_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT REFERENCES users(user_id),
    origin TEXT CHECK(origin IN ('quiz','chat')), rank INTEGER, track_id TEXT, score REAL,
    semantic_similarity REAL, criteria_json TEXT, explanation TEXT, feedback INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CHAT_TESTS = [
    ("Aujourd'hui je ne suis pas dans le mood, je suis énervée et je veux une musique calme", "colère", "Calme & détente", [], None),
    ("je suis à bout, tout m'agace", "colère", None, [], None),
    ("J'ai le cafard, mets-moi quelque chose de joyeux", "tristesse", "Joie & bonne humeur", [], None),
    ("je suis triste et j'ai envie de pleurer un bon coup", "tristesse", "Mélancolie & introspection", [], None),
    ("Je suis stressé avant mon partiel, j'ai besoin de me concentrer", "stress", "Concentration", [], "Étude & travail"),
    ("Je dois réviser toute la nuit, du lofi sans paroles stp", None, "Concentration", [], "Étude & travail"),
    ("Je suis crevé mais je dois aller à la salle, donne-moi de l'énergie", "fatigue", "Énergie & motivation", [], "Sport"),
    ("Soirée chez moi ce soir, je veux faire danser tout le monde, pas de metal", None, "Fête & danse", ["Metal"], "Soirée & fête"),
    ("j'ai un date ce soir, un truc sensuel", "amour", "Romance & sensualité", [], "Moment à deux"),
    ("Je m'ennuie, surprends-moi", "ennui", None, [], None),
    ("Je pense à mes années lycée, je suis nostalgique", "nostalgie", None, [], None),
    ("Il pleut, je suis seule chez moi, un truc mélancolique", None, "Mélancolie & introspection", [], "Solitude & pluie"),
    ("Je veux m'endormir, quelque chose de très doux", None, "Calme & détente", [], "Sommeil & méditation"),
    ("Je suis de super bonne humeur !!", "joie", None, [], None),
    ("Un son pour conduire la nuit, planant", None, "Rêverie & évasion", [], "Trajet"),
    ("je veux du rap qui motive mais pas de rap français", None, "Énergie & motivation", [], None),
    ("I'm so angry right now, I need to calm down", "colère", "Calme & détente", [], None),
    ("I need some chill music to study", None, "Calme & détente", [], "Étude & travail"),
    ("Musique pour méditer, sans électro", None, "Calme & détente", ["Électro / House"], "Sommeil & méditation"),
    ("j suis trop enervé laisse moi tranquil", "colère", None, [], None),
    ("Je ne suis pas triste, juste fatigué", "fatigue", None, [], None),
    ("Rien de calme surtout, je veux me défouler", None, "Colère & défoulement", [], None),
    ("Je cuisine pour des amis, un fond sympa et ensoleillé", None, "Joie & bonne humeur", [], "Matin & quotidien"),
    ("Je viens de me faire larguer", "tristesse", None, [], None),
    ("j'ai besoin de courage pour mon entretien d'embauche", "stress", "Énergie & motivation", [], None),
    ("ambiance café jazz pour bosser", None, "Concentration", [], "Étude & travail"),
    ("du reggae pour l'été sans reggaeton", None, "Joie & bonne humeur", [], None),
    ("Je suis amoureuse !", "amour", None, [], None),
    ("bof", None, None, [], None),
    ("Mets-moi un truc", None, None, [], None),
]


def run() -> None:
    with phase_timer("P20 Données de l'application"):
        STORAGE.mkdir(exist_ok=True)
        (STORAGE / "schema.sql").write_text(SCHEMA.strip() + "\n", encoding="utf-8")
        db = STORAGE / "moodify.db"
        if db.exists():
            db.unlink()
        con = sqlite3.connect(db)
        con.executescript(SCHEMA)

        loaded = {}
        for name in ("tracks", "artists", "communities", "concerts", "cities", "artist_similarity",
                     "track_tags", "user_community", "user_neighbors"):
            p = config.PROCESSED / f"{name}.csv"
            if p.exists():
                df = pd.read_csv(p)
                df.to_sql(f"ref_{name}", con, index=False, if_exists="replace")
                loaded[f"ref_{name}"] = len(df)

        users = load_json(config.PROCESSED / "users_simules.json")["users"]
        con.executemany("INSERT INTO users(user_id, pseudo, source) VALUES (?,?,?)",
                        [(u["user_id"], u["pseudo"], u["source"]) for u in users])
        con.executemany("INSERT INTO quiz_responses(user_id, answers_json) VALUES (?,?)",
                        [(u["user_id"], json.dumps(u["answers"], ensure_ascii=False)) for u in users])
        con.commit(); con.close()

        tests = [{"id": f"M{i:02d}", "message": m, "expected_emotion": e, "expected_target_block": b,
                  "expected_excluded_genres": x, "expected_context_block": c}
                 for i, (m, e, b, x, c) in enumerate(CHAT_TESTS, 1)]
        save_json({"_doc": "Messages de test du chatbot (None = pas d'attente particulière). "
                           "M29-M30 doivent déclencher une question de clarification.",
                   "tests": tests}, config.PROCESSED / "chatbot_test_messages.json")

        log.info("  storage/moodify.db : %s + %d utilisateurs simulés", loaded, len(users))
        report("P20_app_data", sqlite_tables=loaded, simulated_users=len(users), chatbot_tests=len(tests))
