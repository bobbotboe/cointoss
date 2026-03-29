# CoinToss — Multi-Agent Lottery Analysis Engine

Six AI personas debate and analyse lottery results through mathematics, numerology, astrology, and more.

> **Disclaimer:** This application is for entertainment purposes only. Lottery draws are random. No combination of mathematics, astrology, or psychic energy changes the odds. Play responsibly.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/settings/keys)

### Setup

```bash
git clone https://github.com/bobbotboe/cointoss.git
cd cointoss

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Create Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install frontend dependencies
cd ui && npm install && cd ..

# Initialise database and import lottery data
python3 -m cointoss.cli init
python3 -m cointoss.cli import-us
```

### Run

```bash
# Option 1: Single command
./start.sh

# Option 2: Manual (two terminals)
# Terminal 1 — API
source .venv/bin/activate
python3 -m uvicorn cointoss.api.main:app --port 3005

# Terminal 2 — Frontend
cd ui && npm run dev
```

Open **http://localhost:5177** in your browser.

### Docker

```bash
docker compose up --build
```

Open **http://localhost:3005**.

---

## Supported Lotteries

### Australian (via The Lott)

| Lottery | Numbers | Draw Days |
|---|---|---|
| Oz Lotto | 7 from 1-45 + 2 supp | Tuesday |
| Powerball AU | 7 from 1-35 + PB 1-20 | Thursday |
| Saturday Lotto | 6 from 1-45 + 2 supp | Saturday |
| Mon & Wed Lotto | 6 from 1-45 + 2 supp | Monday, Wednesday |
| Set for Life | 7 from 1-44 + 2 bonus | Daily |

### American (via NY Open Data)

| Lottery | Numbers | Draw Days |
|---|---|---|
| Powerball US | 5 from 1-69 + PB 1-26 | Mon, Wed, Sat |
| Mega Millions | 5 from 1-70 + MB 1-25 | Tue, Fri |
| Lotto America | 5 from 1-52 + SB 1-10 | Mon, Wed, Sat |
| Cash4Life | 5 from 1-60 + CB 1-4 | Daily |

---

## The Agents

| Agent | Emoji | Approach |
|---|---|---|
| **The Mathematician** | 🎲 | Frequency analysis, gap detection, chi-square testing |
| **The Numerologist** | 🔢 | Root numbers, sacred geometry, vibrational cycles |
| **The Astrologer** | ⭐ | Planetary positions, moon phases, zodiac alignment |
| **The Psychic** | 🔮 | Energy clusters, intuitive readings, vibrational sensing |
| **The Gambler** | 🎰 | Streak theory, gut instinct, superstition |
| **The Skeptic** | 📊 | Debunking, probability reality checks, rational picks |

---

## CLI Reference

### Data Commands

```bash
# Initialise database
python3 -m cointoss.cli init

# Import lottery data
python3 -m cointoss.cli import-us                          # All US lotteries
python3 -m cointoss.cli import-us --lottery powerball_us    # Specific lottery
python3 -m cointoss.cli import-us --since 2025-01-01        # Since date
python3 -m cointoss.cli import-au                           # All AU lotteries (web)
python3 -m cointoss.cli import-au --csv data.csv --lottery oz_lotto  # From CSV
python3 -m cointoss.cli import-lotto-america

# Celestial data (for Astrologer agent)
python3 -m cointoss.cli celestial --start 2020-01-01 --end 2026-03-29

# Data health
python3 -m cointoss.cli validate
python3 -m cointoss.cli stats
python3 -m cointoss.cli stats --country AU
python3 -m cointoss.cli frequency powerball_us
python3 -m cointoss.cli frequency powerball_us --last 50
```

### Agent Commands

```bash
# List agents
python3 -m cointoss.cli agents

# Single agent analysis
python3 -m cointoss.cli analyse powerball_us --agent mathematician
python3 -m cointoss.cli analyse mega_millions --agent psychic

# All agents analyse (quick, no debate)
python3 -m cointoss.cli predict powerball_us

# Full debate with challenge/defense rounds
python3 -m cointoss.cli debate powerball_us
python3 -m cointoss.cli debate powerball_us --agents mathematician,skeptic
python3 -m cointoss.cli debate powerball_us --rounds 2

# Post-draw analysis (agents explain actual results)
python3 -m cointoss.cli post-draw powerball_us --date 2026-03-25
```

### Scoring Commands

```bash
# Score predictions against actual results
python3 -m cointoss.cli score
python3 -m cointoss.cli score --lottery powerball_us

# View leaderboard
python3 -m cointoss.cli leaderboard
python3 -m cointoss.cli leaderboard --lottery powerball_us

# "I told you so" moments (3+ hits)
python3 -m cointoss.cli told-you-so
```

---

## Web UI

The web interface has four pages:

### Dashboard
- Lottery stats cards showing draw counts, date ranges, and latest numbers
- Agent leaderboard ranked by average hit accuracy

