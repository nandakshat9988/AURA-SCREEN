# AURA-SCREEN: Role-Based Candidate Screening System

**Aura-Screen** is an AI-powered technical candidate screening platform designed to simulate an elite, textbook-grounded technical interview. Built with a modern full-stack architecture, it pairs Claude Opus with textbook Retrieval-Augmented Generation (RAG), MongoDB Atlas persistence, and an interactive React frontend deployed on Vercel.

---

## 1. Executive Summary & Problem Solved

Standard hiring pipelines often rely on generic AI prompt templates or simple multiple-choice quizzes that fail to assess deep theoretical comprehension and architectural trade-off reasoning. 

**Aura-Screen** solves this by:
- Grounding technical interview questions in authoritative reference textbooks (Tom Mitchell Machine Learning, Burkov, Brownlee Applied ML, and Distributed Systems Architecture).
- Adapting the questions to the candidate's uploaded resume skills.
- Enforcing strict grading criteria where superficial or low-effort answers (such as *"yes"*, *"no"*, or vague buzzword guessing) receive failing scores, while answers demonstrating mathematical rigor and systems trade-offs are rewarded.
- Providing complete RAG citation traceability so recruiters and interviewers see the exact textbook passage behind every interview question.
- Persisting all interview runs, questions, answers, feedback, and final scorecards directly to MongoDB Atlas.

---

## 2. System Architecture

A single monorepo repository handles both the interactive Single-Page Application (SPA) frontend and Python serverless API backend on Vercel.

```
AURA-SCREEN /
├── api/                             Vercel Cloud Serverless API Entrypoints
│   ├── index.py                     HTTP handler and ASGI bridge for Vercel
│   ├── database.py                  MongoDB Atlas client with connection failover
│   ├── rag.py                       TF-IDF Vector Space RAG retrieval engine
│   └── llm.py                       Claude Opus integration & strict scoring engine
├── backend/                         Standalone Local FastAPI Server
│   ├── knowledge_base/              Textbook corpuses for grounded RAG
│   │   ├── ai_ml_engineer.txt       (Mitchell & Burkov ML foundations)
│   │   ├── data_scientist.txt       (Applied ML, Feature Engineering, Metrics)
│   │   └── backend_engineer.txt     (ACID, WAL, Event Loops, CAP, Caching)
│   ├── main.py                      FastAPI application with REST endpoints
│   ├── database.py                  MongoDB database operations
│   ├── rag.py                       Textbook indexing and cosine retrieval
│   └── llm.py                       Claude Opus parsing and evaluation
├── frontend/                        Modern React + Vite Frontend
│   ├── api/                         Unified serverless functions for Vercel build
│   │   ├── index.py                 Direct Vercel Python entrypoint
│   │   ├── database.py              Database module for serverless execution
│   │   ├── rag.py                   RAG module with embedded textbook corpuses
│   │   └── llm.py                   Claude Opus and strict evaluation logic
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           Navbar with live status badges
│   │   │   ├── SetupScreen.jsx      Role selector & PDF/TXT resume parser
│   │   │   ├── InterviewScreen.jsx  Interactive 3-stage live interview
│   │   │   └── SummaryScreen.jsx    Scorecard, radar metrics & transcript
│   │   ├── App.jsx                  State machine managing screen transitions
│   │   └── index.css                Dark mode glassmorphism UI & custom styling
│   └── vercel.json                  Unified build & routing specification
└── README.md                        Quickstart and setup guide
```

---

## 3. Core Technical Pillars

### A. Grounded Textbook RAG Pipeline
Questions are not randomly hallucinated. The RAG pipeline:
1. Indexes curated technical textbooks:
   - **AI / ML**: Tom Mitchell's *Machine Learning* & Andriy Burkov's *The Hundred-Page Machine Learning Book* (Inductive Bias, Version Space, Backpropagation, Gradient Propagation, Attention).
   - **Data Science**: Jason Brownlee's *Applied Machine Learning* (Missingness Imputation, Scalers, Imbalance Metrics, Bagging vs. Boosting).
   - **Backend Engineering**: *System Design & Storage Engines* (Write-Ahead Logging, ACID internals, Event Loops, CAP Theorem, Cache-Aside race conditions).
