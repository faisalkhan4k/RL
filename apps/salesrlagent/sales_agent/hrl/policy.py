"""Inference boundaries; policy provenance is always explicit."""
from functools import lru_cache
from pathlib import Path
import numpy as np
from .state import Strategy, VoiceAction, rule_action

@lru_cache(maxsize=4)
def checkpoint(path):
    from stable_baselines3 import PPO
    return PPO.load(path, device='cpu')

def decide(observation, path=None, voice=False):
    names=VoiceAction if voice else Strategy
    if path and Path(path).is_file():
        import torch
        model=checkpoint(path)
        tensor,_=model.policy.obs_to_tensor(np.asarray(observation,dtype=np.float32))
        with torch.no_grad(): probabilities=model.policy.get_distribution(tensor).distribution.probs.cpu().numpy()[0]
        index=int(np.argmax(probabilities)); source='ppo_simulation'
    else:
        index=int(voice_rule(observation) if voice else rule_action(observation))
        probabilities=np.eye(len(names))[index]; source='rule_baseline'
    return {'action':names(index).name,'source':source,'probabilities':{a.name:round(float(probabilities[a.value]),5) for a in names}}

def voice_rule(o):
    if o[0]: return VoiceAction.STOP_SPEAKING if o[1] else VoiceAction.LISTEN
    if o[3] and not o[1]:return VoiceAction.SPEAK
    return VoiceAction.WAIT
