"""Reproducible warm-start + clipped PPO on labeled conversation trajectories.

python -m sales_agent.train --output artifacts/conversion.pt --smoke
python -m sales_agent.train --data conversations.jsonl --output artifacts/conversion.pt
"""
import argparse
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch
from .features import EMBED_DIM, ENCODER_ID, encode
from .model import ConversionActorCritic
from .embeddings import configured_encoder


def synthetic(seed=42, count=240):
    rng = random.Random(seed)
    rows = []
    for i in range(count):
        positive = i % 2 == 0
        product = rng.choice(['headphones', 'earbuds', 'speakers'])
        budget = rng.choice([80, 100, 150, 200, 300])
        opening = rng.choice(['I am looking for', 'Can you help me find', 'I want to compare'])
        end = rng.choice(['Great, I would like to buy it', 'Perfect, how do I checkout?', 'Yes, I want to order']) if positive else rng.choice(['Too expensive, I will leave', 'No thanks, not interested', 'I am unsure and will wait'])
        rows.append({'id': f'synthetic-{seed}-{i}', 'outcome': int(positive), 'messages': [
            {'role': 'user', 'content': f'{opening} {product} under ${budget}'},
            {'role': 'assistant', 'content': 'Which features matter most to you?'},
            {'role': 'user', 'content': rng.choice(['I need wireless', 'Is it good for travel?', 'What is the difference?'])},
            {'role': 'assistant', 'content': 'Let us compare the specifications and price.'},
            {'role': 'user', 'content': end}]})
    return rows


def validate(rows):
    seen = set()
    for row in rows:
        if row['id'] in seen or row['outcome'] not in (0, 1) or not row['messages']:
            raise ValueError('Unique IDs, binary outcomes, and nonempty conversations required')
        seen.add(row['id'])
        for m in row['messages']:
            if m['role'] not in ('user', 'assistant') or not isinstance(m['content'], str) or not m['content'].strip():
                raise ValueError('Invalid message')
    if len(rows) < 10 or len({r['outcome'] for r in rows}) != 2:
        raise ValueError('Need at least 10 conversations and both outcomes')


def samples(rows, embed=None):
    xs, ys, terminal = [], [], []
    for row in rows:
        for turn in range(1, len(row['messages']) + 1):
            # Outcome is a label, NEVER part of the encoded history.
            xs.append(encode(row['messages'][:turn], embed) if embed else encode(row['messages'][:turn]))
            ys.append(row['outcome'])
            terminal.append(turn == len(row['messages']))
    return torch.from_numpy(np.stack(xs)), torch.tensor(ys, dtype=torch.float32), terminal


def fit(x, y, terminal, seed, warm_steps, ppo_steps):
    torch.manual_seed(seed)
    model = ConversionActorCritic()
    optim = torch.optim.Adam(model.parameters(), lr=3e-4)
    for _ in range(warm_steps):
        dist, _ = model(x)
        loss = ((dist.mean - y) ** 2).mean()
        optim.zero_grad(); loss.backward(); optim.step()
    for _ in range(ppo_steps):
        with torch.no_grad():
            old, values = model(x)
            actions = old.sample().clamp(1e-5, 1 - 1e-5)
            old_log = old.log_prob(actions)
            reward = 1 - (actions - y).square()
            advantages = torch.zeros_like(reward)
            gae = torch.tensor(0.)
            for t in reversed(range(len(reward))):
                next_value = values[t + 1] if not terminal[t] else 0.
                delta = reward[t] + .95 * next_value - values[t]
                gae = delta + (.95 * .95 * gae if not terminal[t] else 0.)
                advantages[t] = gae
            returns = advantages + values
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        for _ in range(4):
            dist, value = model(x)
            ratio = (dist.log_prob(actions) - old_log).exp()
            policy_loss = -torch.minimum(ratio * advantages, ratio.clamp(.8, 1.2) * advantages).mean()
            loss = policy_loss + .5 * (value - returns).square().mean() - .001 * dist.entropy().mean() + .1 * (dist.mean - y).square().mean()
            optim.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), .5)
            optim.step()
    return model.eval()


def metrics(p, y):
    p, y = np.asarray(p), np.asarray(y)
    pos, neg = p[y == 1], p[y == 0]
    auc = float(((pos[:, None] > neg).mean() + .5 * (pos[:, None] == neg).mean())) if len(pos) and len(neg) else None
    ece = 0.
    for i in range(10):
        mask = (p >= i / 10) & (p <= (i + 1) / 10 if i == 9 else p < (i + 1) / 10)
        if mask.any():
            ece += float(mask.mean() * abs(p[mask].mean() - y[mask].mean()))
    return {'brier': float(((p - y) ** 2).mean()), 'accuracy': float(((p >= .5) == y).mean()), 'auc': auc, 'ece': ece}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path)
    parser.add_argument('--output', type=Path, default=Path('artifacts/conversion.pt'))
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    torch.set_num_threads(2)
    rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()] if args.data else synthetic(args.seed)
    validate(rows)
    # Keep duplicate full transcripts together to prevent exact train/test leakage.
    groups = {}
    for row in rows:
        key = hashlib.sha256(json.dumps(row['messages'], sort_keys=True).encode()).hexdigest()
        groups.setdefault(key, []).append(row)
    keys = sorted(groups)
    random.Random(args.seed).shuffle(keys)
    boundary = max(1, int(len(keys) * .8))
    train = [r for k in keys[:boundary] for r in groups[k]]
    test = [r for k in keys[boundary:] for r in groups[k]]
    if not test:
        raise ValueError('Need more distinct conversations for a held-out split')
    embed = configured_encoder()
    x, y, terminal = samples(train, embed)
    tx, ty, ends = samples(test, embed)
    models = [fit(x, y, terminal, args.seed + n, 8 if args.smoke else 120, 2 if args.smoke else 40) for n in range(3)]
    with torch.inference_mode():
        predictions = torch.stack([m(tx)[0].mean for m in models]).mean(0).numpy()
    provenance = 'synthetic-smoke' if args.smoke and not args.data else ('synthetic-demo' if not args.data else 'user-dataset-unvalidated')
    report = {'seed': args.seed, 'provenance': provenance, 'train_conversations': len(train), 'test_conversations': len(test),
              'all_turns': metrics(predictions, ty.numpy()), 'final_turn': metrics(predictions[ends], ty.numpy()[ends]),
              'constant_baseline': metrics(np.full(len(ty), float(y.mean())), ty.numpy()),
              'warning': 'Smoke/synthetic results are not evidence of real-world conversion lift. Confidence is not calibrated.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({'encoder_id': embed.id, 'models': [m.state_dict() for m in models],
                'prototypes': x[:256, :EMBED_DIM], 'provenance': provenance}, args.output)
    args.output.with_suffix('.metrics.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
