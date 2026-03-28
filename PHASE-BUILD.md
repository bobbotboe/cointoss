# CoinToss - Multi-Agent Lottery Analysis Engine

## Phase Build Document

**Project:** CoinToss
**Description:** A multi-agent AI application that analyses past lottery results through multiple perspectives — mathematics, numerology, astrology, psychic intuition, and more. Agents debate each other and produce entertaining, personality-driven number analysis.
**Created:** 2026-03-29

> **Disclaimer:** This application is for entertainment purposes only. Lottery draws are random. No combination of mathematics, astrology, or psychic energy changes the odds. Play responsibly.

---

## Phase 1 — Foundation & Data Layer

**Goal:** Establish project structure, data ingestion, and storage.

### 1.1 Project Scaffolding
- [ ] Initialise project (Python or Node.js — TBD based on preference)
- [ ] Set up dependency management (requirements.txt / package.json)
- [ ] Configure linting, formatting, and pre-commit hooks
- [ ] Create base folder structure:
  ```
  cointoss/
  ├── agents/           # Agent persona definitions and prompts
  ├── data/             # Raw and processed lottery data
  ├── engine/           # Core analysis and debate orchestration
  ├── api/              # API layer (FastAPI / Express)
  ├── ui/               # Frontend (Phase 4)
  ├── tests/            # Test suite
  └── docs/             # Documentation
  ```

### 1.2 Lottery Data Ingestion
- [ ] Research and select target lottery (e.g., UK National Lottery, EuroMillions, US Powerball)
- [ ] Build scraper/importer for historical draw results
- [ ] Define data schema:
  - Draw date
  - Main numbers
  - Bonus/special numbers
  - Jackpot amount
  - Number of winners per tier
- [ ] Store in local database (SQLite for dev, Postgres for prod)
- [ ] Build data validation and deduplication logic
- [ ] Seed database with at least 5 years of historical results

### 1.3 Supplementary Data Sources
- [ ] Planetary position data (Swiss Ephemeris or astronomy API)
- [ ] Moon phase data (mapped to draw dates)
- [ ] Calendar/date metadata (day of week, season, holidays)
- [ ] Basic numerology reference tables

**Phase 1 Deliverable:** A populated database of lottery results with supplementary data, accessible via a clean internal API.

---

## Phase 2 — Agent Architecture

**Goal:** Build the multi-agent system with distinct personalities and reasoning frameworks.

### 2.1 Agent Framework
- [ ] Design base agent interface:
  - `analyse(draw_history, context)` — produce analysis
  - `predict(context)` — generate picks with reasoning
  - `challenge(other_agent_analysis)` — critique another agent's logic
  - `defend(challenge)` — respond to criticism
- [ ] Implement agent registry (discover, load, configure agents)
- [ ] Build prompt templates per agent with strong personality voices

### 2.2 Core Agents

#### The Mathematician
- [ ] Frequency analysis (hot/cold numbers over configurable windows)
- [ ] Gap analysis (overdue numbers, expected vs actual appearance)
- [ ] Pair and triplet correlation analysis
- [ ] Distribution and chi-square testing
- [ ] Trend detection (moving averages on number frequency)
- [ ] Personality: precise, evidence-based, mildly condescending toward non-statistical approaches

#### The Numerologist
- [ ] Root number reduction of draw results
- [ ] Date-to-number mapping (draw dates, significant calendar dates)
- [ ] Life path number correlations
- [ ] Master number detection (11, 22, 33)
- [ ] Sacred geometry pattern matching
- [ ] Personality: mystical but structured, speaks with quiet certainty

#### The Astrologer
- [ ] Map planetary positions to each draw date
- [ ] Moon phase correlation analysis
- [ ] Zodiac cycle alignment with number ranges
- [ ] Retrograde period impact analysis
- [ ] Planetary aspect patterns (conjunctions, oppositions, trines)
- [ ] Personality: cosmic, dramatic, references celestial events constantly

