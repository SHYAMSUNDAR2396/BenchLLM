# LocalMind

Local AI assistant powered by Ollama — benchmark, compare, and chat with models entirely on your machine.

## Prerequisites

Install [Ollama](https://ollama.com) and pull the models used by LocalMind:

```bash
ollama serve
ollama pull llama3.2
ollama pull mistral
ollama pull phi3
```

## Backend setup

From the project root (`localMind/`):

```bash
python3.12 -m venv .venv   # Python 3.11–3.13 recommended
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

On startup you should see:

```
LocalMind running → UI: http://localhost:5173
                    → API: http://localhost:8000
```

## Frontend setup

```bash
cd ui
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173

## Example runs

### Benchmark

```bash
python -c "from benchmark.run_benchmark import run_benchmark; r, p = run_benchmark(['llama3.2','mistral'], 5); print(p)"
```

Or use the Benchmark page → **Run Benchmark**.

### Structured output

```bash
python -c "from structured.temperature_exp import run_temperature_experiment; print(run_temperature_experiment('Summarize edge computing in 3 bullets.'))"
```

### Model comparison

```bash
python -m comparison.run_comparison
python -c "from comparison.report import generate_report; print(generate_report()[:500])"
```

Or use Compare → **Generate Report**.

## Project structure

```
localMind/
├── ui/                 # Vite + React (Stitch design)
│   └── src/
│       ├── components/
│       ├── pages/
│       └── lib/api.js
├── shared/             # OllamaClient, config, utils
├── benchmark/          # Throughput benchmarks
├── structured/         # JSON schema validation, temp experiments
├── comparison/         # 40-prompt × 3-model comparison
├── api/                # FastAPI + SSE routes
├── requirements.txt
├── .env.example
└── README.md
```

## API overview

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | Ollama health + model list |
| `POST /api/chat` | Stream (SSE) or JSON-mode chat |
| `POST /api/benchmark/run` | SSE benchmark progress |
| `GET /api/benchmark/latest` | Latest saved results |
| `POST /api/comparison/run` | Run 3×40 prompt comparison |
| `GET /api/comparison/results` | Card data for UI |
| `GET /api/comparison/report` | Markdown report |
| `GET/POST /api/settings` | Read/update `.env` |
# BenchLLM
