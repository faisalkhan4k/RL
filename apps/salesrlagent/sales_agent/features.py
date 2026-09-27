"""Versioned deterministic demo encoding; never masquerades as semantic embeddings."""
import hashlib
import re
import numpy as np

EMBED_DIM = 3072
FEATURE_DIM = 8
ENCODER_ID = 'hash3072-recency-v1'


def embedding(text):
    vector = np.zeros(EMBED_DIM, dtype=np.float32)
    for token in re.findall(r'\b\w+\b', text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        vector[int.from_bytes(digest[:4], 'little') % EMBED_DIM] += 1 if digest[4] % 2 else -1
    return vector / max(float(np.linalg.norm(vector)), 1.)


def encode(messages, embed=embedding):
    history = messages[-24:]
    weights = np.array([.85 ** i for i in reversed(range(len(history)))], dtype=np.float32)
    semantic = sum((embed(m['content']) * w for m, w in zip(history, weights)), np.zeros(EMBED_DIM, dtype=np.float32))
    semantic /= max(float(weights.sum()), 1.)
    text = next((m['content'].lower() for m in reversed(history) if m['role'] == 'user'), '')
    features = np.array([min(len(history) / 24, 1), min(len(text) / 500, 1), min(text.count('?') / 3, 1),
                         float(bool(re.search(r'\b(expensive|unsure|concern|budget)\b', text))),
                         float(bool(re.search(r'\b(buy|checkout|order|perfect)\b', text))),
                         float(bool(re.search(r'\b(no|stop|leave|not interested)\b', text))),
                         float(bool(re.search(r'\b(compare|difference|versus)\b', text))),
                         float(bool(re.search(r'\b(thanks|great|like|yes)\b', text)))], dtype=np.float32)
    return np.concatenate([semantic, features])
