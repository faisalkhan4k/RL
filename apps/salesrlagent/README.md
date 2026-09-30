# Hierarchical RL Voice Sales Agent

The storefront now has Home, Deal of the Day, Sales, Categories, Cart and Order
Lookup pages, a persistent voice pill, and 116 real products across 15 categories with manufacturer
links and dated price references. Inventory/orders use a working **local demo MCP
server**. No merchant account is connected and checkout takes no payment.
See [commerce setup and limitations](docs/COMMERCE.md).

This project now implements a research prototype of the supplied [HRL specification](docs/PROJECT_SPEC.md). The older continuous conversion predictor remains in the repository for comparison but is no longer the live decision maker.

## Run locally

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.\apps\salesrlagent[research,test,postgres]'
 # Set DEEPGRAM_API_KEY and GROQ_API_KEY in apps/salesrlagent/.env
Set-Location apps/salesrlagent/frontend
npm ci
npm run build
Set-Location ..
.\scripts\run-sales.ps1
```

Open http://127.0.0.1:8000. The default is the rule baseline. To run the simulation-trained policies after training, use `scripts/run-sales.ps1 -WithPolicies`. The run script loads the app-local `.env`; process environment values take precedence. Keep keys out of Git and the browser. Groq runs `openai/gpt-oss-20b` by default; model access and free-plan limits depend on your account. Deepgram offers introductory credits and metered usage, not unlimited free service.

Select **Start talking** once and allow microphone access. The default browser voice path is now **Deepgram streaming STT -> Groq streamed responses -> Deepgram streamed TTS**. It does not run Vosk, Piper, or the experimental voice PPO. The old offline endpoints are retained only for research tests.

Microphone audio stays enabled during playback with browser echo cancellation. A raw Deepgram SpeechStarted event does not cancel playback. Recognized non-echo speech cancels the current Groq/TTS task, and the browser stops queued audio. Transcript matching filters likely speaker echoes; explicit Stop reply remains immediate. Playback completion is acknowledged by the browser before the idle timer starts. Monotonic generation IDs reject late audio from cancelled replies. Completed STT segments are accumulated until the endpoint or utterance-end event. Groq's first completed sentence goes to TTS before the entire reply finishes. TTS is streamed PCM from the REST endpoint per sentence; this is a cascade, not a speech-to-speech model.

Limits: one active voice connection per app process, 180 seconds per session by default, 30 seconds idle, 20 turns, 512 completion tokens and 800 synthesized characters per reply. No automatic retries or model upgrades. These limit individual sessions, not account-wide spending; use provider billing controls as well. Missing keys or provider errors are shown explicitly. There is no silent fallback to the old local voice loop.

Acoustic interruption quality and actual provider latency require a live test with your keys and microphone/speakers. The automated tests verify cancellation, stale-audio rejection, credential handling and streaming parsing with mocks; they do not establish real-world latency or echo suppression.

## Architecture

React/Vite -> FastAPI -> LangGraph: belief update -> strategy policy -> product tools -> language realization.

Two separate discrete PPO policies use Stable-Baselines3:
- Sales strategy: 22 actions, once per customer turn.
- Voice timing: 8 actions in the research simulator. The default cascade uses Deepgram endpointing and confirmed speech transcripts; voice PPO is not in its latency-critical path.

Belief features are deterministic estimates, not a calibrated Bayesian posterior. Hidden simulator budget, preferences, patience and purchase intent are never exposed to the policy. User declines and explicit comparisons override exploratory policy choices and are labelled in the research dashboard. Cart and checkout changes require user controls; a policy cannot autonomously purchase or schedule follow-ups.

The language adapter accepts a chat-completions-compatible hosted endpoint through `SALES_LLM_URL`, `SALES_LLM_KEY`, and `SALES_LLM_MODEL`. It receives a selected strategy and grounded product facts. Without credentials, deterministic templates provide the wording, explicitly labelled `template`. The hosted adapter cannot execute tools. Its factual compliance still needs provider-specific evaluation.

## Research commands

From `apps/salesrlagent`:

```powershell
..\..\.venv\Scripts\python.exe -m sales_agent.hrl.train --steps 100000 --episodes 100
..\..\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/voice-controller.test.cjs
```

Training writes separate strategy/voice checkpoints, a behavior-cloning checkpoint, actual episode reward CSVs, reward curves, and `artifacts/hrl/evaluation.json`. Training and test seeds differ. Personas have disjoint names and different simulator parameters/dynamics. This is a small scripted simulator, primarily selecting laptops, not an LLM-powered customer population or a proof of generalization to humans. Most high-level explanation actions have simplified effects.

Baselines: random, rules, supervised behavior cloning, PPO, PPO with the information reward disabled; voice compares fixed rules and PPO. `--llm-baseline` enables the hosted action baseline and may incur API charges; it is skipped by default. No hosted evaluation was run without credentials. Single-seed results and standard errors are exploratory. Repeat with multiple seeds before making research claims.

The information-gain term uses reduction in unknown binary slot entropy. Recommendation and purchase actions taken before budget/use-case evidence are penalized, as are repeated or unnecessary questions and policy-driven cart mutation. A September 2026 run with 50,000 steps and 200 held-out episodes found 63% synthetic success for rules and 0% for PPO. The checkpoint therefore was not promoted. This failed experiment is retained because it exposes remaining reward/model-design work instead of making a false RL-performance claim. The live app uses the stronger rule baseline plus deterministic customer-command overrides. Voice PPO also remained below fixed timing rules and was not promoted.

Research dashboard: http://127.0.0.1:8000/research shows the latest session's belief, action distribution, wording provider and overrides. The store keeps this information out of its primary shopping flow.

## Storage and observability

Local: SQLite. Deployment: set `SALES_DATABASE_URL` for PostgreSQL (install the `postgres` extra). Session serialization assumes one app worker; distributed locking is not implemented. Conversations expire after 24 hours. Reset removes the session and feedback. JSON logs omit conversation content; OpenTelemetry spans cover belief, strategy, products, wording and full turns.

`docker compose up --build -d app` defines a lightweight app with persistent SQLite and provider credentials loaded at runtime. The frontend uses a separate Node build stage; a CPU-only training target is available through the training profile. `compose.observability.yaml` retains the optional PostgreSQL, Collector, Jaeger, Prometheus and Grafana stack. Docker runtime validation remains blocked on this machine by missing WSL / Virtual Machine Platform. See DOCKER.md for setup and verification commands.

## Layout

- `frontend/`: React source, Vite build and lockfile.
- `sales_agent/hrl/`: shared belief schema, CustomerGym, VoiceGym, policies, training, baselines, language adapter and plots.
- `sales_agent/static/`: microphone worklet, voice controller, research dashboard and fallback storefront.
- `tests/`: API, Gym contracts, hidden-state tests and audio lifecycle regressions.
- `artifacts/hrl/`: generated checkpoints, reports and reward curves.
- `data/models/`: local speech models.
- `deploy/`: telemetry configuration.
- `docs/PROJECT_SPEC.md`: supplied specification.

This is a working vertical research prototype, not completion of the empirical research questions in the specification. Live Deepgram/Groq testing, PostgreSQL container verification, real-user/real-audio experiments, calibrated belief inference, and larger multi-seed experiments are still required.


## Interactive shopping and Docker

The voice footer leaves the main screen for products. Voice and typed commands share validated cart and product-navigation tools: “add Vista Phone 8 to my cart”, “show my cart”, “remove Vista Phone 8”, “show Vista Phone 8”, and “next page”. Ambiguous products prompt for a name. “Close to $500” ranks affordable results by proximity; named recommendations focus the corresponding page.

See [DOCKER.md](DOCKER.md) for the lightweight app, isolated CPU trainer, Windows prerequisites, and optional observability stack. The completed local training run and limitations are documented in [RUN.md](artifacts/training-2026-09-23/RUN.md).