2. Uses chunking and vector space similarity matching against candidate skills to select the most relevant domain concept.
3. Attaches the exact source text directly to the question so the candidate and interviewer can review the grounded material.

### B. Claude Opus LLM & Strict Scoring Engine
- **Model**: Anthropic Claude Opus (`claude-3-opus-20240229`).
- **Resume Information Extraction**: Parses uploaded PDF or TXT resumes to identify skills, technologies, experience tier, and profile summary.
- **Strict Scoring Rubric**:
  - **Trivial / 1-Word Answers** (`yes`, `no`, `ok`, or < 4 words): **5 / 100**. Flags lack of technical reasoning.
  - **Superficial Answers** (< 15 words or < 2 domain keywords): **20 / 100**. Missing theoretical grounding.
  - **Moderate / Introductory Answers**: **50 / 100**. Identifies basic concepts but lacks edge-case analysis.
  - **Proficient Technical Responses**: **75 / 100**. Strong conceptual command with terminology.
  - **Mastery / Senior Responses**: **90+ / 100**. Cites mathematical constraints, production trade-offs, and failure modes.

### C. MongoDB Atlas Cloud Persistence
Every interview session is persisted across three collections in the `Aura-Screen` database:
- **`sessions`**: Session ID, candidate name, selected role, extracted resume text, extracted skills, and start timestamp.
- **`interview_turns`**: Turn index (1, 2, 3), question asked, grounded textbook chunks, candidate's submitted answer, feedback score, strengths, and improvements.
- **`evaluations`**: Overall composite score (0-100), sub-scores (Technical Depth, Grounding, Problem Solving, Communication), executive summary, hiring recommendation, and growth areas.
- **Resilience**: Features automatic fallback to in-memory storage if cloud database credentials are temporarily unreachable.

### D. Single-Deploy Vercel Architecture
- Combines the React Single-Page Application and Python serverless endpoints into one deployment via `frontend/vercel.json`.
- Routes:
  - `/api/roles`: Lists available engineering interview tracks.
  - `/api/sessions/start`: Initializes session, parses resume, and generates question #1 with grounded textbook citations.
  - `/api/sessions/{session_id}/answer`: Evaluates submitted answer, records turn, and advances to the next turn or generates final evaluation.
  - `/api/sessions/{session_id}/summary`: Returns full interview summary, scorecards, and transcripts.
  - `/(.*)`: Serves the compiled React frontend application.

---

## 4. End-to-End Interview Lifecycle

```
[Candidate Lands on App]
          │
          ▼
1. Selects Role (AI/ML, Data Science, Backend) & Uploads Resume (PDF/TXT)
          │
          ▼
2. System extracts candidate skills & queries textbook RAG corpus
          │
          ▼
3. Generates Turn 1 Question + Grounded Reference Source
          │
          ▼
4. Candidate enters technical answer
          │
          ▼
5. Strict evaluation assesses depth, domain vocabulary, and trade-offs
          │
   ┌──────┴──────┐
   │ Turn < 3    │ Turn == 3
   ▼             ▼
Generates next  Synthesizes Comprehensive Final Scorecard:
question & turn • Overall Score & Radar Metrics
                • Hiring Recommendation (Strong Hire / Hire / Needs Work)
                • Key Strengths & Growth Areas
                • Full Transcript with Grounded Textbook Citations
                • Saved to MongoDB Atlas
```

---

## 5. Deployment Information

- **Live URL**: `https://aura-screen.vercel.app/`
- **GitHub Repository**: `https://github.com/nandakshat9988/AURA-SCREEN`
- **Database**: MongoDB Atlas (`Aura-Screen` database, `aura-screen-resumes` collection)
- **Codebase Cleanliness**: Zero comment lines across all production source files.
