"""Continuous probability actor/critic and ensemble support diagnostics."""
import numpy as np
import torch
from torch import nn
from torch.distributions import Beta
from .features import EMBED_DIM, FEATURE_DIM, ENCODER_ID, encode
from .embeddings import configured_encoder


class ConversionActorCritic(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(EMBED_DIM + FEATURE_DIM, 64), nn.Tanh(), nn.Linear(64, 32), nn.Tanh())
        self.policy = nn.Linear(32, 2)
        self.value = nn.Linear(32, 1)

    def forward(self, x):
        hidden = self.encoder(x)
        params = torch.nn.functional.softplus(self.policy(hidden)) + 1.
        return Beta(params[..., 0], params[..., 1]), self.value(hidden).squeeze(-1)


class Predictor:
    def __init__(self, path):
        self.embed = configured_encoder()
        data = torch.load(path, map_location='cpu', weights_only=True)
        if data['encoder_id'] != self.embed.id:
            raise ValueError('Checkpoint encoder mismatch; retrain with this encoder.')
        self.models = []
        for weights in data['models']:
            model = ConversionActorCritic()
            model.load_state_dict(weights)
            model.eval()
            self.models.append(model)
        if not self.models:
            raise ValueError('Checkpoint has no ensemble members')
        self.prototypes = data['prototypes']
        self.provenance = data['provenance']

    def predict(self, messages):
        x = torch.from_numpy(encode(messages, self.embed)).unsqueeze(0)
        with torch.inference_mode():
            means = np.array([m(x)[0].mean.item() for m in self.models])
            similarity = torch.nn.functional.cosine_similarity(x[:, :EMBED_DIM], self.prototypes, dim=1).max().item()
        return {'probability': round(float(means.mean()), 4), 'ensemble_std': round(float(means.std()), 4),
                'support_similarity': round(max(0., similarity), 4), 'calibrated': False,
                'status': 'experimental', 'provenance': self.provenance}
