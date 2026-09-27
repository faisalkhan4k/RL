# Training run — 2026-09-23

Completed locally on Windows CPU. Docker execution was blocked by missing WSL / Virtual Machine Platform, so this is not a container benchmark.

Command: `python -m sales_agent.hrl.train --steps 100000 --episodes 100 --output artifacts/training-2026-09-23`

Three PPO experiments completed 100,096 steps each: sales strategy, experimental voice timing, and a strategy ablation without information reward. A behavior-cloning baseline was also trained. The updated 65-product catalog was used. No provider API calls or real customer conversations were used for training.

| Held-out synthetic test (100 episodes) | Rules | Strategy PPO | PPO without information reward |
|---|---:|---:|---:|
| Purchase success | 23% | 39% | 41% |
| Abandonment | 77% | 54% | 52% |
| Mean turns | 10.21 | 8.15 | 7.59 |
| Mean repeated questions | 0 | 0.06 | 0 |

Validation success was 67% for rules and 86% for strategy PPO. These are one-seed simulator estimates, not measured real-world conversion improvements. CustomerGym currently models laptop shoppers, not all 15 catalog categories.

The voice policy scored 27.80 versus 33.64 for fixed rules, with no modeled interruption recoveries versus 5.01 for rules. It was not promoted. The working Deepgram/Groq cascade does not use this experimental timing policy.

Checkpoints are saved for experiments; the live demo keeps its existing rules and deterministic customer commands. Enabling a strategy checkpoint requires explicit configuration plus further evaluation. Voice cart and navigation commands are implemented as validated tools, not learned purchase authority.

Files: `evaluation.json`, `strategy.zip`, `voice.zip`, `strategy_no_information.zip`, `supervised.pt`, `*.monitor.csv`, `reward-curves.svg`, and `manifest.json`.
