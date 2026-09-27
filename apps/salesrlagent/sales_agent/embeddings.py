"""Optional Azure/OpenAI-compatible semantic encoder; explicit opt-in only."""
import hashlib
import os
from collections import OrderedDict
from urllib.parse import urlparse
import httpx
import numpy as np
from .features import EMBED_DIM, ENCODER_ID, embedding


class HashEncoder:
    id = ENCODER_ID

    def __call__(self, text):
        return embedding(text)


class APIEncoder:
    def __init__(self, endpoint, model, api_key, client=None):
        parsed = urlparse(endpoint)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Embedding endpoint must be HTTPS without embedded credentials')
        if not api_key:
            raise ValueError('SALES_EMBEDDING_API_KEY is required')
        self.endpoint, self.model, self.api_key = endpoint, model, api_key
        self.client = client
        self.id = f'api:{model}:{EMBED_DIM}:recency-v1:' + hashlib.sha256(endpoint.encode()).hexdigest()[:12]
        self.cache = OrderedDict()

    def __call__(self, text):
        key = hashlib.sha256(text.encode()).hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key].copy()
        headers = {'Authorization': 'Bearer ' + self.api_key, 'api-key': self.api_key}
        kwargs = dict(headers=headers, json={'model': self.model, 'input': text, 'dimensions': EMBED_DIM, 'encoding_format': 'float'})
        if self.client:
            response = self.client.post(self.endpoint, **kwargs)
        else:
            response = httpx.post(self.endpoint, timeout=8, **kwargs)
        response.raise_for_status()
        vector = np.asarray(response.json()['data'][0]['embedding'], dtype=np.float32)
        if vector.shape != (EMBED_DIM,) or not np.isfinite(vector).all():
            raise ValueError('Embedding provider returned invalid dimensions or nonfinite values')
        vector /= max(float(np.linalg.norm(vector)), 1e-8)
        self.cache[key] = vector.copy()
        if len(self.cache) > 512:
            self.cache.popitem(last=False)
        return vector


def configured_encoder():
    endpoint = os.getenv('SALES_EMBEDDING_ENDPOINT')
    if not endpoint:
        return HashEncoder()
    return APIEncoder(endpoint, os.environ['SALES_EMBEDDING_MODEL'], os.environ['SALES_EMBEDDING_API_KEY'])
