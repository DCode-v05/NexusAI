# NexusAI — Academic Wellbeing & Career Co-Pilot

## What is NexusAI?

NexusAI is an AI-powered platform built for college students (primarily Indian engineering colleges) that acts as a **personal wellbeing companion and career guide**. It continuously monitors student behavior patterns, detects early signs of mental distress using machine learning, and provides real-time support through AI conversations — while keeping human counselors in the loop for critical situations.

Think of it as a **24/7 digital safety net** that catches students who are silently struggling before things escalate.

---

## The Problem We Solve

Indian engineering colleges face a silent mental health crisis:

- **1 in 5** engineering students report severe stress or anxiety
- Most students **never approach a counselor** due to stigma, lack of awareness, or inaccessibility
- Counselors are outnumbered — often **1 counselor for 1,000+ students**
- Early warning signs (skipping classes, irregular schedules, social withdrawal) go unnoticed until it's too late
- Students also lack **structured career guidance** — leading to anxiety about placements and future

**NexusAI bridges this gap** by using AI to detect risk early, provide immediate empathetic support, and alert human counselors only when needed — so no student falls through the cracks.

---

## Who Uses NexusAI?

### 1. Students (Primary Users)
- Take daily mood check-ins (3-question PHQ-inspired surveys)
- Chat with an AI companion (MindBridge) for emotional support
- Get career guidance — upload resumes, identify skill gaps, receive personalized 12-week roadmaps
- Receive crisis support with helpline information when needed

### 2. Counselors (Professional Users)
- Access a real-time alert dashboard showing students flagged by the AI
- View detailed risk scores, behavioral patterns, and AI-detected anomalies
- Write case notes, track student progress, and resolve cases
- Focus their limited time on students who need them most

### 3. College Administrators
- Gain campus-wide mental health visibility
- Make data-driven decisions about student support programs

---

## Core Features

### MindBridge — AI Wellbeing Companion
- Students chat naturally with an empathetic AI that understands their emotional context
- The AI calibrates its responses based on the student's detected risk level:
  - **Low risk** — Encouraging, growth-focused conversations
  - **Moderate risk** — Supportive, coping strategy suggestions
  - **High risk** — Gentle concern, resource sharing
  - **Crisis** — Immediate helpline info (iCall: 9152987821), counselor auto-alert
- Supports voice input (speech-to-text via Whisper)
- Maintains conversation history for contextual, coherent responses

### Smart Risk Detection (Behind the Scenes)
NexusAI uses a **three-signal fusion model** to detect student distress:

| Signal | What It Measures | How |
|--------|-----------------|-----|
| **Behavioral Anomaly** | Irregular patterns (session gaps, login time variance, assignment delays, mood trends) | IsolationForest ML model on 7 behavioral features |
| **Sentiment Distress** | Negative emotion in chat messages | DistilBERT NLP model analyzing conversation text |
| **Survey Decline** | Dropping mood survey scores over time | Trend analysis on daily PHQ-inspired check-ins |

**Risk Formula:** `50% anomaly + 35% sentiment + 15% survey decline`

**Risk Tiers:**
- Below 0.4 → Low (no action)
- 0.4–0.6 → Moderate (enhanced AI support)
- 0.6–0.8 → High (resource recommendations, counselor visibility)
- 0.8+ → Crisis (immediate counselor alert + helpline)

### Crisis Safety Gate (Three-Signal Gate)
To avoid false alarms, a crisis alert to counselors is triggered **only when all three conditions converge:**
1. Anomaly score ≥ 0.7
2. Sentiment distress ≥ 0.75
3. Crisis keywords detected (self-harm, suicide, etc.) OR survey composite ≤ 2.0

This dramatically reduces false positives while catching genuine risk.

### PathwayAI — Career Co-Pilot
- **Resume Upload & Parsing** — Students upload their resume (PDF/DOCX), AI extracts skills
- **Skill Gap Analysis** — Visual radar chart comparing current skills vs. target role requirements
- **12-Week Roadmap** — Personalized learning plan with weekly milestones for their dream job
- **Mock Interviews** — AI-powered practice interviews with progressive difficulty (5 questions per role)
- **Job Market Data** — Real-time role demand, salary insights, and trending skills

### Counselor Dashboard
- **Live Alert Feed** — Auto-refreshes every 30 seconds with risk-flagged students
- **Risk Detail Panel** — Shows anomaly score, sentiment score, survey trends, triggered keywords
- **Case Notes** — Counselors add private notes during follow-ups
- **Case Resolution** — Structured workflow to mark cases as resolved with summary

### Daily Mood Check-In
- 3 quick slider-based questions (inspired by PHQ-2 clinical screening)
- Takes under 60 seconds
- Tracks mood trends over 30 days with visual charts
- Free-text journaling option for deeper expression

---

## How the AI Agent System Works

NexusAI uses a **multi-agent architecture** where specialized AI agents handle different scenarios:

