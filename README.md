# NexusAI — Academic Wellbeing & Career Co-Pilot

## Project Description
NexusAI is an AI-powered academic wellbeing and career co-pilot designed for college students. By combining machine learning-based risk detection with an intelligent multi-agent system, it provides holistic student support — from real-time mental wellbeing monitoring and crisis intervention to personalized career guidance with roadmap generation. The solution features a React frontend for students and a counselor dashboard with automated alerts, enabling institutions to proactively support student success.

---

## Project Details

### Problem Statement
Student mental health and career readiness are critical challenges in higher education. Many students struggle silently with wellbeing issues, and institutions often lack the tools to detect early warning signs or provide timely, personalized support. NexusAI addresses this gap by fusing behavioral analytics, sentiment analysis, and conversational AI to deliver proactive intervention and career guidance at scale.

### Data Preprocessing
- **Behavioral Features:** 7-dimensional feature vector extracted from student activity — session gap days, survey skip streak, average session length, assignment delay hours, chat initiation frequency, mood score trend, and login hour variance.
- **Normalization:** Each feature is scaled to a fixed range (e.g., session_gap_days: 0–30, mood_score_trend: -5 to 5) for consistent model input.
- **Synthetic Training Data:** 2,000 synthetic normal-behavior samples generated with random seed 42 for IsolationForest training.
- **Text Preprocessing:** Student messages cleaned (lowercased, normalized) before sentiment analysis; max 512 tokens for DistilBERT input.
- **Mood Surveys:** PHQ-inspired 3-question format (feeling, energy, motivation on 1–10 scale) producing a composite score used as the survey decline feature.

### Model Training & Evaluation
- **Models Used:**
  - IsolationForest (scikit-learn) — Behavioral anomaly detection on 7 features
  - DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`) — Real-time sentiment/distress scoring
  - Weighted Risk Scorer — Fuses anomaly, sentiment, and survey signals
- **Risk Scoring Formula:**
  ```
  weighted_risk = 0.50 x anomaly + 0.35 x sentiment + 0.15 x survey_decline
  ```
- **Risk Tiers:**
  | Tier | Score Range | Action |
  |------|-------------|--------|
  | Low | < 0.4 | No action |
  | Moderate | 0.4 – 0.6 | Wellbeing agent provides empathetic support |
  | High | 0.6 – 0.8 | Counselor encouraged + iCall helpline shown |
  | Crisis | >= 0.8 | Three-signal gate + counselor alert + helpline |
- **IsolationForest Contamination:** 5% anomaly rate
- **Persistence:** Trained model auto-saved to `ml/anomaly/models/isolation_forest.pkl`; auto-loaded on startup.

### Three-Signal Crisis Gate
The crisis detection system uses a multi-signal gate to minimize false positives:
```
Tier 1 — Explicit keyword match (17 regex patterns) + one corroborating signal
Tier 2 — High fused risk score (>= 0.8)
Tier 3 — Two-signal convergence (any pair):
  - anomaly >= 0.7 AND sentiment >= 0.75
  - anomaly >= 0.7 AND survey <= 2.0
  - sentiment >= 0.75 AND survey <= 2.0
```
Additional safeguards include negation window checks (5-word prefix) and fiction-context filtering to reduce false positives on crisis keywords.

### RAG Pipeline
- **Embeddings:** SentenceTransformers 3.3.1 for semantic encoding of curated academic and career resources.
- **Vector Index:** FAISS (IndexFlatIP) for fast inner-product similarity search.
- **Retrieval:** Top-k semantic search with domain filtering for contextually relevant recommendations (courses, government schemes, job sites).
- **Index Path:** `rag/data/faiss_index/nexus.index`; auto-built on first startup if missing.

### Visualizations
- Real-time risk gauge with percentage indicator on the student dashboard
- 30-day mood history trend charts
- 7-signal breakdown bar charts (anomaly, sentiment, survey decline components)
- Risk-tier color-coded badges (Green / Amber / Orange / Red)
- Streak counter for consistent check-ins
- Counselor alert feed with visual risk-tier indicators

### Web Application
The application serves two user roles:

**Student Interface:**
- **Dashboard** — Risk gauge, mood history chart, 7-signal breakdown, streak counter
- **MindBridge** — AI chat with tier-specific empathetic responses, signal breakdown visualization, voice chat support (audio upload with Whisper transcription), iCall helpline display for high/crisis tiers
- **PathwayAI** — Resume upload with PDF parsing, skill extraction, 12-week career roadmap generation, mock interviews (5 progressive questions), job openings recommendations

**Counselor Interface:**
- Real-time alert feed filterable by risk threshold
- Card view with student name, risk score, anomaly/sentiment breakdown
- Case notes workflow (add notes, mark resolved)
- Student notifications on case resolution

---

## Tech Stack

### Backend
- Python 3.11+
- FastAPI 0.123.2, Uvicorn
- SQLAlchemy 2.0 (async), asyncpg
- Alembic (database migrations)
- scikit-learn (IsolationForest)
- HuggingFace Transformers (DistilBERT), PyTorch
- sentence-transformers 3.3.1, FAISS
- python-jose (JWT), passlib (bcrypt)
- httpx, slowapi, pydantic-settings
- uv (package manager)

### Frontend
- React 18, TypeScript 5.4
- Vite 5.2 (build tool)
- Tailwind CSS 3.4
- Recharts 2.12 (data visualization)
- TanStack React Query 5.28
- Zustand 4.5 (state management)
- Lucide React (icons)

### Infrastructure
- PostgreSQL 15
- Docker & Docker Compose
- GitHub Actions (CI/CD)

### LLM Stack
- Ollama (primary, 3s timeout)
- Claude API / Anthropic (fallback, 25s timeout, circuit breaker pattern)

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/DCode-v05/NexusAI.git
cd NexusAI
```

