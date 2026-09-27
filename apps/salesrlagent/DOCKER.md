# Docker and CPU training

Run these commands from `apps/salesrlagent`. Keep provider credentials in the local `.env`; the Docker build excludes it and training receives no credentials.

## Windows prerequisite

The 2026-09-23 attempt found Docker Desktop installed but its Linux engine stopped. Docker reported `Virtual Machine Platform not enabled / No virtualization available`; `wsl --status` reported WSL missing. Consequently the images have NOT been built or run on this machine yet. Compose syntax validation succeeded.

Enable CPU virtualization in firmware if Windows Task Manager reports it disabled. In an **Administrator PowerShell**, enable the Windows component without automatically restarting:

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl.exe --install --no-distribution
```

Save your work and restart Windows when prompted, then start Docker Desktop. Check `docker info` before building. See [Microsoft's WSL installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install).

For the current per-user installation, if `docker` is not on PATH, its CLI is at:
`$env:LOCALAPPDATA/Programs/DockerDesktop/resources/bin/docker.exe`.

## Run the app

Stop the Python demo on port 8000 before starting the container.

```powershell
docker compose up --build -d app
docker compose ps
docker compose logs --tail 40 app
```

Open http://127.0.0.1:8000. The app uses a persistent SQLite volume, one worker, a non-root user, dropped capabilities, a health check, a 768 MB memory limit, and one CPU. Provider API models run remotely. Existing local Python demo sessions are not imported into the container volume.

## Train and evaluate

```powershell
docker compose --profile training build trainer
docker compose --profile training run --rm trainer
```

This CPU-only job trains three PPO experiments at 100,096 actual steps each (100,000 requested, rounded to complete rollouts), evaluates held-out simulator personas, and writes checkpoints, Monitor CSVs, evaluation JSON, and reward curves under `artifacts/docker-training/`. It has no network, no API credentials, two CPUs, and a 3 GB memory limit. Groq and Deepgram are not fine-tuned; this trains sales-strategy and experimental voice-timing policies on synthetic data.

A matching local run is saved in `artifacts/training-2026-09-23/`. The live demo keeps the rule policy unless a checkpoint is explicitly configured. Do not promote a checkpoint merely because reward increased; compare purchase, abandonment, repeated-question, and interruption metrics against the rules baseline. Explicit shopper commands always execute outside the learned policy, and no policy can authorize purchases.

## Optional observability stack

The previous full stack is retained separately:

```powershell
docker compose -f compose.observability.yaml up --build -d
```

Use either this stack or the lightweight default app, not both on port 8000. It adds PostgreSQL, OpenTelemetry Collector, Jaeger, Prometheus and Grafana. This consumes substantially more RAM than the default SQLite demo. Ports remain bound to localhost.

## Regression checks

```powershell
python -m unittest discover -s tests
node --test tests/cascade-controller.test.cjs tests/voice-controller.test.cjs
```

`scripts/smoke_voice_actions.py` optionally exercises actual Deepgram TTS → streaming STT → cart action → spoken confirmation using synthetic speech in a separate session. This small smoke test uses provider credits; ordinary unit tests do not.