```
Student sends message
        ↓
   Orchestrator Agent
   (fetches behavior data, runs ML models, computes risk)
        ↓
   Routes to specialist based on risk + keywords
        ↓
   ┌─────────────┬──────────────┬──────────────┐
   │ Wellbeing    │ Career       │ Crisis       │
   │ Agent        │ (Pathway)    │ Agent        │
   │              │ Agent        │              │
   │ Empathetic   │ Job market   │ Helpline +   │
   │ support      │ data + RAG   │ counselor    │
   │ calibrated   │ resources    │ alert        │
   │ to risk tier │ + roadmap    │ creation     │
   └─────────────┴──────────────┴──────────────┘
        ↓
   LLM generates response
   (Ollama primary → Claude Haiku fallback)
```

---

## The 7 Behavioral Signals We Track

| # | Signal | What It Indicates | Range |
|---|--------|------------------|-------|
| 1 | **Session Gap Days** | How many days since last login | 0–30 days |
| 2 | **Survey Skip Streak** | Consecutive skipped mood check-ins | 0–14 days |
| 3 | **Avg Session Length** | Time spent per session | 0–120 min |
| 4 | **Assignment Delay Hours** | How late assignments are submitted | 0–48 hrs |
| 5 | **Chat Initiation Frequency** | How often student starts conversations | 0–10/day |
| 6 | **Mood Score Trend** | Direction of mood over time | -5 to +5 |
| 7 | **Login Hour Variance** | Irregularity of login times (sleep disruption indicator) | 0–12 hrs |

These signals are normalized and fed into the anomaly detection model to identify students whose patterns deviate from healthy baselines.

---

## Technology Stack (High Level)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React, TypeScript, Tailwind CSS | Student & counselor interfaces |
| **Backend** | FastAPI (Python), async architecture | API server, business logic |
| **Database** | PostgreSQL | User data, behavior logs, alerts |
| **ML Models** | IsolationForest, DistilBERT, Whisper | Anomaly detection, sentiment, speech |
| **AI/LLM** | Ollama + Claude Haiku (fallback) | Natural language generation |
| **Search** | FAISS + SentenceTransformer | Resource & learning material retrieval |
| **Microservices** | 4 MCP servers | Student data, job market, resources, alerts |
| **Deployment** | Docker Compose | Full-stack orchestration |

---

## User Journey

### Student Journey
```
Register → Create Profile → Daily Mood Check-in (60 sec)
                                    ↓
                         Dashboard (streak, risk gauge,
                         mood chart, behavior signals)
                                    ↓
              ┌─────────────────────┼─────────────────────┐
              ↓                     ↓                     ↓
        MindBridge Chat      Upload Resume         View Resources
     (AI wellbeing talk)    (skill extraction)    (RAG-powered)
              ↓                     ↓
     Risk auto-computed      Skill Gap Radar
              ↓                     ↓
     If crisis detected →   12-Week Roadmap
     Helpline shown +            ↓
     Counselor alerted     Mock Interviews
```

### Counselor Journey
```
Login → Counselor Dashboard → View Alert Feed (auto-refresh 30s)
                                      ↓
                              Click student alert
                                      ↓
                         View risk breakdown (anomaly,
                         sentiment, survey, keywords)
                                      ↓
                         Add case notes → Follow up
                                      ↓
                         Resolve case with summary
```

---

## Key Differentiators

1. **Proactive, not reactive** — Detects distress before students ask for help
2. **Three-signal fusion** — Reduces false positives by requiring multi-signal convergence for crisis alerts
3. **Risk-calibrated AI** — Responses adapt in tone and content based on real-time risk assessment
4. **Privacy-first** — Counselors only see flagged students, not all conversations
5. **Career + Wellbeing combined** — Addresses the two biggest student anxieties in one platform
6. **Cold-start ready** — Works from day one with synthetic baseline training data
7. **Human-in-the-loop** — AI handles volume, counselors handle critical cases
8. **Dual LLM reliability** — Primary + fallback LLM ensures 24/7 availability

---

## Impact Metrics (Targets)

| Metric | Target |
|--------|--------|
| Early detection rate | Identify at-risk students 2–4 weeks earlier than traditional methods |
| Counselor efficiency | 5x more students covered per counselor |
| Student engagement | 70%+ daily check-in completion rate |
| False positive rate | < 5% for crisis alerts (three-signal gate) |
| Response availability | 24/7 AI support vs. counselor office hours |
| Career preparedness | Students with structured roadmaps, not ad-hoc preparation |

---

## Deployment Model

NexusAI is designed as a **self-hosted, college-deployed platform**:
- Runs entirely on college infrastructure via Docker
- Student data never leaves the college network
- Integrates with existing LMS/ERP systems through the MCP server architecture
- Scalable from a single department to an entire university

---

## Summary

NexusAI transforms how colleges support student mental health and career readiness. By combining behavioral analytics, NLP-powered sentiment detection, and empathetic AI conversations — all backed by a human counselor safety net — it ensures **no student suffers in silence** while making limited counseling resources dramatically more effective.