### 2. Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- **uv** (Python package manager) — [Install uv](https://docs.astral.sh/uv/)
- **Docker & Docker Compose** (for full-stack setup)
- **PostgreSQL 15** (if running locally without Docker)

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
> The Vite dev server proxies all `/api` requests to the backend at `localhost:8000`.

### 4. Backend Setup
```bash
cd backend
uv sync
cp ../.env.example ../.env
# Edit .env with your database URL, API keys, etc.

uv run alembic upgrade head
uv run python scripts/seed_demo.py   # Optional: seed demo data
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Environment Variables** (`.env`):
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing key (32+ chars) |
| `OLLAMA_BASE_URL` | Remote Ollama server URL |
| `OLLAMA_MODEL` | Ollama model name |
| `ANTHROPIC_API_KEY` | Claude fallback API key |

### 5. Full Stack (Docker)
```bash
docker compose up --build      # Start all services
docker compose down            # Stop all services
```

---

## Usage
- **Students** log in and access the Dashboard for a real-time overview of their wellbeing signals and risk score.
- **MindBridge** provides AI-powered conversational support — students chat naturally and receive tier-calibrated empathetic responses with crisis escalation when needed.
- **PathwayAI** enables career planning — upload a resume, extract skills, generate a 12-week roadmap, and practice with mock interviews.
- **Counselors** monitor the alert dashboard for at-risk students, manage cases with notes, and resolve alerts with automatic student notifications.

---

## Project Structure
```
NexusAI/
|
+-- agents/                         # AI orchestration & specialist agents
|   +-- orchestrator/               # Main routing agent
|   +-- wellbeing/                  # Wellbeing support agent
|   +-- pathway/                    # Career guidance agent
|   +-- crisis/                     # Crisis intervention agent
|   +-- llm/                        # LLM clients (Ollama + Claude fallback)
+-- backend/                        # FastAPI backend service
|   +-- src/
|   |   +-- auth/                   # Authentication & JWT
|   |   +-- students/               # Student profiles & behavior
|   |   +-- wellbeing/              # Wellbeing alerts & chat APIs
|   |   +-- pathway/                # Career pathway APIs
|   |   +-- counselor/              # Counselor dashboard APIs
|   |   +-- shared/                 # Common utilities
|   |   +-- main.py                 # FastAPI entry point
|   +-- alembic/                    # Database migrations
|   +-- scripts/                    # Seed data & demo scripts
|   +-- Dockerfile
+-- ml/                             # Machine learning models
|   +-- anomaly/                    # IsolationForest detector
|   +-- sentiment/                  # DistilBERT sentiment analyzer
|   +-- risk/                       # Risk scoring algorithm
|   +-- speech/                     # Audio transcription
+-- rag/                            # Retrieval-Augmented Generation
|   +-- embedder.py                 # SentenceTransformers embeddings
|   +-- indexer.py                  # FAISS index management
|   +-- retriever.py                # Semantic search
|   +-- resource_db.py              # Resource database
|   +-- scripts/build_index.py      # Index building script
+-- frontend/                       # React 18 + TypeScript UI
|   +-- src/
|   |   +-- pages/
|   |   |   +-- auth/               # Login / Register
|   |   |   +-- student/            # Dashboard, MindBridge, PathwayAI
|   |   |   +-- counselor/          # Counselor dashboard
|   |   +-- components/             # Reusable UI components
|   |   +-- charts/                 # Data visualization components
|   |   +-- api/                    # API client layer
|   |   +-- store/                  # Zustand state management
|   |   +-- App.tsx                 # Main entry point
|   +-- Dockerfile
+-- mcp-servers/                    # Model Context Protocol servers
|   +-- student-db-server/          # Student data access (port 9001)
|   +-- job-market-server/          # Job market data (port 9002)
|   +-- resource-rag-server/        # Resource RAG endpoint (port 9003)
|   +-- counselor-alerts-server/    # Counselor alert management (port 9004)
+-- shared/                         # Shared utilities across services
+-- docs/                           # Documentation
+-- docker-compose.yml              # Multi-service orchestration
+-- requirements.txt                # Python dependencies
+-- .env.example                    # Environment config template
+-- .github/workflows/ci.yml        # CI/CD pipeline
+-- README.md                       # Project documentation
```

---

## Architecture
```
Frontend (:3000) --> /api proxy --> Backend (:8000) --> MCP Servers (:9001-9004)
                                        |                    |
                                    PostgreSQL (:5432)   PostgreSQL (shared)
                                        |
                                  Agents + ML Pipeline
                                        |
                               LLM Router (Ollama --> Claude fallback)
```

| Service | Port | Stack |
|---------|------|-------|
| Frontend | 3000 | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | 8000 | FastAPI, SQLAlchemy 2.0, asyncpg |
| Student DB MCP | 9001 | FastAPI microservice |
| Job Market MCP | 9002 | FastAPI microservice |
| Resource RAG MCP | 9003 | FastAPI + FAISS + SentenceTransformers |
| Counselor Alerts MCP | 9004 | FastAPI microservice |
| PostgreSQL | 5432 | PostgreSQL 15 Alpine |

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request describing your changes.

### Guidelines
- Follow the existing code style and conventions.
- Python: use `uv` as the package manager, async-first patterns, Pydantic v2 schemas.
- Frontend: use the teal-based design system (`#005A70` primary), `lucide-react` for icons.
- Write meaningful commit messages.
- Test your changes before submitting a PR.

---

## Contact
- **GitHub:** [DCode-v05](https://github.com/DCode-v05)
- **Email:** denistanb05@gmail.com
