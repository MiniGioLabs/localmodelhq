# LocalModel HQ 🖥️

**Find out what local AI models your machine can actually run.**

LocalModel HQ scans your hardware, checks compatibility against a curated model catalog, and benchmarks models so you know exactly what works on your machine — before you spend hours downloading the wrong model.

---

## What It Does

| Feature | Why It Matters |
|---|---|
| 🔍 **Hardware detection** | Automatically finds your CPU, RAM, GPU, and VRAM |
| 📋 **Compatibility check** | Matches your specs against 50+ models to show what fits |
| 🏋️ **Benchmarking** | Tests models on chat, coding, and classification tasks |
| 📊 **Result tracking** | Saves benchmark scores so you can compare over time |
| ⬇️ **Model management** | Pull and delete Ollama models from the dashboard |

## How It Works

```
┌─────────────────────────────────────────┐
│         LocalModel HQ Dashboard          │
│                                          │
│  Hardware  │  Compatible  │  Benchmarks  │
│  ────────  │  Models      │  ──────────  │
│  16GB RAM  │  llama3.2 ✅ │  Chat:   4.2s│
│  NVIDIA    │  mistral  ✅  │  Code:   6.1s│
│  8GB VRAM  │  llama3  ❌  │  Class:  1.3s│
└─────────────────────────────────────────┘
         │
         ▼
      Ollama (local)
```

## Quick Start

```bash
# Start Ollama first
ollama serve

# Run LocalModel HQ
uv run uvicorn localmodelhq.main:app --host 0.0.0.0 --port 8345
```

Then open http://localhost:8345 — the dashboard detects your hardware immediately.

## Stack

- **FastAPI** — backend with routers
- **aiosqlite** — benchmark history
- **psutil** — hardware detection
- **Ollama** — model runtime
- **Jinja2 + Tailwind** — dashboard UI

## Project Structure

```
src/localmodelhq/
├── main.py              # FastAPI app
├── config.py            # Settings
├── database.py          # SQLite schema
├── routers/
│   └── dashboard.py     # All routes
├── services/
│   ├── hardware.py      # CPU/GPU detection
│   ├── compatibility.py # Model matching
│   ├── ollama.py        # Ollama API client
│   └── benchmark.py     # Performance testing
├── templates/           # Jinja2 views
└── static/              # Model catalog
```

---

**MiniGioLabs** — [github.com/MiniGioLabs](https://github.com/MiniGioLabs)