#### The Psychic
- [ ] Pattern "intuition" based on energy clusters in recent draws
- [ ] Dream-logic connections between numbers
- [ ] Vibrational frequency analysis (creative interpretation layer)
- [ ] "Feeling" based weighting of numbers
- [ ] Personality: ethereal, speaks in sensations and impressions, occasionally cryptic

#### The Gambler
- [ ] Streak and momentum theory
- [ ] Gut-feel heuristics based on recent draws
- [ ] Superstition rules (lucky numbers, avoidance patterns)
- [ ] Risk appetite modelling (safe picks vs long shots)
- [ ] Personality: bold, confident, street-smart, talks like they've "been around"

#### The Skeptic
- [ ] Statistical debunking of other agents' claims
- [ ] Confirmation bias detection
- [ ] Base rate reminders (actual odds calculation)
- [ ] Random vs pattern distinction testing
- [ ] Personality: dry, witty, takes pleasure in dismantling arguments

### 2.3 Agent Configuration
- [ ] Each agent defined via config file (persona prompt, tools, data access, voice)
- [ ] Support for user-created custom agents (stretch goal)
- [ ] Agent weighting system (user can trust some agents more than others)

**Phase 2 Deliverable:** Six working agents, each capable of independent analysis and generating picks with personality-driven reasoning.

---

## Phase 3 — Debate Engine & Synthesis

**Goal:** Orchestrate multi-agent debates and produce unified output.

### 3.1 Debate Orchestration
- [ ] Design debate flow:
  1. Each agent analyses independently
  2. Agents review each other's analysis
  3. Challenge/defend rounds (configurable depth: 1-3 rounds)
  4. Final positions stated
- [ ] Implement turn management and context passing between agents
- [ ] Build debate transcript formatter (readable, entertaining output)
- [ ] Add timeout/token budget controls per agent per round

### 3.2 Synthesis Layer
- [ ] Collect final picks from all agents
- [ ] Apply user-defined agent weightings
- [ ] Identify convergence points (where multiple agents accidentally agree)
- [ ] Generate consensus picks with per-agent confidence breakdown
- [ ] Produce "dissent report" (where agents strongly disagree and why)

### 3.3 Analysis Modes
- [ ] **Post-Draw Analysis** — "Why did these numbers come up?" (each agent explains through their lens)
- [ ] **Pre-Draw Prediction** — "What numbers for the next draw?" (each agent picks and defends)
- [ ] **Historical Deep Dive** — "Analyse draws from [date range]" (trend analysis across perspectives)
- [ ] **Head-to-Head** — "Mathematician vs Astrologer on last 100 draws" (targeted debate)

### 3.4 Scoring & Track Record
- [ ] Track each agent's prediction accuracy over time
- [ ] Leaderboard: which agent has been closest to actual results
- [ ] Per-agent hit rate on individual numbers
- [ ] "I told you so" moments — when an agent's unlikely pick actually hits

**Phase 3 Deliverable:** A working debate engine that produces entertaining, multi-perspective analysis with consensus picks and agent track records.

---

## Phase 4 — User Interface

**Goal:** Build an engaging frontend that brings the agent debates to life.

### 4.1 Core UI
- [ ] Dashboard: upcoming draws, recent results, agent leaderboard
- [ ] Draw analysis view: animated agent debate with speech bubbles/cards
- [ ] Prediction view: each agent's picks displayed with reasoning
- [ ] Consensus panel: weighted picks with visual breakdown
- [ ] Historical explorer: browse past draws and agent analysis

### 4.2 Agent Interaction
- [ ] Agent profile cards (avatar, personality summary, track record)
- [ ] User agent weighting sliders
- [ ] "Ask an agent" — direct question to a specific agent about a number/draw
- [ ] Debate replay — step through a debate round by round

