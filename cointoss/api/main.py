"""CoinToss FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from cointoss.data.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Import agents to trigger registration
    import cointoss.agents  # noqa: F401
    yield


app = FastAPI(
    title="CoinToss",
    description="Multi-Agent Lottery Analysis Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from cointoss.api.routes import agents, draws, predictions  # noqa: E402

app.include_router(draws.router, prefix="/api", tags=["draws"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "cointoss"}


# Serve static frontend in production (Docker)
static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
