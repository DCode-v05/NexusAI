# NexusAI

**An academic wellbeing and career co-pilot for college students — ML risk detection with human-counselor escalation, plus an AI career planner.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-0.123-009688?style=flat&logo=fastapi&logoColor=white) ![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat&logo=typescript&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white) ![scikit-learn](https://img.shields.io/badge/scikit--learn-IsolationForest-F7931E?style=flat&logo=scikitlearn&logoColor=white) ![Hugging Face](https://img.shields.io/badge/DistilBERT-FFD21E?style=flat&logo=huggingface&logoColor=black) ![FAISS](https://img.shields.io/badge/FAISS-RAG-0467DF?style=flat&logo=meta&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)

## Overview

NexusAI is a full-stack platform that helps colleges spot students who are struggling and connect them with the right support before things get worse — and, on the other side, helps those same students plan their careers. It does two things under one roof:

1. **Wellbeing monitoring** — an ML pipeline watches behavioral signals and chat sentiment, scores a student's risk, and escalates high-risk cases to a human counselor with an alert.
2. **Career guidance** — a separate agent parses a resume, finds skill gaps, builds a 12-week roadmap, runs mock interviews, and recommends jobs.

The system has two roles. Students get a dashboard, a chat assistant (MindBridge), and the career planner (PathwayAI). Counselors get an alert feed filtered by risk tier, with case notes and a resolution workflow that notifies the student when a case is closed.

I built this as a solo project — backend, frontend, the ML pipeline, the agent layer, and the infrastructure. It is the most complete project I've shipped: a Dockerized FastAPI backend with async SQLAlchemy and Alembic migrations, a React/TypeScript frontend, four MCP microservices, a pytest suite, and a CI workflow. The repo is roughly 4,700 lines of authored Python plus the full TypeScript frontend.

## Key Features

- **Behavioral anomaly detection** — an IsolationForest model scores a 7-dimensional behavior vector (session-gap days, survey-skip streak, average session length, assignment-delay hours, chat-initiation frequency, mood-score trend, login-hour variance) trained on 2,000 synthetic normal-behavior samples (seed 42, 5% contamination).
- **Sentiment / distress scoring** — DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`) scores each student message in real time, capped at 512 tokens.
- **Weighted risk fusion** — anomaly, sentiment, and survey-decline signals fuse into a single risk score: `0.50·anomaly + 0.35·sentiment + 0.15·survey_decline`, bucketed into four tiers (Low / Moderate / High / Crisis).
- **Three-signal crisis gate** — a multi-stage gate (explicit keyword match + a corroborating signal, high fused score, or two-signal convergence) decides when to escalate, with negation-window checks and fiction-context filtering to cut false positives on crisis keywords.
- **Multi-agent routing** — an orchestrator routes each request to the Crisis, Wellbeing, or Pathway agent based on risk score and keyword matching.
- **Hybrid LLM stack** — Ollama runs as the primary model (3s timeout) with a Claude / Anthropic API fallback (25s timeout) behind a circuit breaker, so the system stays responsive if the local model is slow or down.
- **RAG over curated resources** — SentenceTransformers embeddings indexed in FAISS (inner-product) serve career and academic recommendations (courses, government schemes, job sites); the index auto-builds on first startup if missing.
- **Voice chat** — students can upload audio; Whisper transcribes it before it enters the pipeline.
- **PathwayAI career planner** — resume PDF parsing, skill extraction, a skill-gap radar, a 12-week roadmap, and a 5-question progressive mock interview.
- **Counselor dashboard** — real-time alert feed filterable by risk threshold, per-student risk/anomaly/sentiment breakdown, case notes, and resolve-with-notification workflow.
- **Four MCP microservices** — student-db, job-market, resource-rag, and counselor-alerts servers (ports 9001–9004), each a small FastAPI service.
- **Production plumbing** — JWT auth with a token revocation/blacklist table, per-IP rate limiting (slowapi), CORS, DB connection retry on startup, background ML pre-warming, and periodic context-store garbage collection.

## How It Works

### Data and signals

Each student produces a 7-dimensional behavior vector. The features are scaled to fixed ranges (for example `session_gap_days` 0–30, `mood_score_trend` -5 to 5) so the model sees consistent input. Mood surveys use a PHQ-inspired 3-question format (feeling, energy, motivation on a 1–10 scale) and produce a composite score that feeds the survey-decline signal.

### Risk scoring

The scorer (`ml/risk/scorer.py`) clamps each input to [0, 1] and computes the fused score directly:

```python
score = 0.50 * anomaly + 0.35 * sentiment + 0.15 * survey_decline
```

It then assigns a tier: `< 0.4` low, `0.4–0.6` moderate, `0.6–0.8` high, `>= 0.8` crisis. The function returns the score, the tier, and the three component scores so the frontend can show a per-signal breakdown rather than a single opaque number.

| Tier | Score | Action |
|------|-------|--------|
| Low | < 0.4 | No action; default to career guidance |
| Moderate | 0.4 – 0.6 | Wellbeing agent gives empathetic support |
| High | 0.6 – 0.8 | Counselor encouraged + iCall helpline shown |
| Crisis | >= 0.8 | Three-signal gate + counselor alert + helpline |

### Crisis gate

Crisis keyword matching is the part where false positives matter most, so it gets the most care. The detector (`agents/orchestrator/router_logic.py`) compiles 17 regex patterns with word boundaries (so "suicidal" matches but "antidote" does not), covering stem variants and common phrasings. On top of the raw regex match it adds two filters:

- **Fiction-context filter** — if the text mentions movie/game/book/lyrics-style tokens (including specific titles like "suicide squad" or "13 reasons") and contains no first-person markers ("I am", "I feel", "my life"), the match is dropped.
- **Negation window** — for each match, the 5 words immediately before it are checked for negation words ("not", "never", "can't"…); negated matches are not counted.

Only matches that survive both filters count toward the crisis gate, which combines them with the fused risk score and two-signal convergence rules.

### Agent routing

The orchestrator routes in priority order:

1. Confirmed crisis keywords **or** risk `>= 0.8` → Crisis agent
2. Career/pathway keywords (`job`, `resume`, `roadmap`, `internship`, `swayam`, `pmkvy`, …) → Pathway agent
3. Risk `>= 0.4` → Wellbeing agent (MindBridge)
4. Otherwise → Pathway agent (career guidance is the default)

Pathway and wellbeing keyword matching are simple set lookups since their false-positive cost is low; the heavy false-positive handling is reserved for the crisis path.

### LLM layer

Generation goes through a router that tries Ollama first with a 3-second timeout. If that fails or times out, a circuit breaker hands off to the Claude / Anthropic API with a 25-second timeout. This keeps interactive latency low in the common case while still producing a useful answer when the local model isn't available.

### RAG

Curated career and academic resources are embedded with SentenceTransformers (3.3.1) and stored in a FAISS `IndexFlatIP`. Retrieval is top-k inner-product search with domain filtering, so a career query pulls back courses/schemes/job sites rather than wellbeing content. The index lives at `rag/data/faiss_index/nexus.index` and is built automatically on first run if it doesn't exist.

### Backend lifecycle

The FastAPI app (`backend/src/main.py`) wires this together. On startup it retries the DB connection up to 5 times, creates tables, prunes expired revoked tokens, ensures the RAG index exists, pre-warms the ML models in a background task so the first real request isn't slow, and starts a 30-minute loop that evicts stale entries from the agent context store. Requests are rate-limited per client IP.

### Frontend

The React 18 / TypeScript frontend (Vite, Tailwind, TanStack Query, Zustand) renders the student dashboard with a risk gauge, a 30-day mood-history chart, a per-signal breakdown, and a check-in streak counter (Recharts). MindBridge is the chat view with tier-calibrated responses, signal visualization, voice upload, and the iCall helpline for high/crisis tiers. PathwayAI handles resume upload, the skill radar, the roadmap, and mock interviews. The counselor dashboard is a separate route with the alert feed and case workflow. The Vite dev server proxies `/api` to the backend at `localhost:8000`.

## Results / Highlights

This is a working system rather than a benchmarked model, so most of the "numbers" are design parameters rather than measured metrics:

- IsolationForest trained on 2,000 synthetic samples, 5% contamination, fixed seed 42 for reproducibility.
- Risk fusion weights 0.50 / 0.35 / 0.15 across anomaly, sentiment, and survey signals; four tiers.
- 17 crisis regex patterns plus negation-window and fiction-context filtering on the escalation path.
- DistilBERT sentiment scoring capped at 512 tokens; Ollama (3s) → Claude fallback (25s) routing.
- ~4,700 lines of authored Python (agents, backend, ML, RAG, MCP servers) plus the full React/TypeScript frontend, with a pytest suite (`test_auth_service`, `test_risk_scorer`, `test_router_logic`), Alembic migrations, Dockerfiles, and a CI workflow.
- Target operating goals stated in the design (not yet measured in production): under 5% crisis false-positive rate and wider counselor coverage per case.

## Tech Stack

- **Languages:** Python 3.11+, TypeScript 5.4
- **Backend / API:** FastAPI 0.123, Uvicorn, SQLAlchemy 2.0 (async) + asyncpg, Alembic, python-jose (JWT), passlib (bcrypt), slowapi, pydantic-settings, httpx
- **ML / NLP:** scikit-learn (IsolationForest), HuggingFace Transformers + PyTorch (DistilBERT), Whisper, sentence-transformers 3.3.1, FAISS
- **LLM:** Ollama (primary), Claude / Anthropic API (fallback, circuit breaker)
- **Frontend:** React 18, Vite 5, Tailwind CSS 3, Recharts, TanStack React Query, Zustand, Lucide
- **Infra:** PostgreSQL 15, Docker + Docker Compose, four MCP microservices, GitHub Actions CI, `uv` package manager

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- `uv` (Python package manager)
- Docker and Docker Compose (for the full-stack run)
- PostgreSQL 15 (if running the backend locally without Docker)

### Installation

```bash
git clone https://github.com/DCode-v05/NexusAI.git
cd NexusAI
```

**Backend:**

```bash
cd backend
uv sync
cp ../.env.example ../.env          # then edit .env (DB URL, secret key, API keys)
uv run alembic upgrade head
uv run python scripts/seed_demo.py  # optional: seed demo data
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Running the full stack with Docker

```bash
docker compose up --build   # start backend, frontend, MCP servers, and PostgreSQL
docker compose down         # stop everything
```

### Environment variables (`.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing key (32+ chars) |
| `OLLAMA_BASE_URL` | Ollama server URL |
| `OLLAMA_MODEL` | Ollama model name |
| `ANTHROPIC_API_KEY` | Claude fallback API key |

## Usage

- **Students** log in to the dashboard for a live view of their wellbeing signals and risk score, with mood history and a per-signal breakdown.
- **MindBridge** is the chat assistant — students talk to it normally and get tier-calibrated responses, with crisis escalation and the iCall helpline shown automatically when the risk tier warrants it. Voice messages are transcribed by Whisper before they enter the pipeline.
- **PathwayAI** handles career planning — upload a resume, get extracted skills and a skill-gap radar, generate a 12-week roadmap, and run a 5-question mock interview.
- **Counselors** work the alert feed: filter by risk threshold, open a student card to see the anomaly/sentiment breakdown, add case notes, and resolve cases — which notifies the student.

## Project Structure

```
NexusAI/
├── agents/                     # Orchestration + specialist agents
│   ├── orchestrator/           # Router (router_logic.py), context store
│   ├── crisis/                 # Crisis intervention agent
│   ├── wellbeing/              # MindBridge wellbeing agent
│   ├── pathway/                # Career guidance agent
│   └── llm/                    # Ollama client + Claude fallback
├── ml/
│   ├── anomaly/                # IsolationForest detector + 7-feature builder
│   ├── sentiment/              # DistilBERT analyzer + preprocessor
│   ├── risk/                   # Weighted risk scorer (scorer.py)
│   └── speech/                 # Whisper transcription
├── rag/                        # Embedder, FAISS indexer, retriever, resource DB
│   └── scripts/build_index.py  # Index builder
├── backend/                    # FastAPI service
│   ├── src/
│   │   ├── auth/               # JWT auth + token revocation
│   │   ├── students/           # Student profiles & behavior
│   │   ├── wellbeing/          # Alerts & chat APIs
│   │   ├── pathway/            # Career pathway APIs
│   │   ├── counselor/          # Counselor dashboard APIs
│   │   ├── shared/             # Utils & exceptions
│   │   └── main.py             # App entry: lifespan, rate limit, warmup
│   ├── alembic/                # Migrations
│   ├── scripts/seed_demo.py    # Demo seed
│   └── tests/                  # pytest: auth, risk scorer, router logic
├── mcp-servers/                # Four FastAPI MCP services (ports 9001–9004)
│   ├── student-db-server/
│   ├── job-market-server/
│   ├── resource-rag-server/
│   └── counselor-alerts-server/
├── frontend/                   # React 18 + TypeScript (Vite, Tailwind)
│   └── src/
│       ├── pages/              # auth / student / counselor
│       ├── components/         # charts, chat, layout, ui
│       ├── api/                # API client layer
│       └── store/              # Zustand stores
├── docs/NexusAI-Overview.md    # Extended design write-up
├── docker-compose.yml          # Multi-service orchestration
└── README.md
```

---

## Contact

**Portfolio:** [Denistan](https://www.denistan.me)<br>
**LinkedIn:** [Denistan](https://www.linkedin.com/in/denistanb)<br>
**GitHub:** [DCode-v05](https://github.com/DCode-v05)<br>
**LeetCode:** [Denistan_B](https://leetcode.com/u/Denistan_B)<br>
**Email:** [denistanb05@gmail.com](mailto:denistanb05@gmail.com)

Made with ❤️ by **Denistan B**