### Predict
- Select a lottery from the dropdown
- Click "Run All Agents" — 6 agents analyse independently
- View consensus picks with convergence analysis
- Each agent's full analysis and reasoning displayed in cards

### Debate Arena
- Select a lottery and optionally choose specific agents
- Set debate depth (1-3 challenge/defense rounds)
- Step through the debate round by round
- View consensus picks and agent agreement/dissent

### Agents
- Agent profile cards with emoji, name, and approach description
- Click any agent to view their track record (predictions, accuracy, best hits)

---

## API Endpoints

The API runs on port 3005. Interactive docs at **http://localhost:3005/docs**.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/lotteries` | List all lotteries |
| GET | `/api/lotteries/{id}/stats` | Stats for a lottery |
| GET | `/api/draws/{id}` | Historical draws |
| GET | `/api/draws/{id}/latest` | Latest draw result |
| GET | `/api/draws/{id}/frequency` | Number frequency data |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}` | Agent detail + track record |
| GET | `/api/leaderboard` | Agent rankings |
| GET | `/api/told-you-so` | Predictions with 3+ hits |
| POST | `/api/predict` | Run all agents, get consensus |
| POST | `/api/debate` | Full multi-agent debate |
| POST | `/api/score` | Score predictions vs results |

### Example: Quick Prediction

```bash
curl -X POST http://localhost:3005/api/predict \
  -H "Content-Type: application/json" \
  -d '{"lottery_id": "powerball_us"}'
```

### Example: Debate

```bash
curl -X POST http://localhost:3005/api/debate \
  -H "Content-Type: application/json" \
  -d '{
    "lottery_id": "powerball_us",
    "agent_ids": ["mathematician", "gambler", "skeptic"],
    "rounds": 2
  }'
```

---

## Importing Australian Data via CSV

The Lott doesn't provide a public API, so bulk AU historical data is best imported from CSV files (available on Kaggle).

**Expected CSV formats:**

```csv
Draw,Date,N1,N2,N3,N4,N5,N6,N7,S1,S2
4501,01/01/2025,3,7,12,18,25,33,41,9,22
```

Or:

```csv
DrawNumber,DrawDate,WinningNumbers,Supplementary
4501,2025-01-01,3 7 12 18 25 33 41,9 22
```

```bash
python3 -m cointoss.cli import-au --csv path/to/data.csv --lottery oz_lotto
```

Supported lottery IDs: `oz_lotto`, `powerball_au`, `saturday_lotto`, `mon_wed_lotto`, `set_for_life`.

---

## How Scoring Works

1. Agents make predictions via `predict` or `debate` — picks are saved to the database
2. After the actual draw happens, import the new results: `python3 -m cointoss.cli import-us`
3. Score predictions: `python3 -m cointoss.cli score`
4. View results: `python3 -m cointoss.cli leaderboard`

The system tracks:
- **Main hits** — how many of the agent's picks matched actual numbers
- **Bonus hits** — whether the bonus number was correct
- **"I told you so"** — any prediction with 3+ main number hits

---

## Project Structure

```
cointoss/
├── cointoss/
│   ├── agents/          # 6 AI analyst agents
│   │   ├── base.py      # BaseAgent interface
│   │   ├── registry.py  # Agent discovery and context building
│   │   ├── mathematician.py
│   │   ├── numerologist.py
│   │   ├── astrologer.py
│   │   ├── psychic.py
│   │   ├── gambler.py
│   │   └── skeptic.py
│   ├── data/
│   │   ├── models.py    # SQLAlchemy models (Lottery, Draw, Prediction, etc.)
│   │   ├── database.py  # DB init and session management
│   │   ├── queries.py   # Internal query API
│   │   ├── validation.py
│   │   ├── celestial.py # Moon phases and planetary positions
│   │   └── importers/   # Data importers (NY Open Data, The Lott, CSV)
│   ├── engine/
│   │   ├── debate.py    # Multi-agent debate orchestrator
│   │   ├── synthesis.py # Consensus picks and convergence analysis
│   │   ├── scoring.py   # Prediction tracking and leaderboard
│   │   ├── modes.py     # Pre-draw, post-draw, head-to-head modes
│   │   └── scheduler.py # Auto-fetch and auto-score scheduler
│   ├── api/
│   │   ├── main.py      # FastAPI app
│   │   └── routes/      # REST endpoints
│   ├── cli.py           # CLI with 16 commands
│   └── config.py        # Settings (env vars / .env file)
├── ui/                  # React + Vite + Tailwind frontend
├── tests/               # 19 tests
├── Dockerfile
├── docker-compose.yml
├── start.sh             # Dev startup script
└── PHASE-BUILD.md       # Original build plan
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `DATABASE_URL` | No | SQLite path (default: `./cointoss.db`) |
| `NY_OPEN_DATA_APP_TOKEN` | No | Increases rate limits on data.ny.gov |
| `LLM_MODEL` | No | Claude model to use (default: `claude-sonnet-4-20250514`) |

---

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

19 tests covering models, database queries, synthesis logic, and agent registration.

---

## License

MIT