### 4.3 User Features
- [ ] User accounts and saved preferences
- [ ] Custom number watchlists
- [ ] Notification: "Your agents have analysed tonight's draw"
- [ ] Share analysis to social media
- [ ] Dark/light mode

### 4.4 Tech Stack (Proposed)
- Frontend: React or Next.js
- Styling: Tailwind CSS
- State management: Zustand or React Context
- Animations: Framer Motion (for debate sequences)

**Phase 4 Deliverable:** A polished, interactive web UI that makes agent debates engaging and shareable.

---

## Phase 5 — API & Integration

**Goal:** Expose functionality via API and connect to live data.

### 5.1 REST/GraphQL API
- [ ] Endpoints:
  - `GET /draws` — historical results with filters
  - `GET /draws/:id/analysis` — agent analysis for a specific draw
  - `POST /predict` — trigger prediction for next draw
  - `GET /agents` — list agents and their track records
  - `GET /agents/:id/picks` — specific agent's pick history
  - `POST /debate` — trigger a debate on a topic/draw
- [ ] Authentication (API keys for external access)
- [ ] Rate limiting and caching

### 5.2 Live Data Feeds
- [ ] Auto-fetch new draw results on draw nights
- [ ] Trigger automatic agent analysis post-draw
- [ ] Scheduled pre-draw predictions (e.g., 24 hours before draw)
- [ ] Webhook support for new analysis notifications

### 5.3 Multi-Lottery Support
- [ ] Abstract lottery configuration (different number ranges, bonus balls, draw frequencies)
- [ ] Add support for multiple lotteries (UK, EU, US, etc.)
- [ ] Per-lottery agent calibration

**Phase 5 Deliverable:** A production-ready API with live data integration and multi-lottery support.

---

## Phase 6 — Polish & Launch

**Goal:** Harden, test, and ship.

### 6.1 Testing
- [ ] Unit tests for all agent analysis logic
- [ ] Integration tests for debate orchestration
- [ ] End-to-end tests for API and UI flows
- [ ] Agent personality consistency tests (voice stays in character)
- [ ] Load testing for concurrent debate sessions

### 6.2 Observability
- [ ] Logging: structured logs for all agent interactions
- [ ] Monitoring: API health, LLM latency, error rates
- [ ] Cost tracking: LLM token usage per debate/analysis
- [ ] Analytics: which agents users trust most, popular features

### 6.3 Deployment
- [ ] Containerise (Docker)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Staging environment
- [ ] Production deployment (cloud provider TBD)
- [ ] Domain and SSL

### 6.4 Documentation
- [ ] User guide
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Agent authoring guide (for custom agents)
- [ ] Contributing guidelines

**Phase 6 Deliverable:** A tested, deployed, documented application ready for users.

---

## Future Ideas (Post-Launch)

- **Custom Agent Builder** — users create their own analyst personas
- **Sports/Events Mode** — same multi-agent debate framework applied to sports predictions
- **Geopolitics Mode** — pivot the same engine to the scenario analysis app discussed earlier
- **Mobile App** — React Native or Flutter wrapper
- **Community Predictions** — users submit their own picks, tracked alongside agents
- **Voice Mode** — agents speak their analysis (TTS with distinct voices)
- **Twitch/YouTube Integration** — live-stream agent debates before draws

---

## Technical Decisions (To Be Made)

| Decision | Options | Notes |
|---|---|---|
| Language | Python / TypeScript | Python has better data science libs; TS for full-stack JS |
| LLM Provider | Claude API / OpenAI / Local | Claude recommended for personality/reasoning quality |
| Database | SQLite / Postgres | SQLite for dev, Postgres for prod |
| Vector Store | pgvector / Chroma / Qdrant | If RAG needed for historical context |
| Hosting | Vercel / Railway / AWS | Depends on scale expectations |
| Frontend | Next.js / SvelteKit | TBD based on team preference |

---

*This is a living document. Update as decisions are made and phases are completed.*
