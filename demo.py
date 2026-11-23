import sys; sys.path.insert(0, "src")
from moodify.embeddings import get_encoder
from moodify.reference import ReferenceIndex
from moodify.profile import UserProfile
from moodify.scoring import score_tracks, top_k
from moodify.chatbot import parse_message, intent_to_query, compose_reply
from moodify.explain import explain
from moodify import config

ref = ReferenceIndex(get_encoder("sbert"))          # bascule sur TF-IDF si SBERT absent
profile = UserProfile(regulation_strategy="réguler")
msg = input("Ton humeur : ") if len(sys.argv) < 2 else " ".join(sys.argv[1:])
intent = parse_message(ref, msg, profile)
q = intent_to_query(intent, profile)
top = top_k(score_tracks(ref, q, config.WEIGHTS_CHAT), k=3)
recos = [explain(ref, row, q) for _, row in top.iterrows()]
print(compose_reply(intent, recos))
for r in recos:
    print("  →", r["explanation"])
